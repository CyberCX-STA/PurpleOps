"""Tests for extended export/import paths (blueprints/assessment_export.py & assessment_import.py)."""
import io
import json
import zipfile
import pytest
from .conftest import login, make_user


class TestTemplateImport:
    def test_import_from_templates_creates_testcases(self, client, admin_user, assessment, testcase_template):
        login(client, "admin@test.com")
        resp = client.post(
            f"/assessment/{assessment.id}/import/template",
            json={"ids": [str(testcase_template.id)]},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 1
        assert data[0]["name"] == testcase_template.name
        assert data[0]["mitreid"] == testcase_template.mitreid
        assert data[0]["actions"] == testcase_template.actions

    def test_import_multiple_templates(self, client, admin_user, assessment, testcase_template):
        from model import TestCaseTemplate
        second = TestCaseTemplate(
            name="Second template", mitreid="T1059", tactic="Execution",
            objective="obj2", actions="net user", provider="TEST",
        ).save()
        login(client, "admin@test.com")
        resp = client.post(
            f"/assessment/{assessment.id}/import/template",
            json={"ids": [str(testcase_template.id), str(second.id)]},
        )
        assert resp.status_code == 200
        assert len(resp.get_json()) == 2


class TestNavigatorImport:
    def _navigator_payload(self, technique_id, tactic):
        return json.dumps({
            "techniques": [{"techniqueID": technique_id, "tactic": tactic}]
        }).encode()

    def test_navigator_import_uses_matching_template(self, client, admin_user, assessment,
                                                      technique, testcase_template):
        login(client, "admin@test.com")
        payload = self._navigator_payload("T1059", "execution")
        resp = client.post(
            f"/assessment/{assessment.id}/import/navigator",
            data={"file": (io.BytesIO(payload), "nav.json")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 1
        assert data[0]["name"] == testcase_template.name

    def test_navigator_import_falls_back_to_technique_name(self, client, admin_user, assessment, technique):
        login(client, "admin@test.com")
        # No matching template — should use Technique name
        payload = self._navigator_payload("T1059", "execution")
        resp = client.post(
            f"/assessment/{assessment.id}/import/navigator",
            data={"file": (io.BytesIO(payload), "nav.json")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data[0]["name"] == technique.name


class TestCampaignImportMultis:
    def test_campaign_import_creates_new_tool_on_assessment(self, client, admin_user, assessment):
        login(client, "admin@test.com")
        payload = json.dumps([{
            "name": "TC with tool",
            "mitreid": "T1059",
            "tactic": "Execution",
            "objective": "",
            "actions": "",
            "tools": ["Mimikatz|credential dumper"],
            "uuid": "",
            "tags": [],
        }]).encode()
        resp = client.post(
            f"/assessment/{assessment.id}/import/campaign",
            data={"file": (io.BytesIO(payload), "campaign.json")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        assessment.reload()
        tool_names = [t.name for t in assessment.tools]
        assert "Mimikatz" in tool_names

    def test_campaign_import_reuses_existing_tool(self, client, admin_user, assessment):
        from model import Tool
        tool = Tool(name="Mimikatz", description="credential dumper")
        assessment.tools.append(tool)
        assessment.tools.save()

        login(client, "admin@test.com")
        payload = json.dumps([{
            "name": "TC reuse",
            "mitreid": "T1059",
            "tactic": "Execution",
            "tools": ["Mimikatz|credential dumper"],
            "tags": [], "uuid": "", "objective": "", "actions": "",
        }]).encode()
        resp = client.post(
            f"/assessment/{assessment.id}/import/campaign",
            data={"file": (io.BytesIO(payload), "campaign.json")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        assessment.reload()
        assert len(assessment.tools) == 1  # no duplicate created

    def test_campaign_import_creates_tag(self, client, admin_user, assessment):
        login(client, "admin@test.com")
        payload = json.dumps([{
            "name": "Tagged TC",
            "mitreid": "T1059",
            "tactic": "Execution",
            "tools": [],
            "tags": ["Priority|#ff0000"],
            "uuid": "", "objective": "", "actions": "",
        }]).encode()
        resp = client.post(
            f"/assessment/{assessment.id}/import/campaign",
            data={"file": (io.BytesIO(payload), "campaign.json")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        assessment.reload()
        assert any(t.name == "Priority" for t in assessment.tags)


class TestTemplateExport:
    def test_export_templates_adds_provider_field(self, client, admin_user, assessment, testcase):
        login(client, "admin@test.com")
        resp = client.get(f"/assessment/{assessment.id}/export/templates")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert len(data) == 1
        assert "provider" in data[0]
        assert data[0]["provider"] == "???"


class TestNavigatorExport:
    def test_navigator_export_structure(self, client, admin_user, assessment):
        login(client, "admin@test.com")
        resp = client.get(f"/assessment/{assessment.id}/export/navigator")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["domain"] == "enterprise-attack"
        assert "techniques" in data
        assert data["versions"]["layer"] == "4.5"

    def test_navigator_export_scores_technique_with_outcomes(self, client, admin_user, assessment, technique):
        from model import TestCase
        login(client, "admin@test.com")
        TestCase(assessmentid=str(assessment.id), name="TC",
                 mitreid="T1059", tactic="Execution",
                 outcome="Prevented").save()
        resp = client.get(f"/assessment/{assessment.id}/export/navigator")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        scored = [t for t in data["techniques"] if "score" in t]
        assert len(scored) > 0

    def test_navigator_export_blue_only_sees_visible(self, client, roles, assessment, technique):
        from model import TestCase, user_datastore
        from flask_security.utils import hash_password
        TestCase(assessmentid=str(assessment.id), name="Hidden",
                 mitreid="T1059", tactic="Execution",
                 outcome="Prevented", visible=False).save()
        user = user_datastore.create_user(
            email="bluenav@test.com", username="bluenav",
            password=hash_password("Password123!"),
            roles=[roles["Blue"]], assessments=[assessment], initpwd=False,
        )
        login(client, "bluenav@test.com")
        resp = client.get(f"/assessment/{assessment.id}/export/navigator")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        # Visible=False testcase should not contribute a score
        scored = [t for t in data["techniques"] if "score" in t]
        assert len(scored) == 0


class TestReportExport:
    def test_missing_report_template_returns_401(self, client, admin_user, assessment, testcase):
        login(client, "admin@test.com")
        resp = client.post(
            f"/assessment/{assessment.id}/export/report",
            data={"report": "nonexistent.docx"},
        )
        assert resp.status_code == 401

    def test_valid_report_template_renders_docx(self, client, admin_user, assessment,
                                                 testcase, docx_report_template):
        login(client, "admin@test.com")
        resp = client.post(
            f"/assessment/{assessment.id}/export/report",
            data={"report": docx_report_template},
        )
        assert resp.status_code == 200
        assert b"PK" in resp.data[:4]  # DOCX/ZIP magic bytes
        assert "report.docx" in resp.headers.get("Content-Disposition", "")


class TestEntireExport:
    def test_entire_export_is_valid_zip(self, client, admin_user, assessment, testcase):
        login(client, "admin@test.com")
        resp = client.get(f"/assessment/{assessment.id}/export/entire")
        assert resp.status_code == 200
        z = zipfile.ZipFile(io.BytesIO(resp.data))
        names = z.namelist()
        assert "export.json" in names
        assert "meta.json" in names
        assert "navigator.json" in names
        assert "campaign.json" in names

    def test_entire_export_blue_excludes_hidden_testcases(self, client, roles, assessment):
        from model import TestCase, user_datastore
        from flask_security.utils import hash_password
        visible_tc = TestCase(assessmentid=str(assessment.id), name="visible",
                              mitreid="T1059", tactic="Execution", visible=True).save()
        hidden_tc = TestCase(assessmentid=str(assessment.id), name="hidden",
                             mitreid="T1059", tactic="Execution", visible=False).save()
        import os
        os.makedirs(f"files/{assessment.id}/{hidden_tc.id}", exist_ok=True)
        open(f"files/{assessment.id}/{hidden_tc.id}/evidence.txt", "w").close()

        user = user_datastore.create_user(
            email="bluezip@test.com", username="bluezip",
            password=hash_password("Password123!"),
            roles=[roles["Blue"]], assessments=[assessment], initpwd=False,
        )
        login(client, "bluezip@test.com")
        resp = client.get(f"/assessment/{assessment.id}/export/entire")
        assert resp.status_code == 200
        z = zipfile.ZipFile(io.BytesIO(resp.data))
        names = z.namelist()
        assert not any(str(hidden_tc.id) in n for n in names)


class TestEntireImport:
    def test_import_entire_roundtrip(self, client, admin_user, assessment):
        from model import TestCase, Source
        login(client, "admin@test.com")

        # Add a source to the assessment and a testcase that references it
        src = Source(name="Kali", description="attack box")
        assessment.sources.append(src)
        assessment.sources.save()
        tc = TestCase(
            assessmentid=str(assessment.id),
            name="Roundtrip TC",
            mitreid="T1059",
            tactic="Execution",
            objective="test objective",
            outcome="Prevented",
            sources=[str(src.id)],
        ).save()

        # Export entire ZIP
        export_resp = client.get(f"/assessment/{assessment.id}/export/entire")
        assert export_resp.status_code == 200

        # Import entire ZIP
        import_resp = client.post(
            "/assessment/import/entire",
            data={"file": (io.BytesIO(export_resp.data), "entire.zip")},
            content_type="multipart/form-data",
        )
        assert import_resp.status_code == 200
        data = import_resp.get_json()
        assert data["name"] == assessment.name

        # Verify testcases were imported
        from model import Assessment as Ass
        imported = Ass.objects(id=data["id"]).first()
        imported_tcs = TestCase.objects(assessmentid=str(imported.id)).all()
        assert any(t.name == "Roundtrip TC" for t in imported_tcs)

    def test_import_entire_only_admin(self, client, red_user):
        login(client, "red@test.com")
        resp = client.post(
            "/assessment/import/entire",
            data={"file": (io.BytesIO(b"fake"), "entire.zip")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 403
