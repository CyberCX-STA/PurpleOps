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
        description = request.form['description']
    )
    assessment.save()

    return assessment.to_json(), 200

@blueprint_assessment.route('/assessment/<id>', methods = ['POST'])
@auth_required()
@roles_accepted('Admin', 'Red')
def editassessment(id):
    assessment = Assessment.objects(id=id).first()
    assessment = applyFormData(assessment, request.form, ["name", "description"])
    assessment.save()
    return assessment.to_json(), 200

@blueprint_assessment.route('/assessment/<id>', methods = ['DELETE'])
@auth_required()
@roles_accepted('Admin', 'Red')
def deleteassessment(id):
    assessment = Assessment.objects(id=id).first()
    assessment.delete()
    assessment.save()
    return "", 200

@blueprint_assessment.route('/assessment/<id>', methods = ['GET'])
@auth_required()
# TODO have perms?
def loadassessment(id):
    return render_template(
        'assessment.html',
        testcases = TestCase.objects(assessmentid=id).all(),
        ass = Assessment.objects(id=id).first(),
        templates = TestCaseTemplate.objects(),
        mitres = sorted(
            [[m["mitreid"], m["name"]] for m in Technique.objects()],
            key=lambda m: m[0]
        ),
        tactics = [tactic["name"] for tactic in Tactic.objects()]
        # stats=stats
    )

# # # # #

@blueprint_assessment.route('/assessment/multi/<field>', methods = ['POST'])
@auth_required()
@roles_accepted('Admin', 'Red', 'Blue')
def assessmentmulti(field):
    if field not in ["sources", "targets", "tools", "controls", "tags"]:
        return ('', 418)
    
    testcase = TestCase.objects(id=request.referrer.split("/")[-1]).first()
    assessment = Assessment.objects(id=testcase.assessmentid).first()

    newObjs = []
    for row in request.json["data"]:
        obj = {
            "sources": Source(),
            "targets": Target(),
            "tools": Tool(),
            "controls": Control(),
            "tags": Tag(),
        }[field]

        # If pre-existing, then edit pre-existing to preserve ID
        if row["id"] in [str(o.id) for o in assessment[field]]:
            obj = assessment[field].filter(id=row["id"]).first()
        obj.name = row["name"]
        if field == "tags":
            obj.colour = row["colour"]
        else:
            obj.description = row["description"]
        newObjs.append(obj)
    assessment[field] = newObjs
    assessment[field].save()

    return assessment.multi_to_json(field), 200