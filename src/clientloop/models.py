"""Data models for ClientLoop."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class Client:
    id: Optional[int]
    code: str
    name: str
    hourly_rate: float = 0.0
    currency: str = "USD"
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "hourly_rate": self.hourly_rate,
            "currency": self.currency,
            "notes": self.notes,
            "created_at": self.created_at,
        }


@dataclass
class Task:
    id: Optional[int]
    client_id: int
    title: str
    status: str = "todo"  # todo, in_progress, blocked, done
    priority: str = "med"  # low, med, high, urgent
    due_date: Optional[str] = None  # YYYY-MM-DD
    estimated_hours: float = 0.0
    logged_hours: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "client_id": self.client_id,
            "title": self.title,
            "status": self.status,
            "priority": self.priority,
            "due_date": self.due_date,
            "estimated_hours": self.estimated_hours,
            "logged_hours": self.logged_hours,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }


@dataclass
class TimeLog:
    id: Optional[int]
    task_id: int
    hours: float
    description: str
    logged_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "hours": self.hours,
            "description": self.description,
            "logged_at": self.logged_at,
        }


@dataclass
class ClientSummary:
    client: Client
    tasks: list[Task]
    total_logged_hours: float
    total_estimated_hours: float
    total_amount: float
    completed_tasks_count: int
    open_tasks_count: int
