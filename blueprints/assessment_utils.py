from copy import deepcopy
from model import *
from utils import applyFormData
from flask_security import auth_required, current_user, roles_accepted
from flask import Blueprint, render_template, redirect, request, session

blueprint_assessment_utils = Blueprint('blueprint_assessment_utils', __name__)

@blueprint_assessment_utils.route('/assessment/multi/<field>', methods = ['POST'])
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

# @blueprint_assessment_utils.route('/assessment/stats/<id>',methods = ['GET'])
# @auth_required()
# def assessmentstats(id):
#     session["assessmentid"] = id
#     testcases = TestCase.objects(assessmentid=id).all()
#     ass = Assessment.objects(id=id).first()
#     mitres = [[m["mitreid"], m["name"]] for m in Technique.objects()]
#     mitres.sort(key=lambda x: x[0])
    
#     stats = generatestats(testcases, ass)

#     return render_template('assessment.stats.html', stats=stats, assid=id) 


# def generatestats(testcases, ass):
#     # Initalise metrics that are captured
#     stats = {
#         "All": {
#             "prevented": 0,
#             "alerted": 0,
#             "logged": 0,
#             "missed": 0,

#             "critical": 0,
#             "high": 0,
#             "medium": 0,
#             "low": 0,
#             "informational": 0,

#             "scoresPrevent": [],
#             "scoresDetect": [],

#             "priorityType": [],
#             "priorityUrgency": [],

#             "controls": []
#         }
#     }

#     # What MITRE tactics do we currently have data for?
#     activeTactics = list(set([t["tactic"] for t in testcases if t["state"] == "Complete"]))

#     for testcase in testcases:
#         if testcase["tactic"] in activeTactics:
#             # Initalise tactic if not in the dataframe yet
#             if testcase["tactic"] not in stats:
#                 stats[testcase["tactic"]] = deepcopy(stats["All"])

#             # Populate prevented/alerted/logged/missed stats
#             # NOTE: If a testcase is both alerted and prevented, it will be
#             # counted twice
#             if testcase["prevented"] == "Yes" or testcase["prevented"] == "Partial":
#                 stats[testcase["tactic"]]["prevented"] += 1

#             if testcase["alerted"] == "Yes":
#                 stats[testcase["tactic"]]["alerted"] += 1
#                 if testcase["alertseverity"]:
#                     stats[testcase["tactic"]][testcase["alertseverity"].lower()] += 1

#             if testcase["logged"] == "Yes":
#                 stats[testcase["tactic"]]["logged"] += 1

#             if testcase["prevented"] == "No" and testcase["alerted"] == "No" and testcase["logged"] == "No":
#                 stats[testcase["tactic"]]["missed"] += 1

#             # Store scores to later average with
#             stats[testcase["tactic"]]["scoresPrevent"].append(float(testcase["preventedrating"] or "0.0"))
#             stats[testcase["tactic"]]["scoresDetect"].append(float(testcase["detectionrating"] or "0.0"))

#             # Collate priorities, ratings and blue tools
#             if testcase["priority"]:
#                 stats[testcase["tactic"]]["priorityType"].append(testcase["priority"])
#             if testcase["priorityurgency"]:
#                 stats[testcase["tactic"]]["priorityUrgency"].append(testcase["priorityurgency"])
#             if testcase["controls"]:
#                 names = [[k["name"] for k in ass["controls"] if str(k["id"]) == i][0] for i in testcase["controls"]]
#                 stats[testcase["tactic"]]["controls"].extend(names)

#     # We've populated per-tactic data, this function adds it all together for
#     # an "All" tactic
#     for tactic in stats:
#         if tactic == "All":
#             continue
#         for key in ["prevented", "alerted", "logged", "missed", "critical", "high", "medium", "low", "informational"]:
#             stats["All"][key] += stats[tactic][key]
#         for key in ["scoresPrevent", "scoresDetect", "priorityType", "priorityUrgency", "controls"]:
#             stats["All"][key].extend(stats[tactic][key])

#     return stats