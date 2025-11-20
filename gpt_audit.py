#!/usr/bin/env python3
"""
Optional GPT-based audit for diary.sqlite contents.
By default this script runs in dry-run mode to avoid accidental API calls.
"""

from __future__ import annotations

import argparse
import logging
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from textwrap import dedent
from typing import List, Optional, Tuple

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, rely on system env vars

try:
    from openai import OpenAI
    legacy_openai = None
except ImportError:  # pragma: no cover - optional dependency
    OpenAI = None
    try:  # Fallback for older openai releases
        import openai as legacy_openai
    except ImportError:  # pragma: no cover - optional dependency
        legacy_openai = None


logger = logging.getLogger("gpt_audit")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Spot-check diary entries with GPT.")
    parser.add_argument("--database", default="diary.sqlite", help="SQLite database to audit.")
    parser.add_argument("--samples", type=int, default=3, help="Number of random entries to review.")
    parser.add_argument("--model", default="gpt-4o-mini", help="OpenAI model to query.")
    parser.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Print the prompts without calling the API (default on). Use --no-dry-run to send requests.",
    )
    return parser.parse_args()


def fetch_samples(conn: sqlite3.Connection, table: str, count: int) -> List[Tuple[int, str, str, str]]:
    cursor = conn.execute(
        f"""
        SELECT id, diary_date, source_file, comment
        FROM {table}
        ORDER BY RANDOM()
        LIMIT ?
        """,
        (count,),
    )
    return cursor.fetchall()


def build_prompt(diary_date: str, source_file: str, comment: str) -> str:
    return dedent(
        f"""
        Review the following supervisor comment extracted from {source_file} on {diary_date}.

        Comment:
        {comment}

        Does this read like a faithful summary of column K in the supervisor report?
        Reply with "PASS" if it is plausible, otherwise briefly describe concerns.
        """
    ).strip()


def _get_openai_client(api_key: str):
    if OpenAI is not None:
        return "chat_completions", OpenAI(api_key=api_key)
    if legacy_openai is not None:
        legacy_openai.api_key = api_key
        return "legacy", legacy_openai
    return None, None


def _send_prompt(client_kind: str, client, model: str, prompt: str) -> str:
    if client_kind == "chat_completions":
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        if response.choices and response.choices[0].message:
            return response.choices[0].message.content.strip()
        return str(response).strip()
    completion = client.ChatCompletion.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    choice: Optional[dict] = None
    if completion and completion.get("choices"):
        choice = completion["choices"][0]
    if not choice:
        return str(completion).strip()
    message = choice.get("message", {})
    content = message.get("content")
    if isinstance(content, list):
        content = " ".join(part.get("text", "") for part in content if isinstance(part, dict))
        return str(content or "").strip()


def ensure_audit_columns(conn: sqlite3.Connection) -> None:
    required = {
        "audit_status": "TEXT",
        "audit_model": "TEXT",
        "audit_timestamp": "TEXT",
        "audit_notes": "TEXT",
    }
    cur = conn.execute("PRAGMA table_info(supervisor_comments)")
    existing = {row[1] for row in cur.fetchall()}
    for column, definition in required.items():
        if column not in existing:
            conn.execute(f"ALTER TABLE supervisor_comments ADD COLUMN {column} {definition}")
    conn.commit()


def interpret_response(answer: str) -> Tuple[str, str]:
    cleaned = (answer or "").strip()
    if not cleaned:
        return "FLAG", "[no response]"
    if cleaned.upper().startswith("PASS"):
        return "PASS", ""
    return "FLAG", cleaned


def record_audit_result(
    conn: sqlite3.Connection,
    comment_id: int,
    status: str,
    model: str,
    notes: str,
    timestamp: Optional[str] = None,
) -> str:
    ts = timestamp or datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        UPDATE supervisor_comments
        SET audit_status = ?, audit_model = ?, audit_timestamp = ?, audit_notes = ?
        WHERE id = ?
        """,
        (status, model, ts, notes, comment_id),
    )
    conn.commit()
    return ts


def main() -> None:
    args = parse_args()
    connection = sqlite3.connect(Path(args.database).expanduser().resolve())
    samples = fetch_samples(connection, "supervisor_comments", args.samples)
    if not samples:
        print("No supervisor comments found; nothing to audit.")
        return

    api_key = os.environ.get("OPENAI_API_KEY")
    if args.dry_run:
        print("Dry-run mode: printing prompts only.")
        for _, diary_date, source_file, comment in samples:
            print("-" * 40)
            print(build_prompt(diary_date, source_file, comment))
        return

    if not api_key:
        print("OPENAI_API_KEY not set; cannot perform audit.")
        return
    client_kind, client = _get_openai_client(api_key)
    if client is None:
        print("The openai package is not installed; run `pip install -r requirements.txt` to enable audits.")
        return

    ensure_audit_columns(connection)
    model_name = args.model
    if client_kind == "legacy" and model_name == "gpt-4o-mini":
        logger.info("Legacy openai client detected; falling back to gpt-3.5-turbo")
        model_name = "gpt-3.5-turbo"

    totals = {"audited": 0, "pass": 0, "flag": 0, "errors": 0}
    for comment_id, diary_date, source_file, comment in samples:
        prompt = build_prompt(diary_date, source_file, comment)
        totals["audited"] += 1
        try:
            answer = _send_prompt(client_kind, client, model_name, prompt)
        except Exception as exc:  # pragma: no cover - defensive logging
            totals["errors"] += 1
            logger.error("OpenAI request failed for %s on %s: %s", source_file, diary_date, exc)
            continue
        status, notes = interpret_response(answer)
        try:
            record_audit_result(connection, comment_id, status, model_name, notes)
        except sqlite3.Error as exc:  # pragma: no cover - defensive logging
            totals["errors"] += 1
            logger.error("Failed to store audit result for %s on %s: %s", source_file, diary_date, exc)
            continue
        if status == "PASS":
            totals["pass"] += 1
        else:
            totals["flag"] += 1
        print("-" * 40)
        print(f"Entry {diary_date} :: {source_file}")
        print(answer.strip() or "[no response]")
        print(f"Audit status: {status}")

    print(
        "Audit summary: audited {audited}, PASS {pass}, FLAG {flag}, errors {errors}".format(
            **totals
        )
    )


if __name__ == "__main__":
    logging.basicConfig(level=os.environ.get("GPT_AUDIT_LOGLEVEL", "INFO"), format="%(levelname)s: %(message)s")
    main()
