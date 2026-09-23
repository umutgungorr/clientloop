"""Service logic tests for ClientLoop."""

from pathlib import Path
import pytest
from clientloop.db import Database
from clientloop.service import ClientLoopService


def test_service_client_and_tasks(tmp_path: Path):
    db = Database(tmp_path / "test.db")
    svc = ClientLoopService(db)

    c = svc.add_client("KAPPA", "Kappa Media", hourly_rate=50.0)
    assert c.code == "KAPPA"

    # Duplicate code should fail
    with pytest.raises(ValueError):
        svc.add_client("KAPPA", "Duplicate Kappa")

    # Add tasks
    t1 = svc.add_task("KAPPA", "Landing page design", priority="high", estimated_hours=4.0)
    t2 = svc.add_task("KAPPA", "Stripe payment integration", priority="urgent", estimated_hours=6.0)

    # Log time
    svc.log_time(t1.id, 4.0, "Completed design in Figma")
    svc.complete_task(t1.id)

    svc.log_time(t2.id, 3.5, "Initial webhook configuration")

    # Summary
    summary = svc.get_client_summary("KAPPA")
    assert summary is not None
    assert summary.completed_tasks_count == 1
    assert summary.open_tasks_count == 1
    assert summary.total_logged_hours == 7.5
    assert summary.total_amount == 375.0  # 7.5 * 50.0


def test_service_metrics(tmp_path: Path):
    db = Database(tmp_path / "test.db")
    svc = ClientLoopService(db)

    svc.add_client("ZETA", "Zeta Tech")
    svc.add_task("ZETA", "Old task", due_date="2020-01-01")

    metrics = svc.get_dashboard_metrics()
    assert metrics["total_clients"] == 1
    assert metrics["total_tasks"] == 1
    assert metrics["overdue_count"] == 1
