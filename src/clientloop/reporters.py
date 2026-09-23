"""Markdown and HTML report generators for ClientLoop."""

from datetime import datetime, timezone
from clientloop.models import ClientSummary


def generate_markdown_report(summary: ClientSummary) -> str:
    c = summary.client
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        f"# Client Delivery & Billing Handover: {c.name} ({c.code})",
        "",
        f"> **Generated:** {now_str}  ",
        f"> **Hourly Rate:** {c.hourly_rate:,.2f} {c.currency}  ",
        f"> **Total Billable Hours:** {summary.total_logged_hours} hrs  ",
        f"> **Total Billable Amount:** {summary.total_amount:,.2f} {c.currency}",
        "",
        "---",
        "",
        "## 🎯 Completed Deliverables",
        "",
    ]

    completed = [t for t in summary.tasks if t.status == "done"]
    if completed:
        lines.append("| ID | Task / Deliverable | Priority | Hours Logged | Subtotal |")
        lines.append("|---|---|---|---|---|")
        for t in completed:
            subtotal = t.logged_hours * c.hourly_rate
            lines.append(f"| #{t.id} | {t.title} | `{t.priority.upper()}` | {t.logged_hours} hrs | {subtotal:,.2f} {c.currency} |")
    else:
        lines.append("_No completed deliverables yet._")

    lines.extend([
        "",
        "## ⏳ Active & Upcoming Tasks",
        "",
    ])

    open_tasks = [t for t in summary.tasks if t.status != "done"]
    if open_tasks:
        lines.append("| ID | Task / Deliverable | Status | Priority | Due Date | Est. Hrs | Logged Hrs |")
        lines.append("|---|---|---|---|---|---|---|")
        for t in open_tasks:
            due = t.due_date if t.due_date else "—"
            lines.append(f"| #{t.id} | {t.title} | `{t.status}` | `{t.priority.upper()}` | {due} | {t.estimated_hours} hrs | {t.logged_hours} hrs |")
    else:
        lines.append("_All tasks are completed! 🎉_")

    lines.extend([
        "",
        "---",
        "### 📝 Notes",
        c.notes if c.notes else "No specific client notes.",
        "",
        "_Report compiled via ClientLoop CLI (Zero-dependency Developer Routine Tracker)._",
    ])

    return "\n".join(lines) + "\n"


def generate_html_report(summary: ClientSummary) -> str:
    c = summary.client
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    completed = [t for t in summary.tasks if t.status == "done"]
    open_tasks = [t for t in summary.tasks if t.status != "done"]

    completed_rows = ""
    for t in completed:
        subtotal = t.logged_hours * c.hourly_rate
        completed_rows += f"""
        <tr>
            <td>#{t.id}</td>
            <td><strong>{t.title}</strong></td>
            <td><span class="badge {t.priority}">{t.priority.upper()}</span></td>
            <td>{t.logged_hours} hrs</td>
            <td><strong>{subtotal:,.2f} {c.currency}</strong></td>
        </tr>
        """

    open_rows = ""
    for t in open_tasks:
        due = t.due_date if t.due_date else "—"
        open_rows += f"""
        <tr>
            <td>#{t.id}</td>
            <td><strong>{t.title}</strong></td>
            <td><span class="badge status-{t.status}">{t.status.upper()}</span></td>
            <td><span class="badge {t.priority}">{t.priority.upper()}</span></td>
            <td>{due}</td>
            <td>{t.estimated_hours} hrs</td>
            <td>{t.logged_hours} hrs</td>
        </tr>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Handover Report - {c.name}</title>
<style>
    body {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        background: #0f172a;
        color: #f1f5f9;
        margin: 0;
        padding: 40px 20px;
    }}
    .container {{
        max-width: 900px;
        margin: 0 auto;
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 32px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
    }}
    h1 {{ margin-top: 0; color: #38bdf8; }}
    .metrics-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 16px;
        margin: 24px 0;
    }}
    .card {{
        background: #0f172a;
        border: 1px solid #334155;
        padding: 16px;
        border-radius: 8px;
    }}
    .card .val {{ font-size: 24px; font-weight: bold; color: #10b981; }}
    .card .lbl {{ font-size: 12px; color: #94a3b8; text-transform: uppercase; margin-top: 4px; }}
    table {{
        width: 100%;
        border-collapse: collapse;
        margin-top: 16px;
        margin-bottom: 28px;
    }}
    th, td {{
        padding: 10px 14px;
        text-align: left;
        border-bottom: 1px solid #334155;
    }}
    th {{ background: #0f172a; color: #cbd5e1; font-size: 13px; }}
    .badge {{
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
    }}
    .urgent {{ background: #ef4444; color: #fff; }}
    .high {{ background: #f97316; color: #fff; }}
    .med {{ background: #3b82f6; color: #fff; }}
    .low {{ background: #64748b; color: #fff; }}
    .status-in_progress {{ background: #eab308; color: #000; }}
    .status-todo {{ background: #475569; color: #fff; }}
</style>
</head>
<body>
<div class="container">
    <h1>🚀 {c.name} ({c.code})</h1>
    <p style="color: #94a3b8;">Client Deliverable & Handover Report &bull; {now_str}</p>
    
    <div class="metrics-grid">
        <div class="card">
            <div class="val">{summary.total_logged_hours} hrs</div>
            <div class="lbl">Total Logged</div>
        </div>
        <div class="card">
            <div class="val">{summary.total_amount:,.2f} {c.currency}</div>
            <div class="lbl">Billable Amount</div>
        </div>
        <div class="card">
            <div class="val">{summary.completed_tasks_count} / {len(summary.tasks)}</div>
            <div class="lbl">Tasks Completed</div>
        </div>
        <div class="card">
            <div class="val">{c.hourly_rate:,.2f} {c.currency}/hr</div>
            <div class="lbl">Rate</div>
        </div>
    </div>

    <h2>🎯 Completed Deliverables</h2>
    <table>
        <thead>
            <tr><th>ID</th><th>Deliverable</th><th>Priority</th><th>Hours</th><th>Subtotal</th></tr>
        </thead>
        <tbody>
            {completed_rows if completed_rows else '<tr><td colspan="5" style="color:#64748b;">No completed tasks yet.</td></tr>'}
        </tbody>
    </table>

    <h2>⏳ Active & Upcoming Tasks</h2>
    <table>
        <thead>
            <tr><th>ID</th><th>Task</th><th>Status</th><th>Priority</th><th>Due Date</th><th>Est.</th><th>Logged</th></tr>
        </thead>
        <tbody>
            {open_rows if open_rows else '<tr><td colspan="7" style="color:#64748b;">All tasks completed!</td></tr>'}
        </tbody>
    </table>
</div>
</body>
</html>
"""
