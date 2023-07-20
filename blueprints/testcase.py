import os
from model import *
from utils import *
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, jsonify
from flask_security import auth_required, roles_accepted, current_user

blueprint_testcase = Blueprint('blueprint_testcase', __name__)

@blueprint_testcase.route('/testcase/<id>/single', methods = ['POST'])
@auth_required()
@roles_accepted('Admin', 'Red')
@user_assigned_assessment
def newtestcase(id):
    newcase = TestCase()
    newcase.assessmentid = id
    newcase = applyFormData(newcase, request.form, ["name", "mitreid", "tactic"])
    newcase.save()
    return jsonify(newcase.to_json()), 200

@blueprint_testcase.route('/testcase/<id>',methods = ['GET'])
@auth_required()
@user_assigned_assessment
def runtestcasepost(id):
    testcase = TestCase.objects(id=id).first()
    assessment = Assessment.objects(id=testcase.assessmentid).first()

    if not testcase.visible and current_user.has_role("Blue"):
        return ("", 403)

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

@blueprint_testcase.route('/testcase/<id>',methods = ['POST'])
@auth_required()
@roles_accepted('Admin', 'Red', 'Blue')
@user_assigned_assessment
def testcasesave(id):
    testcase = TestCase.objects(id=id).first()
    isBlue = current_user.has_role("Blue")

    if not testcase.visible and isBlue:
        return ("", 403)

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

    testcase.modifytime = datetime.utcnow()
    if "logged" in request.form and request.form["logged"] == "Yes" and not testcase.detecttime:
        testcase.detecttime = datetime.utcnow()

    if testcase.prevented in ["Yes", "Partial"]:
        testcase.outcome = "Prevented"
    elif testcase.alerted:
        testcase.outcome = "Alerted"
    elif testcase.logged:
        testcase.outcome = "Logged"
    elif not testcase.logged and testcase.prevented:
        testcase.outcome = "Missed"
    else:
        testcase.outcome = ""

    testcase.save()

    return "", 200