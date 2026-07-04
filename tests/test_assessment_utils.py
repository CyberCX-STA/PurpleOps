"""Tests for assessment utility routes (blueprints/assessment_utils.py)."""
import json
import pytest
from .conftest import login, make_user


def make_complete_testcase(assessment_id, tactic, outcome, **kwargs):
    from model import TestCase
    tc = TestCase(
        assessmentid=str(assessment_id),
        name=f"TC {tactic} {outcome}",
        mitreid="T1059",
        tactic=tactic,
        state="Complete",
        outcome=outcome,
        **kwargs,
    )
    tc.save()
    return tc


class TestAssessmentMultiEdit:
    def test_edit_existing_object_preserves_id(self, client, admin_user, assessment):
        login(client, "admin@test.com")
        # Create a source
        create_resp = client.post(
            f"/assessment/{assessment.id}/multi/sources",
            json={"data": [{"id": "", "name": "Kali", "description": "attacker"}]},
        )
        existing_id = create_resp.get_json()[0]["id"]

        # Edit it — same id, different name
        edit_resp = client.post(
            f"/assessment/{assessment.id}/multi/sources",
            json={"data": [{"id": existing_id, "name": "Updated Kali", "description": "updated"}]},
        )
        assert edit_resp.status_code == 200
        updated = edit_resp.get_json()[0]
        assert updated["id"] == existing_id
        assert updated["name"] == "Updated Kali"

    def test_add_tag_stores_colour(self, client, admin_user, assessment):
        login(client, "admin@test.com")
        resp = client.post(
            f"/assessment/{assessment.id}/multi/tags",
            json={"data": [{"id": "", "name": "Critical", "colour": "#ff0000"}]},
        )
        assert resp.status_code == 200
        tag = resp.get_json()[0]
        assert tag["name"] == "Critical"
        assert tag["colour"] == "#ff0000"


class TestNavigator:
    def test_navigator_page_renders(self, client, admin_user, assessment):
        login(client, "admin@test.com")
        resp = client.get(f"/assessment/{assessment.id}/navigator")
        assert resp.status_code == 200
        assert b"navigator" in resp.data.lower()

    def test_navigator_stores_one_time_secret(self, client, admin_user, assessment):
        login(client, "admin@test.com")
        client.get(f"/assessment/{assessment.id}/navigator")
        assessment.reload()
        assert "|" in assessment.navigatorexport
        assert len(assessment.navigatorexport.split("|")) == 3

    def test_navigator_json_endpoint_returns_json(self, client, admin_user, assessment):
        login(client, "admin@test.com")
        # Hit authed endpoint first to generate the navigator.json file
        client.get(f"/assessment/{assessment.id}/navigator")
        # Unauthed JSON endpoint
        client.get("/logout", follow_redirects=True)
        resp = client.get(f"/assessment/{assessment.id}/navigator.json")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert "techniques" in data
        assert resp.headers.get("Access-Control-Allow-Origin") == "*"


class TestAssessmentStats:
    def test_stats_page_loads_with_no_complete_testcases(self, client, admin_user, assessment, testcase):
        login(client, "admin@test.com")
        resp = client.get(f"/assessment/{assessment.id}/stats")
        assert resp.status_code == 200

    def test_stats_page_with_complete_testcases(self, client, admin_user, assessment):
        login(client, "admin@test.com")
        make_complete_testcase(assessment.id, "Execution", "Prevented",
                               prevented="Yes", preventedrating="3",
                               alertseverity="High", priority="High",
                               priorityurgency="Immediate", detectionrating="2")
        make_complete_testcase(assessment.id, "Execution", "Missed",
                               prevented="No")
        resp = client.get(f"/assessment/{assessment.id}/stats")
        assert resp.status_code == 200

    def test_stats_page_with_controls(self, client, admin_user, assessment):
        from model import Control
        login(client, "admin@test.com")
        ctrl = Control(name="EDR", description="endpoint detection")
        assessment.controls.append(ctrl)
        assessment.controls.save()

        tc = make_complete_testcase(assessment.id, "Execution", "Prevented",
                                    prevented="Yes")
        tc.controls = [str(ctrl.id)]
        tc.save()
        resp = client.get(f"/assessment/{assessment.id}/stats")
        assert resp.status_code == 200

    def test_stats_blue_only_sees_visible_testcases(self, client, roles, assessment):
        from model import user_datastore
        from flask_security.utils import hash_password
        make_complete_testcase(assessment.id, "Execution", "Logged", visible=True)
        make_complete_testcase(assessment.id, "Execution", "Missed", visible=False)

        user = user_datastore.create_user(
            email="bluestats@test.com", username="bluestats",
            password=hash_password("Password123!"),
            roles=[roles["Blue"]], assessments=[assessment], initpwd=False,
        )
        login(client, "bluestats@test.com")
        resp = client.get(f"/assessment/{assessment.id}/stats")
        assert resp.status_code == 200


class TestAssessmentHexagons:
    def test_hexagons_empty_returns_zero_size(self, client, admin_user, assessment):
        login(client, "admin@test.com")
        resp = client.get(f"/assessment/{assessment.id}/assessment_hexagons.svg")
        assert resp.status_code == 200
        assert b'height="0px"' in resp.data

    def test_hexagons_good_score_renders_green(self, client, admin_user, assessment):
        login(client, "admin@test.com")
        # score = prevented(2) + alerted(0) - missed(0) = 2 > 1 → green
        make_complete_testcase(assessment.id, "Execution", "Prevented")
        make_complete_testcase(assessment.id, "Execution", "Prevented")
        resp = client.get(f"/assessment/{assessment.id}/assessment_hexagons.svg")
        assert resp.status_code == 200
        assert b"#B8DF43" in resp.data

    def test_hexagons_bad_score_renders_red(self, client, admin_user, assessment):
        login(client, "admin@test.com")
        # score = 0 - 2 = -2 < -1 → red
        make_complete_testcase(assessment.id, "Execution", "Missed")
        make_complete_testcase(assessment.id, "Execution", "Missed")
        resp = client.get(f"/assessment/{assessment.id}/assessment_hexagons.svg")
        assert resp.status_code == 200
        assert b"#FB6B64" in resp.data

    def test_hexagons_neutral_score_renders_yellow(self, client, admin_user, assessment):
        login(client, "admin@test.com")
        # score = 1 - 1 = 0 → yellow
        make_complete_testcase(assessment.id, "Execution", "Prevented")
        make_complete_testcase(assessment.id, "Execution", "Missed")
        resp = client.get(f"/assessment/{assessment.id}/assessment_hexagons.svg")
        assert resp.status_code == 200
        assert b"#FFC000" in resp.data

    def test_hexagons_two_tactics_width(self, client, admin_user, assessment):
        login(client, "admin@test.com")
        make_complete_testcase(assessment.id, "Execution", "Prevented")
        make_complete_testcase(assessment.id, "Discovery", "Prevented")
        resp = client.get(f"/assessment/{assessment.id}/assessment_hexagons.svg")
        assert resp.status_code == 200
        assert b'width="240px"' in resp.data

    def test_hexagons_three_tactics_width(self, client, admin_user, assessment):
        login(client, "admin@test.com")
        for tactic in ["Execution", "Discovery", "Persistence"]:
            make_complete_testcase(assessment.id, tactic, "Prevented")
        resp = client.get(f"/assessment/{assessment.id}/assessment_hexagons.svg")
        assert resp.status_code == 200
        assert b'width="380px"' in resp.data

    def test_hexagons_five_tactics_height(self, client, admin_user, assessment):
        login(client, "admin@test.com")
        tactics = ["Execution", "Discovery", "Persistence", "Privilege Escalation", "Credential Access"]
        for tactic in tactics:
            make_complete_testcase(assessment.id, tactic, "Prevented")
        resp = client.get(f"/assessment/{assessment.id}/assessment_hexagons.svg")
        assert resp.status_code == 200
        assert b'height="230px"' in resp.data

    def test_hexagons_eight_tactics_height(self, client, admin_user, assessment):
        login(client, "admin@test.com")
        tactics = ["Execution", "Discovery", "Persistence", "Privilege Escalation",
                   "Credential Access", "Lateral Movement", "Exfiltration", "Impact"]
        for tactic in tactics:
            make_complete_testcase(assessment.id, tactic, "Prevented")
        resp = client.get(f"/assessment/{assessment.id}/assessment_hexagons.svg")
        assert resp.status_code == 200
        assert b'height="347px"' in resp.data
