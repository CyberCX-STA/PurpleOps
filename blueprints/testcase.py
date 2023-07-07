import os
import json
import string
from model import *
from utils import applyFormData
from sqlite3 import Date
from datetime import datetime
from werkzeug.utils import secure_filename
from flask_security import auth_required, roles_accepted, current_user
from flask import Blueprint, render_template, redirect, request, session, send_from_directory, jsonify

# TODO, reuse from MAIN purplebench.py
# Couldn't be bothered to figure out the dependancy hiararchy and
# cross ref :)
# mitreimportmapping = {"defense-evasion": "Defense Evasion", "collection": "Collection", "exfiltration": "Exfiltration", "command-and-control": "Command and Control", "impact": "Impact", "discovery": "Discovery", "execution": "Execution", "credential-access": "Credential Access", "persistence": "Persistence", "initial-access": "Initial Access", "lateral-movement": "Lateral Movement", "exfiltration": "Exfiltration", "privilege-escalation": "Privilege Escalation", "resource-development": "Resource Development", "reconnaissance": "Reconnaissance"}

blueprint_testcase = Blueprint('blueprint_testcase', __name__)

@blueprint_testcase.route('/testcase/single', methods = ['POST'])
@auth_required()
@roles_accepted('Admin', 'Red')
def newtestcase():
    newcase = TestCase()
    # TODO prevent cross-ass tampering on user supplied input
    newcase.assessmentid = request.referrer.split("/")[-1]
    newcase = applyFormData(newcase, request.form, ["name", "mitreid", "tactic"])
    newcase.save()
    return newcase.to_json()

@blueprint_testcase.route('/testcase/import/template', methods = ['POST'])
@auth_required()
@roles_accepted('Admin', 'Red')
def testcasetemplates():
    newcases = []
    for id in request.json["ids"]:
        template = TestCaseTemplate.objects(id=id).first()
        # TODO prevent cross-ass tampering on user supplied input
        newcase = TestCase(
            name = template.name,
            mitreid = template.mitreid,
            tactic = template.tactic,
            objective = template.objective,
            actions = template.actions,
            rednotes = template.rednotes,
            assessmentid = request.referrer.split("/")[-1]
        ).save()
        newcases.append(newcase.to_json())
        
    return newcases, 200

@blueprint_testcase.route('/testcase/import/navigator', methods = ['POST'])
@auth_required()
@roles_accepted('Admin', 'Red')
def testcasenavigator():
    newcases = []
    navigatorTestcases = json.loads(request.files['file'].read())
    for testcase in navigatorTestcases["techniques"]:
        # TODO prevent cross-ass tampering on user supplied input
        newcase = TestCase(
            name = Technique.objects(mitreid=testcase["techniqueID"]).first().name,
            mitreid = testcase["techniqueID"],
            tactic = string.capwords(testcase["tactic"].replace("-", " ")),
            assessmentid = request.referrer.split("/")[-1]
        ).save()
        newcases.append(newcase.to_json())
        
    return newcases, 200

@blueprint_testcase.route('/testcase/import/campaign', methods = ['POST'])
@auth_required()
@roles_accepted('Admin', 'Red')
def testcasecampaign():
    newcases = []
    campaignTestcases = json.loads(request.files['file'].read())
    for testcase in campaignTestcases:
        # TODO prevent cross-ass tampering on user supplied input
        newcase = TestCase()
        newcase.assessmentid = request.referrer.split("/")[-1]
        for field in ["name", "mitreid", "tactic", "objective", "actions"]: # TODO: "tools", "tags"
            if field in testcase:
                newcase[field] = testcase[field]
        newcase.save()
        newcases.append(newcase.to_json())
        
    return newcases, 200

@blueprint_testcase.route('/testcase/toggle-visibility/<id>', methods = ['GET'])
@auth_required()
@roles_accepted('Admin', 'Red')
def testcasevisibility(id):
    newcase = TestCase.objects(id=id).first()
    print(newcase.visible)
    newcase.visible = not newcase.visible
    newcase.save()
        
    return newcase.to_json(), 200

@blueprint_testcase.route('/testcase/clone/<id>', methods = ['GET'])
@auth_required()
@roles_accepted('Admin', 'Red')
def testcaseclone(id):
    orig = TestCase.objects(id=id).first()
    newcase = TestCase()
    copy = ["name", "assessmentid", "objective", "actions", "rednotes", "mitreid", "tactic", "tools", "tags"]
    for field in copy:
        newcase[field] = orig[field]
    newcase.name = orig["name"] + " (Copy)"
    newcase.save()

    return newcase.to_json(), 200

@blueprint_testcase.route('/testcase/delete/<id>', methods = ['GET'])
@auth_required()
@roles_accepted('Admin', 'Red')
def testcasedelete(id):
    # TODO has writes to deltee?
    TestCase.objects(id=id).first().delete()
    return "", 200







@blueprint_testcase.route('/testcase/<id>',methods = ['POST'])
@auth_required()
def runtestcaseget(id):
    assessmentid = session["assessmentid"]
    ass = Assessment.objects(id=assessmentid).first()
    assessmentname = ass.name
    if current_user.has_role("Spectator"):
            return redirect(f"/assessment/{assessmentid}")
    testcase = TestCase.objects(id=id).first()
    if not testcase.assessmentid:
        testcase.assessmentid=assessmentid
    blue = current_user.has_role("Blue")
    fields = ["name", "overview", "objective", "actions", "rednotes", "bluenotes", "advice", "mitreid", "tactic", "state", "location", "blocked", "blockedrating", "alerted", "alertseverity", "logged", "detectionrating", "priority", "priorityurgency"]
    checkFields = ["visible"]
    multiFields = ["sources", "targets", "tools", "controls", "tags"]
    timeFields = ["starttime", "endtime", "detecttime"]
    blueFields = ["bluenotes", "blocked", "alerted", "alertseverity", "logged", "controls", "tags", "detecttime"]
    for field in fields:
        if field in request.form and not (blue and field not in blueFields):
            testcase[field] = request.form[field]
    for field in checkFields:
        if not (blue and field not in blueFields):
            if field == "visible" and field in request.form and testcase[field] == False:
                postTestcaseReleaseCard(testcase, ass, request.url)
            testcase[field] = field in request.form
    for field in multiFields:
        if field in request.form and not (blue and field not in blueFields):
            testcase[field] = request.form.getlist(field)
        if field not in request.form and (not blue or field in blueFields):
            testcase[field] = None
    for field in timeFields:
        if field in request.form and not (blue and field not in blueFields):
            if request.form[field] != "":
                try:
                    testcase[field] = datetime.strptime(request.form[field], "%d/%m/%Y, %I:%M %p")
                except:
                    testcase[field] = datetime.strptime(request.form[field], "%d/%m/%Y, %I:%M:%p")
    if "alerted" in request.form and "logged" in request.form:
        if not blue and request.form["alerted"] == "No" and request.form["logged"] == "No":
            testcase["detectionrating"] = "0.0"
    if "blocked" in request.form:
        if not blue and request.form["blocked"] == "No":
            testcase["blockedrating"] = "0.0"
    if not os.path.exists(f"files/{assessmentid}/{id}"):
        os.makedirs(f"files/{assessmentid}/{id}")
    files = []
    for file in testcase.redfiles:
        files.append({"name": file.name, "path": file.path, "caption": request.form["RED" + file.path]})
    for file in request.files.getlist('redfiles'):
        if request.files.getlist('redfiles')[0].filename and not blue:
            filename = secure_filename(file.filename)
            path = f"files/{assessmentid}/{id}/{filename}"
            file.save(path)
            files.append({"name": filename, "path": path, "caption": ""})
    testcase.update(set__redfiles=files)
    files = []
    for file in testcase.bluefiles:
        files.append({"name": file.name, "path": file.path, "caption": request.form["BLUE" + file.path]})
    for file in request.files.getlist('bluefiles'):
        if request.files.getlist('bluefiles')[0].filename:
            filename = secure_filename(file.filename)
            path = f"files/{assessmentid}/{id}/{filename}"
            file.save(path)
            files.append({"name": filename, "path": path, "caption": ""})
    testcase.update(set__bluefiles=files)
    if KnowlegeBase.objects(mitreid=testcase["mitreid"]).first():
        testcase.kbentry = True
    else:
        testcase.kbentry = False
    testcase.modifytime = datetime.now()
    testcase.save()
    return redirect(f"/testcase/{id}#saved")

@blueprint_testcase.route('/testcase/<id>',methods = ['GET'])
@auth_required()
def runtestcasepost(id):
    testcase = TestCase.objects(id=id).first()
    assessment = Assessment.objects(id=testcase.assessmentid).first()
    return render_template('testcase.html',
        testcase = testcase,
        tactics = Tactic.objects().all(),
        assessment = assessment,
        kb = KnowlegeBase.objects(mitreid=testcase.mitreid).first(),
        templates = TestCaseTemplate.objects(mitreid=testcase["mitreid"]),
        mitres = [[m["mitreid"], m["name"]] for m in Technique.objects()],
        sigmas = Sigma.objects(mitreid=testcase["mitreid"]),
        multi = {
            "sources": assessment.sources
        }
    )