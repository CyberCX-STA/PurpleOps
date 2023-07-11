import os
import shutil
from model import *
from flask import Blueprint, request, send_from_directory
from flask_security import auth_required, roles_accepted, current_user

blueprint_testcase_utils = Blueprint('blueprint_testcase_utils', __name__)

@blueprint_testcase_utils.route('/testcase/toggle-visibility/<id>', methods = ['GET'])
@auth_required()
@roles_accepted('Admin', 'Red')
def testcasevisibility(id):
    newcase = TestCase.objects(id=id).first()
    newcase.visible = not newcase.visible
    newcase.save()
        
    return newcase.to_json(), 200

@blueprint_testcase_utils.route('/testcase/clone/<id>', methods = ['GET'])
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

@blueprint_testcase_utils.route('/testcase/delete/<id>', methods = ['GET'])
@auth_required()
@roles_accepted('Admin', 'Red')
def testcasedelete(id):
    testcase = TestCase.objects(id=id).first()
    assessment = Assessment.objects(id=testcase.assessmentid).first()
    # TODO has writes to delete?
    if os.path.exists(f"files/{str(assessment.id)}/{str(testcase.id)}"):
        shutil.rmtree(f"files/{str(assessment.id)}/{str(testcase.id)}")
    testcase.delete()

    return "", 200

@blueprint_testcase_utils.route('/testcase/<id>/evidence/<colour>/<file>', methods = ['DELETE'])
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

@blueprint_testcase_utils.route('/testcase/<id>/evidence/<file>', methods = ['GET'])
@auth_required()
def fetchFile(id, file):
    testcase = TestCase.objects(id=id).first()
    
    return send_from_directory(
        'files',
        f"{testcase.assessmentid}/{str(testcase.id)}/{file}",
        as_attachment = True if "download" in request.args else False
    )