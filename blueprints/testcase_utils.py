import os
import json
import requests
from model import *
from utils import applyFormData
from sqlite3 import Date
from datetime import datetime
from flask_security import auth_required, roles_accepted
from flask import Blueprint, redirect, request, session, send_from_directory, jsonify

blueprint_testcase_utils = Blueprint('blueprint_testcase_utils', __name__)

@blueprint_testcase_utils.route('/testcase/add',methods = ['POST'])
@auth_required()
@roles_accepted('Admin', 'Red')
def newtestcase():
    id = session["assessmentid"]
    if request.method == 'POST':
        if "name" in request.form:
            newcase = TestCase()
            newcase.assessmentid=id
            newcase = applyFormData(newcase, request.form, ["name", "mitreid", "tactic"])
            if KnowlegeBase.objects(mitreid=newcase.mitreid):
                newcase.kbentry = True
            newcase.save()
            return jsonify([{"id": str(newcase.id), "name": newcase.name, "tactic": newcase.tactic, "mitreid": newcase.mitreid}])
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
                newcase.tactic = tmpl.tactic
                newcase.provider = tmpl.provider
                newcase.kbentry = tmpl.kbentry
                newcase.save()
                newtests.append({"id": str(newcase.id), "name": newcase.name, "tactic": newcase.tactic, "mitreid": newcase.mitreid})
            return jsonify(newtests)


@blueprint_testcase_utils.route('/testcase/delete', methods = ['GET'])
@auth_required()
@roles_accepted('Admin', 'Red')
def deletetestcase():
    assessmentid = session["assessmentid"]
    if "ids" in request.args:
        for id in request.args.get("ids").split(","):
            testcase = TestCase.objects(id=id).first()
            testcase.delete()
    return redirect(f"/assessment/{assessmentid}") 

@blueprint_testcase_utils.route('/testcase/clone/<id>', methods = ['GET'])
@auth_required()
@roles_accepted('Admin', 'Red')
def duplicatetestcase(id):
    if request.method == 'GET':
        orig = TestCase.objects(id=id).first()
        newcase = TestCase()
        copy = ["name", "assessmentid", "overview", "objective", "actions", "advice", "rednotes", "mitreid", "tactic", "tools", "references", "kbentry", "tags"]
        for field in copy:
            newcase[field] = orig[field]
        newcase.name = orig["name"] + " (Copy)"
        newcase.save()

        return jsonify({"id": str(newcase.id), "name": newcase.name, "tactic": newcase.tactic, "mitreid": newcase.mitreid})

@blueprint_testcase_utils.route('/testcase/reset/<id>', methods = ['GET'])
@auth_required()
@roles_accepted('Admin', 'Red')
def resettestcase(id):
    if request.method == 'GET':
        orig = TestCase.objects(id=id).first()
        copy = ["id", "name", "assessmentid", "overview", "objective", "actions", "advice", "rednotes", "mitreid", "tactic", "tools", "references", "kbentry"]
        for field in orig:
            if field not in copy:
                orig[field] = None
        orig.save()

        return jsonify({"id": str(orig.id), "name": orig.name, "tactic": orig.tactic, "mitreid": orig.mitreid})

@blueprint_testcase_utils.route('/testcase/visible', methods = ['GET'])
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

    return redirect(f"/assessment/{assessmentid}") 


@blueprint_testcase_utils.route('/testcase/state',methods = ['GET', 'POST'])
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
        cardJSON = cardJSON.replace("#TACTIC#", testcase.tactic)
        cardJSON = cardJSON.replace("#NAME#", testcase.name)
        cardJSON = cardJSON.replace("#OBJECTIVE#", testcase.objective)
        sources = ", ".join([[k["name"] for k in ass["sources"] if str(k["id"]) == i][0] for i in testcase["sources"]])
        targets = ", ".join([[k["name"] for k in ass["targets"] if str(k["id"]) == i][0] for i in testcase["targets"]])
        cardJSON = cardJSON.replace("#SOURCE#", sources)
        cardJSON = cardJSON.replace("#TARGET#", targets)
        url = f"https://{url.split('/')[2]}/testcase/{testcase.id}"
        cardJSON = cardJSON.replace("#URL#", url)

        if ass.webhook:
            requests.post(ass.webhook, json=json.loads(cardJSON))
    except:
        pass

@blueprint_testcase_utils.route('/testcase/import/mitre', methods = ['POST'])
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
        tactic = t["tactic"]
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
                newcase.tactic = tactic
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
            newcase.tactic = tactic
            newcase.save()
    return redirect(f"/assessment/{assessmentid}")

@blueprint_testcase_utils.route('/testcase/file/<color>/<id>/<file>',methods = ['DELETE'])
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

@blueprint_testcase_utils.route('/testcase/download/<id>/<file>', methods = ['GET'])
@auth_required()
def downloadfile(id, file):
    assessmentid = session["assessmentid"]
    return send_from_directory('files', f"{assessmentid}/{id}/{file}", as_attachment=True)

@blueprint_testcase_utils.route('/testcase/display/<id>/<file>', methods = ['GET'])
@auth_required()
def displayfile(id, file):
    assessmentid = session["assessmentid"]
    return send_from_directory('files', f"{assessmentid}/{id}/{file}")

@blueprint_testcase_utils.route('/testcase/sigma/<id>', methods = ['GET'])
@auth_required()
def downloadsigma(id):
    sigma = Sigma.objects(id=id).first()
    if not os.path.exists(f"files/sigma/"):
        os.makedirs(f"files/sigma/")
    if not os.path.exists(f"files/sigma/{sigma.filename}"):
        with open(f"files/sigma/{sigma.filename}", "w") as sigmaF:
            sigmaF.write(sigma.raw)
    return send_from_directory('files', f"sigma/{sigma.filename}")