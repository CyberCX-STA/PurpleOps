from model import *
from utils import applyFormData
from flask import Blueprint, redirect, request
from flask_security import auth_required, utils, current_user, roles_accepted

blueprint_manage_user = Blueprint('blueprint_manage_user', __name__)

@blueprint_manage_user.route('/manage/access/user/<id>', methods = ['POST', 'GET', 'DELETE'])
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

@blueprint_manage_user.route('/manage/access/user', methods = ['POST'])
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

@blueprint_manage_user.route('/manage/access/user/update-password', methods = ['POST'])
@auth_required()
def updatepassword():
    if request.method == 'POST':
        userID = current_user.get_id()
        curUser = User.objects(fs_uniquifier=userID).first()
        if utils.verify_password(request.form['oldpass'], curUser.password):
            if request.form['newpass'] == request.form['newpassconfirm']:
                curUser.password = utils.hash_password(request.form['newpass'])
                curUser.initpwd = False
                curUser.save()
            else:
                print("TODO PASSWD DONT MATCH")
        else:
            print("TODO WRONG OLD PASS")
        return redirect("/")