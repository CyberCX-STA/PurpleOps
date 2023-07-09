import os
import json
import string
from model import *
from utils import *
from datetime import datetime
from werkzeug.utils import secure_filename
from flask_security import auth_required, roles_accepted, current_user
from flask import Blueprint, render_template, redirect, request, session, send_from_directory

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
    return newcase.to_json(), 200

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
@roles_accepted('Admin', 'Red', 'Blue')
def testcasesave(id):
    testcase = TestCase.objects(id=id).first()
    isBlue = current_user.has_role("Blue")
    directFields = ["name", "objective", "actions", "rednotes", "bluenotes", "mitreid", "tactic", "state", "prevented", "preventedrating", "alertseverity", "logged", "detectionrating", "priority", "priorityurgency"] if not isBlue else ["bluenotes", "prevented", "alerted", "alertseverity"]
    listFields = ["sources", "targets", "tools", "controls", "tags"]
    boolFields = ["alerted", "logged", "visible"] if not isBlue else ["alerted", "logged"]
    timeFields = ["starttime", "endtime"]
    fileFields = ["redfiles", "bluefiles"] if not isBlue else ["bluefiles"]

    testcase = applyFormData(testcase, request.form, directFields)
    testcase = applyFormListData(testcase, request.form, listFields)
    testcase = applyFormBoolData(testcase, request.form, boolFields)
    testcase = applyFormTimeData(testcase, request.form, timeFields)

    if not os.path.exists(f"files/{testcase.assessmentid}/{str(testcase.id)}"):
        os.makedirs(f"files/{testcase.assessmentid}/{str(testcase.id)}")

    for field in fileFields:
        files = []
        for file in testcase[field]:
            if file.name.lower().split(".")[-1] in ["png", "jpg", "jpeg"]:
                caption = request.form[field.replace("files", "").upper() + file.name]
            else:
                caption = ""
            files.append({
                "name": file.name,
                "path": file.path,
                "caption": caption
            })
        for file in request.files.getlist(field):
            if request.files.getlist(field)[0].filename:
                filename = secure_filename(file.filename)
                path = f"files/{testcase.assessmentid}/{str(testcase.id)}/{filename}"
                file.save(path)
                files.append({"name": filename, "path": path, "caption": ""})
        if field == "redfiles":
            testcase.update(set__redfiles=files)
        else:
            testcase.update(set__bluefiles=files)

    testcase.modifytime = datetime.now()
    if "logged" in request.form and request.form["logged"] == "Yes" and not testcase.detecttime:
        testcase.detecttime = datetime.now()
    testcase.save()

    return "", 200







@blueprint_testcase.route('/testcase/<id>/evidence/<colour>/<file>', methods = ['DELETE'])
@auth_required()
@roles_accepted('Admin', 'Red', 'Blue')
def deletefile(id, colour, file):
    if colour not in ["red", "blue"] or colour == "red" and current_user.has_role("Blue"):
        return 401
    
    testcase = TestCase.objects(id=id).first()
    os.remove(f"files/{testcase.assessmentid}/{testcase.id}/{file}")

    files = []
    for f in testcase["redfiles" if colour == "red" else "bluefiles"]:
        if f.name != file:
            files.append(f)
            
    if colour == "red":
        testcase.update(set__redfiles=files)
    else:
        testcase.update(set__bluefiles=files)

    return ('', 204)

@blueprint_testcase.route('/testcase/<id>/evidence/<file>', methods = ['GET'])
@auth_required()
def fetchFile(id, file):
    testcase = TestCase.objects(id=id).first()
    return send_from_directory(
        'files',
        f"{testcase.assessmentid}/{str(testcase.id)}/{file}",
        as_attachment = True if "download" in request.args else False
    )

















@blueprint_testcase.route('/testcase/<id>',methods = ['GET'])
@auth_required()
def runtestcasepost(id):
    testcase = TestCase.objects(id=id).first()
    assessment = Assessment.objects(id=testcase.assessmentid).first()
    return render_template('testcase.html',
        testcase = testcase,
        testcases = TestCase.objects(assessmentid=str(assessment.id)).all(),
        tactics = Tactic.objects().all(),
        assessment = assessment,
        kb = KnowlegeBase.objects(mitreid=testcase.mitreid).first(),
        templates = TestCaseTemplate.objects(mitreid=testcase["mitreid"]),
        mitres = [[m["mitreid"], m["name"]] for m in Technique.objects()],
        sigmas = Sigma.objects(mitreid=testcase["mitreid"]),
        multi = {
            "sources": assessment.sources,
            "targets": assessment.targets,
            "tools": assessment.tools,
            "controls": assessment.controls,
            "tags": assessment.tags
        }
    )