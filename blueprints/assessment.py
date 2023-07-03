import os
import csv
import json
import yaml
import shutil
from copy import deepcopy
from model import *
from utils import applyFormData
from flask_security import auth_required, current_user, roles_accepted
from flask import Blueprint, render_template, redirect, request, session, send_from_directory

blueprint_assessment = Blueprint('blueprint_assessment', __name__)

@blueprint_assessment.route('/assessment/new', methods = ['POST'])
@auth_required()
@roles_accepted('Admin', 'Red')
def newassessment():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        assessment = Assessment(name=name, description=description)

        fields = ["industry", "techmaturity", "opmaturity", "socmodel", "socprovider", "webhook"]
        assessment = applyFormData(assessment, request.form, fields)

        tools = []
        with open('sampledata/tools.json', 'r') as f:
            toolJSON = json.load(f)
        for tool in toolJSON:
            t = Tool(name=tool["name"], description=tool["description"])
            tools.append(t)
        assessment.tools = tools

        controls = []
        with open('sampledata/controls.json', 'r') as f:
            controlJSON = json.load(f)
        for control in controlJSON:
            c = Control(name=control["name"], description=control["description"])
            controls.append(c)
        assessment.controls = controls

        assessment.save()
        return jsonify({"id": str(assessment.id)})

@blueprint_assessment.route('/assessment/update/<id>', methods = ['POST'])
@auth_required()
@roles_accepted('Admin', 'Red')
def updateassessment(id):
    if request.method == 'POST':
        ass = Assessment.objects(id=id).first()
        
        fields = ["name", "description", "industry", "techmaturity", "opmaturity", "socmodel", "socprovider", "webhook"]
        ass = applyFormData(ass, request.form, fields)

        ass.save()
        return ('', 204)

@blueprint_assessment.route('/assessment/clone/<id>', methods = ['GET'])
@auth_required()
@roles_accepted('Admin', 'Red')
def duplicateassessment(id):
    if request.method == 'GET':
        ass = Assessment.objects(id=id).first()
        newAss = deepcopy(ass)
        newAss.id = None
        newAss.name = "Copy of " + ass.name
        newAss.save()

        tests = TestCase.objects(assessmentid=id)
        for test in tests:
            newcase = TestCase()
            newcase.assessmentid=str(newAss.id)

            copy = ["name", "overview", "objective", "actions", "advice", "rednotes", "mitreid", "phase", "tools", "references", "kbentry"]
            for field in copy:
                newcase[field] = test[field]

            newcase.save()

        return jsonify({"id": str(newAss.id)})



@blueprint_assessment.route('/assessment/delete/<id>',methods = ['GET'])
@auth_required()
@roles_accepted('Admin', 'Red')
def deleteassessment(id):
    TestCase.objects(assessmentid=id).delete()
    Assessment.objects(id=id).delete()
    return redirect(f"/")


@blueprint_assessment.route('/assessment/run/<id>',methods = ['GET'])
@auth_required()
def loadassessment(id):
    session["assessmentid"] = id
    tests = TestCase.objects(assessmentid=id).all()
    ass = Assessment.objects(id=id).first()
    templates = TestCaseTemplate.objects()
    mitres = [[m["mitreid"], m["name"]] for m in Technique.objects()]
    mitres.sort(key=lambda x: x[0])
    tactics = {}
    count = 1
    for t in tests:
        if not t.phase in tactics.keys():
            tactics[t.phase] = count
            count += 1

    stats = generatestats(tests, ass)

    return render_template('assessment.assessment.html', tests=tests, ass=ass, templates=templates, mitres=mitres, stats=stats) 

def generatestats(tests, ass):
    # Initalise metrics that are captured
    stats = {
        "All": {
            "blocked": 0,
            "alerted": 0,
            "logged": 0,
            "missed": 0,

            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "informational": 0,

            "scoresPrevent": [],
            "scoresDetect": [],

            "priorityType": [],
            "priorityUrgency": [],

            "controls": []
        }
    }

    # What MITRE tactics do we currently have data for?
    activeTactics = list(set([t["phase"] for t in tests if t["state"] == "Complete"]))

    for testcase in tests:
        if testcase["phase"] in activeTactics:
            # Initalise phase if not in the dataframe yet
            if testcase["phase"] not in stats:
                stats[testcase["phase"]] = deepcopy(stats["All"])

            # Populate blocked/alerted/logged/missed stats
            # NOTE: If a testcase is both alerted and blocked, it will be
            # counted twice
            if testcase["blocked"] == "Yes" or testcase["blocked"] == "Partial":
                stats[testcase["phase"]]["blocked"] += 1

            if testcase["alerted"] == "Yes":
                stats[testcase["phase"]]["alerted"] += 1
                if testcase["alertseverity"]:
                    stats[testcase["phase"]][testcase["alertseverity"].lower()] += 1

            if testcase["logged"] == "Yes":
                stats[testcase["phase"]]["logged"] += 1

            if testcase["blocked"] == "No" and testcase["alerted"] == "No" and testcase["logged"] == "No":
                stats[testcase["phase"]]["missed"] += 1

            # Store scores to later average with
            stats[testcase["phase"]]["scoresPrevent"].append(float(testcase["blockedrating"] or "0.0"))
            stats[testcase["phase"]]["scoresDetect"].append(float(testcase["detectionrating"] or "0.0"))

            # Collate priorities, ratings and blue tools
            if testcase["priority"]:
                stats[testcase["phase"]]["priorityType"].append(testcase["priority"])
            if testcase["priorityurgency"]:
                stats[testcase["phase"]]["priorityUrgency"].append(testcase["priorityurgency"])
            if testcase["controls"]:
                names = [[k["name"] for k in ass["controls"] if str(k["id"]) == i][0] for i in testcase["controls"]]
                stats[testcase["phase"]]["controls"].extend(names)

    # We've populated per-tactic data, this function adds it all together for
    # an "All" tactic
    for tactic in stats:
        if tactic == "All":
            continue
        for key in ["blocked", "alerted", "logged", "missed", "critical", "high", "medium", "low", "informational"]:
            stats["All"][key] += stats[tactic][key]
        for key in ["scoresPrevent", "scoresDetect", "priorityType", "priorityUrgency", "controls"]:
            stats["All"][key].extend(stats[tactic][key])

    return stats

@blueprint_assessment.route('/assessment/stats/<id>',methods = ['GET'])
@auth_required()
def assessmentstats(id):
    session["assessmentid"] = id
    tests = TestCase.objects(assessmentid=id).all()
    ass = Assessment.objects(id=id).first()
    mitres = [[m["mitreid"], m["name"]] for m in Technique.objects()]
    mitres.sort(key=lambda x: x[0])
    
    stats = generatestats(tests, ass)

    return render_template('assessment.stats.html', stats=stats, assid=id) 

@blueprint_assessment.route('/assessment/<field>/<id>',methods = ['POST', 'GET'])
@auth_required()
def manageengagmentdata(field, id):
    assessment = Assessment.objects(id=id).first()
    if field not in ["sources", "targets", "tools", "controls", "tags"]:
        return ('', 418)
    if request.method == 'POST':
        if current_user.has_role("Spectator"):
            return ('', 204)
        delFieldIDs = [str(item.id) for item in assessment[field]]
        for item in request.json:
            # New item
            if str(item["id"]) == "0":
                if field == "sources":
                    newObj = Source(name=item["name"], description=item["description"])
                elif field == "targets":
                    newObj = Target(name=item["name"], description=item["description"])
                elif field == "tools":
                    newObj = Tool(name=item["name"], description=item["description"])
                elif field == "controls":
                    newObj = Control(name=item["name"], description=item["description"])
                elif field == "tags":
                    if "colour" not in item:
                        item["colour"] = "#ff0000"
                    newObj = Tag(name=item["name"], colour=item["colour"])
                assessment[field].append(newObj)
                assessment[field].save()
            # Update old
            else:
                delFieldIDs.remove(item["id"])
                oldObj = assessment[field].filter(id=item["id"]).first()
                oldObj.name = item["name"]
                if field != "tags":
                    oldObj.description = item["description"]
                else:
                    oldObj.colour = item["colour"] or "#000"
                assessment[field].save()
        for delID in delFieldIDs:
            if field == "sources":
                assessment.update(pull__sources__id=delID)
            elif field == "targets":
                assessment.update(pull__targets__id=delID)
            elif field == "tools":
                assessment.update(pull__tools__id=delID)
            elif field == "controls":
                assessment.update(pull__controls__id=delID)
            elif field == "tags":
                assessment.update(pull__tags__id=delID)
        return ('', 204)
    else:
        return assessment.to_json_data(field)


@blueprint_assessment.route('/assessment/export/<filetype>/<id>',methods = ['GET'])
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
            "Phase": test["phase"],
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
            "Blocked": test["blocked"],
            "Blocked Rating": test["blockedrating"],
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

@blueprint_assessment.route('/assessment/export/template/<id>',methods = ['GET'])
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

    fields = ["mitreid", "phase", "name", "objective", "actions", "tools", "tags"]

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

@blueprint_assessment.route('/assessment/export/atomics/<id>',methods = ['GET'])
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

@blueprint_assessment.route('/assessment/export/entire/<id>',methods = ['GET'])
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

@blueprint_assessment.route('/assessment/import/template/<id>', methods = ['POST'])
@auth_required()
@roles_accepted('Admin', 'Red')
def importtemplate(id):
    ass = Assessment.objects(id=id).first()

    f = request.files['file']
    tests = json.loads(f.read())

    fields = ["mitreid", "phase", "name", "objective", "actions", "tools", "tags"]

    for test in tests:
        tc = TestCase()
        for field in fields:
            if field in test:
                if field == "tools":
                    tc[field] = []
                    for tool in test[field]:
                        if not tool in [t["name"] for t in ass["tools"]]:
                            newTool = Tool(name=tool, description="")
                            ass.tools.append(newTool)
                            ass.tools.save()
                        tc[field].append([str(t["id"]) for t in ass["tools"] if str(t["name"]) == tool][0])
                elif field == "tags":
                    tc[field] = []
                    for tag in test[field]:
                        if not tag in [t["name"] for t in ass["tags"]]:
                            newTag = Tag(name=tag, colour="#ff0000")
                            ass.tags.append(newTag)
                            ass.tags.save()
                        tc[field].append([str(t["id"]) for t in ass["tags"] if str(t["name"]) == tag][0])
                            
                else:
                    tc[field] = test[field]
        tc.assessmentid = str(ass["id"])
        tc.provider = "TMPL"
        if KnowlegeBase.objects(mitreid=tc.mitreid):
                tc.kbentry = True
        tc.save()
    
    return redirect(request.referrer)

@blueprint_assessment.route('/assessment/import/entire', methods = ['POST'])
@auth_required()
@roles_accepted('Admin', 'Red')
def importentire():
    newA = Assessment(name="Importing...")
    newA.save()
    newAID = str(newA.id)

    os.makedirs(f"files/{newAID}/tmp")
    f = request.files['file']
    f.save(f"files/{newAID}/tmp/entire.zip")
    shutil.unpack_archive(f"files/{newAID}/tmp/entire.zip", f"files/{newAID}/tmp/", "zip")

    with open(f"files/{newAID}/tmp/meta.json", 'r') as f:
        meta = json.load(f)
    for key in meta:
        newA[key] = meta[key]
    newA.save()

    engagmentWide = {
        "sources": {},
        "targets": {},
        "tools": {},
        "controls": {},
        "tags": {}
    }
    directs = {
        "Mitre ID": "mitreid",
        "Name": "name",
        "Phase": "phase",
        "Name": "name",
        "State": "state",
        "Objective": "objective",
        "Actions": "actions",
        "Red Notes": "rednotes",
        "Blocked": "blocked",
        "Blocked Rating": "blockedrating",
        "Alerted": "alerted",
        "Alert Severity": "alertseverity",
        "Logged": "logged",
        "Detection Rating": "detectionrating",
        "Priority": "priority",
        "Priority Urgency": "priorityurgency",
        "Observations": "bluenotes",
        "Visible": "visible",
    }
    times = {
        "Modified Time": "modifytime",
        "Start Time": "starttime",
        "End Time": "endtime",
        "Detection Time": "detecttime"
    }
    multis = {
        "Source(s)": "sources",
        "Target(s)": "targets",
        "Red Tool(s)": "tools",
        "Control(s)": "controls",
        "Tags": "tags",
    }
    files = {
        "Red Evidence": "redfiles",
        "Blue Evidence": "bluefiles"
    }

    with open(f"files/{newAID}/tmp/export.json", 'r') as f:
        export = json.load(f)

    for oldT in export:
        newT = TestCase()
        newT.assessmentid = newAID
        newT.save()
        newTID = str(newT.id)

        if KnowlegeBase.objects(mitreid=oldT["Mitre ID"]):
            newT.kbentry = True

        for key in directs:
            newT[directs[key]] = oldT[key]

        for key in times:
            if oldT[key] and oldT[key] != "None":
                oldT[key] = oldT[key].split(".")[0]
                newT[times[key]] = datetime.datetime.strptime(oldT[key], "%Y-%m-%d %H:%M:%S")

        for key in multis:
            newT[multis[key]] = []
            for multi in oldT[key]:
                if multi in engagmentWide[multis[key]]:
                    newT[multis[key]].append(engagmentWide[multis[key]][multi])
                else:
                    if multis[key] == "sources":
                        newM = Source(name=multi)
                    elif multis[key] == "targets":
                        newM = Target(name=multi)
                    elif multis[key] == "tools":
                        newM = Tool(name=multi)
                    elif multis[key] == "controls":
                        newM = Control(name=multi)
                    if multis[key] == "tags":
                        newM = Tag(name=multi, colour="#ff0000")
                    newA[multis[key]].append(newM)
                    newA[multis[key]].save()
                    engagmentWide[multis[key]][multi] = str(newA[multis[key]][-1].id)
                    newT[multis[key]].append(engagmentWide[multis[key]][multi])

        for key in files:
            newFiles = []
            for file in oldT[key]:
                origFilePath, caption = file.split("|")
                origFilePath = origFilePath.split("/")
                name = origFilePath[3]
                # TODO maybe LFI with dir traverse supplied?
                origFilePath = f'files/{newAID}/tmp/{origFilePath[2]}/{origFilePath[3]}'
                if not os.path.exists(f"files/{newAID}/{newTID}"):
                    os.makedirs(f"files/{newAID}/{newTID}")
                newFilePath = f"files/{newAID}/{newTID}/{name}"
                shutil.copy2(origFilePath, newFilePath)
                newFiles.append({"name": name, "path": newFilePath, "caption": caption})
            if files[key] == "redfiles":
                newT.update(set__redfiles=newFiles)
            elif files[key] == "bluefiles":
                newT.update(set__bluefiles=newFiles)

        newT.save()

    shutil.rmtree(f"files/{newAID}/tmp")
    
    return redirect(request.referrer)