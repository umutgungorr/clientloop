"""SQLite WAL database storage for ClientLoop."""

import sqlite3
from pathlib import Path
from typing import Optional
from clientloop.models import Client, Task, TimeLog


DEFAULT_DB_PATH = Path.home() / ".clientloop" / "clientloop.db"


class Database:
    def __init__(self, db_path: Path | str | None = None):
        if db_path is None:
            self.path = DEFAULT_DB_PATH
        else:
            self.path = Path(db_path)

        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _init_schema(self):
        with self._get_connection() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                hourly_rate REAL DEFAULT 0.0,
                currency TEXT DEFAULT 'USD',
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                status TEXT DEFAULT 'todo',
                priority TEXT DEFAULT 'med',
                due_date TEXT,
                estimated_hours REAL DEFAULT 0.0,
                logged_hours REAL DEFAULT 0.0,
                created_at TEXT NOT NULL,
                completed_at TEXT,
                FOREIGN KEY (client_id) REFERENCES clients (id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS time_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                hours REAL NOT NULL,
                description TEXT DEFAULT '',
                logged_at TEXT NOT NULL,
                FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_tasks_client_id ON tasks (client_id);
            CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks (status);
            CREATE INDEX IF NOT EXISTS idx_time_logs_task_id ON time_logs (task_id);
            """)

    # Clients
    def insert_client(self, client: Client) -> int:
        with self._get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO clients (code, name, hourly_rate, currency, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (client.code.upper(), client.name, client.hourly_rate, client.currency, client.notes, client.created_at)
            )
            return cur.lastrowid

    def get_client(self, client_id_or_code: int | str) -> Optional[Client]:
        with self._get_connection() as conn:
            if isinstance(client_id_or_code, int) or str(client_id_or_code).isdigit():
                cur = conn.execute("SELECT * FROM clients WHERE id = ?", (int(client_id_or_code),))
            else:
                cur = conn.execute("SELECT * FROM clients WHERE UPPER(code) = UPPER(?)", (str(client_id_or_code),))
            row = cur.fetchone()
            if not row:
                return None
            return Client(
                id=row["id"],
                code=row["code"],
                name=row["name"],
                hourly_rate=row["hourly_rate"],
                currency=row["currency"],
                notes=row["notes"],
                created_at=row["created_at"],
            )

    def list_clients(self) -> list[Client]:
        with self._get_connection() as conn:
            cur = conn.execute("SELECT * FROM clients ORDER BY name ASC")
            return [
                Client(
                    id=row["id"],
                    code=row["code"],
                    name=row["name"],
                    hourly_rate=row["hourly_rate"],
                    currency=row["currency"],
                    notes=row["notes"],
                    created_at=row["created_at"],
                )
                for row in cur.fetchall()
            ]

    def delete_client(self, client_id: int) -> bool:
        with self._get_connection() as conn:
            cur = conn.execute("DELETE FROM clients WHERE id = ?", (client_id,))
            return cur.rowcount > 0

    # Tasks
    def insert_task(self, task: Task) -> int:
        with self._get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO tasks (client_id, title, status, priority, due_date, estimated_hours, logged_hours, created_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task.client_id,
                    task.title,
                    task.status,
                    task.priority,
                    task.due_date,
                    task.estimated_hours,
                    task.logged_hours,
                    task.created_at,
                    task.completed_at,
                )
            )
            return cur.lastrowid

    def get_task(self, task_id: int) -> Optional[Task]:
        with self._get_connection() as conn:
            cur = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            row = cur.fetchone()
            if not row:
                return None
            return Task(
                id=row["id"],
                client_id=row["client_id"],
                title=row["title"],
                status=row["status"],
                priority=row["priority"],
                due_date=row["due_date"],
                estimated_hours=row["estimated_hours"],
                logged_hours=row["logged_hours"],
                created_at=row["created_at"],
                completed_at=row["completed_at"],
            )

    def list_tasks(self, client_id: Optional[int] = None, status: Optional[str] = None) -> list[Task]:
        query = "SELECT * FROM tasks WHERE 1=1"
        params: list[object] = []
        if client_id is not None:
            query += " AND client_id = ?"
            params.append(client_id)
        if status is not None:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY id DESC"

        with self._get_connection() as conn:
            cur = conn.execute(query, params)
            return [
                Task(
                    id=row["id"],
                    client_id=row["client_id"],
                    title=row["title"],
                    status=row["status"],
                    priority=row["priority"],
                    due_date=row["due_date"],
                    estimated_hours=row["estimated_hours"],
                    logged_hours=row["logged_hours"],
                    created_at=row["created_at"],
                    completed_at=row["completed_at"],
                )
                for row in cur.fetchall()
            ]

    def update_task_status(self, task_id: int, status: str, completed_at: Optional[str] = None) -> bool:
        with self._get_connection() as conn:
            cur = conn.execute(
                "UPDATE tasks SET status = ?, completed_at = ? WHERE id = ?",
                (status, completed_at, task_id)
            )
            return cur.rowcount > 0

    def delete_task(self, task_id: int) -> bool:
        with self._get_connection() as conn:
            cur = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            return cur.rowcount > 0

    # Time logs
    def log_time(self, log: TimeLog) -> int:
        with self._get_connection() as conn:
            cur = conn.execute(
                "INSERT INTO time_logs (task_id, hours, description, logged_at) VALUES (?, ?, ?, ?)",
                (log.task_id, log.hours, log.description, log.logged_at)
            )
            # Increment task logged_hours
            conn.execute(
                "UPDATE tasks SET logged_hours = logged_hours + ? WHERE id = ?",
                (log.hours, log.task_id)
            )
            return cur.lastrowid

    def list_time_logs(self, task_id: Optional[int] = None) -> list[TimeLog]:
        query = "SELECT * FROM time_logs"
        params = []
        if task_id is not None:
            query += " WHERE task_id = ?"
            params.append(task_id)
        query += " ORDER BY id DESC"

        with self._get_connection() as conn:
            cur = conn.execute(query, params)
            return [
                TimeLog(
                    id=row["id"],
                    task_id=row["task_id"],
                    hours=row["hours"],
                    description=row["description"],
                    logged_at=row["logged_at"],
                )
                for row in cur.fetchall()
            ]
