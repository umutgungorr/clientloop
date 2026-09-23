# ClientLoop ⚡

> **Zero-dependency routine, task & billable deliverable tracker for freelance & indie developers.**  
> Keep your client contracts, daily technical tasks, logged billable hours, and client handover delivery reports tightly managed directly from your terminal.

[![CI](https://img.shields.io/badge/CI-Passing-brightgreen?style=flat-square)](https://github.com/umutgungorr/clientloop)
[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg?style=flat-square)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-0-success.svg?style=flat-square)](#)

---

## 🎯 Why ClientLoop?

Modern project management tools (Jira, Monday, ClickUp) are slow, bloated, and context-switching nightmares for developers who live in their terminal.

**ClientLoop** gives you:
- **Instant Speed**: 0-millisecond SQLite WAL engine on your local machine.
- **Zero External Dependencies**: Pure Python standard library. Nothing to install or configure.
- **Client & Billing Separation**: Track hourly rates, currencies, and deliverables per client.
- **Smart Urgency Badges**: Immediate warning on overdue milestones and tasks due today.
- **1-Click Handover Reports**: Generate professional **Markdown** or styled **HTML** invoices and deliverable handover summaries.

---

## 📦 Installation

```bash
# Using uv (recommended)
uv tool install clientloop

# Using pip
pip install clientloop
```

---

## 🛠️ Quick Start & CLI Usage

### 1. Register a Client
```bash
clientloop client add ACME "Acme Corp" --rate 85.00 --currency USD
```

### 2. Add Client Tasks & Deadlines
```bash
clientloop task add ACME "Build authentication flow with JWT" -p urgent -d 2026-09-30 --est 6.0
clientloop task add ACME "Setup PostgreSQL migration scripts" -p med --est 3.5
```

### 3. Log Billable Work
```bash
clientloop task log 1 2.5 -m "Wrote refresh token rotators"
```

### 4. Check Routine Dashboard
```bash
clientloop dashboard
```
Output:
```text
📊 ClientLoop Routine & Delivery Dashboard
────────────────────────────────────────────────
  Clients: 1  |  Total Tasks: 2  |  Open: 2
  Logged Hours: 2.5 hrs  (Est: 9.5 hrs)
────────────────────────────────────────────────
⚡ Due Today:
  • #1 Build authentication flow with JWT
```

### 5. Mark Task Done & Generate Handover Report
```bash
clientloop task done 1

# Generate clean Markdown handover document
clientloop report ACME -f md -o handover_report.md

# Or generate a styled HTML billing summary
clientloop report ACME -f html -o invoice_september.html
```

---

## 📖 Subcommands Overview

| Subcommand | Action | Key Options |
|---|---|---|
| `client add` | Register new client contract | `<code>`, `<name>`, `--rate`, `--currency`, `--notes` |
| `client list` | List clients | `--json` |
| `client get` | Client summary & financial status | `<code_or_id>`, `--json` |
| `task add` | Add task under client | `<client>`, `<title>`, `-p/--priority`, `-d/--due`, `--est` |
| `task log` | Log billable time | `<task_id>`, `<hours>`, `-m/--desc` |
| `task done` | Complete task | `<task_id>` |
| `dashboard` | View active deadlines & workload | — |
| `report` | Generate deliverable handover report | `<client>`, `-f md\|html`, `-o` |
| `export` / `import` | JSON backup & restore | `-o`, `<file>` |

---

## 🧪 Running Tests

```bash
uv run pytest
```

---

## 📜 License

MIT License. Crafted with precision by [Umut Güngör](https://github.com/umutgungorr).
