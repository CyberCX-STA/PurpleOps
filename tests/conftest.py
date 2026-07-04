import os
import shutil
import mongomock

# Override env vars before any project imports. Direct assignment ensures
# Docker Compose env_file values (MONGO_HOST=mongodb etc.) are overridden.
os.environ["MONGO_DB"] = "test_purpleops"
os.environ["MONGO_HOST"] = "localhost"
os.environ["MONGO_PORT"] = "27017"
os.environ["FLASK_DEBUG"] = "False"
os.environ["FLASK_MFA"] = "False"
os.environ["HOST"] = "0.0.0.0"
os.environ["PORT"] = "5000"
os.environ["NAME"] = "test"
os.environ["FLASK_SECRET_KEY"] = "test-secret-key"
os.environ["FLASK_SECURITY_PASSWORD_SALT"] = "test-salt-12345678901234567890"
os.environ["FLASK_SECURITY_TOTP_SECRETS"] = "{1: JBSWY3DPEHPK3PXP}"
os.environ["POPS_ADMIN_PWD"] = "test-admin-password"

import pytest
import mongoengine


@pytest.fixture(scope="session")
def app():
    # Importing purpleops registers a real MongoDB connection via flask_mongoengine.
    # We immediately disconnect and re-register with mongomock so no real DB is needed.
    from purpleops import app as flask_app
    mongoengine.disconnect_all()
    mongoengine.connect(
        "test_purpleops",
        mongo_client_class=mongomock.MongoClient,
        uuidRepresentation="standard",
    )
    flask_app.config["TESTING"] = True
    flask_app.config["WTF_CSRF_ENABLED"] = False
    flask_app.config["SERVER_NAME"] = "localhost"
    return flask_app


@pytest.fixture(autouse=True)
def clean_db(app):
    from model import (
        Assessment, TestCase, TestCaseTemplate, Tactic, Technique,
        KnowlegeBase, Sigma, Role, User
    )
    yield
    Assessment.objects.delete()
    TestCase.objects.delete()
    TestCaseTemplate.objects.delete()
    Tactic.objects.delete()
    Technique.objects.delete()
    KnowlegeBase.objects.delete()
    Sigma.objects.delete()
    Role.objects.delete()
    User.objects.delete()


@pytest.fixture
def client(app, clean_db):
    with app.test_client() as c:
        with app.app_context():
            yield c


def make_roles():
    from model import Role
    roles = {}
    for name in ["Admin", "Red", "Blue", "Spectator"]:
        r = Role(name=name)
        r.save()
        roles[name] = r
    return roles


def make_user(roles_list, email, username, password="Password123!", assessments=None):
    from model import user_datastore
    from flask_security.utils import hash_password
    user = user_datastore.create_user(
        email=email,
        username=username,
        password=hash_password(password),
        roles=roles_list,
        assessments=assessments or [],
        initpwd=False,
    )
    return user


def login(client, email, password="Password123!"):
    return client.post("/login", data={"email": email, "password": password}, follow_redirects=True)


@pytest.fixture
def roles(clean_db):
    return make_roles()


@pytest.fixture
def admin_user(roles):
    return make_user([roles["Admin"]], "admin@test.com", "admin")


@pytest.fixture
def red_user(roles):
    return make_user([roles["Red"]], "red@test.com", "red")


@pytest.fixture
def blue_user(roles):
    return make_user([roles["Blue"]], "blue@test.com", "blue")


@pytest.fixture
def assessment(roles, admin_user):
    from model import Assessment
    a = Assessment(name="Test Assessment", description="desc")
    a.save()
    os.makedirs(f"files/{a.id}", exist_ok=True)
    yield a
    if os.path.exists(f"files/{a.id}"):
        shutil.rmtree(f"files/{a.id}")


@pytest.fixture
def technique():
    from model import Technique
    t = Technique(
        mitreid="T1059",
        name="Command and Scripting Interpreter",
        description="Adversaries may abuse command interpreters.",
        detection="Monitor for unusual process activity.",
        tactics=[" Execution"],
    )
    t.save()
    return t


@pytest.fixture
def testcase_template():
    from model import TestCaseTemplate
    tmpl = TestCaseTemplate(
        name="Run cmd.exe",
        mitreid="T1059",
        tactic="Execution",
        objective="Execute commands",
        actions="cmd.exe /c whoami",
        rednotes="",
        provider="TEST",
    )
    tmpl.save()
    return tmpl


@pytest.fixture
def docx_report_template():
    """Create a minimal DOCX in custom/reports/ and clean up afterwards."""
    import os
    from docx import Document
    os.makedirs("custom/reports", exist_ok=True)
    path = "custom/reports/test_template.docx"
    doc = Document()
    doc.add_paragraph("Assessment: {{ assessment.name }}")
    doc.save(path)
    yield "test_template.docx"
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def testcase(assessment):
    from model import TestCase
    tc = TestCase(
        assessmentid=str(assessment.id),
        name="Test Case 1",
        mitreid="T1059",
        tactic="Execution",
    )
    tc.save()
    return tc
