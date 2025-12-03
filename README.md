# Diary Analyser

A Python-based tool for analyzing and auditing diary entries from client and supervisor reports.

## Features

- 📊 Parse and extract data from Excel-based daily reports
- 🗄️ Build SQLite database from diary entries
- 🔍 Deduplicate entries across multiple reports
- 🤖 GPT-powered audit for quality assurance
- 📈 Generate analysis reports and summaries

## Setup

### Prerequisites

codex/update-readme-to-specify-python-version
- Python 3.11 (matches the interpreter configured in the Makefile)
- Required virtual environment (local usage only):
/Users/johnoshea/Documents/programming/venvs/94_Project_Cost Analyser/
- OpenAI API key (stored in `.env` file)

### Installation

1. Clone the repository
2. Create a `.env` file with your OpenAI API key:
   ```
   OPENAI_API_KEY=your-key-here
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Build Database
```bash
make ingest
```

### Deduplicate Entries
```bash
make dedupe
```

### Parse Daily Reports
```bash
make parse_daily
```

### Run GPT Audit
```bash
make audit
```

### Run All Steps
```bash
make refresh
```

## Project Structure

- `build_diary_database.py` - Ingest reports into SQLite database
- `dedupe_diary_entries.py` - Remove duplicate entries
- `parse_daily_reports.py` - Parse and analyze daily reports
- `generate_daily_report.py` - Generate summary reports
- `gpt_audit.py` - GPT-powered quality audit
- `001-Client reports/` - Client daily reports (PDF/Excel)
- `002-Supervisor_Reports/` - Supervisor reports (Excel)
- `analysis/` - Generated analysis outputs

## Testing

```bash
make tests
```

## Security Notes

- `.env` file is excluded from git (contains API key)
- Never commit your OpenAI API key
- Database files are excluded from version control

## License

Private project for BMI diary analysis.
