import yaml
import argparse
import os
import re
import shutil
import requests
from model import *
from flask import Flask, redirect
from openpyxl import load_workbook
from git import Repo
from glob import glob
import json, csv

app = Flask(__name__)
app.config['MONGODB_SETTINGS'] = {
    'db': 'assessments',
    'host': 'localhost',
    'port': 27017
}
app.secret_key = "marc-hates-edward"

db.init_app(app)

def exporttemplate(id):
    tests = TestCase.objects(assessmentid=id).all()
    ass = Assessment.objects(id=id).first()

    rowsJSON = []

    fields = ["mitreid", "tactic", "name", "objective", "actions", "tools", "tags"]

    for test in tests:
        df = {}
        for field in fields:
            if field == "tools":
                df[field] = []
                for toolID in test[field]:
                    df[field].append([t["name"] for t in ass["tools"] if str(t["id"]) == toolID][0])
            elif field == "tags":
                df[field] = []
                for tagID in test[field]:
                    try:
                        df[field].append([t["name"] for t in ass["tags"] if str(t["id"]) == tagID][0])
                    except IndexError:
                        # Tag was deleted but there's still a reference to it, thus we can ignore it
                        pass
            else:
                df[field] = test[field]
        rowsJSON.append(df)

    if not os.path.exists(f"files/{id}"):
        os.makedirs(f"files/{id}")

    with open(f'files/{id}/template.json', 'w') as f:
        json.dump(rowsJSON, f)

def exportassessment(filetype, id):
    tests = TestCase.objects(assessmentid=id).all()
    ass = Assessment.objects(id=id).first()
    rowsJSON = []
    rowsCSV = []

    for test in tests:
        df = {
            "Mitre ID": test["mitreid"],
            "Name": test["name"],
            "Tactic": test["tactic"],
            "State": test["state"],
            "Modified Time": str(test["modifytime"]),
            "Start Time": str(test["starttime"]),
            "End Time": str(test["endtime"]),
            "Source(s)": [[k["name"] for k in ass["sources"] if str(k["id"]) == i][0] for i in test["sources"]], 
            "Target(s)": [[k["name"] for k in ass["targets"] if str(k["id"]) == i][0] for i in test["targets"]],
            "Red Tool(s)": [[k["name"] for k in ass["tools"] if str(k["id"]) == i][0] for i in test["tools"]],
            "Objective": test["objective"],
            "Actions": test["actions"],
            "Red Notes": test["rednotes"],
            "Red Evidence": [i["path"] + "|" + i["caption"] for i in test["redfiles"]],
            "Blocked": test["blocked"],
            "Blocked Rating": test["blockedrating"],
            "Alert": test["alert"],
            "Alert Severity": test["alertseverity"],
            "Logged": test["logged"],
            "Detection Rating": test["detectionrating"],
            "Detection Time": str(test["detecttime"]),
            "Priority": test["priority"],
            "Priority Urgency": test["priorityurgency"],
            "Control(s)": [[k["name"] for k in ass["controls"] if str(k["id"]) == i][0] for i in test["controls"]],
            "Tags": [[k["name"] for k in ass["tags"] if str(k["id"]) == i][0] for i in test["tags"]],
            "Observations": test["bluenotes"],
            "Blue Evidence": [i["path"] + "|" + i["caption"] for i in test["bluefiles"]]
        }
          
        # Keep JSON arrays as is, but flatten for CSV
        rowsJSON.append(df.copy())

        for field in ["Source(s)", "Target(s)", "Red Tool(s)", "Red Evidence", "Tags", "Blue Evidence", "Control(s)"]:
            df[field] = ",".join(df[field])
        rowsCSV.append(df)

    if not os.path.exists(f"files/{id}"):
        os.makedirs(f"files/{id}")

    with open(f'files/{id}/export.json', 'w') as f:
        json.dump(rowsJSON, f)

    with open(f'files/{id}/export.csv', 'w', encoding='UTF8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=rowsJSON[0].keys())
        writer.writeheader()
        writer.writerows(rowsCSV)

def exportmeta(id):
    ass = Assessment.objects(id=id).first()

    if not os.path.exists(f"files/"):
        os.makedirs(f"files")

    with open(f'files/{id}/meta.json', 'w') as f:
        json.dump(ass.to_json(), f)

def exportentire(id):
    name = Assessment.objects(id=id).first()["name"]

    exporttemplate(id)
    exportassessment("csv", id)
    exportmeta(id)

    shutil.make_archive("files/" + id, 'zip', "files/" + id)

def exportAssessments ():
    for ass in Assessment.objects().all():
        try:
            exportentire(str(ass.id))
        except:
            pass

exportAssessments()
