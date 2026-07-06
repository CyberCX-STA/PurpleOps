"""Tests for TestCase outcome computation logic (blueprints/testcase.py:102-109)."""
import pytest
from .conftest import login


def save_testcase_via_api(client, testcase_id, **fields):
    """POST to /testcase/<id> with the given fields."""
    data = {
        "name": "Test Case",
        "mitreid": "T1059",
        "tactic": "Execution",
        "timezone": "0",
        **fields,
    }
    return client.post(f"/testcase/{testcase_id}", data=data)


class TestOutcomeComputation:
    def test_prevented_yes_sets_prevented_outcome(self, client, admin_user, testcase):
        login(client, "admin@test.com")
        resp = save_testcase_via_api(client, testcase.id, prevented="Yes", logged="No")
        assert resp.status_code == 200
        testcase.reload()
        assert testcase.outcome == "Prevented"

    def test_prevented_partial_sets_prevented_outcome(self, client, admin_user, testcase):
        login(client, "admin@test.com")
        resp = save_testcase_via_api(client, testcase.id, prevented="Partial", logged="No")
        assert resp.status_code == 200
        testcase.reload()
        assert testcase.outcome == "Prevented"

    def test_alerted_sets_alerted_outcome(self, client, admin_user, testcase):
        login(client, "admin@test.com")
        resp = save_testcase_via_api(client, testcase.id, prevented="No", alerted="Yes", logged="No")
        assert resp.status_code == 200
        testcase.reload()
        assert testcase.outcome == "Alerted"

    def test_logged_only_sets_logged_outcome(self, client, admin_user, testcase):
        login(client, "admin@test.com")
        resp = save_testcase_via_api(client, testcase.id, prevented="No", alerted="No", logged="Yes")
        assert resp.status_code == 200
        testcase.reload()
        assert testcase.outcome == "Logged"

    def test_not_logged_not_prevented_sets_missed(self, client, admin_user, testcase):
        login(client, "admin@test.com")
        resp = save_testcase_via_api(client, testcase.id, prevented="No", alerted="No", logged="No")
        assert resp.status_code == 200
        testcase.reload()
        assert testcase.outcome == "Missed"

    def test_prevented_takes_priority_over_alerted(self, client, admin_user, testcase):
        login(client, "admin@test.com")
        resp = save_testcase_via_api(client, testcase.id, prevented="Yes", alerted="Yes", logged="Yes")
        assert resp.status_code == 200
        testcase.reload()
        assert testcase.outcome == "Prevented"

    def test_alerted_takes_priority_over_logged(self, client, admin_user, testcase):
        login(client, "admin@test.com")
        resp = save_testcase_via_api(client, testcase.id, prevented="No", alerted="Yes", logged="Yes")
        assert resp.status_code == 200
        testcase.reload()
        assert testcase.outcome == "Alerted"

    def test_no_fields_gives_empty_outcome(self, client, admin_user, testcase):
        login(client, "admin@test.com")
        # Don't submit prevented/alerted/logged — outcome stays blank
        resp = save_testcase_via_api(client, testcase.id)
        assert resp.status_code == 200
        testcase.reload()
        assert testcase.outcome == ""


class TestDetectTime:
    def test_detecttime_set_when_logged_first_time(self, client, admin_user, testcase):
        login(client, "admin@test.com")
        assert testcase.detecttime is None
        save_testcase_via_api(client, testcase.id, logged="Yes", prevented="No")
        testcase.reload()
        assert testcase.detecttime is not None

    def test_detecttime_not_overwritten_on_second_save(self, client, admin_user, testcase):
        login(client, "admin@test.com")
        save_testcase_via_api(client, testcase.id, logged="Yes", prevented="No")
        testcase.reload()
        first_detecttime = testcase.detecttime
        save_testcase_via_api(client, testcase.id, logged="Yes", prevented="No")
        testcase.reload()
        assert testcase.detecttime == first_detecttime
