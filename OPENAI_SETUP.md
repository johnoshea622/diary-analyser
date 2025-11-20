# OpenAI API Setup

## Configuration

1. **Environment File**: Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=sk-your-actual-api-key-here
   ```

2. **Virtual Environment**: This project uses an external virtual environment:
   ```
   /Users/johnoshea/Documents/programming/venvs/94_Project_Cost Analyser/
   ```

3. **Required Packages**:
   - Install everything with `python3 -m pip install -r requirements.txt`
   - Includes `openai`, `python-dotenv`, `openpyxl`, and `pytest`

## Automated Workflow

Use the provided `Makefile` to keep the SQLite database and `analysis/` outputs in sync:

| Command | Description |
| --- | --- |
| `make ingest` | Rebuilds `diary.sqlite` with `--reset` so the database mirrors the latest Excel files. |
| `make dedupe` | Regenerates duplicate/personnel CSVs under `analysis/`. |
| `make parse_daily` | Rebuilds supervisor/client CSV extracts under `analysis/`. |
| `make reports` | Writes `analysis/daily_report.json` + `daily_report_summary.csv`. |
| `make validate` | Runs database-only validation plus the pytest suite without modifying data. |
| `make refresh` | Runs all of the above targets sequentially. |
| `make refresh-audit` | Runs `make refresh` and then executes the GPT audit (`gpt_audit.py --no-dry-run`). |
| `make tests` | Executes the pytest suite (ingest regression + analysis coverage). |

Outputs are written to:

- `diary.sqlite` – canonical data store
- `analysis/activities_*` & `analysis/personnel_*` – duplicate insights
- `analysis/supervisor_comments.csv`, `analysis/supervisor_daily_extension.csv`, `analysis/client_fallback_production.csv`
- `analysis/daily_report.json` & `analysis/daily_report_summary.csv`

## Usage

The `gpt_audit.py` script will automatically load the API key from the `.env` file.

### Test API Access (Dry Run)
```bash
python gpt_audit.py --dry-run
```

### Run Actual API Calls
```bash
python gpt_audit.py --no-dry-run --samples 3
```
or use `make audit` / `make refresh-audit` to include it in the automated workflow.

## Security Notes

- The `.env` file is excluded from git via `.gitignore`
- Never commit your API key to version control
- The `.env` file is in your OneDrive folder, but should not sync if properly configured
