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

# Adjust for local dev
PWD = "/home/harrison/Tools/PurpleOps"

app = Flask(__name__)
app.config['MONGODB_SETTINGS'] = {
    'db': 'assessments',
    'host': 'localhost',
    'port': 27017
}
app.secret_key = "marc-hates-edward"

db = getdb()
db.init_app(app)

if not os.path.exists(f"{PWD}/external/"):
    os.makedirs(f"{PWD}/external")

###

def pullMitreAttack (component):
    # Pull the HTML page to find and download the link to the latest framework version
    req = requests.get("https://attack.mitre.org/resources/working-with-attack/").text.split('"')
    url = [x for x in req if "xlsx" in x and "enterprise" in x and "docs" in x and component in x][0]
    req = requests.get("https://attack.mitre.org" + url)
    with open(f"{PWD}/external/mitre-{component}.xlsx", "wb") as mitreXLSX:
        mitreXLSX.write(req.content)

    wb = load_workbook(f"{PWD}/external/mitre-{component}.xlsx", read_only=True)
    ws = wb.active

    headers = [col.value for col in list(ws.rows)[0]]

    return [ws.rows, headers]

def parseMitreTactics ():
    rows, headers = pullMitreAttack("tactics")
    for row in rows:
        if row[0].value == "ID": # Skip header row
            continue
        tactic = Tactic()
        tactic.mitreid = row[headers.index("ID")].value
        tactic.name = row[headers.index("name")].value
        tactic.save()

def parseMitreTechniques ():
    rows, headers = pullMitreAttack("techniques")
    for row in rows:
        if row[0].value == "ID": # Skip header row
            continue
        technique = Technique()
        technique.mitreid = row[headers.index("ID")].value
        technique.name = row[headers.index("name")].value
        technique.description = row[headers.index("description")].value
        technique.detection = row[headers.index("detection")].value or "Missing data."
        technique.tactics = row[headers.index("tactics")].value.split(",")
        technique.save()

        # Include a default reporting writeup - can be overwritten with customs
        kb = KnowlegeBase()
        kb.mitreid = technique.mitreid
        kb.overview = technique.description
        kb.advice = technique.detection
        kb.provider = "MITRE"
        kb.save()

def pullSigma ():
    if os.path.exists(f"{PWD}/external/sigma") and os.path.isdir(f"{PWD}/external/sigma"):
        shutil.rmtree(f"{PWD}/external/sigma")
    Repo.clone_from("https://github.com/SigmaHQ/sigma", f"{PWD}/external/sigma")

def parseSigma ():
    pullSigma()
    for sigmaRule in glob(f'{PWD}/external/sigma/rules/**/*.yml', recursive=True):
        with open(sigmaRule, "r") as sigmaFile:
            yml = yaml.safe_load(sigmaFile)

        url = "https://github.com/SigmaHQ/sigma/blob/master/rules"
        url += sigmaRule.replace(f"{PWD}/external/sigma/rules", "")

        # ART stores relevant MitreIDs in tags, parse them out
        associatedTTP = []
        if "tags" in yml:
            for tag in yml["tags"]:
                search = re.search(r'attack\.([tT]\d\d\d\d(\.\d\d\d)*)', tag)
                if search:
                    associatedTTP.append(search.group(1).upper())

        for ttp in associatedTTP:
            sigma = Sigma()
            sigma.mitreid = ttp
            sigma.title = yml["title"]
            sigma.description = yml["description"]
            sigma.url=url
            sigma.save()

def pullAtomicRedTeam ():
    if os.path.exists(f"{PWD}/external/art") and os.path.isdir(f"{PWD}/external/art"):
        shutil.rmtree(f"{PWD}/external/art")
    Repo.clone_from("https://github.com/redcanaryco/atomic-red-team", f"{PWD}/external/art")

def parseAtomicRedTeam ():
    pullAtomicRedTeam()
    for artTestcases in glob(f'{PWD}/external/art/atomics/T*/*.yaml', recursive=True):
        with open(artTestcases, "r") as artFile:
            yml = yaml.safe_load(artFile)
            
        for artTestcase in yml["atomic_tests"]:
            # If there's no command, then we don't want it
            if "command" in artTestcase["executor"]:
                baseCommand = artTestcase["executor"]["command"].strip()
                # If there's variables in the command, populate it with the
                # default sample variables e.g. #{dumpname} > lsass.dmp
                if "input_arguments" in artTestcase:
                    for i in artTestcase["input_arguments"].keys():
                        k = "#{" + i + "}"
                        baseCommand = baseCommand.replace(k, str(artTestcase["input_arguments"][i]["default"]))
                
                template = TestCaseTemplate()
                template.name = artTestcase["name"]
                template.mitreid = yml["attack_technique"]
                # Infer the relevant phase from the first match from MITRE techniques
                template.phase = Technique.objects(mitreid=template.mitreid).first()["tactics"][0]
                template.objective = artTestcase["description"]
                template.actions = baseCommand
                template.provider = "ART"
                template.save()

def parseCustomTestcases ():
    for customTestcase in glob(f'{PWD}/custom/testcases/*.yaml'):
        with open(customTestcase, "r") as customTestcaseFile:
            yml = yaml.safe_load(customTestcaseFile)

        template = TestCaseTemplate()
        template.name = yml["name"]
        template.mitreid = yml["mitreid"]
        template.phase = yml["phase"]
        template.objective = yml["objective"]
        template.actions = yml["actions"]
        template.rednotes = yml["rednotes"]
        template.provider = yml["provider"]
        template.save()

def parseCustomKBs ():
    for customKB in glob(f'{PWD}/custom/knowledgebase/*.yaml'):
        with open(customKB, "r") as customKBFile:
            yml = yaml.safe_load(customKBFile)

        # Overwrite the reporting KB for the mitre id with the custom writeup
        KB = KnowlegeBase.objects(mitreid=yml["mitreid"]).first()
        KB.overview = yml["overview"]
        KB.advice = yml["advice"]
        KB.provider = yml["provider"]
        KB.save()

#####

print("Clearing old gubbs")
Tactic.objects.delete()
Technique.objects.delete()
Sigma.objects.delete()
TestCaseTemplate.objects.delete()
KnowlegeBase.objects.delete()

print("Pulling MITRE tactics")
parseMitreTactics()

print("Pulling MITRE techniques")
parseMitreTechniques()

print("Pulling SIGMA detections")
parseSigma()

print("Pulling Atomic Red Team testcases")
parseAtomicRedTeam()

print("Parsing Custom testcases")
parseCustomTestcases()

print("Parsing Custom KBs")
parseCustomKBs()
