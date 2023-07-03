import os
import csv
import json
import yaml
import shutil
from copy import deepcopy
from model import *
from utils import applyFormData
from flask_security import auth_required, current_user, roles_accepted
from flask import Blueprint, render_template, redirect, request, session, send_from_directory
from blueprints.assessment_utils import generatestats

blueprint_assessment = Blueprint('blueprint_assessment', __name__)

@blueprint_assessment.route('/assessment/new', methods = ['POST'])
@auth_required()
@roles_accepted('Admin', 'Red')
def newassessment():
    if request.method == 'POST':
        # TODO way to import custom packs of tools/controls
        assessment = Assessment(
            name = request.form['name'],
            description = request.form['description'],
            tools = [Tool(name="Sample Tool", description="Sample Desc")],
            controls = [Control(name="Sample Control", description="Sample Desc")]
        )
        assessment.save()

        return jsonify({"id": str(assessment.id)})

@blueprint_assessment.route('/assessment/<id>', methods = ['GET'])
@auth_required()
def loadassessment(id):
    session["assessmentid"] = id
    tests = TestCase.objects(assessmentid=id).all()
    ass = Assessment.objects(id=id).first()
    templates = TestCaseTemplate.objects()
    mitres = [[m["mitreid"], m["name"]] for m in Technique.objects()]
    mitres.sort(key=lambda x: x[0])
    tactics = {}
    count = 1
    for t in tests:
        if not t.phase in tactics.keys():
            tactics[t.phase] = count
            count += 1

    stats = generatestats(tests, ass)

    return render_template('assessment.html', tests=tests, ass=ass, templates=templates, mitres=mitres, stats=stats)