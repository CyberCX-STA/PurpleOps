"""Tests for remaining testcase paths: Blue restrictions, time fields, file evidence."""
import io
import os
import pytest
from .conftest import login, make_user


def save_tc(client, testcase_id, **fields):
    data = {"name": "TC", "mitreid": "T1059", "tactic": "Execution", "timezone": "0", **fields}
    return client.post(f"/testcase/{testcase_id}", data=data)


class TestBlueSaveRestrictions:
    def test_blue_can_only_update_allowed_fields(self, client, roles, assessment, testcase):
        from model import user_datastore
        from flask_security.utils import hash_password
        testcase.visible = True
        testcase.save()

        user = user_datastore.create_user(
            email="bluesave@test.com", username="bluesave",
            password=hash_password("Password123!"),
            roles=[roles["Blue"]], assessments=[assessment], initpwd=False,
        )
        login(client, "bluesave@test.com")
        resp = client.post(f"/testcase/{testcase.id}", data={
            "timezone": "0",
            "bluenotes": "my blue note",
            "alerted": "Yes",
            "alertseverity": "High",
            # These should be ignored for blue users:
            "name": "Hacked Name",
            "objective": "Hacked Objective",
        })
        assert resp.status_code == 200
        testcase.reload()
        assert testcase.bluenotes == "my blue note"
        assert testcase.name == "Test Case 1"   # unchanged
        assert testcase.objective == ""          # unchanged

    def test_blue_cannot_save_hidden_testcase(self, client, roles, assessment, testcase):
        from model import user_datastore
        from flask_security.utils import hash_password
        # testcase.visible defaults to False
        user = user_datastore.create_user(
            email="bluesave2@test.com", username="bluesave2",
            password=hash_password("Password123!"),
            roles=[roles["Blue"]], assessments=[assessment], initpwd=False,
        )
        login(client, "bluesave2@test.com")
        resp = client.post(f"/testcase/{testcase.id}", data={
            "timezone": "0",
            "bluenotes": "should fail",
        })
        assert resp.status_code == 403


class TestTimeFields:
    def test_starttime_and_endtime_are_saved(self, client, admin_user, testcase):
        login(client, "admin@test.com")
        resp = save_tc(client, testcase.id,
                       starttime="2024-01-15T09:00",
                       endtime="2024-01-15T10:30",
                       timezone="0")
        assert resp.status_code == 200
        testcase.reload()
        assert testcase.starttime is not None
        assert testcase.endtime is not None
        assert testcase.starttime.hour == 9
        assert testcase.endtime.hour == 10

    def test_timezone_offset_is_applied(self, client, admin_user, testcase):
        login(client, "admin@test.com")
        # UTC+60 minutes — stored time should be 1 hour ahead
        save_tc(client, testcase.id, starttime="2024-01-15T09:00", timezone="60")
        testcase.reload()
        assert testcase.starttime.hour == 10

    def test_empty_time_clears_field(self, client, admin_user, testcase):
        login(client, "admin@test.com")
        # Set a time first
        save_tc(client, testcase.id, starttime="2024-01-15T09:00", timezone="0")
        testcase.reload()
        assert testcase.starttime is not None
        # Now clear it
        save_tc(client, testcase.id, starttime="", timezone="0")
        testcase.reload()
        assert testcase.starttime is None


class TestFileEvidence:
    def test_upload_red_evidence_file(self, client, admin_user, assessment, testcase):
        login(client, "admin@test.com")
        os.makedirs(f"files/{assessment.id}/{testcase.id}", exist_ok=True)
        resp = client.post(f"/testcase/{testcase.id}", data={
            "name": "TC",
            "mitreid": "T1059",
            "tactic": "Execution",
            "timezone": "0",
            "redfiles": (io.BytesIO(b"fake content"), "evidence.txt"),
        }, content_type="multipart/form-data")
        assert resp.status_code == 200
        testcase.reload()
        assert any(f.name == "evidence.txt" for f in testcase.redfiles)

    def test_fetch_evidence_file(self, client, admin_user, assessment, testcase):
        login(client, "admin@test.com")
        path = f"files/{assessment.id}/{testcase.id}/evidence.txt"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write("test content")

        resp = client.get(f"/testcase/{testcase.id}/evidence/evidence.txt")
        assert resp.status_code == 200

    def test_fetch_evidence_as_attachment(self, client, admin_user, assessment, testcase):
        login(client, "admin@test.com")
        path = f"files/{assessment.id}/{testcase.id}/download.txt"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write("download me")

        resp = client.get(f"/testcase/{testcase.id}/evidence/download.txt?download")
        assert resp.status_code == 200
        assert "attachment" in resp.headers.get("Content-Disposition", "")

    def test_delete_red_evidence_file(self, client, admin_user, assessment, testcase):
        from model import File
        path = f"files/{assessment.id}/{testcase.id}/todelete.txt"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write("delete me")
        testcase.update(set__redfiles=[{"name": "todelete.txt", "path": path, "caption": ""}])

        login(client, "admin@test.com")
        resp = client.delete(f"/testcase/{testcase.id}/evidence/red/todelete.txt")
        assert resp.status_code == 204
        assert not os.path.exists(path)
        testcase.reload()
        assert len(testcase.redfiles) == 0

    def test_delete_file_invalid_colour_returns_401(self, client, admin_user, testcase):
        login(client, "admin@test.com")
        resp = client.delete(f"/testcase/{testcase.id}/evidence/purple/file.txt")
        assert resp.status_code == 401

    def test_blue_cannot_delete_red_evidence(self, client, roles, assessment, testcase):
        from model import user_datastore
        from flask_security.utils import hash_password
        user = user_datastore.create_user(
            email="bluefile@test.com", username="bluefile",
            password=hash_password("Password123!"),
            roles=[roles["Blue"]], assessments=[assessment], initpwd=False,
        )
        login(client, "bluefile@test.com")
        resp = client.delete(f"/testcase/{testcase.id}/evidence/red/file.txt")
        assert resp.status_code == 403
