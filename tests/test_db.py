"""Database tests for ClientLoop."""

from pathlib import Path
from clientloop.db import Database
from clientloop.models import Client, Task, TimeLog


def test_client_crud(tmp_path: Path):
    db = Database(tmp_path / "test.db")
    client = Client(id=None, code="ACME", name="Acme Corp", hourly_rate=75.0)
    cid = db.insert_client(client)
    assert cid > 0

    fetched = db.get_client("ACME")
    assert fetched is not None
    assert fetched.name == "Acme Corp"
    assert fetched.hourly_rate == 75.0

    all_c = db.list_clients()
    assert len(all_c) == 1

    db.delete_client(cid)
    assert db.get_client("ACME") is None


def test_task_and_time_logging(tmp_path: Path):
    db = Database(tmp_path / "test.db")
    cid = db.insert_client(Client(id=None, code="BETA", name="Beta Inc"))
    tid = db.insert_task(Task(id=None, client_id=cid, title="Refactor Auth"))
    assert tid > 0

    t = db.get_task(tid)
    assert t.title == "Refactor Auth"
    assert t.logged_hours == 0.0

    # Log 2.5 hours
    db.log_time(TimeLog(id=None, task_id=tid, hours=2.5, description="OAuth setup"))
    t_updated = db.get_task(tid)
    assert t_updated.logged_hours == 2.5

    logs = db.list_time_logs(tid)
    assert len(logs) == 1
    assert logs[0].hours == 2.5
