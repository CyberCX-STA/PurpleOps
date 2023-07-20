from datetime import datetime
from model import TestCase
from flask_security import current_user
from functools import wraps

def applyFormData (obj, form, fields):
    for field in fields:
        if field in form: # and form[field]:
            obj[field] = form[field]
    return obj

def applyFormListData (obj, form, fields):
    for field in fields:
        if field in form: # and form[field]:
            obj[field] = form.getlist(field)
    return obj

def applyFormBoolData (obj, form, fields):
    for field in fields:
        if field in form: # and form[field]:
            obj[field] = form[field].lower() in ["true", "yes", "on"]
    return obj

def applyFormTimeData (obj, form, fields):
    for field in fields:
        if field in form: # and form[field]:
            if form[field] and form[field] != "None":
                obj[field] = datetime.strptime(form[field], "%Y-%m-%dT%H:%M")
            else:
                obj[field] = None
    return obj

def user_assigned_assessment(f):
    @wraps(f)
    def inner(*args, **kwargs):
        if current_user.has_role("Admin"):
            return f(*args, **kwargs)
        id = kwargs.get("id")
        if not id:
            id = args[0]
        if TestCase.objects(id=id).count():
            id = TestCase.objects(id=id).first().assessmentid
        if (id in [str(a.id) for a in current_user.assessments]):
            return f(*args, **kwargs)
        else:
            return ("", 403)
    return inner