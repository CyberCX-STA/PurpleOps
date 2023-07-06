from model import *
from utils import applyFormData
from flask_security import auth_required, roles_accepted
from flask import Blueprint, render_template, request, session
# from blueprints.assessment_utils import generatestats

blueprint_assessment = Blueprint('blueprint_assessment', __name__)

@blueprint_assessment.route('/assessment', methods = ['POST'])
@auth_required()
@roles_accepted('Admin', 'Red')
def newassessment():
    # TODO way to import custom packs of tools/controls
    assessment = Assessment(
        name = request.form['name'],
        description = request.form['description'],
        tools = [Tool(name="Sample Tool", description="Sample Desc")],
        controls = [Control(name="Sample Control", description="Sample Desc")]
    )
    assessment.save()

    return assessment.to_json(), 200

@blueprint_assessment.route('/assessment/<id>', methods = ['POST', 'DELETE'])
@auth_required()
@roles_accepted('Admin', 'Red')
def editassessment(id):
    assessment = Assessment.objects(id=id).first()
    if request.method == 'POST':
        assessment = applyFormData(assessment, request.form, ["name", "description"])
        assessment.save()

        return assessment.to_json(), 200
        
    if request.method == 'DELETE':
        assessment.delete()
        assessment.save()
        
        return "", 200

@blueprint_assessment.route('/assessment/<id>', methods = ['GET'])
@auth_required()
# TODO have perms?
def loadassessment(id):
    return render_template(
        'assessment.html',
        tests = TestCase.objects(assessmentid=id).all(),
        ass = Assessment.objects(id=id).first(),
        templates = TestCaseTemplate.objects(),
        mitres = sorted(
            [[m["mitreid"], m["name"]] for m in Technique.objects()],
            key=lambda m: m[0]
        ),
        tactics = [tactic["name"] for tactic in Tactic.objects()]
        # stats=stats
    )