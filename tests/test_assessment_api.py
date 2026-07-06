"""Tests for assessment and testcase CRUD APIs."""
import json
import pytest
from .conftest import login


class TestAssessmentCRUD:
    def test_create_assessment(self, client, admin_user):
        login(client, "admin@test.com")
        resp = client.post("/assessment", data={"name": "Op Nightshade", "description": "test op"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["name"] == "Op Nightshade"
        assert data["description"] == "test op"
        assert "id" in data

    def test_edit_assessment(self, client, admin_user, assessment):
        login(client, "admin@test.com")
        resp = client.post(f"/assessment/{assessment.id}", data={"name": "Renamed", "description": "new desc"})
        assert resp.status_code == 200
        assert resp.get_json()["name"] == "Renamed"

    def test_delete_assessment(self, client, admin_user, assessment, testcase):
        login(client, "admin@test.com")
        resp = client.delete(f"/assessment/{assessment.id}")
        assert resp.status_code == 200
        from model import Assessment, TestCase
        assert Assessment.objects(id=assessment.id).count() == 0
        assert TestCase.objects(assessmentid=str(assessment.id)).count() == 0

    def test_load_assessment_page(self, client, admin_user, assessment):
        login(client, "admin@test.com")
        resp = client.get(f"/assessment/{assessment.id}")
        assert resp.status_code == 200
        assert b"Test Assessment" in resp.data


class TestTestcaseCRUD:
    def test_create_testcase(self, client, admin_user, assessment):
        login(client, "admin@test.com")
        resp = client.post(
            f"/testcase/{assessment.id}/single",
            data={"name": "New TC", "mitreid": "T1059", "tactic": "Execution"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["name"] == "New TC"
        assert data["assessmentid"] == str(assessment.id)

    def test_clone_testcase(self, client, admin_user, testcase):
        login(client, "admin@test.com")
        resp = client.get(f"/testcase/{testcase.id}/clone")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["name"] == testcase.name + " (Copy)"
        assert data["assessmentid"] == testcase.assessmentid

    def test_delete_testcase(self, client, admin_user, testcase):
        login(client, "admin@test.com")
        tc_id = str(testcase.id)
        resp = client.get(f"/testcase/{tc_id}/delete")
        assert resp.status_code == 200
        from model import TestCase
        assert TestCase.objects(id=tc_id).count() == 0

    def test_toggle_visibility(self, client, admin_user, testcase):
        login(client, "admin@test.com")
        assert testcase.visible is False
        resp = client.get(f"/testcase/{testcase.id}/toggle-visibility")
        assert resp.status_code == 200
        testcase.reload()
        assert testcase.visible is True
        client.get(f"/testcase/{testcase.id}/toggle-visibility")
        testcase.reload()
        assert testcase.visible is False

    def test_save_testcase_fields(self, client, admin_user, testcase):
        login(client, "admin@test.com")
        resp = client.post(f"/testcase/{testcase.id}", data={
            "name": "Updated Name",
            "objective": "Do the thing",
            "actions": "run cmd.exe",
            "mitreid": "T1059",
            "tactic": "Execution",
            "timezone": "0",
        })
        assert resp.status_code == 200
        testcase.reload()
        assert testcase.name == "Updated Name"
        assert testcase.objective == "Do the thing"


class TestAssessmentMulti:
    def test_add_source_to_assessment(self, client, admin_user, assessment):
        login(client, "admin@test.com")
        resp = client.post(
            f"/assessment/{assessment.id}/multi/sources",
            json={"data": [{"id": "", "name": "Kali VM", "description": "attacker box"}]},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 1
        assert data[0]["name"] == "Kali VM"

    def test_invalid_multi_field_rejected(self, client, admin_user, assessment):
        login(client, "admin@test.com")
        resp = client.post(
            f"/assessment/{assessment.id}/multi/malicious",
            json={"data": []},
        )
        assert resp.status_code == 418
