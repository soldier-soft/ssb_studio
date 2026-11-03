"""Report generation (PDF via ReportLab, CSV) and database backup management."""

import csv
import io
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from database.models import Session, SessionResponse

logger = logging.getLogger(__name__)


class NumberedCanvas:
    """Two-pass canvas for ReportLab to print accurate 'Page X of Y' in footer."""

    def __init__(self, *args, **kwargs):
        from reportlab.pdfgen import canvas

        self._canvas_class = canvas.Canvas
        # We will use closure in build callback instead for standard SimpleDocTemplate


class ReportService:
    """Generates structured PDF reports, CSV exports, and manages SQLite backups."""

    def __init__(self) -> None:
        pass

    # -------------------------------------------------------------
    # CSV Export
    # -------------------------------------------------------------
    def export_session_to_csv(
        self,
        session: Session,
        responses: List[SessionResponse],
        output_path: Path | str,
    ) -> Path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        with open(out, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            # Header info
            writer.writerow(["SSB Practice Studio - Session Export"])
            writer.writerow(["Test Type", session.test_type])
            writer.writerow(["Preset Name", session.preset_name])
            writer.writerow(["Content Set", session.content_set_name])
            writer.writerow(["Date", session.start_time])
            writer.writerow(["Status", session.status])
            writer.writerow(["Mode", "Exam Mode" if session.is_exam_mode else "Practice Mode"])
            writer.writerow(["Total Items", session.total_items])
            writer.writerow(["Completed Items", session.completed_items])
            writer.writerow(["Elapsed Seconds", f"{session.elapsed_seconds:.1f}"])
            if session.evaluator_notes:
                writer.writerow(["Evaluator Notes", session.evaluator_notes])
            writer.writerow([])  # Blank separator

            # Table header
            writer.writerow(
                [
                    "Item #",
                    "Identifier / Serial",
                    "Prompt / Content",
                    "Candidate Response",
                    "Length (chars)",
                    "Time Spent (s)",
                    "Completed",
                ]
            )

            for r in responses:
                writer.writerow(
                    [
                        r.item_index + 1,
                        r.item_identifier,
                        r.prompt_text,
                        r.response_text,
                        r.response_length,
                        f"{r.time_spent_seconds:.1f}",
                        "Yes" if r.is_completed else "No",
                    ]
                )

        return out

    # -------------------------------------------------------------
    # PDF Report Generation (ReportLab)
    # -------------------------------------------------------------
    def generate_pdf_report(
        self,
        session: Session,
        responses: List[SessionResponse],
        output_path: Path | str,
    ) -> Path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        doc = SimpleDocTemplate(
            str(out),
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=40,
            bottomMargin=40,
        )

        styles = getSampleStyleSheet()

        # Custom typography styles
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#0F172A"),
            spaceAfter=4,
        )

        subtitle_style = ParagraphStyle(
            "DocSubtitle",
            parent=styles["Normal"],
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#475569"),
            spaceAfter=12,
        )

        section_heading = ParagraphStyle(
            "SectionHeading",
            parent=styles["Heading2"],
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#1E3A8A"),
            spaceBefore=12,
            spaceAfter=6,
        )

        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#1E293B"),
        )

        table_header_style = ParagraphStyle(
            "TableHeader",
            parent=styles["Normal"],
            fontSize=9,
            leading=11,
            fontName="Helvetica-Bold",
            textColor=colors.white,
        )

        table_cell_style = ParagraphStyle(
            "TableCell",
            parent=styles["Normal"],
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#0F172A"),
        )

        table_prompt_style = ParagraphStyle(
            "TablePrompt",
            parent=styles["Normal"],
            fontSize=8.5,
            leading=11,
            fontName="Helvetica-Bold",
            textColor=colors.HexColor("#1E3A8A"),
        )

        story = []

        # Title & Subtitle
        full_test_names = {
            "TAT": "Thematic Apperception Test (TAT)",
            "WAT": "Word Association Test (WAT)",
            "SRT": "Situation Reaction Test (SRT)",
        }
        test_full_name = full_test_names.get(session.test_type, session.test_type)

        story.append(Paragraph(f"SSB Practice Studio — {test_full_name}", title_style))
        story.append(
            Paragraph(
                f"Candidate Session Performance Report • Generated on {datetime.now().strftime('%d %b %Y, %I:%M %p')}",
                subtitle_style,
            )
        )
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#CBD5E1"), spaceAfter=12))

        # Metadata Summary Card Table
        completion_pct = (
            (session.completed_items / session.total_items * 100)
            if session.total_items > 0
            else 0.0
        )
        mins = int(session.elapsed_seconds // 60)
        secs = int(session.elapsed_seconds % 60)

        meta_data = [
            [
                Paragraph("<b>Session ID:</b>", body_style),
                Paragraph(str(session.id), body_style),
                Paragraph("<b>Date:</b>", body_style),
                Paragraph(session.start_time[:19].replace("T", " "), body_style),
            ],
            [
                Paragraph("<b>Preset:</b>", body_style),
                Paragraph(session.preset_name, body_style),
                Paragraph("<b>Mode:</b>", body_style),
                Paragraph("Exam Mode" if session.is_exam_mode else "Practice Mode", body_style),
            ],
            [
                Paragraph("<b>Content Set:</b>", body_style),
                Paragraph(session.content_set_name or "Default", body_style),
                Paragraph("<b>Status:</b>", body_style),
                Paragraph(f"<b>{session.status}</b>", body_style),
            ],
            [
                Paragraph("<b>Items Completed:</b>", body_style),
                Paragraph(f"{session.completed_items} / {session.total_items} ({completion_pct:.1f}%)", body_style),
                Paragraph("<b>Time Taken:</b>", body_style),
                Paragraph(f"{mins}m {secs}s", body_style),
            ],
        ]

        meta_table = Table(meta_data, colWidths=[100, 170, 100, 170])
        meta_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(meta_table)
        story.append(Spacer(1, 14))

        # Evaluator Notes if any
        if session.evaluator_notes:
            story.append(Paragraph("Evaluator / Self-Assessment Notes", section_heading))
            notes_p = Paragraph(session.evaluator_notes.replace("\n", "<br/>"), body_style)
            notes_table = Table([[notes_p]], colWidths=[540])
            notes_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FEF3C7")),
                        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#F59E0B")),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                        ("LEFTPADDING", (0, 0), (-1, -1), 10),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ]
                )
            )
            story.append(notes_table)
            story.append(Spacer(1, 14))

        # Item Response Table
        story.append(Paragraph("Detailed Responses", section_heading))

        if session.test_type == "TAT":
            # For TAT: Item #, Picture, Story
            resp_table_data = [
                [
                    Paragraph("#", table_header_style),
                    Paragraph("Picture Label", table_header_style),
                    Paragraph("Candidate Story", table_header_style),
                    Paragraph("Chars", table_header_style),
                ]
            ]
            for r in responses:
                resp_table_data.append(
                    [
                        Paragraph(str(r.item_index + 1), table_cell_style),
                        Paragraph(r.item_identifier or f"Pic {r.item_index + 1}", table_prompt_style),
                        Paragraph(r.response_text.replace("\n", "<br/>") if r.response_text else "<i>(No story written)</i>", table_cell_style),
                        Paragraph(str(r.response_length), table_cell_style),
                    ]
                )
            col_widths = [30, 90, 375, 45]

        elif session.test_type == "WAT":
            # For WAT: Item #, Word, Response
            resp_table_data = [
                [
                    Paragraph("#", table_header_style),
                    Paragraph("Word Prompt", table_header_style),
                    Paragraph("Candidate Association", table_header_style),
                    Paragraph("Status", table_header_style),
                ]
            ]
            for r in responses:
                resp_table_data.append(
                    [
                        Paragraph(str(r.item_index + 1), table_cell_style),
                        Paragraph(r.prompt_text, table_prompt_style),
                        Paragraph(r.response_text if r.response_text else "<i>(Skipped / Blank)</i>", table_cell_style),
                        Paragraph("Done" if r.is_completed else "Blank", table_cell_style),
                    ]
                )
            col_widths = [30, 130, 310, 70]

        else:  # SRT
            # For SRT: Q#, Situation, Reaction
            resp_table_data = [
                [
                    Paragraph("Q#", table_header_style),
                    Paragraph("Situation Prompt", table_header_style),
                    Paragraph("Candidate Reaction", table_header_style),
                    Paragraph("Chars", table_header_style),
                ]
            ]
            for r in responses:
                resp_table_data.append(
                    [
                        Paragraph(str(r.item_identifier), table_prompt_style),
                        Paragraph(r.prompt_text, table_cell_style),
                        Paragraph(r.response_text if r.response_text else "<i>(No reaction recorded)</i>", table_cell_style),
                        Paragraph(str(r.response_length), table_cell_style),
                    ]
                )
            col_widths = [35, 235, 225, 45]

        response_table = Table(resp_table_data, colWidths=col_widths, repeatRows=1)
        response_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ]
            )
        )
        story.append(response_table)

        # Footer notes
        story.append(Spacer(1, 14))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E1"), spaceAfter=8))
        story.append(
            Paragraph(
                "SSB Practice Studio • Offline Practice Record • Objective responses stored locally in candidate SQLite repository.",
                ParagraphStyle("FooterNote", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#64748B")),
            )
        )

        doc.build(story)
        return out

    # -------------------------------------------------------------
    # Database Backup & Restore
    # -------------------------------------------------------------
    def backup_database(self, source_db_path: Path | str, target_backup_path: Path | str) -> Path:
        """Create atomic online backup of SQLite database."""
        src = Path(source_db_path)
        dest = Path(target_backup_path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        if not src.exists():
            raise FileNotFoundError(f"Database file not found: {src}")

        src_conn = sqlite3.connect(str(src))
        dest_conn = sqlite3.connect(str(dest))

        try:
            with dest_conn:
                src_conn.backup(dest_conn, pages=100)
        finally:
            dest_conn.close()
            src_conn.close()

        return dest

    def restore_database(self, backup_file_path: Path | str, active_db_path: Path | str) -> bool:
        """Restore database from backup file safely."""
        bk = Path(backup_file_path)
        active = Path(active_db_path)

        if not bk.exists():
            raise FileNotFoundError(f"Backup file not found: {bk}")

        # Verify integrity of backup file first
        bk_conn = sqlite3.connect(str(bk))
        try:
            cur = bk_conn.cursor()
            cur.execute("PRAGMA integrity_check;")
            res = cur.fetchone()[0]
            if res != "ok":
                raise ValueError(f"Backup file integrity check failed: {res}")
        finally:
            bk_conn.close()

        # Perform atomic copy to active db
        active_conn = sqlite3.connect(str(active))
        bk_conn2 = sqlite3.connect(str(bk))
        try:
            with active_conn:
                bk_conn2.backup(active_conn, pages=100)
            return True
        finally:
            bk_conn2.close()
            active_conn.close()
