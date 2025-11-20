import sys
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import dedupe_diary_entries as dedupe
import parse_daily_reports as pdr


def _create_client_workbook(
    path: Path,
    diary_date: datetime,
    personnel_rows: list[list[object]],
    activities: list[str],
    sheet_title: str = "001",
) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_title
    ws.append(["", "Date:", diary_date])
    ws.append(["", "PERSONNEL"])
    ws.append(["Team A", "", "", "Team B", "", "", "Subcontractors"])
    ws.append(["Name", "Position", "Hours", "Name", "Position", "Hours", "Name", "Position", "Hours"])
    for row in personnel_rows:
        ws.append(row)
    ws.append(["Total", "", "", "", "", "", "", "", ""])
    ws.append(["PLANT & EQUIPMENT"])
    ws.append(["DELAYS-OPPORTUNITY"])
    ws.append(["", "", ""])
    ws.append(["PRODUCTION (CONSTRUCTION STATUS & PROGRESS)"])
    for text in activities:
        ws.append(["", text])
    ws.append(["", "PHOTOS"])
    wb.save(path)


def _create_supervisor_workbook(
    path: Path,
    diary_date: datetime,
    labour_rows: list[dict],
    extension_notes: list[str],
    sheet_title: str = "A",
) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_title
    ws.append(["", "Supervisor Shift Report"])
    ws.append(["", "Project Name:", "", "Project X", "Date:", diary_date])
    ws.append(["", "Weather Conditions"])
    ws.append(["", "LABOUR"])
    ws.append(["", "", "Hours", "Machine", "Start SMU", "End SMU", "Machine Hrs", "Location", "Activity", "Material", "Comments"])
    for row in labour_rows:
        ws.append(
            [
                "",
                row["label"],
                row["hours"],
                row["machine"],
                row["start_smu"],
                row["end_smu"],
                row["machine_hours"],
                row["location"],
                row["activity"],
                row["material"],
                row["comment"],
            ]
        )
    ws.append(["", "Daily Work Extension"])
    for note in extension_notes:
        ws.append(["", note])
    ws.append(["", "Daily Work Photos"])
    wb.save(path)


def test_dedupe_annotations_flag_single_and_multi_source(tmp_path: Path) -> None:
    diary_date = datetime(2025, 5, 1)
    file_a = tmp_path / "client_A.xlsx"
    file_b = tmp_path / "client_B.xlsx"
    _create_client_workbook(
        file_a,
        diary_date,
        personnel_rows=[
            ["Alice", "Supervisor", 8, "", "", "", "", "", ""],
            ["", "", "", "", "", "", "Crew Solo", "Labourer", 5],
        ],
        activities=["Form footings", "Install anchors"],
        sheet_title="A",
    )
    _create_client_workbook(
        file_b,
        diary_date,
        personnel_rows=[
            ["Alice", "Supervisor", 8, "", "", "", "", "", ""],
            ["", "", "", "Bob", "Operator", 7, "", "", ""],
        ],
        activities=["Form footings", "Tie rebar"],
        sheet_title="B",
    )

    activities, personnel, date_sources, errors = dedupe.gather_entries(tmp_path)
    assert not errors
    assert len(date_sources[diary_date.date()]) == 2

    activity_rows, activity_summary = dedupe.annotate_activity_entries(activities, date_sources)
    activity_map = {row["activity_text"]: row for row in activity_summary}
    assert activity_map["Form footings"]["status"] == "present in all 2 copies"
    assert activity_map["Form footings"]["report_copies_for_date"] == 2
    assert activity_map["Install anchors"]["status"].startswith("single instance in")
    assert "client_B.xlsx::B" in activity_map["Install anchors"]["sources_missing"]
    install_row = next(row for row in activity_rows if row["activity_text"] == "Install anchors")
    assert install_row["unique_to_source"] is True

    personnel_rows, personnel_summary = dedupe.annotate_personnel_entries(personnel, date_sources)
    personnel_map = {(row["team"], row["name"]): row for row in personnel_summary}
    assert personnel_map[("Team A", "Alice")]["status"] == "present in all 2 copies"
    solo_summary = personnel_map[("Subcontractors", "Crew Solo")]
    assert solo_summary["status"].startswith("single instance in")
    solo_row = next(row for row in personnel_rows if row["name"] == "Crew Solo")
    assert solo_row["unique_to_source"] is True


def test_parse_supervisor_reports_extracts_comments_and_notes(tmp_path: Path) -> None:
    supervisor_dir = tmp_path / "002-Supervisor_Reports"
    supervisor_dir.mkdir()
    diary_date = datetime(2025, 5, 2)
    workbook_path = supervisor_dir / "supervisor.xlsx"
    _create_supervisor_workbook(
        workbook_path,
        diary_date,
        labour_rows=[
            {
                "label": "Worker One",
                "hours": 8,
                "machine": "Excavator",
                "start_smu": 1,
                "end_smu": 2,
                "machine_hours": 1,
                "location": "North cut",
                "activity": "Dig",
                "material": "Soil",
                "comment": "Trenching around pits",
            },
            {
                "label": "Worker Two",
                "hours": 6,
                "machine": "Loader",
                "start_smu": 3,
                "end_smu": 4,
                "machine_hours": 1,
                "location": "South pad",
                "activity": "Backfill",
                "material": "Rock",
                "comment": "Backfilling retaining walls",
            },
        ],
        extension_notes=["Completed extra compaction"],
    )

    comments, notes, dates = pdr.parse_supervisor_reports(supervisor_dir, tmp_path)
    assert dates == {diary_date.date()}
    assert {entry.comment for entry in comments} == {
        "Trenching around pits",
        "Backfilling retaining walls",
    }
    assert [note.note for note in notes] == ["Completed extra compaction"]
    assert all(entry.source_file.endswith("supervisor.xlsx") for entry in comments)


def test_parse_client_reports_skips_supervisor_dates(tmp_path: Path) -> None:
    client_dir = tmp_path / "001-Client reports"
    client_dir.mkdir()
    date_without_supervisor = datetime(2025, 5, 3)
    date_with_supervisor = datetime(2025, 5, 4)
    _create_client_workbook(
        client_dir / "client_missing_super.xlsx",
        date_without_supervisor,
        personnel_rows=[
            ["Crew", "Lead", 8, "", "", "", "", "", ""],
        ],
        activities=["Pour slab", "Strip forms"],
    )
    _create_client_workbook(
        client_dir / "client_has_super.xlsx",
        date_with_supervisor,
        personnel_rows=[
            ["Crew", "Lead", 8, "", "", "", "", "", ""],
        ],
        activities=["Skip me"],
    )

    entries = pdr.parse_client_reports(client_dir, tmp_path, {date_with_supervisor.date()})
    assert [entry.diary_date for entry in entries] == [date_without_supervisor.date(), date_without_supervisor.date()]
    assert [entry.text for entry in entries] == ["Pour slab", "Strip forms"]
