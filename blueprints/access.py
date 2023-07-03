from model import *
from utils import applyFormData
from flask import Blueprint, redirect, request, render_template
from flask_security import auth_required, utils, current_user, roles_accepted

blueprint_access = Blueprint('blueprint_access', __name__)

@blueprint_access.route('/manage/access')
@auth_required()
@roles_accepted('Admin')
def adminaccess():
    users = User.objects
    return render_template('manage.access.html', users=users, assessments=Assessment.objects)

@blueprint_access.route('/manage/access/user/<id>', methods = ['POST', 'GET', 'DELETE'])
@auth_required()
@roles_accepted('Admin')
def manageuser(id):
    user = User.objects(id=id).first()
    if request.method == 'POST':
        if "password" in request.form and request.form['password']:
            user.password = utils.hash_password(request.form['password'])
        user.roles = []
        user = applyFormData(user, request.form, ["username", "email"])
        
        for role in request.form.getlist('roles'):
            user.roles.append(Role.objects(name=role).first())
        if user.username == "admin" and not [u for u in user.roles if u.name == "Admin"]:
            user.roles.append(Role.objects(name="Admin").first())
        user.assessments = []
        for assessment in request.form.getlist('assessments'):
            user.assessments.append(Assessment.objects(name=assessment).first())
        
        user.save()
        return redirect("/manage/access")
        
    if request.method == 'DELETE':
        if user.username != "admin":
            user.delete()
            user.save()
        else:
            print("Can't delete admin")
        return ("", 204)

@blueprint_access.route('/manage/access/user', methods = ['POST'])
@auth_required()
@roles_accepted('Admin')
def createuser():
    if request.method == 'POST':
        user_datastore.create_user(
            email=request.form['email'],
            username=request.form['username'],
            password=utils.hash_password(request.form['password']),
            roles=[Role.objects(name=role).first() for role in request.form.getlist('roles')],
            assessments=[Assessment.objects(name=assessment).first() for assessment in request.form.getlist('assessments')]
        )
        return redirect("/manage/access")