"""Unit tests for utility functions (utils.py) — no Flask context needed."""
from datetime import datetime
from werkzeug.datastructures import ImmutableMultiDict


class TestApplyFormListData:
    def test_list_field_returns_all_values(self):
        from utils import applyFormListData
        obj = {}
        form = ImmutableMultiDict([("tags", "a"), ("tags", "b"), ("tags", "c")])
        result = applyFormListData(obj, form, ["tags"])
        assert result["tags"] == ["a", "b", "c"]

    def test_missing_field_is_skipped(self):
        from utils import applyFormListData
        obj = {}
        applyFormListData(obj, ImmutableMultiDict([]), ["tags"])
        assert "tags" not in obj


class TestApplyFormBoolData:
    def test_yes_string_is_true(self):
        from utils import applyFormBoolData
        obj = {}
        result = applyFormBoolData(obj, ImmutableMultiDict([("alerted", "Yes")]), ["alerted"])
        assert result["alerted"] is True

    def test_no_string_is_false(self):
        from utils import applyFormBoolData
        obj = {}
        result = applyFormBoolData(obj, ImmutableMultiDict([("alerted", "No")]), ["alerted"])
        assert result["alerted"] is False

    def test_on_string_is_true(self):
        from utils import applyFormBoolData
        obj = {}
        result = applyFormBoolData(obj, ImmutableMultiDict([("logged", "on")]), ["logged"])
        assert result["logged"] is True


class TestApplyFormTimeData:
    def test_valid_datetime_is_parsed(self):
        from utils import applyFormTimeData
        obj = {}
        form = ImmutableMultiDict([("starttime", "2024-06-01T10:30"), ("timezone", "0")])
        result = applyFormTimeData(obj, form, ["starttime"])
        assert result["starttime"] == datetime(2024, 6, 1, 10, 30)

    def test_timezone_offset_is_applied(self):
        from utils import applyFormTimeData
        obj = {}
        form = ImmutableMultiDict([("starttime", "2024-06-01T10:00"), ("timezone", "60")])
        result = applyFormTimeData(obj, form, ["starttime"])
        assert result["starttime"] == datetime(2024, 6, 1, 11, 0)

    def test_empty_string_sets_none(self):
        from utils import applyFormTimeData
        obj = {}
        form = ImmutableMultiDict([("starttime", ""), ("timezone", "0")])
        result = applyFormTimeData(obj, form, ["starttime"])
        assert result["starttime"] is None

    def test_none_string_sets_none(self):
        from utils import applyFormTimeData
        obj = {}
        form = ImmutableMultiDict([("starttime", "None"), ("timezone", "0")])
        result = applyFormTimeData(obj, form, ["starttime"])
        assert result["starttime"] is None

    def test_missing_field_is_skipped(self):
        from utils import applyFormTimeData
        obj = {}
        applyFormTimeData(obj, ImmutableMultiDict([("timezone", "0")]), ["starttime"])
        assert "starttime" not in obj
