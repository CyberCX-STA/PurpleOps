import os
import csv
import json
import yaml
import shutil
from model import *
from flask_security import auth_required, current_user, roles_accepted
from flask import Blueprint, request, session, send_from_directory

blueprint_assessment_export = Blueprint('blueprint_assessment_export', __name__)

@blueprint_assessment_export.route('/assessment/export/<filetype>/<id>',methods = ['GET'])
@auth_required()
def exportassessment(filetype, id):
    session["assessmentid"] = id
    tests = TestCase.objects(assessmentid=id).all()
    if "ids" in request.args:
        ids = request.args.get("ids").split(",")
        selectTests = []
        for test in tests:
            if str(test.id) in ids:
                selectTests.append(test)
        tests = selectTests
    elif current_user.has_role("Blue"):
        selectTests = [t for t in tests if t.visible]
        tests = selectTests
    ass = Assessment.objects(id=id).first()
    rowsJSON = []
    rowsCSV = []

    for test in tests:
        df = {
            "Mitre ID": test["mitreid"],
            "Name": test["name"],
            "Tactic": test["tactic"],
            "State": test["state"],
            "Modified Time": str(test["modifytime"]),
            "Start Time": str(test["starttime"]),
            "End Time": str(test["endtime"]),
            "Source(s)": [[k["name"] for k in ass["sources"] if str(k["id"]) == i][0] for i in test["sources"]], 
            "Target(s)": [[k["name"] for k in ass["targets"] if str(k["id"]) == i][0] for i in test["targets"]],
            "Red Tool(s)": [[k["name"] for k in ass["tools"] if str(k["id"]) == i][0] for i in test["tools"]],
            "Objective": test["objective"],
            "Actions": test["actions"],
            "Red Notes": test["rednotes"],
            "Red Evidence": [i["path"] + "|" + i["caption"] for i in test["redfiles"]],
            "Prevented": test["prevented"],
            "Prevented Rating": test["preventedrating"],
            "Alerted": test["alerted"],
            "Alert Severity": test["alertseverity"],
            "Logged": test["logged"],
            "Detection Rating": test["detectionrating"],
            "Detection Time": str(test["detecttime"]),
            "Priority": test["priority"],
            "Priority Urgency": test["priorityurgency"],
            "Control(s)": [[k["name"] for k in ass["controls"] if str(k["id"]) == i][0] for i in test["controls"]],
            "Tags": [[k["name"] for k in ass["tags"] if str(k["id"]) == i][0] for i in test["tags"]],
            "Observations": test["bluenotes"],
            "Blue Evidence": [i["path"] + "|" + i["caption"] for i in test["bluefiles"]],
            "Visible": test["visible"]
        }
          
        # Keep JSON arrays as is, but flatten for CSV
        rowsJSON.append(df.copy())

        for field in ["Source(s)", "Target(s)", "Red Tool(s)", "Red Evidence", "Tags", "Blue Evidence", "Control(s)"]:
            df[field] = ",".join(df[field])
        rowsCSV.append(df)

    if not os.path.exists(f"files/{id}"):
        os.makedirs(f"files/{id}")

    with open(f'files/{id}/export.json', 'w') as f:
        json.dump(rowsJSON, f)

    with open(f'files/{id}/export.csv', 'w', encoding='UTF8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=rowsJSON[0].keys())
        writer.writeheader()
        writer.writerows(rowsCSV)
    
    if filetype in ["csv", "json"]:
        return send_from_directory('files', f"{id}/export.{filetype}", as_attachment=True)
    
    return ("", 204)

@blueprint_assessment_export.route('/assessment/export/template/<id>',methods = ['GET'])
@auth_required()
@roles_accepted('Admin', 'Red')
def exporttemplate(id):
    session["assessmentid"] = id
    tests = TestCase.objects(assessmentid=id).all()
    ass = Assessment.objects(id=id).first()

    if "ids" in request.args:
        ids = request.args.get("ids").split(",")
        selectTests = []
        for test in tests:
            if str(test.id) in ids:
                selectTests.append(test)
        tests = selectTests

    rowsJSON = []

    fields = ["mitreid", "tactic", "name", "objective", "actions", "tools", "tags"]

    for test in tests:
        df = {}
        for field in fields:
            if field == "tools":
                df[field] = []
                for toolID in test[field]:
                    df[field].append([t["name"] for t in ass["tools"] if str(t["id"]) == toolID][0])
            elif field == "tags":
                df[field] = []
                for tagID in test[field]:
                    try:
                        df[field].append([t["name"] for t in ass["tags"] if str(t["id"]) == tagID][0])
                    except IndexError:
                        # Tag was deleted but there's still a reference to it, thus we can ignore it
                        pass
            else:
                df[field] = test[field]
        rowsJSON.append(df)

    if not os.path.exists(f"files/{id}"):
        os.makedirs(f"files/{id}")

    with open(f'files/{id}/template.json', 'w') as f:
        json.dump(rowsJSON, f)
    
    return send_from_directory('files', f"{id}/template.json", as_attachment=True)

@blueprint_assessment_export.route('/assessment/export/atomics/<id>',methods = ['GET'])
@auth_required()
@roles_accepted('Admin', 'Red')
def exportatomics(id):
    session["assessmentid"] = id
    tests = TestCase.objects(assessmentid=id).all()
    ass = Assessment.objects(id=id).first()

    if "ids" in request.args:
        ids = request.args.get("ids").split(",")
        selectTests = []
        for test in tests:
            if str(test.id) in ids:
                selectTests.append(test)
        tests = selectTests

    big = ""

    for test in tests:
        atomics = {"tests": []}
        testcase = {}
        if test["name"]: testcase["name"] = test["name"]
        if test["objective"]: testcase["description"] = test["objective"]
        if test["actions"]: testcase["command"] = test["actions"]
        if test["rednotes"]: testcase["notes"] = test["rednotes"]
        if test["priority"]: testcase["priority"] = test["priority"]
        tags = []
        for tag in test["tags"]:
            tags.append([t["name"] for t in ass["tags"] if str(t["id"]) == tag][0])
        if tags: testcase["tags"] = tags
        atomics["tests"].append(testcase)
        big += "\n\n\n\n"
        big += test["mitreid"] + "\n\n"
        big += yaml.dump(atomics, sort_keys=False)

    if not os.path.exists(f"files/"):
        os.makedirs(f"files")

    with open(f'files/atomics.yaml', 'w') as f:
        f.write(big)
        
    return send_from_directory('files', f"atomics.yaml", as_attachment=True)

def exportmeta(id):
    ass = Assessment.objects(id=id).first()

    if not os.path.exists(f"files/"):
        os.makedirs(f"files")

    with open(f'files/{id}/meta.json', 'w') as f:
        json.dump(ass.to_json(), f)

@blueprint_assessment_export.route('/assessment/export/entire/<id>',methods = ['GET'])
@auth_required()
@roles_accepted('Admin', 'Red')
def exportentire(id):
    session["assessmentid"] = id
    name = Assessment.objects(id=id).first()["name"]

    exporttemplate(id)
    exportassessment("csv", id)
    exportmeta(id)

    shutil.make_archive("files/" + id, 'zip', "files/" + id)
    
    return send_from_directory('files', f"{id}.zip", as_attachment=True, download_name=f"{name}.zip")
