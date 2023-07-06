from copy import deepcopy
from model import *
from utils import applyFormData
from flask_security import auth_required, current_user, roles_accepted
from flask import Blueprint, render_template, redirect, request, session

blueprint_assessment_utils = Blueprint('blueprint_assessment_utils', __name__)

@blueprint_assessment_utils.route('/assessment/update/<id>', methods = ['POST'])
@auth_required()
@roles_accepted('Admin', 'Red')
def updateassessment(id):
    if request.method == 'POST':
        ass = Assessment.objects(id=id).first()
        
        fields = ["name", "description", "industry", "techmaturity", "opmaturity", "socmodel", "socprovider", "webhook"]
        ass = applyFormData(ass, request.form, fields)

        ass.save()
        return ('', 204)

@blueprint_assessment_utils.route('/assessment/clone/<id>', methods = ['GET'])
@auth_required()
@roles_accepted('Admin', 'Red')
def duplicateassessment(id):
    if request.method == 'GET':
        ass = Assessment.objects(id=id).first()
        newAss = deepcopy(ass)
        newAss.id = None
        newAss.name = "Copy of " + ass.name
        newAss.save()

        tests = TestCase.objects(assessmentid=id)
        for test in tests:
            newcase = TestCase()
            newcase.assessmentid=str(newAss.id)

            copy = ["name", "overview", "objective", "actions", "advice", "rednotes", "mitreid", "tactic", "tools", "references", "kbentry"]
            for field in copy:
                newcase[field] = test[field]

            newcase.save()

        return jsonify({"id": str(newAss.id)})



@blueprint_assessment_utils.route('/assessment/delete/<id>',methods = ['GET'])
@auth_required()
@roles_accepted('Admin', 'Red')
def deleteassessment(id):
    TestCase.objects(assessmentid=id).delete()
    Assessment.objects(id=id).delete()
    return redirect(f"/")

@blueprint_assessment_utils.route('/assessment/stats/<id>',methods = ['GET'])
@auth_required()
def assessmentstats(id):
    session["assessmentid"] = id
    tests = TestCase.objects(assessmentid=id).all()
    ass = Assessment.objects(id=id).first()
    mitres = [[m["mitreid"], m["name"]] for m in Technique.objects()]
    mitres.sort(key=lambda x: x[0])
    
    stats = generatestats(tests, ass)

    return render_template('assessment.stats.html', stats=stats, assid=id) 

@blueprint_assessment_utils.route('/assessment/<field>/<id>',methods = ['POST', 'GET'])
@auth_required()
def manageengagmentdata(field, id):
    assessment = Assessment.objects(id=id).first()
    if field not in ["sources", "targets", "tools", "controls", "tags"]:
        return ('', 418)
    if request.method == 'POST':
        if current_user.has_role("Spectator"):
            return ('', 204)
        delFieldIDs = [str(item.id) for item in assessment[field]]
        for item in request.json:
            # New item
            if str(item["id"]) == "0":
                if field == "sources":
                    newObj = Source(name=item["name"], description=item["description"])
                elif field == "targets":
                    newObj = Target(name=item["name"], description=item["description"])
                elif field == "tools":
                    newObj = Tool(name=item["name"], description=item["description"])
                elif field == "controls":
                    newObj = Control(name=item["name"], description=item["description"])
                elif field == "tags":
                    if "colour" not in item:
                        item["colour"] = "#ff0000"
                    newObj = Tag(name=item["name"], colour=item["colour"])
                assessment[field].append(newObj)
                assessment[field].save()
            # Update old
            else:
                delFieldIDs.remove(item["id"])
                oldObj = assessment[field].filter(id=item["id"]).first()
                oldObj.name = item["name"]
                if field != "tags":
                    oldObj.description = item["description"]
                else:
                    oldObj.colour = item["colour"] or "#000"
                assessment[field].save()
        for delID in delFieldIDs:
            if field == "sources":
                assessment.update(pull__sources__id=delID)
            elif field == "targets":
                assessment.update(pull__targets__id=delID)
            elif field == "tools":
                assessment.update(pull__tools__id=delID)
            elif field == "controls":
                assessment.update(pull__controls__id=delID)
            elif field == "tags":
                assessment.update(pull__tags__id=delID)
        return ('', 204)
    else:
        return assessment.to_json_data(field)

def generatestats(tests, ass):
    # Initalise metrics that are captured
    stats = {
        "All": {
            "blocked": 0,
            "alerted": 0,
            "logged": 0,
            "missed": 0,

            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "informational": 0,

            "scoresPrevent": [],
            "scoresDetect": [],

            "priorityType": [],
            "priorityUrgency": [],

            "controls": []
        }
    }

    # What MITRE tactics do we currently have data for?
    activeTactics = list(set([t["tactic"] for t in tests if t["state"] == "Complete"]))

    for testcase in tests:
        if testcase["tactic"] in activeTactics:
            # Initalise tactic if not in the dataframe yet
            if testcase["tactic"] not in stats:
                stats[testcase["tactic"]] = deepcopy(stats["All"])

            # Populate blocked/alerted/logged/missed stats
            # NOTE: If a testcase is both alerted and blocked, it will be
            # counted twice
            if testcase["blocked"] == "Yes" or testcase["blocked"] == "Partial":
                stats[testcase["tactic"]]["blocked"] += 1

            if testcase["alerted"] == "Yes":
                stats[testcase["tactic"]]["alerted"] += 1
                if testcase["alertseverity"]:
                    stats[testcase["tactic"]][testcase["alertseverity"].lower()] += 1

            if testcase["logged"] == "Yes":
                stats[testcase["tactic"]]["logged"] += 1

            if testcase["blocked"] == "No" and testcase["alerted"] == "No" and testcase["logged"] == "No":
                stats[testcase["tactic"]]["missed"] += 1

            # Store scores to later average with
            stats[testcase["tactic"]]["scoresPrevent"].append(float(testcase["blockedrating"] or "0.0"))
            stats[testcase["tactic"]]["scoresDetect"].append(float(testcase["detectionrating"] or "0.0"))

            # Collate priorities, ratings and blue tools
            if testcase["priority"]:
                stats[testcase["tactic"]]["priorityType"].append(testcase["priority"])
            if testcase["priorityurgency"]:
                stats[testcase["tactic"]]["priorityUrgency"].append(testcase["priorityurgency"])
            if testcase["controls"]:
                names = [[k["name"] for k in ass["controls"] if str(k["id"]) == i][0] for i in testcase["controls"]]
                stats[testcase["tactic"]]["controls"].extend(names)

    # We've populated per-tactic data, this function adds it all together for
    # an "All" tactic
    for tactic in stats:
        if tactic == "All":
            continue
        for key in ["blocked", "alerted", "logged", "missed", "critical", "high", "medium", "low", "informational"]:
            stats["All"][key] += stats[tactic][key]
        for key in ["scoresPrevent", "scoresDetect", "priorityType", "priorityUrgency", "controls"]:
            stats["All"][key].extend(stats[tactic][key])

    return stats