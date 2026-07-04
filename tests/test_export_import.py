"""Tests for export/import roundtrips."""
import io
import json
import zipfile
import pytest
from .conftest import login


def create_testcase_with_outcome(assessment_id, name, outcome, prevented="No"):
    from model import TestCase
    tc = TestCase(
        assessmentid=str(assessment_id),
        name=name,
        mitreid="T1059",
        tactic="Execution",
        outcome=outcome,
        prevented=prevented,
        visible=True,
    )
    tc.save()
    return tc


class TestJSONExport:
    def test_json_export_returns_all_testcases(self, client, admin_user, assessment):
        login(client, "admin@test.com")
        create_testcase_with_outcome(assessment.id, "TC1", "Prevented", "Yes")
        create_testcase_with_outcome(assessment.id, "TC2", "Logged")
        resp = client.get(f"/assessment/{assessment.id}/export/json")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert len(data) == 2
        names = [t["name"] for t in data]
        assert "TC1" in names
        assert "TC2" in names

    def test_json_export_contains_expected_fields(self, client, admin_user, assessment, testcase):
        login(client, "admin@test.com")
        resp = client.get(f"/assessment/{assessment.id}/export/json")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert len(data) == 1
        record = data[0]
        for field in ["name", "mitreid", "tactic", "outcome", "assessmentid"]:
            assert field in record

    def test_blue_only_sees_visible_testcases_in_export(self, client, roles, assessment):
        from model import user_datastore
        from flask_security.utils import hash_password
        create_testcase_with_outcome(assessment.id, "Visible TC", "Logged")
        hidden = create_testcase_with_outcome(assessment.id, "Hidden TC", "Prevented", "Yes")
        hidden.visible = False
        hidden.save()

        user = user_datastore.create_user(
            email="blue_export@test.com",
            username="blue_export",
            password=hash_password("Password123!"),
            roles=[roles["Blue"]],
            assessments=[assessment],
            initpwd=False,
        )
        login(client, "blue_export@test.com")
        resp = client.get(f"/assessment/{assessment.id}/export/json")
        data = json.loads(resp.data)
        names = [t["name"] for t in data]
        assert "Visible TC" in names
        assert "Hidden TC" not in names


class TestCSVExport:
    def test_csv_export_ok(self, client, admin_user, assessment, testcase):
        login(client, "admin@test.com")
        resp = client.get(f"/assessment/{assessment.id}/export/csv")
        assert resp.status_code == 200
        assert b"name" in resp.data  # CSV header

    def test_invalid_export_format_rejected(self, client, admin_user, assessment):
        login(client, "admin@test.com")
        resp = client.get(f"/assessment/{assessment.id}/export/xml")
        assert resp.status_code != 200


class TestCampaignExportImport:
    def test_campaign_export_fields(self, client, admin_user, assessment, testcase):
        login(client, "admin@test.com")
        resp = client.get(f"/assessment/{assessment.id}/export/campaign")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert len(data) == 1
        for field in ["mitreid", "tactic", "name", "objective", "actions", "tools", "uuid", "tags"]:
            assert field in data[0]

    def test_campaign_import_creates_testcases(self, client, admin_user, assessment):
        login(client, "admin@test.com")
        campaign = json.dumps([{
            "name": "Imported TC",
            "mitreid": "T1059",
            "tactic": "Execution",
            "objective": "Test obj",
            "actions": "whoami",
            "tools": [],
            "uuid": "",
            "tags": [],
        }]).encode()
        resp = client.post(
            f"/assessment/{assessment.id}/import/campaign",
            data={"file": (io.BytesIO(campaign), "campaign.json")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 1
        assert data[0]["name"] == "Imported TC"

    def test_assessment_progress_reflects_outcomes(self, client, admin_user, assessment):
        login(client, "admin@test.com")
        create_testcase_with_outcome(assessment.id, "P", "Prevented", "Yes")
        create_testcase_with_outcome(assessment.id, "L", "Logged")
        assessment.reload()
        progress = assessment.get_progress()
        parts = progress.split("|")
        # Format: Prevented|Alerted|Logged|Missed
        assert len(parts) == 4
        assert parts[0] != "0"  # Prevented > 0
        assert parts[2] != "0"  # Logged > 0
