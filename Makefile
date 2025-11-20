PYTHON ?= /Users/johnoshea/Documents/programming/venvs/94_Project_Cost\ Analyser/bin/python
ROOT ?= .
DATABASE ?= diary.sqlite
OUTPUT_DIR ?= analysis
SAMPLES ?= 3

.PHONY: ingest dedupe parse_daily reports refresh audit refresh-audit tests validate

ingest:
	$(PYTHON) build_diary_database.py --root "$(ROOT)" --database "$(DATABASE)" --reset

dedupe:
	$(PYTHON) dedupe_diary_entries.py --root "$(ROOT)" --output-dir "$(OUTPUT_DIR)"

parse_daily:
	$(PYTHON) parse_daily_reports.py --root "$(ROOT)" --output-dir "$(OUTPUT_DIR)"

reports:
	$(PYTHON) generate_daily_report.py --database "$(DATABASE)" --output-dir "$(OUTPUT_DIR)"

tests:
	$(PYTHON) -m pytest -q

validate:
	$(PYTHON) build_diary_database.py --database "$(DATABASE)" --validate-only
	$(PYTHON) -m pytest -q

audit:
	$(PYTHON) gpt_audit.py --database "$(DATABASE)" --samples $(SAMPLES) --no-dry-run

refresh: ingest dedupe parse_daily reports

refresh-audit: refresh audit
