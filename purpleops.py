import os
from model import *
from dotenv import load_dotenv
from flask import Flask, render_template
from flask_security import Security, auth_required

from blueprints import access, assessment, assessment_utils, assessment_import, assessment_export, testcase, testcase_utils

load_dotenv()

app = Flask(__name__)
app.config.from_pyfile("flask.cfg")

app.register_blueprint(access.blueprint_access)
app.register_blueprint(assessment.blueprint_assessment)
app.register_blueprint(assessment_utils.blueprint_assessment_utils)
app.register_blueprint(assessment_import.blueprint_assessment_import)
app.register_blueprint(assessment_export.blueprint_assessment_export)
app.register_blueprint(testcase.blueprint_testcase)
app.register_blueprint(testcase_utils.blueprint_testcase_utils)

db.init_app(app)

security = Security(app, user_datastore)

@app.route('/')
@app.route('/index')
@auth_required()
def index():
    assessments = Assessment.objects().all()
    return render_template('assessments.html', assessments=assessments)

if __name__ == "__main__":
    app.run(host=os.getenv('HOST'), port=int(os.getenv('PORT')))