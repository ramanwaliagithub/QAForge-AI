import json
import logging

from framework.logging_utils import JsonFormatter, get_logger


def _format(**extra):
    record = logging.LogRecord("t", logging.INFO, __file__, 1, "hello %s", ("world",), None)
    record.__dict__.update(extra)
    return json.loads(JsonFormatter().format(record))


def test_json_formatter_core_fields():
    entry = _format()
    assert entry["msg"] == "hello world"
    assert entry["level"] == "INFO"
    assert entry["logger"] == "t"


def test_json_formatter_includes_extra_fields():
    assert _format(step="login", user="u1")["step"] == "login"


def test_get_logger_is_idempotent():
    assert get_logger("qaforge.test") is get_logger("qaforge.test")
    assert len(get_logger("qaforge.test").handlers) == 1
