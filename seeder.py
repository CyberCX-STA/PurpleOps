import os
import re
import sys
import yaml
import uuid
import shutil
import dotenv
import secrets
import requests
import passlib.totp
from model import *
from git import Repo
from glob import glob
from flask import Flask
from openpyxl import load_workbook

dotenvFile = dotenv.find_dotenv()
dotenv.load_dotenv(dotenvFile)

PWD = os.getcwd()

app = Flask(__name__)
app.config.from_pyfile("flask.cfg")
db.init_app(app)

if not os.path.exists(f"{PWD}/external/"):
    os.makedirs(f"{PWD}/external")

###

def pullMitreAttack (component):
    # Pull the HTML page to find and download the link to the latest framework version
    req = requests.get(f"https://attack.mitre.org/versions/v15/docs/enterprise-attack-v15.1/enterprise-attack-v15.1-{component}.xlsx")
    if req.status_code == 200:
        #req = r.text.split('"')
        #url = [x for x in req if "xlsx" in x and "enterprise" in x and "docs" in x and component in x][0]
        #req = requests.get("https://attack.mitre.org" + url)
        with open(f"{PWD}/external/mitre-{component}.xlsx", "wb") as mitreXLSX:
            mitreXLSX.write(req.content)

        wb = load_workbook(f"{PWD}/external/mitre-{component}.xlsx", read_only=True)
        ws = wb.active

        headers = [col.value for col in list(ws.rows)[0]]

        return [ws.rows, headers]
    else:
        print(f"Failed getting information from MITRE [{req.status_code}]")
        sys.exit()
        
def parseMitreTactics ():
    rows, headers = pullMitreAttack("tactics")
    for row in rows:
        if row[0].value == "ID": # Skip header row
            continue
        Tactic(
            mitreid = row[headers.index("ID")].value,
            name = row[headers.index("name")].value
        ).save()

def parseMitreTechniques ():
    rows, headers = pullMitreAttack("techniques")
    for row in rows:
        if row[0].value == "ID": # Skip header row
            continue
        Technique(
            mitreid = row[headers.index("ID")].value,
            name = row[headers.index("name")].value,
            description = row[headers.index("description")].value,
            detection = row[headers.index("detection")].value or "Missing data.",
            tactics = row[headers.index("tactics")].value.split(",")
        ).save()

        # Include a default reporting writeup - can be overwritten with customs
        KnowlegeBase(
            mitreid = row[headers.index("ID")].value,
            overview = row[headers.index("description")].value,
            advice = row[headers.index("detection")].value or "Missing data.",
            provider = "MITRE"
        ).save()

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
            Sigma(
                mitreid = ttp,
                name = yml["title"],
                description = yml["description"],
                url=url
            ).save()

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
                
                TestCaseTemplate(
                    name = artTestcase["name"],
                    mitreid = yml["attack_technique"],
                    # Infer the relevant tactic from the first match from MITRE techniques
                    tactic = Technique.objects(mitreid=yml["attack_technique"]).first()["tactics"][0],
                    objective = artTestcase["description"],
                    actions = baseCommand,
                    provider = "ART"
                ).save()

def parseCustomTestcases ():
    for customTestcase in glob(f'{PWD}/custom/testcases/*.yaml'):
        with open(customTestcase, "r") as customTestcaseFile:
            yml = yaml.safe_load(customTestcaseFile)

        TestCaseTemplate(
            name = yml["name"],
            mitreid = yml["mitreid"],
            tactic = yml["tactic"],
            objective = yml["objective"],
            actions = yml["actions"],
            provider = yml["provider"]
        ).save()

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

def prepareRolesAndAdmin ():
    if Role.objects().count() == 0:
        for role in ["Admin", "Red", "Blue", "Spectator"]:
            roleObj = Role(name=role)
            roleObj.save()
    
    if User.objects().count() == 0:
        password = str(uuid.uuid4())
        dotenv.set_key(dotenvFile, "POPS_ADMIN_PWD", password)
        # TODO set to invalid email
        user_datastore.create_user(
            email = 'admin@purpleops.com',
            username = 'admin',
            password = password,
            roles = [Role.objects(name="Admin").first()],
            initpwd = False
        )
        print("==============================================================\n\n\n")
        print(f"\tCreated initial admin: U: admin@purpleops.com P: {password}")
        print("\n\n\n==============================================================")

def populateSecrets ():
    if Role.objects().count() == 0:
        dotenv.set_key(
            dotenvFile,
            "FLASK_SECURITY_PASSWORD_SALT",
            str(secrets.SystemRandom().getrandbits(128))
        )
        dotenv.set_key(
            dotenvFile,
            "FLASK_SECRET_KEY",
            secrets.token_urlsafe()
        )
        dotenv.set_key(
            dotenvFile,
            "FLASK_SECURITY_TOTP_SECRETS",
            f"{{1: {passlib.totp.generate_secret()}}}"
        )

#####

if Tactic.objects.count() == 0:
    print("==============================================================\n\n\n")
    print(f"\t NEW INSTANCE DETECTED, LETS GET THE DATA WE NEED")
    print("\n\n\n==============================================================")
    
    Tactic.objects.delete()
    Technique.objects.delete()
    Sigma.objects.delete()
    TestCaseTemplate.objects.delete()
    KnowlegeBase.objects.delete()
    # Role.objects.delete()
    # User.objects.delete()

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

    print("Populating (randomising) secrets")
    populateSecrets()

    print("Preparing roles and initial admin")
    prepareRolesAndAdmin()
