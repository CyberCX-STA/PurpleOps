def applyFormData (obj, form, fields):
    for field in fields:
        if field in form and form[field]:
            obj[field] = form[field]
    return obj