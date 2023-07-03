import os
import json
import requests
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

@blueprint_testcase.route('/testcase/run/<id>',methods = ['POST'])
@auth_required()
def runtestcaseget(id):
    assessmentid = session["assessmentid"]
    ass = Assessment.objects(id=assessmentid).first()
    assessmentname = ass.name
    if current_user.has_role("Spectator"):
            return redirect(f"/assessment/run/{assessmentid}")
    testcase = TestCase.objects(id=id).first()
    if not testcase.assessmentid:
        testcase.assessmentid=assessmentid
    blue = current_user.has_role("Blue")
    fields = ["name", "overview", "objective", "actions", "rednotes", "bluenotes", "advice", "mitreid", "phase", "state", "location", "blocked", "blockedrating", "alerted", "alertseverity", "logged", "detectionrating", "priority", "priorityurgency"]
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
    return redirect(f"/testcase/run/{id}#saved")

@blueprint_testcase.route('/testcase/run/<id>',methods = ['GET'])
@auth_required()
def runtestcasepost(id):
    assessmentid = session["assessmentid"]
    ass = Assessment.objects(id=assessmentid).first()
    assessmentname = ass.name
    testcase = TestCase.objects(id=id).first()
    tactics = Tactic.objects().all()
    if testcase.detecttime == None:
        testcase.detecttime = ""
    templates = TestCaseTemplate.objects(mitreid=testcase["mitreid"])
    if Technique.objects(mitreid=testcase["mitreid"]).first():
        mitrename = Technique.objects(mitreid=testcase["mitreid"]).first()["name"]
    else:
        mitrename = ""
    kb = KnowlegeBase.objects(mitreid=testcase["mitreid"]).first()
    mitres = [[m["mitreid"], m["name"]] for m in Technique.objects()]
    mitres.sort(key=lambda x: x[0])
    sigmas = Sigma.objects(mitreid=testcase["mitreid"])
    testcases = []
    asstests = TestCase.objects(assessmentid=assessmentid).all()
    for test in asstests:
        testcases.append({
            "name": test.name,
            "id": test.id,
            "visible": test.visible,
            "state": test.state
        })
    return render_template('testcase.run_testcase.html', testcase=testcase, tactics=tactics, assessmentid=assessmentid, assessmentname=assessmentname, templates=templates, kb=kb, mitrename=mitrename, mitres=mitres, sigmas=sigmas, testcases=testcases)