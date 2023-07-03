import os
from model import *
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template
from flask_security import Security, current_user, auth_required

from blueprint_testcase import blueprint_testcase
from blueprint_assessment import blueprint_assessment
from blueprint_manage import blueprint_manage, blueprint_manage_user

load_dotenv()

# TODO Can these be injected directly into env vars rather than re-specifying?
app = Flask(__name__)
app.config['MONGODB_SETTINGS'] = {
    'db': os.getenv('MONGO_DB'),
    'host': os.getenv('MONGO_HOST'),
    'port': int(os.getenv('MONGO_PORT'))
}
app.config['DEBUG'] = os.getenv('DEBUG') == "True"
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SECURITY_PASSWORD_SALT'] = os.getenv('SALT')
app.config['SECURITY_TWO_FACTOR'] = os.getenv('MFA') == "True"
app.config['SECURITY_TWO_FACTOR_REQUIRED'] = os.getenv('MFA') == "True"
app.config["SECURITY_LOGIN_USER_TEMPLATE"] = "login_form.html"
app.config['SECURITY_TWO_FACTOR_ENABLED_METHODS'] = ['authenticator']
app.config['SECURITY_TWO_FACTOR_SETUP_URL'] = "/mfa-register"
app.config['SECURITY_TWO_FACTOR_TOKEN_VALIDATION_URL'] = "/mfa-verify"
app.config['SECURITY_TWO_FACTOR_SETUP_TEMPLATE'] = "mfa-register.html"
app.config['SECURITY_TWO_FACTOR_VERIFY_CODE_TEMPLATE'] = "mfa-verify.html"
app.config['SECURITY_TWO_FACTOR_RESCUE_MAIL'] = "rescue@purpleops.invalid"
app.config['SECURITY_TWO_FACTOR_ALWAYS_VALIDATE'] = False
app.config['SECURITY_TWO_FACTOR_LOGIN_VALIDITY'] = "1 weeks"
app.config['SECURITY_TOTP_SECRETS'] = {"1": os.getenv('TOTP_SECRET')}
app.config['SECURITY_TOTP_ISSUER'] = f"PurpleOps - {os.getenv('NAME')}"

app.register_blueprint(blueprint_manage.blueprint_manage)
app.register_blueprint(blueprint_manage_user.blueprint_manage_user)
app.register_blueprint(blueprint_assessment.blueprint_assessment)
app.register_blueprint(blueprint_testcase.blueprint_testcase)

# db = getdb()
db.init_app(app)

security = Security(app, user_datastore)

@app.route('/')
@app.route('/index')
@auth_required()
def index():
    curUser = User.objects(fs_uniquifier=current_user.get_id()).first()
    curUser.lastauth = datetime.now()
    curUser.save()

    assessments = Assessment.objects().all()
    return render_template('list_assessments.html', assessments=assessments)

if __name__ == "__main__":
    app.run(host=os.getenv('HOST'), port=int(os.getenv('PORT')))