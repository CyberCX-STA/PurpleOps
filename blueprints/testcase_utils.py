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