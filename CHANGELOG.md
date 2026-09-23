# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-09-24

### Added
- SQLite WAL storage engine for clients, task lifecycles, and work log entries.
- Subcommand suite:
  - `client`: `add`, `list`, `get`, `delete`.
  - `task`: `add`, `list`, `done`, `log`, `delete`.
  - `dashboard` / `status`: Workload and urgency overview.
  - `report`: Automated client delivery & billing handover generator (Markdown and HTML).
  - `export` / `import`: Portable JSON data backup and restoration.
- Deadline tracking with automated urgency calculations (overdue alerts, due today).
- Billable hour tracking and automated revenue calculation per client.
- Complete automated pytest test suite.
