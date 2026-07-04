"""Tests for user management routes (blueprints/access.py)."""
import pytest
from .conftest import login, make_roles, make_user


class TestPasswordChanged:
    def test_password_changed_clears_initpwd(self, client, roles):
        user = make_user([roles["Red"]], "newuser@test.com", "newuser")
        user.initpwd = True
        user.save()

        login(client, "newuser@test.com")
        resp = client.get("/password/changed", follow_redirects=False)
        assert resp.status_code == 302

        user.reload()
        assert user.initpwd is False


class TestCreateUser:
    def test_create_user_returns_user_json(self, client, admin_user, roles):
        login(client, "admin@test.com")
        resp = client.post("/manage/access/user", data={
            "email": "new@test.com",
            "username": "newuser",
            "password": "Password123!",
            "roles": ["Red"],
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["username"] == "newuser"
        assert data["email"] == "new@test.com"
        assert "Red" in data["roles"]

    def test_create_user_with_assessment(self, client, admin_user, roles, assessment):
        login(client, "admin@test.com")
        resp = client.post("/manage/access/user", data={
            "email": "assigned@test.com",
            "username": "assigned",
            "password": "Password123!",
            "roles": ["Red"],
            "assessments": [assessment.name],
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert assessment.name in data["assessments"]

    def test_non_admin_cannot_create_user(self, client, red_user):
        login(client, "red@test.com")
        resp = client.post("/manage/access/user", data={
            "email": "x@x.com", "username": "x", "password": "Password123!",
        })
        assert resp.status_code == 403


class TestEditUser:
    def _create_target_user(self, roles):
        return make_user([roles["Red"]], "target@test.com", "targetuser")

    def test_edit_email_and_username(self, client, admin_user, roles):
        target = self._create_target_user(roles)
        login(client, "admin@test.com")
        resp = client.post(f"/manage/access/user/{target.id}", data={
            "email": "updated@test.com",
            "username": "updated",
            "roles": ["Red"],
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["email"] == "updated@test.com"
        assert data["username"] == "updated"

    def test_edit_password(self, client, admin_user, roles):
        target = self._create_target_user(roles)
        login(client, "admin@test.com")
        resp = client.post(f"/manage/access/user/{target.id}", data={
            "email": "target@test.com",
            "username": "targetuser",
            "password": "NewPassword456!",
            "roles": ["Red"],
        })
        assert resp.status_code == 200
        # Verify new password works
        client.get("/logout", follow_redirects=True)
        login_resp = login(client, "target@test.com", "NewPassword456!")
        assert login_resp.status_code == 200

    def test_cannot_rename_inbuilt_admin(self, client, admin_user, roles):
        login(client, "admin@test.com")
        resp = client.post(f"/manage/access/user/{admin_user.id}", data={
            "email": "admin@test.com",
            "username": "hacker",
            "roles": ["Admin"],
        })
        assert resp.status_code == 200
        assert resp.get_json()["username"] == "admin"

    def test_cannot_remove_admin_role_from_admin(self, client, admin_user, roles):
        login(client, "admin@test.com")
        resp = client.post(f"/manage/access/user/{admin_user.id}", data={
            "email": "admin@test.com",
            "username": "admin",
            "roles": ["Red"],  # try to strip Admin role
        })
        assert resp.status_code == 200
        assert "Admin" in resp.get_json()["roles"]

    def test_admin_role_wipes_assessment_list(self, client, admin_user, roles, assessment):
        target = self._create_target_user(roles)
        login(client, "admin@test.com")
        resp = client.post(f"/manage/access/user/{target.id}", data={
            "email": "target@test.com",
            "username": "targetuser",
            "roles": ["Admin"],
            "assessments": [assessment.name],
        })
        assert resp.status_code == 200
        assert resp.get_json()["assessments"] == []

    def test_delete_user(self, client, admin_user, roles):
        target = self._create_target_user(roles)
        target_id = str(target.id)
        login(client, "admin@test.com")
        resp = client.delete(f"/manage/access/user/{target_id}")
        assert resp.status_code == 200
        from model import User
        assert User.objects(id=target_id).count() == 0

    def test_cannot_delete_inbuilt_admin(self, client, admin_user, roles):
        login(client, "admin@test.com")
        resp = client.delete(f"/manage/access/user/{admin_user.id}")
        assert resp.status_code == 200
        from model import User
        assert User.objects(id=admin_user.id).count() == 1
