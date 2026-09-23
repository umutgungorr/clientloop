"""Service layer for ClientLoop business logic and aggregation."""

from datetime import date, datetime, timezone
from typing import Any, Optional
from clientloop.db import Database
from clientloop.models import Client, ClientSummary, Task, TimeLog


class ClientLoopService:
    def __init__(self, db: Database):
        self.db = db

    def add_client(
        self,
        code: str,
        name: str,
        hourly_rate: float = 0.0,
        currency: str = "USD",
        notes: str = "",
    ) -> Client:
        code_clean = code.strip().upper()
        if not code_clean:
            raise ValueError("Client code cannot be empty.")
        if not name.strip():
            raise ValueError("Client name cannot be empty.")

        existing = self.db.get_client(code_clean)
        if existing:
            raise ValueError(f"Client with code '{code_clean}' already exists.")

        client = Client(
            id=None,
            code=code_clean,
            name=name.strip(),
            hourly_rate=float(hourly_rate),
            currency=currency.strip().upper(),
            notes=notes.strip(),
        )
        client_id = self.db.insert_client(client)
        client.id = client_id
        return client

    def list_clients(self) -> list[Client]:
        return self.db.list_clients()

    def get_client(self, id_or_code: int | str) -> Optional[Client]:
        return self.db.get_client(id_or_code)

    def delete_client(self, client_id: int) -> bool:
        return self.db.delete_client(client_id)

    def add_task(
        self,
        client_id_or_code: int | str,
        title: str,
        priority: str = "med",
        due_date: Optional[str] = None,
        estimated_hours: float = 0.0,
    ) -> Task:
        client = self.db.get_client(client_id_or_code)
        if not client:
            raise ValueError(f"Client '{client_id_or_code}' not found.")

        title_clean = title.strip()
        if not title_clean:
            raise ValueError("Task title cannot be empty.")

        priority_clean = priority.lower().strip()
        if priority_clean not in ("low", "med", "high", "urgent"):
            priority_clean = "med"

        if due_date:
            # Validate YYYY-MM-DD
            try:
                date.fromisoformat(due_date.strip())
                due_date = due_date.strip()
            except ValueError:
                raise ValueError(f"Invalid due date format '{due_date}'. Expected YYYY-MM-DD.")

        task = Task(
            id=None,
            client_id=client.id,
            title=title_clean,
            status="todo",
            priority=priority_clean,
            due_date=due_date,
            estimated_hours=float(estimated_hours),
            logged_hours=0.0,
        )
        task_id = self.db.insert_task(task)
        task.id = task_id
        return task

    def list_tasks(self, client_id_or_code: Optional[int | str] = None, status: Optional[str] = None) -> list[Task]:
        cid = None
        if client_id_or_code is not None:
            c = self.db.get_client(client_id_or_code)
            if not c:
                return []
            cid = c.id
        return self.db.list_tasks(client_id=cid, status=status)

    def complete_task(self, task_id: int) -> bool:
        now_iso = datetime.now(timezone.utc).isoformat()
        return self.db.update_task_status(task_id, status="done", completed_at=now_iso)

    def update_status(self, task_id: int, status: str) -> bool:
        valid_statuses = ("todo", "in_progress", "blocked", "done")
        s = status.lower().strip()
        if s not in valid_statuses:
            raise ValueError(f"Invalid status '{s}'. Valid: {valid_statuses}")
        completed_at = datetime.now(timezone.utc).isoformat() if s == "done" else None
        return self.db.update_task_status(task_id, status=s, completed_at=completed_at)

    def log_time(self, task_id: int, hours: float, description: str = "") -> TimeLog:
        task = self.db.get_task(task_id)
        if not task:
            raise ValueError(f"Task #{task_id} not found.")
        if hours <= 0:
            raise ValueError("Hours must be greater than 0.")

        log = TimeLog(
            id=None,
            task_id=task_id,
            hours=float(hours),
            description=description.strip(),
        )
        log_id = self.db.log_time(log)
        log.id = log_id
        return log

    def get_client_summary(self, client_id_or_code: int | str) -> Optional[ClientSummary]:
        client = self.db.get_client(client_id_or_code)
        if not client:
            return None

        tasks = self.db.list_tasks(client_id=client.id)
        total_logged = sum(t.logged_hours for t in tasks)
        total_est = sum(t.estimated_hours for t in tasks)
        total_amt = total_logged * client.hourly_rate
        completed_cnt = sum(1 for t in tasks if t.status == "done")
        open_cnt = len(tasks) - completed_cnt

        return ClientSummary(
            client=client,
            tasks=tasks,
            total_logged_hours=round(total_logged, 2),
            total_estimated_hours=round(total_est, 2),
            total_amount=round(total_amt, 2),
            completed_tasks_count=completed_cnt,
            open_tasks_count=open_cnt,
        )

    def get_dashboard_metrics(self) -> dict[str, Any]:
        all_clients = self.db.list_clients()
        all_tasks = self.db.list_tasks()

        today_str = date.today().isoformat()
        overdue_tasks = []
        due_today_tasks = []
        in_progress_tasks = []

        total_hours = 0.0
        total_estimated = 0.0

        for t in all_tasks:
            total_hours += t.logged_hours
            total_estimated += t.estimated_hours
            if t.status == "in_progress":
                in_progress_tasks.append(t)
            if t.status != "done" and t.due_date:
                if t.due_date < today_str:
                    overdue_tasks.append(t)
                elif t.due_date == today_str:
                    due_today_tasks.append(t)

        return {
            "total_clients": len(all_clients),
            "total_tasks": len(all_tasks),
            "open_tasks": len([t for t in all_tasks if t.status != "done"]),
            "overdue_count": len(overdue_tasks),
            "due_today_count": len(due_today_tasks),
            "in_progress_count": len(in_progress_tasks),
            "total_logged_hours": round(total_hours, 2),
            "total_estimated_hours": round(total_estimated, 2),
            "overdue_tasks": overdue_tasks,
            "due_today_tasks": due_today_tasks,
        }

    def export_all(self) -> dict[str, Any]:
        clients = [c.to_dict() for c in self.db.list_clients()]
        tasks = [t.to_dict() for t in self.db.list_tasks()]
        logs = [l.to_dict() for l in self.db.list_time_logs()]
        return {
            "version": "0.1.0",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "clients": clients,
            "tasks": tasks,
            "time_logs": logs,
        }

    def import_all(self, data: dict[str, Any]) -> tuple[int, int, int]:
        clients_added = 0
        tasks_added = 0
        logs_added = 0

        client_map = {}  # old_id -> new_id
        task_map = {}  # old_id -> new_id

        for c_data in data.get("clients", []):
            code = c_data["code"]
            existing = self.db.get_client(code)
            if existing:
                client_map[c_data["id"]] = existing.id
            else:
                c = Client(
                    id=None,
                    code=code,
                    name=c_data["name"],
                    hourly_rate=c_data.get("hourly_rate", 0.0),
                    currency=c_data.get("currency", "USD"),
                    notes=c_data.get("notes", ""),
                    created_at=c_data.get("created_at", datetime.now(timezone.utc).isoformat()),
                )
                new_id = self.db.insert_client(c)
                client_map[c_data["id"]] = new_id
                clients_added += 1

        for t_data in data.get("tasks", []):
            old_cid = t_data.get("client_id")
            new_cid = client_map.get(old_cid)
            if not new_cid:
                continue
            t = Task(
                id=None,
                client_id=new_cid,
                title=t_data["title"],
                status=t_data.get("status", "todo"),
                priority=t_data.get("priority", "med"),
                due_date=t_data.get("due_date"),
                estimated_hours=t_data.get("estimated_hours", 0.0),
                logged_hours=t_data.get("logged_hours", 0.0),
                created_at=t_data.get("created_at", datetime.now(timezone.utc).isoformat()),
                completed_at=t_data.get("completed_at"),
            )
            new_tid = self.db.insert_task(t)
            task_map[t_data["id"]] = new_tid
            tasks_added += 1

        for l_data in data.get("time_logs", []):
            old_tid = l_data.get("task_id")
            new_tid = task_map.get(old_tid)
            if not new_tid:
                continue
            l = TimeLog(
                id=None,
                task_id=new_tid,
                hours=l_data.get("hours", 0.0),
                description=l_data.get("description", ""),
                logged_at=l_data.get("logged_at", datetime.now(timezone.utc).isoformat()),
            )
            self.db.log_time(l)
            logs_added += 1

        return clients_added, tasks_added, logs_added
