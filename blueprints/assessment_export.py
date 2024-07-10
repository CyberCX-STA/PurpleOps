import os
import csv
import json
import shutil
from model import *
from docxtpl import DocxTemplate
from utils import user_assigned_assessment
from werkzeug.utils import secure_filename
from flask_security import auth_required, current_user
from flask import Blueprint, request, send_from_directory

blueprint_assessment_export = Blueprint('blueprint_assessment_export', __name__)

# CSV / JSON export (we testcase[].to_json() then CSV the JSON dict, so function is reused)
@blueprint_assessment_export.route('/assessment/<id>/export/<filetype>',methods = ['GET'])
@auth_required()
@user_assigned_assessment
def exportassessment(id, filetype):
    if filetype not in ["json", 'csv']:
        return 401
    
    assessment = Assessment.objects(id=id).first()
    if current_user.has_role("Blue"):
        testcases = TestCase.objects(assessmentid=str(assessment.id), visible=True).all()
    else:
        testcases = TestCase.objects(assessmentid=str(assessment.id)).all()
    
    jsonDict = []
    for testcase in testcases:
        jsonDict.append(testcase.to_json(raw=True))
        
    # Write JSON and if JSON requested, deliver file and return
    with open(f'files/{str(assessment.id)}/export.json', 'w') as f:
        json.dump(jsonDict, f, indent=4)  
    if filetype == "json":
        return send_from_directory('files', f"{str(assessment.id)}/export.{filetype}", as_attachment=True)
    
    # Otherwise flatten JSON arrays into comma delimited strings
    for t, testcase in enumerate(jsonDict):
        for field in ["sources", "targets", "tools", "controls", "tags", "preventionsources", "detectionsources", "redfiles", "bluefiles"]:
            jsonDict[t][field] = ",".join(testcase[field])

    # Convert the JSON dict to CSV and deliver
    with open(f'files/{str(assessment.id)}/export.csv', 'w', encoding='UTF8', newline='') as f:
        if not testcases:
            f.write("")
        else:
            writer = csv.DictWriter(f, fieldnames=jsonDict[0].keys())
            writer.writeheader()
            writer.writerows(jsonDict)

    return send_from_directory('files', f"{str(assessment.id)}/export.{filetype}", as_attachment=True)

@blueprint_assessment_export.route('/assessment/<id>/export/campaign', methods = ['GET'])
@auth_required()
@user_assigned_assessment
def exportcampaign(id):
    assessment = Assessment.objects(id=id).first()
    if current_user.has_role("Blue"):
        testcases = TestCase.objects(assessmentid=str(assessment.id), visible=True).all()
    else:
        testcases = TestCase.objects(assessmentid=str(assessment.id)).all()
    
    jsonDict = []
    for testcase in testcases:
        # Generate a full JSON dump but then filter to only the applicable fields
        fullJson = testcase.to_json(raw=True)
        campaignJson = {}
        for field in ["mitreid", "tactic", "name", "objective", "actions", "tools", "uuid", "tags", "priority", "priorityurgency", "expectedalertseverity"]:
            campaignJson[field] = fullJson[field]
        jsonDict.append(campaignJson)

    with open(f'files/{str(assessment.id)}/campaign.json', 'w') as f:
        json.dump(jsonDict, f, indent=4)

    return send_from_directory('files', f"{str(assessment.id)}/campaign.json", as_attachment=True)

@blueprint_assessment_export.route('/assessment/<id>/export/templates',methods = ['GET'])
@auth_required()
@user_assigned_assessment
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

@blueprint_assessment_export.route('/assessment/<id>/export/report',methods = ['POST'])
@auth_required()
@user_assigned_assessment
def exportreport(id):
    assessment = Assessment.objects(id=id).first().to_json(raw=True)

    if not os.path.isfile(f"custom/reports/{secure_filename(request.form['report'])}"):
        return "", 401
    
    # Hijack assessment JSON export
    exportassessment(id, "json")
    with open(f'files/{id}/export.json', 'r') as f:
        testcases = json.load(f)

    doc = DocxTemplate(f"custom/reports/{secure_filename(request.form['report'])}")
    doc.render({
        "assessment": assessment,
        "testcases": testcases
    }, autoescape=True)
    doc.save(f'files/{id}/report.docx')

    return send_from_directory('files', f"{id}/report.docx", as_attachment=True)

@blueprint_assessment_export.route('/assessment/<id>/export/navigator',methods = ['GET'])
@auth_required()
@user_assigned_assessment
def exportnavigator(id):
    # Sanity check to ensure assessment exists and to die if not
    _ = Assessment.objects(id=id).first()
    navigator = {
        "name": Assessment.objects(id=id).first().name,
        "versions": {
            # "attack": "13",       "Required" but no warning - so ignoring
            # "navigator": "4.9.1", "Required" but no warning - so ignoring
            "layer": "4.5"
        },
        "domain": "enterprise-attack",
        "sorting": 3,
        "layout": {
            "layout": "flat",
            "aggregateFunction": "average",
            "showID": True,
            "showName": True,
            "showAggregateScores": True,
            "countUnscored": False
        },
        "hideDisabled": False,
        "techniques": [],
        "gradient": {
            "colors": [
                "#ff6666ff",
                "#ffe766ff",
                "#8ec843ff"
            ],
            "minValue": 0,
            "maxValue": 100
        },
        "showTacticRowBackground": True,
        "tacticRowBackground": "#593196",
        "selectTechniquesAcrossTactics": True,
        "selectSubtechniquesWithParent": False
    }

    if current_user.has_role("Blue"):
        testcases = TestCase.objects(assessmentid=id, visible=True).all()
    else:
        testcases = TestCase.objects(assessmentid=id).all()

    results = {}
    for testcase in testcases:
        if not testcase.tactic in results:
                results[testcase.tactic] = {}
        
        if not testcase.mitreid in results[testcase.tactic]:
                results[testcase.tactic][testcase.mitreid] = {"Prevented and Alerted": 0, "Prevented": 0, "Alerted": 0, "Logged": 0, "Missed": 0}

        if testcase.outcome in results[testcase.tactic][testcase.mitreid].keys():
            results[testcase.tactic][testcase.mitreid][testcase.outcome] += 1  

    for tactic_key, techniques in results.items():
        for technique_key,outcomes in techniques.items():
            count = 0
            for outcome_key, outcome in outcomes.items():
                count += outcome

            if count:
                score = int((outcomes["Prevented and Alerted"] * 4 + outcomes["Prevented"] * 3 + outcomes["Alerted"] * 2 +
                            outcomes["Logged"]) / (count * 4) * 100)
            
                ttp = {
                    "techniqueID": technique_key, 
                    "tactic": tactic_key.lower().strip().replace(" ", "-"),
                    "score": score
                }
                navigator["techniques"].append(ttp)

    with open(f'files/{id}/navigator.json', 'w') as f:
        json.dump(navigator, f, indent=4)  

    return send_from_directory('files', f"{id}/navigator.json", as_attachment=True)

@blueprint_assessment_export.route('/assessment/<id>/export/entire',methods = ['GET'])
@auth_required()
@user_assigned_assessment
def exportentire(id):
    assessment = Assessment.objects(id=id).first()

    # Exports fresh JSON as precursor to CSV, so we get both
    exportassessment(id, "csv")
    # Exports fresh campaign template as precursor to testcase templates, so we get both
    exporttestcases(id)

    exportnavigator(id)
    
    # Export assessment meta JSON
    with open(f'files/{id}/meta.json', 'w') as f:
        json.dump(assessment.to_json(raw=True), f)

    # ZIP up the above generated files and testcase evidence and deliver
    if not current_user.has_role("Blue"):
        shutil.make_archive("files/" + id, 'zip', "files/" + id)
    else:
        # If they're blue then they can only export the evidence files of visible testcases
        shutil.copytree(f"files/{id}", f"files/tmp{id}")
        testcases = TestCase.objects(assessmentid=str(assessment.id)).all()
        for testcase in testcases:
            if not testcase.visible and os.path.isdir(f"files/tmp{id}/{str(testcase.id)}"):
                shutil.rmtree(f"files/tmp{id}/{str(testcase.id)}")
        shutil.make_archive(f"files/{id}", 'zip', f"files/tmp{id}")
        shutil.rmtree(f"files/tmp{id}")
    
    return send_from_directory('files', f"{id}.zip", as_attachment=True, download_name=f"{assessment.name}.zip")
