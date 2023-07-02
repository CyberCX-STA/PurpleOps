from model import *
from flask import Blueprint, render_template, request
from flask_security import auth_required, roles_accepted

blueprint_manage = Blueprint('blueprint_manage', __name__)


@blueprint_manage.route('/manage/access')
@auth_required()
@roles_accepted('Admin')
def adminaccess():
    users = User.objects
    return render_template('manage.access.html', users=users, assessments=Assessment.objects)


@blueprint_manage.route('/manage/tactics')
@auth_required()
@roles_accepted('Admin')
def admintactics():
    tactics = Tactic.objects.order_by("mitreid")
    return render_template('manage.tactics.html', tactics=tactics)


@blueprint_manage.route('/manage/techniques')
@auth_required()
@roles_accepted('Admin')
def admintechniques():
    techniques = Technique.objects.order_by("mitreid")
    return render_template('manage.techniques.html', techniques=techniques)