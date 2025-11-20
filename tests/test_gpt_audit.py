import sqlite3
from datetime import date
from pathlib import Path

from gpt_audit import ensure_audit_columns, interpret_response, record_audit_result

import build_diary_database as bdb


def test_ensure_audit_columns_adds_missing(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy.sqlite"
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE supervisor_comments (
            id INTEGER PRIMARY KEY,
            diary_date TEXT,
            worker_or_group TEXT,
            comment TEXT
        )
        """
    )
    conn.commit()

    ensure_audit_columns(conn)

    columns = {row[1] for row in conn.execute("PRAGMA table_info(supervisor_comments)")}
    for expected in {"audit_status", "audit_model", "audit_timestamp", "audit_notes"}:
        assert expected in columns


def test_record_audit_result_updates_row(tmp_path: Path) -> None:
    db_path = tmp_path / "audit.sqlite"
    db = bdb.DiaryDatabase(db_path, reset=True)
    record = bdb.SupervisorCommentRecord(
        diary_date=date(2025, 5, 1),
        label="Worker One",
        hours=8.0,
        machine="Excavator",
        start_smu="1",
        end_smu="2",
        machine_hours="1",
        location="Site",
        activity="Dig",
        material="Soil",
        comment="Trenching around pits",
        source_file="test.xlsx",
        worksheet="A",
    )
    db.insert_supervisor_comment(record)
    db.commit()

    conn = sqlite3.connect(db_path)
    comment_id = conn.execute("SELECT id FROM supervisor_comments").fetchone()[0]
    ensure_audit_columns(conn)
    record_audit_result(conn, comment_id, "PASS", "gpt-test", "", timestamp="2025-01-01T00:00:00Z")

    row = conn.execute(
        """
        SELECT audit_status, audit_model, audit_timestamp, audit_notes
        FROM supervisor_comments
        WHERE id = ?
        """,
        (comment_id,),
    ).fetchone()
    assert row == ("PASS", "gpt-test", "2025-01-01T00:00:00Z", "")


def test_interpret_response_flags_non_pass() -> None:
    assert interpret_response("PASS - looks good") == ("PASS", "")
    assert interpret_response("Needs work") == ("FLAG", "Needs work")
    assert interpret_response("") == ("FLAG", "[no response]")
