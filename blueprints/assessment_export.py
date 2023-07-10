import os
import csv
import json
import yaml
import shutil
from model import *
from flask_security import auth_required, current_user, roles_accepted
from flask import Blueprint, request, session, send_from_directory

blueprint_assessment_export = Blueprint('blueprint_assessment_export', __name__)

# CSV / JSON export (we testcase[].to_json() then CSV the JSON dict, so function is reused)
@blueprint_assessment_export.route('/assessment/<id>/export/<filetype>',methods = ['GET'])
@auth_required()
@roles_accepted("Admin", "Red")
def exportassessment(id, filetype):
    if filetype not in ["json", 'csv']:
        return 401
    
    assessment = Assessment.objects(id=id).first()
    testcases = TestCase.objects(assessmentid=str(assessment.id)).all()
    
    jsonDict = []
    for testcase in testcases:
        jsonDict.append(testcase.to_json())
        
    # Write JSON and if JSON requested, deliver file and return
    with open(f'files/{str(assessment.id)}/export.json', 'w') as f:
        json.dump(jsonDict, f, indent=4)  
    if filetype == "json":
        return send_from_directory('files', f"{str(assessment.id)}/export.{filetype}", as_attachment=True)
    
    # Otherwise flatten JSON arrays into comma delimited strings
    for t, testcase in enumerate(jsonDict):
        for field in ["sources", "targets", "tools", "controls", "tags", "redfiles", "bluefiles"]:
            jsonDict[t][field] = ",".join(testcase[field])

    # Convert the JSON dict to CSV and deliver
    with open(f'files/{str(assessment.id)}/export.csv', 'w', encoding='UTF8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=jsonDict[0].keys())
        writer.writeheader()
        writer.writerows(jsonDict)

    return send_from_directory('files', f"{str(assessment.id)}/export.{filetype}", as_attachment=True)

@blueprint_assessment_export.route('/assessment/<id>/export/campaign',methods = ['GET'])
@auth_required()
@roles_accepted("Admin", "Red")
def exportcampaign(id):
    assessment = Assessment.objects(id=id).first()
    testcases = TestCase.objects(assessmentid=str(assessment.id)).all()
    
    jsonDict = []
    for testcase in testcases:
        # Generate a full JSON dump but then filter to only the applicable fields
        fullJson = testcase.to_json()
        campaignJson = {}
        for field in ["mitreid", "tactic", "name", "objective", "actions", "tools", "tags"]:
            campaignJson[field] = fullJson[field]
        jsonDict.append(campaignJson)

    with open(f'files/{str(assessment.id)}/campaign.json', 'w') as f:
        json.dump(jsonDict, f, indent=4)


    return send_from_directory('files', f"{str(assessment.id)}/campaign.json", as_attachment=True)

@blueprint_assessment_export.route('/assessment/<id>/export/templates',methods = ['GET'])
@auth_required()
@roles_accepted("Admin", "Red")
def exporttestcases(id):
    # Hijack the campaign exporter and inject a "provider" field
    exportcampaign(id)
    with open(f'files/{id}/campaign.json', 'r') as f:
        jsonDict = json.load(f)
        
    for t, _ in enumerate(jsonDict):
        jsonDict[t]["provider"] = "???"

    with open(f'files/{id}/testcases.json', 'w') as f:
        json.dump(jsonDict, f, indent=4)

    return send_from_directory('files', f"{id}/testcases.json", as_attachment=True)

@blueprint_assessment_export.route('/assessment/<id>/export/entire',methods = ['GET'])
@auth_required()
@roles_accepted('Admin', 'Red')
def exportentire(id):
    assessment = Assessment.objects(id=id).first()

    # Exports fresh JSON as precursor to CSV, so we get both
    exportassessment(id, "csv")
    # Exports fresh campaign template as precursor to testcase templates, so we get both
    exporttestcases(id)
    
    # Export assessment meta JSON
    with open(f'files/{id}/meta.json', 'w') as f:
        json.dump(assessment.to_json(), f)

    # ZIP up the above generated files and testcase evidence and deliver
    shutil.make_archive("files/" + id, 'zip', "files/" + id)
    
    return send_from_directory('files', f"{id}.zip", as_attachment=True, download_name=f"{assessment.name}.zip")