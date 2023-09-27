import secrets
from model import *
from time import time
from copy import deepcopy
from utils import user_assigned_assessment
from flask_security import auth_required, roles_accepted, current_user
from blueprints.assessment_export import exportnavigator
from flask import Blueprint, render_template, request, send_from_directory, make_response, jsonify

blueprint_assessment_utils = Blueprint('blueprint_assessment_utils', __name__)

@blueprint_assessment_utils.route('/assessment/<id>/multi/<field>', methods = ['POST'])
@auth_required()
@roles_accepted('Admin', 'Red', 'Blue')
@user_assigned_assessment
def assessmentmulti(id, field):
    if field not in ["sources", "targets", "tools", "controls", "tags"]:
        return '', 418
    
    assessment = Assessment.objects(id=id).first()

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

    return jsonify(assessment.multi_to_json(field)), 200

@blueprint_assessment_utils.route('/assessment/<id>/navigator', methods = ['GET'])
@auth_required()
@user_assigned_assessment
def assessmentnavigator(id):
    assessment = Assessment.objects(id=id).first()

    # Create and store one-time secret; timestamp and ip for later comparison in
    # the unauthed `thisurl`.json endpoint
    secret = secrets.token_urlsafe()
    assessment.navigatorexport = f"{int(time())}|{request.remote_addr}|{secret}"
    assessment.save()

    exportnavigator(id)

    return render_template('assessment_navigator.html', assessment=assessment, secret=secret)

@blueprint_assessment_utils.route('/assessment/<id>/navigator.json', methods = ['GET'])
def assessmentnavigatorjson(id):
    assessment = Assessment.objects(id=id).first()
    timestamp, ip, secret = assessment.navigatorexport.split("|")
    
    # This endpoint is unauthed so that we can embed the ATT&CK Navigator and
    # allow it to fetch a layer.json on behalf of the user. To mitigate security issues
    # the endpoint needs to be hit
    # 1. Within 10 seconds of hitting the authed endpoint /assessment/<id>/navigator
    # 2. With the same IP used to his the above authed endpoint
    # 3. With a one-time secret key returned in the above authed endpoint
    # 4. From the mitre-attack origin (yes this is spoofable, but why not)
    # if (int(time()) - int(timestamp) <= 30 and
        #request.remote_addr == ip and
        # request.args.get("secret") == secret): # and
        #request.origin == "https://mitre-attack.github.io"):
    response = make_response(send_from_directory('files', f"{id}/navigator.json"))
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

    return "", 401

@blueprint_assessment_utils.route('/assessment/<id>/stats',methods = ['GET'])
@auth_required()
@user_assigned_assessment
def assessmentstats(id):
    assessment = Assessment.objects(id=id).first()
    if current_user.has_role("Blue"):
        testcases = TestCase.objects(assessmentid=str(assessment.id), visible=True).all()
    else:
        testcases = TestCase.objects(assessmentid=str(assessment.id)).all()

    # Initalise metrics that are captured
    stats = {
        "All": {
            "Prevented": 0, "Alerted": 0, "Logged": 0, "Missed": 0,
            "Critical": 0, "High": 0, "Medium": 0, "Low": 0, "Informational": 0,
            "scoresPrevent": [], "scoresDetect": [],
            "priorityType": [], "priorityUrgency": [],
            "controls": []
        }
    }

    # What MITRE tactics do we currently have data for?
    activeTactics = list(set([t["tactic"] for t in testcases if t["state"] == "Complete"]))

    for testcase in testcases:
        if testcase["tactic"] in activeTactics:
            # Initalise tactic if not in the dataframe yet
            if testcase["tactic"] not in stats:
                stats[testcase["tactic"]] = deepcopy(stats["All"])

            # Populate prevented/alerted/logged/missed stats
            if testcase["outcome"]:
                stats[testcase["tactic"]][testcase["outcome"]] += 1

            # Populate alert severities
            if testcase["alertseverity"]:
                stats[testcase["tactic"]][testcase["alertseverity"]] += 1

            # Store scores to later average with
            if testcase["preventedrating"] and testcase["preventedrating"] != "N/A":
                stats[testcase["tactic"]]["scoresPrevent"].append(float(testcase["preventedrating"]))
            if testcase["detectionrating"]:
                stats[testcase["tactic"]]["scoresDetect"].append(float(testcase["detectionrating"]))

            # Collate priorities, ratings and controls
            if testcase["priority"] and testcase["priority"] != "N/A":
                stats[testcase["tactic"]]["priorityType"].append(testcase["priority"])
            if testcase["priorityurgency"] and testcase["priorityurgency"] != "N/A":
                stats[testcase["tactic"]]["priorityUrgency"].append(testcase["priorityurgency"])
            if testcase["controls"]:
                controls = []
                for control in testcase["controls"]:
                    controls.append([c.name for c in assessment.controls if str(c.id) == control][0])
                stats[testcase["tactic"]]["controls"].extend(controls)

    # We've populated per-tactic data, this function adds it all together for an "All" tactic
    for tactic in stats:
        if tactic == "All":
            continue
        for key in ["Prevented", "Alerted", "Logged", "Missed", "Critical", "High", "Medium", "Low", "Informational"]:
            stats["All"][key] += stats[tactic][key]
        for key in ["scoresPrevent", "scoresDetect", "priorityType", "priorityUrgency", "controls"]:
            stats["All"][key].extend(stats[tactic][key])

    return render_template(
        'assessment_stats.html',
        assessment=assessment,
        stats=stats,
        hexagons=assessmenthexagons(id)
    ) 

@blueprint_assessment_utils.route('/assessment/<id>/assessment_hexagons.svg',methods = ['GET'])
@auth_required()
@user_assigned_assessment
def assessmenthexagons(id):
    # Use SVG to create the hexagon graph because making a hex grid in HTML is a no
    tactics = ["Execution", "Command and Control", "Discovery", "Persistence", "Privilege Escalation", "Credential Access", "Lateral Movement", "Exfiltration", "Impact"]

    shownHexs = []
    hiddenHexs = []
    for i in range(len(tactics)):
        if not TestCase.objects(assessmentid=id, tactic=tactics[i], state="Complete").count():
            hiddenHexs.append({
                "display": "none",
                "stroke": "#ffffff",
                "fill": "#ffffff",
                "arrow": "rgba(0, 0, 0, 0)",
                "text": ""
            })
            continue
            
        score = (TestCase.objects(assessmentid=id, tactic=tactics[i], outcome="Prevented").count() +
                TestCase.objects(assessmentid=id, tactic=tactics[i], outcome="Alerted").count() -
                TestCase.objects(assessmentid=id, tactic=tactics[i], outcome="Missed").count())
        if score > 1:
            color = "#B8DF43"
        elif score < -1:
            color = "#FB6B64"
        else:
            color = "#FFC000"

        shownHexs.append({
            "display": "block",
            "stroke": color,
            "fill": "#eeeeee",
            "arrow": "rgb(0, 0, 0)",
            "text": tactics[i]
        })

    # Dynamic SVG height and width depending on # hexs as CSS has no visibility
    # over which hexs are shown so we can center it for prettyness
    if len(shownHexs) == 0:
        height = 0
    if len(shownHexs) <= 4:
        height = 115
    elif len(shownHexs) <= 7:
        height = 230
    else:
        height = 347

    if len(shownHexs) == 0:
        width = 0
    if len(shownHexs) == 1:
        width = 100
    elif len(shownHexs) == 2:
        width = 240
    elif len(shownHexs) == 3:
        width = 380
    else:
        width = 517
        
    return render_template('assessment_hexagons.svg', hexs = [*shownHexs, *hiddenHexs], height = height, width = width)