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
PWD = "/opt/purpleops"

app = Flask(__name__)
app.config['MONGODB_SETTINGS'] = {
    'db': 'assessments',
    'host': 'localhost',
    'port': 27017
}
app.secret_key = "marc-hates-edward"

db = getdb()
db.init_app(app)

def parseTFile(path):
    cObjective = "[objective]"
    cDetection = "[detection]"
    cReference = "[reference]"

    if os.path.isfile(path):
        raw = open(path, encoding="utf8").read()
        objective = raw[len(cObjective):raw.find(cDetection) -1].strip().replace("\n", "\n\r")
        detection = raw[raw.find(cDetection) + len(cDetection):raw.find(cReference) -1].strip().replace("\n", "\n\r").replace("█", "- ").replace("▓", "  ").replace("▒", "  - ").replace("░", "    ").replace("\n\n", "\n")
        if detection.count("`") and detection.count("`") % 2 == 0:
            while "`" in detection:
                detection = detection.replace("`", "<i>", 1)
                detection = detection.replace("`", "</i>", 1)
        reference = []
        rr = raw[raw.find(cReference) + len(cReference):]
        for r in rr.split("\n"):
            if r.startswith("█"):
                reference.append({"name": r[1:].strip()})
            if r.startswith("▓"):
                reference[-1]["link"] = r[1:].strip()
        return {"detection": detection, "objective": objective, "reference": reference}
    return 


def parseArtFile(technique):
    art = None
    path = f"{PWD}/external/art/atomics/{technique}/{technique}.yaml"
    if os.path.isfile(path):
        raw = open(path).read()
        art = yaml.safe_load(raw)
    return art


def artToHTML(arts, art):
    html  = f"<h3>{arts['attack_technique']} - {arts['display_name']}</h3>"
    html += f"<h2>{art['name']}</h2>"
    reqs = []
    if "elevation_required" in art["executor"]:
        reqs.append("Local Admin")
    if "name" in art["executor"]:
        reqs.append(art["executor"]["name"].replace('command_prompt', "cmd").title())
    if "supported_platforms" in art:
        [reqs.append(p.title()) for p in art["supported_platforms"]]
    if reqs:
        html += f"<p><b>Context:</b> {', '.join(reqs)}</p>"
    if "command" in art["executor"]:
        html += f"<pre><code>{art['executor']['command']}</pre></code>"
    else:
        html += f"<pre><code>NO COMMAND FOUND</pre></code>"
    html += f"<p><b>Description:</b> {art['description']}</p>"
    if "dependencies" in art:
        for req in art["dependencies"]:
            html += f"<p><b>Prereq:</b> {req['description']}</p>\n<pre><code>{req['prereq_command']}</code></pre>"
    if "cleanup_command" in art["executor"]:
        html += f"<p><b>Cleanup:</b></p>\n<pre><code>{art['executor']['cleanup_command']}</pre></code>"
    return html

def ccxToHTML(test):
    html  = f"<h3>{test['mitreid']} - {test['mitretitle']}</h3>"
    html += f"<h2>{test['name']}</h2>"
    html += f"<pre><code>{test['actions']}</pre></code>"
    html += f"<p><b>Objective:</b> {test['objective']}</p>"
    if test["notes"]:
        html += f"<p><b>Notes:</b> {test['notes']}</p>"
    return html


print("Clearing old gubbs")
TestCaseTemplate.objects.delete()
KnowlegeBase.objects.delete()
Sigma.objects.delete()
Tactic.objects.delete()
Technique.objects.delete()


# ART

def art ():
    if os.path.exists(f"{PWD}/external/art") and os.path.isdir(f"{PWD}/external/art"):
        shutil.rmtree(f"{PWD}/external/art")
    Repo.clone_from("https://github.com/redcanaryco/atomic-red-team", f"{PWD}/external/art")

# SIGMA

def sigma ():
    if os.path.exists(f"{PWD}/external/sigma") and os.path.isdir(f"{PWD}/external/sigma"):
        shutil.rmtree(f"{PWD}/external/sigma")
    Repo.clone_from("https://github.com/SigmaHQ/sigma", f"{PWD}/external/sigma")

    for f in glob(f'{PWD}/external/sigma/rules/**/*.yml', recursive=True):
        with open(f, "r") as sigmaf:
            raw = sigmaf.read()
        with open(f, "r") as sigmaf:
            yml = yaml.safe_load(sigmaf)
        title = yml["title"]
        desc = yml["description"]
        file = f.split("/")[-1]
        ref = "https://github.com/SigmaHQ/sigma/blob/master/rules" + f.replace(f"{PWD}/external/sigma/rules", "")
        ttps = []
        if "tags" in yml:
            for tag in yml["tags"]:
                if re.search(r'attack\.([tT]\d\d\d\d(\.\d\d\d)*)', tag):
                    ttps.append(re.search(r'attack\.([tT]\d\d\d\d(\.\d\d\d)*)', tag).group(1).upper())
        for ttp in ttps:
            sigma = Sigma(mitreid=ttp, name=title, description=desc, filename=file, ref=ref, raw=raw)
            sigma.save()

# MITRE Tactic

def importTactics ():
    r = requests.get("https://attack.mitre.org/resources/working-with-attack/").text.split('"')
    url = [x for x in r if "xlsx" in x and "enterprise" in x and "docs" in x and "tactics" in x][0]
    r = requests.get("https://attack.mitre.org" + url)
    with open(f"{PWD}/external/mitre-tactics.xlsx", "wb") as mitre:
        mitre.write(r.content)

    wb = load_workbook(f"{PWD}/external/mitre-tactics.xlsx", read_only=True)
    ws = wb.active

    headers = [c.value for c in list(ws.rows)[0]]

    for row in ws.rows:
        if row[0].value == "ID":
            continue
        tactic = Tactic()
        tactic.mitreid = row[headers.index("ID")].value
        tactic.name = row[headers.index("name")].value
        tactic.description = row[headers.index("description")].value
        tactic.url = row[headers.index("url")].value
        tactic.created = row[headers.index("created")].value
        tactic.lastmodified = row[headers.index("last modified")].value
        tactic.save()
        
    return

# MITRE Technique

def importTechniques ():
    r = requests.get("https://attack.mitre.org/resources/working-with-attack/").text.split('"')
    url = [x for x in r if "xlsx" in x and "enterprise" in x and "docs" in x and "techniques" in x][0]
    r = requests.get("https://attack.mitre.org" + url)
    with open(f"{PWD}/external/mitre-techniques.xlsx", "wb") as mitre:
        mitre.write(r.content)

    wb = load_workbook(f"{PWD}/external/mitre-techniques.xlsx", read_only=True)
    ws = wb.active

    headers = [c.value for c in list(ws.rows)[0]]

    for row in ws.rows:
        if row[0].value == "ID":
            continue
        technique = Technique()
        technique.mitreid = row[headers.index("ID")].value
        technique.name = row[headers.index("name")].value
        technique.description = row[headers.index("description")].value
        technique.url = row[headers.index("url")].value
        technique.created = row[headers.index("created")].value
        technique.lastmodified = row[headers.index("last modified")].value
        technique.version = row[headers.index("version")].value
        if row[headers.index("tactics")].value:
            technique.tactics = row[headers.index("tactics")].value.split(",")
        if row[headers.index("detection")].value:
            technique.detection = row[headers.index("detection")].value
        if row[headers.index("platforms")].value:
            technique.platforms = row[headers.index("platforms")].value.split(",")
        if row[headers.index("data sources")].value:
            technique.datasources = row[headers.index("data sources")].value.split(",")
        technique.issubtechnique = str(row[headers.index("is sub-technique")].value)
        if row[headers.index("sub-technique of")].value:
            technique.subtechniqueof = row[headers.index("sub-technique of")].value
        technique.contributors = row[headers.index("contributors")].value
        if row[headers.index("system requirements")].value:
            technique.requirements = row[headers.index("system requirements")].value.split(",")
        if row[headers.index("permissions required")].value:
            technique.permissionsrequired = row[headers.index("permissions required")].value.split(",")
        if row[headers.index("effective permissions")].value:
            technique.effectivepermissions = row[headers.index("effective permissions")].value
        if row[headers.index("defenses bypassed")].value:
            technique.defensesbypassed = row[headers.index("defenses bypassed")].value.split(",")
        technique.impacttype = row[headers.index("impact type")].value
        technique.supportsremote = str(row[headers.index("supports remote")].value)
        technique.save()
        
    return 

def masta ():
    for technique in Technique.objects().all():
        artitem = os.path.isfile(f"{PWD}/external/art/{technique.mitreid}/{technique.mitreid}.yaml")
        ccxitem = os.path.isfile(f"{PWD}/external/ccxatomics/{technique.mitreid}.yaml")
        tfiledata = parseTFile(f"{PWD}/external/twilight/ttp/{technique.mitreid}.txt")

        if tfiledata:        
            kb = KnowlegeBase(mitreid=technique.mitreid, overview=tfiledata["objective"],advice=tfiledata["detection"] )
            for i in tfiledata["reference"]:
                r = Reference(name=i["name"], url=i["link"])
                kb.references.append(r)
            kb.save()

        try: art = parseArtFile(technique.mitreid)
        except: art = None
        kb = KnowlegeBase.objects(mitreid=technique.mitreid).first()
        if art:
            for arttest in art["atomic_tests"]:
                if "command" in arttest["executor"]:
                    if "input_arguments" in arttest:
                        basecommand = arttest["executor"]["command"]
                        for i in arttest["input_arguments"].keys():
                            k = "#{" + i + "}"
                            basecommand = basecommand.replace(k, str(arttest["input_arguments"][i]["default"]))
                        tmpl = TestCaseTemplate.objects(mitreid=technique.mitreid, name=arttest["name"], provider="ART").first()
                        if not tmpl:
                            tmpl = TestCaseTemplate()
                            tmpl.mitreid = technique.mitreid
                            tmpl.name = arttest["name"]
                            tmpl.provider = "ART"
                            if kb:
                                tmpl.overview = kb.overview
                                tmpl.advice = kb.advice
                                tmpl.kbentry = True
                            else:
                                tmpl.overview = technique.description
                            tmpl.objective = arttest["description"]
                            tmpl.actions = basecommand.strip()
                            tmpl.html = artToHTML(art, arttest)
                            tmpl.phase = Technique.objects(mitreid=technique.mitreid).first()["tactics"][0]
                            tmpl.mitretitle = Technique.objects(mitreid=technique.mitreid).first()["name"]
                            tmpl.save()

        if ccxitem:
            raw = open(f"{PWD}/external/ccxatomics/{technique.mitreid}.yaml").read()
            ccx = yaml.safe_load(raw)
            for test in ccx["tests"]:
                tmpl = TestCaseTemplate.objects(mitreid=technique.mitreid, name=test["name"], provider="CCX").first()
                if not tmpl:
                    tmpl = TestCaseTemplate()
                    tmpl.name = test["name"].strip()
                    tmpl.objective = test["description"].strip()
                    tmpl.actions = test["command"].strip()
                    tmpl.provider = "CCX"
                    if "notes" in test and test["notes"].strip():
                        tmpl.notes = test["notes"].strip()
                    tmpl.mitreid = technique.mitreid
                    tmpl.mitretitle = Technique.objects(mitreid=technique.mitreid).first()["name"]
                    tmpl.phase = Technique.objects(mitreid=technique.mitreid).first()["tactics"][0]
                    if kb:
                        tmpl.overview = kb.overview
                        tmpl.advice = kb.advice
                        tmpl.kbentry = True
                    tmpl.html = ccxToHTML(tmpl)
                    tmpl.save()

print("Ingesting Atomic Red Team")
art()
print("Ingesting SIGMA Rules")
sigma()
print("Ingesting MITRE Tactics")
importTactics()
print("Ingesting MITRE Techniques")
importTechniques()
print("XREF'ing Everything")
masta()
