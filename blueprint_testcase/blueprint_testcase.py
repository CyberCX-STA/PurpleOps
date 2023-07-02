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
mitreimportmapping = {"defense-evasion": "Defense Evasion", "collection": "Collection", "exfiltration": "Exfiltration", "command-and-control": "Command and Control", "impact": "Impact", "discovery": "Discovery", "execution": "Execution", "credential-access": "Credential Access", "persistence": "Persistence", "initial-access": "Initial Access", "lateral-movement": "Lateral Movement", "exfiltration": "Exfiltration", "privilege-escalation": "Privilege Escalation", "resource-development": "Resource Development", "reconnaissance": "Reconnaissance"}

blueprint_testcase = Blueprint('blueprint_testcase', __name__)


@blueprint_testcase.route('/testcase/add',methods = ['POST'])
@auth_required()
@roles_accepted('Admin', 'Red')
def newtestcase():
    id = session["assessmentid"]
    if request.method == 'POST':
        if "name" in request.form:
            newcase = TestCase()
            newcase.assessmentid=id
            newcase = applyFormData(newcase, request.form, ["name", "mitreid", "phase"])
            if KnowlegeBase.objects(mitreid=newcase.mitreid):
                newcase.kbentry = True
            newcase.save()
            return jsonify([{"id": str(newcase.id), "name": newcase.name, "phase": newcase.phase, "mitreid": newcase.mitreid}])
        else:
            newtests = []
            for templateID in request.form.getlist('ids[]'):
                tmpl = TestCaseTemplate.objects(id=templateID).first()
                newcase = TestCase()
                newcase.assessmentid = id
                newcase.name = tmpl.name
                newcase.overview = tmpl.overview
                newcase.objective = tmpl.objective
                newcase.rednotes = tmpl.notes
                newcase.actions = tmpl.actions
                newcase.advice = tmpl.advice
                newcase.mitreid = tmpl.mitreid
                newcase.phase = tmpl.phase
                newcase.provider = tmpl.provider
                newcase.kbentry = tmpl.kbentry
                newcase.save()
                newtests.append({"id": str(newcase.id), "name": newcase.name, "phase": newcase.phase, "mitreid": newcase.mitreid})
            return jsonify(newtests)


@blueprint_testcase.route('/testcase/delete', methods = ['GET'])
@auth_required()
@roles_accepted('Admin', 'Red')
def deletetestcase():
    assessmentid = session["assessmentid"]
    if "ids" in request.args:
        for id in request.args.get("ids").split(","):
            testcase = TestCase.objects(id=id).first()
            testcase.delete()
    return redirect(f"/assessment/run/{assessmentid}") 

@blueprint_testcase.route('/testcase/clone/<id>', methods = ['GET'])
@auth_required()
@roles_accepted('Admin', 'Red')
def duplicatetestcase(id):
    if request.method == 'GET':
        orig = TestCase.objects(id=id).first()
        newcase = TestCase()
        copy = ["name", "assessmentid", "overview", "objective", "actions", "advice", "rednotes", "mitreid", "phase", "tools", "references", "kbentry", "tags"]
        for field in copy:
            newcase[field] = orig[field]
        newcase.name = orig["name"] + " (Copy)"
        newcase.save()

        return jsonify({"id": str(newcase.id), "name": newcase.name, "phase": newcase.phase, "mitreid": newcase.mitreid})

@blueprint_testcase.route('/testcase/reset/<id>', methods = ['GET'])
@auth_required()
@roles_accepted('Admin', 'Red')
def resettestcase(id):
    if request.method == 'GET':
        orig = TestCase.objects(id=id).first()
        copy = ["id", "name", "assessmentid", "overview", "objective", "actions", "advice", "rednotes", "mitreid", "phase", "tools", "references", "kbentry"]
        for field in orig:
            if field not in copy:
                orig[field] = None
        orig.save()

        return jsonify({"id": str(orig.id), "name": orig.name, "phase": orig.phase, "mitreid": orig.mitreid})

@blueprint_testcase.route('/testcase/visible', methods = ['GET'])
@auth_required()
@roles_accepted('Admin', 'Red')
def visibletestcase():
    assessmentid = session["assessmentid"]
    ass = Assessment.objects(id=assessmentid).first()
    if request.method == 'GET' and "ids" in request.args:
        for id in request.args.get("ids").split(","):
            orig = TestCase.objects(id=id).first()
            if orig.visible == False:
                postTestcaseReleaseCard(orig, ass, request.url)
            orig.visible = not orig.visible
            orig.save()

    return redirect(f"/assessment/run/{assessmentid}") 


@blueprint_testcase.route('/testcase/state',methods = ['GET', 'POST'])
@auth_required()
@roles_accepted('Admin', 'Red')
def changetestcasestate():
    assessmentid = session["assessmentid"]
    newstate = "Unknown"
    if request.method == "POST":
        testid = request.form["testid"]
        state = request.form["state"]
        try:
            starttime = datetime.strptime(request.form["starttime"], "%d/%m/%Y, %I:%M %p")
        except:
            starttime = datetime.strptime(request.form["starttime"], "%d/%m/%Y, %I:%M:%p")
        
        try:
            endtime = datetime.strptime(request.form["endtime"], "%d/%m/%Y, %I:%M %p")
        except:
            endtime = datetime.strptime(request.form["endtime"], "%d/%m/%Y, %I:%M:%p")
        
        if testid:
            testcase = TestCase.objects(id=testid).first()
            if state == "Pending":
                newstate = "In progress"
                testcase.starttime = starttime
            elif state == "In progress":
                newstate = "Complete"
                testcase.endtime = endtime
            elif state == "Complete":
                newstate = "In progress"
                testcase.starttime = starttime
                testcase.endtime = None
            else:
                newstate = "Pending"
                testcase.starttime = None
                testcase.endtime = None
            testcase.state = newstate
            testcase.modifytime = datetime.now()
            testcase.save()
        
    return newstate, 200 


def postTestcaseReleaseCard(testcase, ass, url):
    # TODO While thread locking and BETA, try/except
    try:
        with open("sampledata/testcase_release_card.json", "r") as rawJSON:
            cardJSON = rawJSON.read()
        cardJSON = cardJSON.replace("#POSTTIME#", datetime.now().strftime("%I:%M%p on %B %d, %Y"))
        cardJSON = cardJSON.replace("#STARTTIME#", str(testcase.starttime))
        cardJSON = cardJSON.replace("#ENDTIME#", str(testcase.endtime))
        cardJSON = cardJSON.replace("#MITREID#", testcase.mitreid)
        cardJSON = cardJSON.replace("#PHASE#", testcase.phase)
        cardJSON = cardJSON.replace("#NAME#", testcase.name)
        cardJSON = cardJSON.replace("#OBJECTIVE#", testcase.objective)
        sources = ", ".join([[k["name"] for k in ass["sources"] if str(k["id"]) == i][0] for i in testcase["sources"]])
        targets = ", ".join([[k["name"] for k in ass["targets"] if str(k["id"]) == i][0] for i in testcase["targets"]])
        cardJSON = cardJSON.replace("#SOURCE#", sources)
        cardJSON = cardJSON.replace("#TARGET#", targets)
        url = f"https://{url.split('/')[2]}/testcase/run/{testcase.id}"
        cardJSON = cardJSON.replace("#URL#", url)

        if ass.webhook:
            requests.post(ass.webhook, json=json.loads(cardJSON))
    except:
        pass


@blueprint_testcase.route('/testcase/run/<id>',methods = ['POST', 'GET'])
@auth_required()
def runtestcase(id):
    assessmentid = session["assessmentid"]
    ass = Assessment.objects(id=assessmentid).first()
    assessmentname = ass.name
    if request.method == 'POST':
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
    else:
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


@blueprint_testcase.route('/testcase/import/mitre', methods = ['POST'])
@auth_required()
@roles_accepted('Admin', 'Red')
def importmitrelayer():
    assessmentid = session["assessmentid"]
    f = request.files['file']
    jsonstring = f.read()
    mitredata = json.loads(jsonstring)
    for t in mitredata["techniques"]:
        mitreid = t["techniqueID"]
        print(f"{assessmentid}")
        tactic = mitreimportmapping[t["tactic"]]
        technique = Technique.objects(mitreid=mitreid).first()
        hastmpl = (TestCaseTemplate.objects(mitreid=mitreid).first() != None)
        if hastmpl:
            for tmpl in TestCaseTemplate.objects(mitreid=mitreid).all():
                if TestCase.objects(assessmentid=assessmentid, mitreid=mitreid, name=tmpl.name):
                    continue
                newcase  = TestCase()
                newcase.assessmentid=assessmentid
                newcase.name = tmpl.name
                newcase.overview = tmpl.overview
                newcase.objective = tmpl.objective
                newcase.actions = tmpl.actions
                newcase.advice = tmpl.advice
                newcase.mitreid = mitreid
                newcase.phase = tactic
                newcase.kbentry = tmpl.kbentry
                newcase.provider = tmpl.provider
                newcase.save()

        else:
            if TestCase.objects(mitreid=mitreid, name=technique.name):
                continue
            newcase = TestCase()
            newcase.assessmentid=assessmentid
            newcase.name = f"{technique.name}"
            newcase.overview = technique.description
            newcase.objective = ""
            newcase.actions = ""
            
            newcase.mitreid = mitreid
            newcase.phase = tactic
            newcase.save()
    return redirect(f"/assessment/run/{assessmentid}")

@blueprint_testcase.route('/testcase/file/<color>/<id>/<file>',methods = ['DELETE'])
@auth_required()
@roles_accepted('Admin', 'Red', 'Blue')
def deletefile(color, id, file):
    assessmentid = session["assessmentid"]
    os.remove(f"files/{assessmentid}/{id}/{file}")
    testcase = TestCase.objects(id=id).first()
    files = []
    if color == "red":
        for f in testcase.redfiles:
            if f.name != file:
                files.append({"name": f.name, "path": f.path, "caption": f.caption})
        testcase.update(set__redfiles=files)
    if color == "blue":
        for f in testcase.bluefiles:
            if f.name != file:
                files.append({"name": f.name, "path": f.path, "caption": f.caption})
        testcase.update(set__bluefiles=files)
    return ('', 204)

@blueprint_testcase.route('/testcase/download/<id>/<file>', methods = ['GET'])
@auth_required()
def downloadfile(id, file):
    assessmentid = session["assessmentid"]
    return send_from_directory('files', f"{assessmentid}/{id}/{file}", as_attachment=True)

@blueprint_testcase.route('/testcase/display/<id>/<file>', methods = ['GET'])
@auth_required()
def displayfile(id, file):
    assessmentid = session["assessmentid"]
    return send_from_directory('files', f"{assessmentid}/{id}/{file}")

@blueprint_testcase.route('/testcase/sigma/<id>', methods = ['GET'])
@auth_required()
def downloadsigma(id):
    sigma = Sigma.objects(id=id).first()
    if not os.path.exists(f"files/sigma/"):
        os.makedirs(f"files/sigma/")
    if not os.path.exists(f"files/sigma/{sigma.filename}"):
        with open(f"files/sigma/{sigma.filename}", "w") as sigmaF:
            sigmaF.write(sigma.raw)
    return send_from_directory('files', f"sigma/{sigma.filename}")