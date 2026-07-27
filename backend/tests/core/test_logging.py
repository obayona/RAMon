"""Unit tests for src.core.logging._LoggerNameFilter."""

import logging

from src.core.logging import _LoggerNameFilter


def _make_record(name: str) -> logging.LogRecord:
    return logging.LogRecord(
        name=name,
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="test",
        args=(),
        exc_info=None,
    )


class TestLoggerNameFilter:
    def test_exact_match(self) -> None:
        f = _LoggerNameFilter("ramon.api")
        assert f.filter(_make_record("ramon.api")) is True

    def test_sub_logger_match(self) -> None:
        f = _LoggerNameFilter("ramon.api")
        assert f.filter(_make_record("ramon.api.route")) is True

    def test_deeply_nested_match(self) -> None:
        f = _LoggerNameFilter("ramon.sync.worker")
        assert f.filter(_make_record("ramon.sync.worker.batch")) is True

    def test_different_prefix_no_match(self) -> None:
        f = _LoggerNameFilter("ramon.api")
        assert f.filter(_make_record("ramon.websocket")) is False

    def test_similar_prefix_no_match(self) -> None:
        f = _LoggerNameFilter("ramon.api")
        assert f.filter(_make_record("ramon.api2")) is False

    def test_shorter_string_no_match(self) -> None:
        f = _LoggerNameFilter("ramon.api")
        assert f.filter(_make_record("ramon.ap")) is False

    def test_empty_prefix_matches_empty_name(self) -> None:
        f = _LoggerNameFilter("")
        assert f.filter(_make_record("")) is True

    def test_empty_prefix_does_not_match_arbitrary_name(self) -> None:
        f = _LoggerNameFilter("")
        assert f.filter(_make_record("anything")) is False

    def test_root_logger_name_no_match(self) -> None:
        f = _LoggerNameFilter("ramon")
        assert f.filter(_make_record("root")) is False
