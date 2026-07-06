from unittest.mock import Mock

import mongomock
import mongoengine
import pytest


@pytest.fixture(scope="module")
def seeder_module(app):
    # Importing seeder registers its own Flask app + db.init_app(), which
    # calls mongoengine.connect() again with real MONGO_HOST settings.
    # Disconnect first so that call doesn't clash with the mongomock
    # connection the `app` fixture already registered, then reconnect
    # mongomock afterwards so later queries don't hit a real MongoDB.
    mongoengine.disconnect_all()
    import seeder
    mongoengine.disconnect_all()
    mongoengine.connect(
        "test_purpleops",
        mongo_client_class=mongomock.MongoClient,
        uuidRepresentation="standard",
    )
    return seeder


@pytest.fixture
def env_file(tmp_path, seeder_module, monkeypatch):
    path = tmp_path / ".env"
    path.write_text("")
    monkeypatch.setattr(seeder_module, "dotenvFile", str(path))
    return path


class TestPopulateSecrets:
    def test_generates_secrets_when_missing(self, seeder_module, env_file):
        seeder_module.populateSecrets()

        import dotenv
        values = dotenv.dotenv_values(str(env_file))
        assert values.get("FLASK_SECRET_KEY")
        assert values.get("FLASK_SECURITY_PASSWORD_SALT")
        assert values.get("FLASK_SECURITY_TOTP_SECRETS")

    def test_does_not_overwrite_existing_secret(self, seeder_module, env_file):
        import dotenv
        dotenv.set_key(str(env_file), "FLASK_SECRET_KEY", "existing-secret")

        seeder_module.populateSecrets()

        values = dotenv.dotenv_values(str(env_file))
        assert values["FLASK_SECRET_KEY"] == "existing-secret"
        assert "FLASK_SECURITY_PASSWORD_SALT" not in values


class TestPrepareRolesAndAdmin:
    def test_creates_roles_and_admin_user(self, seeder_module, env_file, clean_db):
        from model import Role, User

        seeder_module.prepareRolesAndAdmin()

        role_names = {r.name for r in Role.objects()}
        assert role_names == {"Admin", "Red", "Blue", "Spectator"}

        admin = User.objects(email="admin@purpleops.com").first()
        assert admin is not None
        assert admin.roles[0].name == "Admin"

        import dotenv
        assert dotenv.dotenv_values(str(env_file)).get("POPS_ADMIN_PWD")

    def test_is_idempotent_when_already_populated(self, seeder_module, env_file, clean_db):
        from model import Role, User

        seeder_module.prepareRolesAndAdmin()
        seeder_module.prepareRolesAndAdmin()

        assert Role.objects().count() == 4
        assert User.objects().count() == 1


PARSE_FUNCTIONS = [
    "parseMitreTactics",
    "parseMitreTechniques",
    "parseSigma",
    "parseAtomicRedTeam",
    "parseCustomTestcases",
    "parseCustomKBs",
]


@pytest.fixture
def mocked_parsers(seeder_module, monkeypatch):
    mocks = {}
    for name in PARSE_FUNCTIONS:
        mock = Mock()
        monkeypatch.setattr(seeder_module, name, mock)
        mocks[name] = mock
    return mocks


class TestSeedReferenceData:
    def test_pulls_data_when_db_empty(self, seeder_module, mocked_parsers, clean_db):
        from model import Tactic

        assert Tactic.objects.count() == 0

        seeder_module.seedReferenceData()

        for mock in mocked_parsers.values():
            mock.assert_called_once()

    def test_skips_when_already_populated(self, seeder_module, mocked_parsers, clean_db):
        from model import Tactic

        Tactic(mitreid="TA0001", name="Initial Access").save()

        seeder_module.seedReferenceData()

        for mock in mocked_parsers.values():
            mock.assert_not_called()
        assert Tactic.objects.count() == 1
