import argparse
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import pytest
from openpyxl import Workbook

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import build_diary_database as bdb


def _create_client_workbook(path: Path, diary_date: datetime) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "001"
    ws.append(["", "Date:", diary_date])
    ws.append(["", "PERSONNEL"])
    ws.append(["TCD Indirects", "", "", "TCD Directs", "", "", "Subcontractors"])
    ws.append(["Name", "Position", "Hours", "Name", "Position", "Hours", "Name", "Position", "Hours"])
    ws.append(["John Doe", "Supervisor", 8, "", "", "", "Acme Crew", "Labourer", 10])
    ws.append(["Total", "", "", "", "", "", "", "", ""])
    ws.append(["PLANT & EQUIPMENT"])
    ws.append(["DELAYS-OPPORTUNITY"])
    ws.append(["Waiting on materials"])
    ws.append(["HSEQ MESSAGES"])
    ws.append(["INCIDENTS & REPORTS"])
    ws.append(["Type", "QTY", "Comments"])
    ws.append(["INCIDENT", 1, "Sample incident"])
    ws.append(["COMMUNICATIONS"])
    ws.append(["PRODUCTION (CONSTRUCTION STATUS & PROGRESS)"])
    ws.append(["Formed entry ramp"])
    ws.append(["Placed rebar at sump"])
    ws.append(["PHOTOS"])
    wb.save(path)


def _create_supervisor_workbook(path: Path, diary_date: datetime) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "A"
    ws.append(["", "Supervisor Shift Report"])
    ws.append(["", "Project Name:", "", "Batavia", "Date:", diary_date])
    ws.append(["", "Weather Conditions"])
    ws.append(["", "LABOUR"])
    ws.append(["", "", "Hours", "Machine", "Start SMU", "End SMU", "Machine Hrs", "Location", "Activity", "Material", "Comments"])
    ws.append(["", "Worker One", 8, "Excavator", 1, 2, 1, "Site", "Excavate", "Soil", "Trenching around pits"])
    ws.append(["", "Daily Work Extension"])
    ws.append(["", "Completed extra compaction"])
    ws.append(["", "Daily Work Photos"])
    wb.save(path)


def _make_args(root: Path, db_path: Path) -> argparse.Namespace:
    return argparse.Namespace(
        root=str(root),
        client_dir="001-Client reports",
        supervisor_dir="002-Supervisor_Reports",
        database=str(db_path),
        reset=True,
        use_supervisor=True,
        use_client_fallback=True,
        skip_supervisor=False,
        skip_client_fallback=False,
    )


def test_ingest_with_supervisor_data(tmp_path: Path) -> None:
    client_dir = tmp_path / "001-Client reports"
    supervisor_dir = tmp_path / "002-Supervisor_Reports"
    client_dir.mkdir(parents=True)
    supervisor_dir.mkdir(parents=True)
    _create_client_workbook(client_dir / "client.xlsx", datetime(2025, 10, 3))
    _create_supervisor_workbook(supervisor_dir / "supervisor.xlsx", datetime(2025, 10, 3))

    args = _make_args(tmp_path, tmp_path / "diary.sqlite")
    stats = bdb.run_ingest(args)

    assert stats["activities"] == 2
    assert stats["personnel"] == 2
    assert stats["supervisor_comments"] == 1
    assert stats["supervisor_extension_notes"] == 1
    assert stats["fallback_activities"] == 0

    conn = sqlite3.connect(args.database)
    activities = conn.execute("SELECT activity FROM activities").fetchall()
    assert {row[0] for row in activities} == {"Formed entry ramp", "Placed rebar at sump"}
    personnel = conn.execute("SELECT name, hours FROM personnel").fetchall()
    assert set(personnel) == {("John Doe", 8.0), ("Acme Crew", 10.0)}
    comments = conn.execute("SELECT worker_or_group, comment FROM supervisor_comments").fetchall()
    assert comments == [("Worker One", "Trenching around pits")]
    extensions = conn.execute("SELECT note FROM supervisor_extension_notes").fetchall()
    assert extensions == [("Completed extra compaction",)]
    fallback_rows = conn.execute("SELECT COUNT(*) FROM client_fallback_activities").fetchone()[0]
    assert fallback_rows == 0


def test_client_fallback_without_supervisor(tmp_path: Path) -> None:
    client_dir = tmp_path / "001-Client reports"
    client_dir.mkdir(parents=True)
    _create_client_workbook(client_dir / "client.xlsx", datetime(2025, 10, 4))

    args = _make_args(tmp_path, tmp_path / "diary.sqlite")
    stats = bdb.run_ingest(args)

    assert stats["fallback_activities"] == 2

    conn = sqlite3.connect(args.database)
    fallback_rows = conn.execute("SELECT activity FROM client_fallback_activities").fetchall()
    assert {row[0] for row in fallback_rows} == {"Formed entry ramp", "Placed rebar at sump"}


def test_validate_only_success(tmp_path: Path) -> None:
    client_dir = tmp_path / "001-Client reports"
    supervisor_dir = tmp_path / "002-Supervisor_Reports"
    client_dir.mkdir(parents=True)
    supervisor_dir.mkdir(parents=True)
    _create_client_workbook(client_dir / "client.xlsx", datetime(2025, 10, 5))
    _create_supervisor_workbook(supervisor_dir / "supervisor.xlsx", datetime(2025, 10, 5))

    args = _make_args(tmp_path, tmp_path / "diary.sqlite")
    bdb.run_ingest(args)
    # Should not raise
    bdb.run_validate(args.database)


def test_validate_only_reports_issues(tmp_path: Path) -> None:
    db_path = tmp_path / "diary.sqlite"
    db = bdb.DiaryDatabase(db_path, reset=False)
    db.insert_activity("2025-10-06", "Activity only", "manual.xlsx", "Sheet1")
    db.commit()

    with pytest.raises(RuntimeError):
        bdb.run_validate(db_path)
