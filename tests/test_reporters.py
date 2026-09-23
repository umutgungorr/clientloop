"""Tests for report generators."""

from clientloop.models import Client, ClientSummary, Task
from clientloop.reporters import generate_html_report, generate_markdown_report


def test_markdown_and_html_report():
    client = Client(id=1, code="ALPHA", name="Alpha Studio", hourly_rate=80.0, currency="USD")
    t1 = Task(id=10, client_id=1, title="API Architecture", status="done", priority="urgent", logged_hours=5.0)
    t2 = Task(id=11, client_id=1, title="CI/CD Pipeline", status="todo", priority="med", estimated_hours=2.0)

    summary = ClientSummary(
        client=client,
        tasks=[t1, t2],
        total_logged_hours=5.0,
        total_estimated_hours=2.0,
        total_amount=400.0,
        completed_tasks_count=1,
        open_tasks_count=1,
    )

    md = generate_markdown_report(summary)
    assert "# Client Delivery & Billing Handover: Alpha Studio (ALPHA)" in md
    assert "400.00 USD" in md
    assert "API Architecture" in md
    assert "CI/CD Pipeline" in md

    html = generate_html_report(summary)
    assert "<!DOCTYPE html>" in html
    assert "Alpha Studio (ALPHA)" in html
    assert "400.00 USD" in html
    assert "API Architecture" in html
