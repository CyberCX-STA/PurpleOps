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