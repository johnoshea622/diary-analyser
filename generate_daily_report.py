#!/usr/bin/env python3
"""
Create a comprehensive day-by-day report from diary.sqlite.

Outputs:
  - analysis/daily_report.json        Full detail per day (activities, personnel, etc.)
  - analysis/daily_report_summary.csv One row per day with useful counts/flags.
"""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate daily diary report from SQLite database.")
    parser.add_argument("--database", default="diary.sqlite", help="SQLite database path.")
    parser.add_argument("--output-dir", default="analysis", help="Directory for generated reports.")
    return parser.parse_args()


def fetch_rows(conn: sqlite3.Connection, query: str, params: Tuple = ()) -> List[Dict[str, object]]:
    cursor = conn.execute(query, params)
    columns = [description[0] for description in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def build_day_record(conn: sqlite3.Connection, diary_date: str) -> Dict[str, object]:
    day: Dict[str, object] = {"diary_date": diary_date}
    day["activities"] = fetch_rows(
        conn,
        """
        SELECT activity, source_file, worksheet
        FROM activities
        WHERE diary_date = ?
        ORDER BY source_file, worksheet, activity
        """,
        (diary_date,),
    )
    day["personnel"] = fetch_rows(
        conn,
        """
        SELECT team_type, name, position, hours, source_file, worksheet
        FROM personnel
        WHERE diary_date = ?
        ORDER BY team_type, name
        """,
        (diary_date,),
    )
    day["delays_issues"] = fetch_rows(
        conn,
        """
        SELECT entry_type, label, description, qty, comments, source_file, worksheet
        FROM delays_issues
        WHERE diary_date = ?
        ORDER BY entry_type, label
        """,
        (diary_date,),
    )
    day["supervisor_comments"] = fetch_rows(
        conn,
        """
        SELECT worker_or_group, hours, machine, start_smu, end_smu, machine_hours,
               location, activity, material, comment, source_file, worksheet
        FROM supervisor_comments
        WHERE diary_date = ?
        ORDER BY worker_or_group
        """,
        (diary_date,),
    )
    day["supervisor_extension_notes"] = fetch_rows(
        conn,
        """
        SELECT note, source_file, worksheet
        FROM supervisor_extension_notes
        WHERE diary_date = ?
        ORDER BY source_file, worksheet
        """,
        (diary_date,),
    )
    day["fallback_activities"] = fetch_rows(
        conn,
        """
        SELECT activity, source_file, worksheet
        FROM client_fallback_activities
        WHERE diary_date = ?
        ORDER BY source_file, worksheet, activity
        """,
        (diary_date,),
    )
    return day


def summarize_day(day: Dict[str, object]) -> Dict[str, object]:
    return {
        "diary_date": day["diary_date"],
        "activities": len(day["activities"]),
        "personnel": len(day["personnel"]),
        "delays": sum(1 for item in day["delays_issues"] if item["entry_type"] == "delay"),
        "issues": sum(1 for item in day["delays_issues"] if item["entry_type"] == "issue"),
        "supervisor_comments": len(day["supervisor_comments"]),
        "supervisor_extension_notes": len(day["supervisor_extension_notes"]),
        "fallback_activities": len(day["fallback_activities"]),
        "has_supervisor": bool(day["supervisor_comments"] or day["supervisor_extension_notes"]),
        "uses_fallback": bool(day["fallback_activities"]),
    }


def main() -> None:
    args = parse_args()
    db_path = Path(args.database).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.execute(
        """
        SELECT diary_date FROM (
            SELECT diary_date FROM activities
            UNION
            SELECT diary_date FROM personnel
            UNION
            SELECT diary_date FROM delays_issues
            UNION
            SELECT diary_date FROM supervisor_comments
            UNION
            SELECT diary_date FROM supervisor_extension_notes
            UNION
            SELECT diary_date FROM client_fallback_activities
        )
        ORDER BY diary_date
        """
    )
    dates = [row[0] for row in cursor.fetchall()]
    days: List[Dict[str, object]] = []
    summaries: List[Dict[str, object]] = []
    for diary_date in dates:
        day = build_day_record(conn, diary_date)
        days.append(day)
        summaries.append(summarize_day(day))

    json_path = output_dir / "daily_report.json"
    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(days, handle, indent=2)

    summary_path = output_dir / "daily_report_summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summaries[0].keys()) if summaries else [])
        writer.writeheader()
        for row in summaries:
            writer.writerow(row)

    print(f"Wrote {len(days)} day-level reports to {json_path}")
    print(f"Wrote summary CSV to {summary_path}")


if __name__ == "__main__":
    main()
