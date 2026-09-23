"""CLI command tests for ClientLoop."""

import json
from pathlib import Path
from clientloop.cli import main


def test_cli_full_flow(tmp_path: Path, capsys):
    db_file = str(tmp_path / "test.db")

    # 1. Add client
    ret = main(["--db", db_file, "client", "add", "TEST", "Test Co", "--rate", "100"])
    assert ret == 0
    capsys.readouterr()

    # 2. Add task
    ret = main(["--db", db_file, "task", "add", "TEST", "Setup DB", "--est", "3"])
    assert ret == 0
    capsys.readouterr()

    # 3. List tasks
    ret = main(["--db", db_file, "task", "list", "--json"])
    assert ret == 0
    tasks = json.loads(capsys.readouterr().out)
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Setup DB"
    tid = tasks[0]["id"]

    # 4. Log time
    ret = main(["--db", db_file, "task", "log", str(tid), "2.5", "-m", "Initial schema"])
    assert ret == 0
    capsys.readouterr()

    # 5. Mark done
    ret = main(["--db", db_file, "task", "done", str(tid)])
    assert ret == 0
    capsys.readouterr()

    # 6. Report
    rep_file = tmp_path / "report.md"
    ret = main(["--db", db_file, "report", "TEST", "-o", str(rep_file)])
    assert ret == 0
    assert rep_file.exists()
    assert "Setup DB" in rep_file.read_text(encoding="utf-8")
