from datetime import datetime

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