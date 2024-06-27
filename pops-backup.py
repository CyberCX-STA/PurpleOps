import csv
import os
import json
import shutil
import logging
import argparse
from model import *
from dotenv import load_dotenv
from pathlib import Path
from flask import Flask 

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)
load_dotenv()

app = Flask(__name__)
app.config.from_pyfile("flask.cfg")

def exportassessment(assessment, filetype):
    testcases = TestCase.objects(assessmentid=str(assessment.id)).all()
    
    jsonDict = []
    for testcase in testcases:
        jsonDict.append(testcase.to_json(raw=True))
        
    # Write JSON and if JSON requested, deliver file and return
    with open(f"{args.backupdir}/{str(assessment.id)}/export.json", 'w') as f:
        json.dump(jsonDict, f, indent=4)  
    
    # Otherwise flatten JSON arrays into comma delimited strings
    for t, testcase in enumerate(jsonDict):
        for field in ["sources", "targets", "tools", "controls", "tags", "redfiles", "bluefiles", "preventionsources", "detectionsources"]:
            jsonDict[t][field] = ",".join(testcase[field])

    # Convert the JSON dict to CSV and deliver
    with open(f"{args.backupdir}/{str(assessment.id)}/export.csv", 'w', encoding='UTF8', newline='') as f:
        if not testcases:
            f.write("")
        else:
            writer = csv.DictWriter(f, fieldnames=jsonDict[0].keys())
            writer.writeheader()
            writer.writerows(jsonDict)

def exportcampaign(id):
    assessment = Assessment.objects(id=id).first()
    testcases = TestCase.objects(assessmentid=str(assessment.id)).all()
    
    jsonDict = []
    for testcase in testcases:
        # Generate a full JSON dump but then filter to only the applicable fields
        fullJson = testcase.to_json(raw=True)
        campaignJson = {}
        for field in ["mitreid", "tactic", "name", "objective", "actions", "tools", "uuid", "tags"]:
            campaignJson[field] = fullJson[field]
        jsonDict.append(campaignJson)

    with open(f"{args.backupdir}/{str(assessment.id)}/campaign.json", 'w') as f:
        json.dump(jsonDict, f, indent=4)


def exporttestcases(id):
    # Hijack the campaign exporter and inject a "provider" field
    exportcampaign(id)
    with open(f"{args.backupdir}/{id}/campaign.json", 'r') as f:
        jsonDict = json.load(f)
        
    for t, _ in enumerate(jsonDict):
        jsonDict[t]["provider"] = "???"

    with open(f"{args.backupdir}/{id}/testcases.json", 'w') as f:
        json.dump(jsonDict, f, indent=4)

def exportnavigator(id):
    # Sanity check to ensure assessment exists and to die if not
    _ = Assessment.objects(id=id).first()
    navigator = {
        "name": Assessment.objects(id=id).first().name,
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

    for technique in Technique.objects().all():
        testcases = TestCase.objects(assessmentid=id, mitreid=technique.mitreid).all()
        ttp = {
            "techniqueID": technique.mitreid
        }

        if testcases:
            count = 0
            outcomes = {"Prevented": 0, "Alerted": 0, "Logged": 0, "Missed": 0}
            for testcase in testcases:
                if testcase.outcome in outcomes.keys():
                    count += 1
                    outcomes[testcase.outcome] += 1

            if count:
                score = int((outcomes["Prevented"] * 3 + outcomes["Alerted"] * 2 +
                            outcomes["Logged"]) / (count * 3) * 100)
                ttp["score"] = score

            for tactic in technique.tactics:
                tactic = tactic.lower().strip().replace(" ", "-")
                tacticTTP = dict(ttp)
                tacticTTP["tactic"] = tactic
                navigator["techniques"].append(tacticTTP)

    with open(f"{args.backupdir}/{id}/navigator.json", 'w') as f:
        json.dump(navigator, f, indent=4)  


def exportentirebackupid(assessment):
    # Clear previous backup artifacts in the backup dir
    shutil.rmtree(f"{args.backupdir}/{str(assessment.id)}", ignore_errors=True)
    Path(f"{args.backupdir}/{str(assessment.id)}").mkdir(parents=True, exist_ok=True)
    
    exportassessment(assessment, "csv")
    exporttestcases(assessment.id)
    exportnavigator(assessment.id)
    
    with open(f'{args.backupdir}/{assessment.id}/meta.json', 'w') as f:
        json.dump(assessment.to_json(raw=True), f)
        
    #Copy remaining uploaded artifacts across to the backup dir
    shutil.copytree(f"{args.files}/{str(assessment.id)}", f"{args.backupdir}/{str(assessment.id)}", dirs_exist_ok=True)
    shutil.make_archive(f"{args.backupdir}/{str(assessment.id)}", 'zip', f"{args.backupdir}/{str(assessment.id)}")
   

if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("-d", "--dir", dest="backupdir", help="The backup directory",required=True)
        parser.add_argument("-f", "--files", dest="files", help="The PurpleOps files directory", default="files")
        parser.add_argument("-H", "--host", help="Mongodb host. Default: host defined in flask.cfg")
        parser.add_argument("-p", "--port", type=int,help="Mongodb port. Default: port defined in flask.cfg")
        args = parser.parse_args()
        
        logging.info("Backup started")
        if not args.port is None:
            app.config["MONGODB_SETTINGS"]["port"] = args.port #32768
        if not args.host is None:
            app.config["MONGODB_SETTINGS"]["host"] = args.host
            
        db.init_app(app)
        
        if not os.path.isdir(args.files):
            raise Exception("Invalid PurpleOps files directory, does not exist")
        
        if os.path.isdir(args.backupdir):
            if os.path.abspath(args.backupdir) == os.path.abspath(args.files):
                raise Exception("Invalid backup director, can't backup to the PurpleOps files directory")
        
        for a in Assessment.objects().all():
            logging.info(f"Exporting: {a.name}")
            exportentirebackupid(a)
        
        logging.info("Backup completed")
    except:
        logging.exception("Error during backup, please fix and try again")
