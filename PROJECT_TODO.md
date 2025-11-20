# Project TODO – Snapshot

| Section | Focus | Tasks Done / Total | Completion | Last Test Snapshot |
| --- | --- | --- | --- | --- |
| A | Ingestion & Schema | 3 / 5 | 60% | 2025-11-21 – `python3 -m pytest -q`, `make validate` |
| B | Analysis Tools | 3 / 6 | 50% | 2025-11-21 – `python3 -m pytest -q` |
| C | GPT Audit & Persistence | 6 / 6 | 100% | 2025-11-21 – `python3 gpt_audit.py --no-dry-run --samples 1` |
| D | Operations & Automation | 2 / 5 | 40% | 2025-11-21 – `make refresh` (previous run) |
| E | Documentation & Onboarding | 1 / 4 | 25% | 2025-11-21 – Manual review |

Update this file at the end of every work session: adjust completion counts, record the last test commands that passed (or note failures), and add/remove tasks as scope evolves.

---

## Section A – Ingestion & Schema
- **Status owner:** Data ingestion maintainers
- **Key files:** `build_diary_database.py`, `tests/test_ingest.py`

| ID | Task | Status | Notes / Tests |
| --- | --- | --- | --- |
| A1 | Ingestion CLI + schema foundation | ✅ Done | Covered by `tests/test_ingest.py` |
| A2 | Existing `validate_ingest` checks | ✅ Done | Called implicitly in `run_ingest` |
| A3 | `--validate-only` CLI flag + Make target | ✅ Done | `make validate`; new pytest cases |
| A4 | Stricter per-date coverage checks | ⏳ Todo | Extend `validate_ingest`; tests for missing combos |
| A5 | Edge-case workbook ingestion tests | ⏳ Todo | Expand `tests/test_ingest.py` with synthetic sheets |

## Section B – Analysis Tools
- **Key files:** `dedupe_diary_entries.py`, `parse_daily_reports.py`, `generate_daily_report.py`, `tests/test_analysis_tools.py`

| ID | Task | Status | Notes / Tests |
| --- | --- | --- | --- |
| B1 | Activity/personnel dedupe CSVs | ✅ Done | `tests/test_analysis_tools.py::test_dedupe_annotations...` |
| B2 | Supervisor/client CSV extracts | ✅ Done | `tests/test_analysis_tools.py` |
| B3 | Daily JSON + summary CSV | ✅ Done | Manual verification via `generate_daily_report.py` |
| B4 | Document standalone analysis targets | ⏳ Todo | Ensure `make dedupe/parse_daily/reports` docs |
| B5 | Cross-check DB vs CSV consistency tests | ⏳ Todo | New pytest to compare outputs |
| B6 | Day-level flags CSV | ⏳ Todo | Extend `generate_daily_report.py` |

## Section C – GPT Audit & Persistence
- **Key files:** `gpt_audit.py`, `requirements.txt`

| ID | Task | Status | Notes / Tests |
| --- | --- | --- | --- |
| C1 | Prompt construction + dry-run | ✅ Done | Manual dry-run output |
| C2 | Modern/legacy OpenAI client handling | ✅ Done | Verified with live API |
| C3 | Dependencies pinned in `requirements.txt` | ✅ Done | `python3 -m pip install -r requirements.txt` |
| C4 | Add audit columns to SQLite schema | ✅ Done | Schema migration ensures audit columns |
| C5 | Persist audit status/model/timestamp/notes | ✅ Done | `gpt_audit.py` updates DB; pytest coverage |
| C6 | Audit coverage summary + reporting hooks | ✅ Done | CLI prints summary; stored results for reports |

## Section D – Operations & Automation
- **Key files:** `Makefile`, automation scripts

| ID | Task | Status | Notes / Tests |
| --- | --- | --- | --- |
| D1 | Makefile workflow (`refresh`, etc.) | ✅ Done | `make refresh`, `make refresh-audit` |
| D2 | Workflow in `OPENAI_SETUP.md` | ✅ Done | See doc for command table |
| D3 | `make validate` target (validate-only + pytest) | ⏳ Todo | Depends on A3 |
| D4 | `make audit-flags` target | ⏳ Todo | Depends on C6 |
| D5 | Scheduler instructions (cron/launchd) | ⏳ Todo | Document once workflow stable |

## Section E – Documentation & Onboarding
- **Key files:** `OPENAI_SETUP.md`, (future) `README.md`

| ID | Task | Status | Notes / Tests |
| --- | --- | --- | --- |
| E1 | OpenAI setup + workflow (current doc) | ✅ Done | `OPENAI_SETUP.md` |
| E2 | Create/maintain `PROJECT_TODO.md` | ✅ In progress | Update after each session |
| E3 | Top-level README / project overview | ⏳ Todo | Explain purpose, inputs, outputs |
| E4 | Module-level TODOs (optional) | ⏳ Todo | Add when sections grow |

---

### Test Log Template
After completing tasks, append entries here:

```
## 2025-11-21
- Tasks: Completed A3, C4, C5, C6
- Tests: python3 -m pytest -q (pass); make validate (pass); python3 gpt_audit.py --no-dry-run --samples 1 (pass)
```

Keep the latest entry at the top for quick reference.
