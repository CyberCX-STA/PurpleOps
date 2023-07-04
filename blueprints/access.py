from model import *
from utils import applyFormData
from flask import Blueprint, redirect, request, render_template
from flask_security import auth_required, utils, current_user, roles_accepted

blueprint_access = Blueprint('blueprint_access', __name__)

@blueprint_access.route('/manage/access', methods = ['GET'])
@auth_required()
@roles_accepted('Admin')
def users():
    return render_template(
        'access.html',
        users = User.objects,
        assessments = Assessment.objects,
        roles = Role.objects
    )

@blueprint_access.route('/manage/access/user', methods = ['POST'])
@auth_required()
@roles_accepted('Admin')
def createuser():
    user_datastore.create_user(
        email = request.form['email'],
        username = request.form['username'],
        password = utils.hash_password(request.form['password']),
        roles = [Role.objects(name=role).first() for role in request.form.getlist('roles')],
        assessments = [Assessment.objects(name=assessment).first() for assessment in request.form.getlist('assessments')]
    )
    return redirect("/manage/access")

@blueprint_access.route('/manage/access/user/<id>', methods = ['POST', 'DELETE'])
@auth_required()
@roles_accepted('Admin')
def edituser(id):
    origUser = User.objects(id=id).first()
    user = User.objects(id=id).first()
    if request.method == 'POST':
        if "password" in request.form and request.form['password'].strip():
            user.password = utils.hash_password(request.form['password'])

        user = applyFormData(user, request.form, ["username", "email"])
        # You cannot rename the inbuilt admin account
        if origUser.username == "admin" and user.username != "admin":
            user.username = "admin"

        user.roles = []
        for role in request.form.getlist('roles'):
            user.roles.append(Role.objects(name=role).first())
        # You cannot de-admin the inbuilt admin, re-add admin wiped admin role
        if user.username == "admin" and "Admin" not in [u.name for u in user.roles]:
            user.roles.append(Role.objects(name="Admin").first())

        user.assessments = []
        for assessment in request.form.getlist('assessments'):
            user.assessments.append(Assessment.objects(name=assessment).first())
        # Admin users have implied access to all assessments, wipe selected assessments
        if "Admin" in [u.name for u in user.roles]:
            user.assessments = []

        user.save()
        return redirect("/manage/access")
        
    if request.method == 'DELETE':
        # Prevent inbuilt admin deletion
        if user.username != "admin":
            user.delete()
            user.save()
        return "", 200