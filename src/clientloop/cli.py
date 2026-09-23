"""Command Line Interface for ClientLoop."""

import argparse
import json
import sys
from pathlib import Path
from clientloop.db import DEFAULT_DB_PATH, Database
from clientloop.reporters import generate_html_report, generate_markdown_report
from clientloop.service import ClientLoopService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="clientloop",
        description="⚡ Zero-dependency routine, task & billable deliverable tracker for freelance & indie developers.",
    )
    parser.add_argument("--version", action="version", version="clientloop 0.1.0")
    parser.add_argument("--db", dest="db_path", default=None, help=f"Custom SQLite database path (default: {DEFAULT_DB_PATH})")

    subparsers = parser.add_subparsers(dest="command", help="Main subcommand")

    # client command
    client_p = subparsers.add_parser("client", help="Client management")
    client_sub = client_p.add_subparsers(dest="client_action")

    c_add = client_sub.add_parser("add", help="Add a new client")
    c_add.add_argument("code", help="Unique short code (e.g. ACME)")
    c_add.add_argument("name", help="Full client/company name")
    c_add.add_argument("--rate", type=float, default=0.0, help="Hourly rate")
    c_add.add_argument("--currency", default="USD", help="Currency code (USD, EUR, TRY, etc.)")
    c_add.add_argument("--notes", default="", help="Client notes")

    c_list = client_sub.add_parser("list", help="List all clients")
    c_list.add_argument("--json", dest="json_mode", action="store_true", help="Output as JSON")

    c_get = client_sub.add_parser("get", help="Get client details and summary")
    c_get.add_argument("code_or_id", help="Client code or ID")
    c_get.add_argument("--json", dest="json_mode", action="store_true", help="Output as JSON")

    c_del = client_sub.add_parser("delete", help="Delete a client")
    c_del.add_argument("id", type=int, help="Client ID")

    # task command
    task_p = subparsers.add_parser("task", help="Task and deliverable tracking")
    task_sub = task_p.add_subparsers(dest="task_action")

    t_add = task_sub.add_parser("add", help="Add a new task")
    t_add.add_argument("client", help="Client code or ID")
    t_add.add_argument("title", help="Task description / title")
    t_add.add_argument("-p", "--priority", default="med", choices=["low", "med", "high", "urgent"])
    t_add.add_argument("-d", "--due", default=None, help="Due date (YYYY-MM-DD)")
    t_add.add_argument("--est", type=float, default=0.0, help="Estimated hours")

    t_list = task_sub.add_parser("list", help="List tasks")
    t_list.add_argument("-c", "--client", default=None, help="Filter by client code or ID")
    t_list.add_argument("-s", "--status", default=None, choices=["todo", "in_progress", "blocked", "done"])
    t_list.add_argument("--json", dest="json_mode", action="store_true", help="Output as JSON")

    t_done = task_sub.add_parser("done", help="Mark task as completed")
    t_done.add_argument("id", type=int, help="Task ID")

    t_log = task_sub.add_parser("log", help="Log billable hours against a task")
    t_log.add_argument("id", type=int, help="Task ID")
    t_log.add_argument("hours", type=float, help="Hours spent")
    t_log.add_argument("-m", "--desc", default="", help="Work note / log description")

    # dashboard / status
    subparsers.add_parser("dashboard", help="Display overview dashboard of tasks, deadlines and hours")
    subparsers.add_parser("status", help="Alias for dashboard")

    # report
    rep_p = subparsers.add_parser("report", help="Generate client handover & billing report")
    rep_p.add_argument("client", help="Client code or ID")
    rep_p.add_argument("-f", "--format", dest="fmt", default="md", choices=["md", "html"])
    rep_p.add_argument("-o", "--output", default=None, help="Output file path (prints to stdout if omitted)")

    # export
    exp_p = subparsers.add_parser("export", help="Export full database as JSON")
    exp_p.add_argument("-o", "--output", default=None, help="Output JSON file")

    # import
    imp_p = subparsers.add_parser("import", help="Import data from JSON backup")
    imp_p.add_argument("file", help="Input JSON file path")

    return parser


def handle_client(service: ClientLoopService, args: argparse.Namespace) -> int:
    if args.client_action == "add":
        c = service.add_client(args.code, args.name, args.rate, args.currency, args.notes)
        sys.stderr.write(f"\033[32m✓ Client #{c.id} '{c.name}' ({c.code}) created.\033[0m\n")
        return 0
    elif args.client_action == "list":
        clients = service.list_clients()
        if args.json_mode:
            sys.stdout.write(json.dumps([c.to_dict() for c in clients], indent=2) + "\n")
            return 0
        if not clients:
            sys.stdout.write("No clients registered. Use 'clientloop client add <code> <name>' to create one.\n")
            return 0
        sys.stdout.write("\033[1mClients:\033[0m\n")
        for c in clients:
            sys.stdout.write(f"  \033[36m[{c.code}]\033[0m #{c.id} {c.name} - {c.hourly_rate:,.2f} {c.currency}/hr\n")
        return 0
    elif args.client_action == "get":
        summary = service.get_client_summary(args.code_or_id)
        if not summary:
            sys.stderr.write(f"Client '{args.code_or_id}' not found.\n")
            return 1
        if args.json_mode:
            res = {
                "client": summary.client.to_dict(),
                "total_logged_hours": summary.total_logged_hours,
                "total_estimated_hours": summary.total_estimated_hours,
                "total_amount": summary.total_amount,
                "open_tasks": summary.open_tasks_count,
                "completed_tasks": summary.completed_tasks_count,
                "tasks": [t.to_dict() for t in summary.tasks],
            }
            sys.stdout.write(json.dumps(res, indent=2) + "\n")
            return 0
        c = summary.client
        sys.stdout.write(f"\033[1m[{c.code}] {c.name}\033[0m (#{c.id})\n")
        sys.stdout.write(f"Rate: {c.hourly_rate:,.2f} {c.currency}/hr | Total: {summary.total_logged_hours} hrs ({summary.total_amount:,.2f} {c.currency})\n")
        sys.stdout.write(f"Tasks: {summary.completed_tasks_count} done, {summary.open_tasks_count} open\n")
        return 0
    elif args.client_action == "delete":
        ok = service.delete_client(args.id)
        if ok:
            sys.stderr.write(f"\033[32m✓ Client #{args.id} deleted.\033[0m\n")
            return 0
        sys.stderr.write(f"Client #{args.id} not found.\n")
        return 1
    return 0


def handle_task(service: ClientLoopService, args: argparse.Namespace) -> int:
    if args.task_action == "add":
        t = service.add_task(args.client, args.title, args.priority, args.due, args.est)
        sys.stderr.write(f"\033[32m✓ Task #{t.id} '{t.title}' created (Priority: {t.priority.upper()}).\033[0m\n")
        return 0
    elif args.task_action == "list":
        tasks = service.list_tasks(args.client, args.status)
        if args.json_mode:
            sys.stdout.write(json.dumps([t.to_dict() for t in tasks], indent=2) + "\n")
            return 0
        if not tasks:
            sys.stdout.write("No matching tasks found.\n")
            return 0
        for t in tasks:
            status_icon = "✓" if t.status == "done" else "○"
            due_str = f" [Due: {t.due_date}]" if t.due_date else ""
            sys.stdout.write(f"  {status_icon} #{t.id} \033[1m{t.title}\033[0m ({t.priority.upper()}) - {t.logged_hours}/{t.estimated_hours}h{due_str}\n")
        return 0
    elif args.task_action == "done":
        ok = service.complete_task(args.id)
        if ok:
            sys.stderr.write(f"\033[32m✓ Task #{args.id} marked as done.\033[0m\n")
            return 0
        sys.stderr.write(f"Task #{args.id} not found.\n")
        return 1
    elif args.task_action == "log":
        log = service.log_time(args.id, args.hours, args.desc)
        sys.stderr.write(f"\033[32m✓ Logged {log.hours} hrs on Task #{log.task_id}.\033[0m\n")
        return 0
    return 0


def handle_dashboard(service: ClientLoopService) -> int:
    m = service.get_dashboard_metrics()
    sys.stdout.write("\033[1m📊 ClientLoop Routine & Delivery Dashboard\033[0m\n")
    sys.stdout.write("─" * 48 + "\n")
    sys.stdout.write(f"  Clients: \033[36m{m['total_clients']}\033[0m  |  Total Tasks: {m['total_tasks']}  |  Open: \033[33m{m['open_tasks']}\033[0m\n")
    sys.stdout.write(f"  Logged Hours: \033[32m{m['total_logged_hours']} hrs\033[0m  (Est: {m['total_estimated_hours']} hrs)\n")
    sys.stdout.write("─" * 48 + "\n")

    if m["overdue_tasks"]:
        sys.stdout.write("\033[31m⚠️ Overdue Tasks:\033[0m\n")
        for t in m["overdue_tasks"]:
            sys.stdout.write(f"  • #{t.id} {t.title} (Due: {t.due_date})\n")

    if m["due_today_tasks"]:
        sys.stdout.write("\033[33m⚡ Due Today:\033[0m\n")
        for t in m["due_today_tasks"]:
            sys.stdout.write(f"  • #{t.id} {t.title}\n")

    if not m["overdue_tasks"] and not m["due_today_tasks"]:
        sys.stdout.write("\033[32m✨ No urgent deadlines pending today!\033[0m\n")

    return 0


def handle_report(service: ClientLoopService, args: argparse.Namespace) -> int:
    summary = service.get_client_summary(args.client)
    if not summary:
        sys.stderr.write(f"Client '{args.client}' not found.\n")
        return 1

    if args.fmt == "html":
        content = generate_html_report(summary)
    else:
        content = generate_markdown_report(summary)

    if args.output:
        p = Path(args.output)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        sys.stderr.write(f"\033[32m✓ Handover report saved to {args.output}\033[0m\n")
    else:
        sys.stdout.write(content)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    db = Database(args.db_path)
    service = ClientLoopService(db)

    try:
        if args.command == "client":
            return handle_client(service, args)
        elif args.command == "task":
            return handle_task(service, args)
        elif args.command in ("dashboard", "status"):
            return handle_dashboard(service)
        elif args.command == "report":
            return handle_report(service, args)
        elif args.command == "export":
            data = service.export_all()
            out_str = json.dumps(data, indent=2)
            if args.output:
                Path(args.output).write_text(out_str, encoding="utf-8")
                sys.stderr.write(f"\033[32m✓ Exported database to {args.output}\033[0m\n")
            else:
                sys.stdout.write(out_str + "\n")
            return 0
        elif args.command == "import":
            path = Path(args.file)
            if not path.exists():
                sys.stderr.write(f"File not found: {args.file}\n")
                return 1
            data = json.loads(path.read_text(encoding="utf-8"))
            c_cnt, t_cnt, l_cnt = service.import_all(data)
            sys.stderr.write(f"\033[32m✓ Imported {c_cnt} clients, {t_cnt} tasks, {l_cnt} time logs.\033[0m\n")
            return 0
    except Exception as e:
        sys.stderr.write(f"\033[31mError: {e}\033[0m\n")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
