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
            "tags": assessment.tags,
            "preventionsources": assessment.preventionsources,
            "detectionsources": assessment.detectionsources
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

    directFields = ["name", "objective", "actions", "rednotes", "bluenotes", "uuid", "mitreid", "tactic", "state", "prevented", "preventedrating", "alertseverity", "logged", "detectionrating", "priority", "priorityurgency", "expectedalertseverity"] if not isBlue else ["bluenotes", "prevented", "alerted", "alertseverity","state"] 
    listFields = ["sources", "targets", "tools", "controls", "tags", "preventionsources", "detectionsources"]
    boolFields = ["alerted", "logged", "visible"] if not isBlue else ["alerted", "logged"]
    timeFields = ["starttime", "endtime", "alerttime", "preventtime"]
    fileFields = ["redfiles", "bluefiles"] if not isBlue else ["bluefiles"]

    # only allow state update from blue if correct state is sent and testcase is in changable state
    if isBlue:
        if request.form.get("state") != 'Waiting Blue' and request.form.get("state") != 'Waiting Red' and request.form.get("state"):
            return ("Not allowed state value", 403)
        if testcase.state != 'Waiting Blue' and testcase.state != 'Waiting Red':
            return ("State cannot be changed at the moment", 403)

    # do not update testcase if it was modified in the meantime
    if request.form.get("modifytime"):
        requestmodifytime = request.form.get("modifytime")
        # ugly string compare of date
        if requestmodifytime != str(testcase.modifytime):
            return ("", 409)

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
                "name": secure_filename(file.name),
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
        if testcase.alerted: 
            testcase.outcome = "Prevented and Alerted"
        else:
            testcase.outcome = "Prevented"
    elif testcase.alerted:
        testcase.outcome = "Alerted"
    elif testcase.logged:
        testcase.outcome = "Logged"
    elif not testcase.logged and testcase.prevented:
        testcase.outcome = "Missed"
    else:
        testcase.outcome = ""

    # Calculate Testcase Outcome Score based on expected result
    if testcase.priority == "Prevent and Alert":
        match testcase.outcome:
            case "Prevented and Alerted":
                testcase.testcasescore = 100
            case "Prevented":
                testcase.testcasescore = 75
            case "Alerted":
                testcase.testcasescore = 50
            case "Logged":
                testcase.testcasescore = 25
            case "Missed":
                testcase.testcasescore = 0

    elif testcase.priority == "Prevent":
        match testcase.outcome:
            case "Prevented and Alerted":
                testcase.testcasescore = 100
            case "Prevented":
                testcase.testcasescore = 100
            case "Alerted":
                testcase.testcasescore = 75
            case "Logged":
                testcase.testcasescore = 25
            case "Missed":
                testcase.testcasescore = 0

    elif testcase.priority == "Alert":
        match testcase.outcome:
            case "Prevented and Alerted":
                testcase.testcasescore = 100
            case "Prevented":
                testcase.testcasescore = 75
            case "Alerted":
                testcase.testcasescore = 100
            case "Logged":
                testcase.testcasescore = 25
            case "Missed":
                testcase.testcasescore = 0
    else:
     testcase.testcasescore = None
 

    # This is some sanity check code where we check if some of the UI elements are out of sync with the backend. This is trggered by the horrible tabs bug
    # Does not fix user not saving test case before navigating away
    # Todo: Turns this BS code into a single mongoengine query against the subdocument list
    assessment = Assessment.objects(id=testcase.assessmentid).first()
    for field in listFields:
        ids = []
        valid_ids = []
        for t in assessment[field]:
            ids.append(str(t.id))
        for field_id in testcase[field]:
            if field_id in ids:
                valid_ids.append(field_id)
        testcase[field] = valid_ids
    testcase.save()

    return "", 200
