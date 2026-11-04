"""JSON logs: one object per line, with the request id or the task id of the current context."""

import json
import logging

from common import logs


def test_logs_are_json() -> None:
    record = logging.makeLogRecord({"name": "app", "levelname": "INFO", "msg": "ready", "request_id": "r1"})
    entry = json.loads(logs.JsonFormatter().format(record))
    assert entry["message"] == "ready" and entry["level"] == "info" and entry["request_id"] == "r1"


def test_logs_carry_the_task_id() -> None:
    token = logs.task_id.set("t1")
    try:
        entry = json.loads(logs.JsonFormatter().format(logging.makeLogRecord({"msg": "done"})))
    finally:
        logs.task_id.reset(token)
    assert entry["task_id"] == "t1" and "request_id" not in entry
