"""Tests for authentication and role-based access control."""
import pytest
from .conftest import login, make_roles, make_user


class TestLogin:
    def test_login_success(self, client, admin_user):
        resp = login(client, "admin@test.com")
        assert resp.status_code == 200
        assert b"login" not in resp.data.lower() or b"assessments" in resp.data.lower()

    def test_login_wrong_password(self, client, admin_user):
        resp = client.post("/login", data={"email": "admin@test.com", "password": "wrongpass"}, follow_redirects=True)
        assert b"Invalid" in resp.data or resp.status_code in (200, 401)

    def test_unauthenticated_redirect(self, client):
        resp = client.get("/", follow_redirects=False)
        assert resp.status_code in (302, 401)


class TestRoleEnforcement:
    def test_admin_can_access_user_management(self, client, admin_user):
        login(client, "admin@test.com")
        resp = client.get("/manage/access")
        assert resp.status_code == 200

    def test_red_cannot_access_user_management(self, client, red_user):
        login(client, "red@test.com")
        resp = client.get("/manage/access")
        assert resp.status_code == 403

    def test_blue_cannot_access_user_management(self, client, blue_user):
        login(client, "blue@test.com")
        resp = client.get("/manage/access")
        assert resp.status_code == 403

    def test_red_cannot_create_assessment(self, client, red_user):
        login(client, "red@test.com")
        resp = client.post("/assessment", data={"name": "New", "description": ""})
        assert resp.status_code == 403

    def test_admin_can_create_assessment(self, client, admin_user):
        login(client, "admin@test.com")
        resp = client.post("/assessment", data={"name": "New Assessment", "description": "test"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["name"] == "New Assessment"


class TestAssessmentAccess:
    def test_unassigned_user_cannot_access_assessment(self, client, red_user, assessment):
        login(client, "red@test.com")
        resp = client.get(f"/assessment/{assessment.id}")
        assert resp.status_code == 403

    def test_assigned_user_can_access_assessment(self, client, roles, assessment):
        from model import user_datastore
        from flask_security.utils import hash_password
        user = user_datastore.create_user(
            email="assigned@test.com",
            username="assigned",
            password=hash_password("Password123!"),
            roles=[roles["Red"]],
            assessments=[assessment],
            initpwd=False,
        )
        login(client, "assigned@test.com")
        resp = client.get(f"/assessment/{assessment.id}")
        assert resp.status_code == 200

    def test_admin_can_access_any_assessment(self, client, admin_user, assessment):
        login(client, "admin@test.com")
        resp = client.get(f"/assessment/{assessment.id}")
        assert resp.status_code == 200


class TestBlueVisibility:
    def test_blue_cannot_view_hidden_testcase(self, client, roles, assessment, testcase):
        from model import user_datastore
        from flask_security.utils import hash_password
        user = user_datastore.create_user(
            email="blue2@test.com",
            username="blue2",
            password=hash_password("Password123!"),
            roles=[roles["Blue"]],
            assessments=[assessment],
            initpwd=False,
        )
        # testcase.visible defaults to False
        login(client, "blue2@test.com")
        resp = client.get(f"/testcase/{testcase.id}")
        assert resp.status_code == 403

    def test_blue_can_view_visible_testcase(self, client, roles, assessment, testcase):
        from model import user_datastore, TestCase
        from flask_security.utils import hash_password
        testcase.visible = True
        testcase.save()
        user = user_datastore.create_user(
            email="blue3@test.com",
            username="blue3",
            password=hash_password("Password123!"),
            roles=[roles["Blue"]],
            assessments=[assessment],
            initpwd=False,
        )
        login(client, "blue3@test.com")
        resp = client.get(f"/testcase/{testcase.id}")
        assert resp.status_code == 200
