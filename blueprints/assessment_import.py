import os
import json
import shutil
from model import *
from flask_security import auth_required, roles_accepted
from flask import Blueprint, redirect, request

blueprint_assessment_import = Blueprint('blueprint_assessment_import', __name__)

@blueprint_assessment_import.route('/assessment/import/template/<id>', methods = ['POST'])
@auth_required()
@roles_accepted('Admin', 'Red')
def importtemplate(id):
    ass = Assessment.objects(id=id).first()

    f = request.files['file']
    tests = json.loads(f.read())

    fields = ["mitreid", "tactic", "name", "objective", "actions", "tools", "tags"]

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

@blueprint_assessment_import.route('/assessment/import/entire', methods = ['POST'])
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
        "Tactic": "tactic",
        "Name": "name",
        "State": "state",
        "Objective": "objective",
        "Actions": "actions",
        "Red Notes": "rednotes",
        "Prevented": "prevented",
        "Prevented Rating": "preventedrating",
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