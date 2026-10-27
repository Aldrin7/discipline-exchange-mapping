"""Generate a PDF from manuscript.md using reportlab (no LaTeX available).
Produces manuscript.pdf with corrected content."""
from __future__ import annotations
from pathlib import Path
import re
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Preformatted,
                                 Table, TableStyle, PageBreak)
from reportlab.lib import colors

BASE = Path(__file__).resolve().parents[1]
MD = BASE / "manuscript" / "manuscript.md"
OUT = BASE / "manuscript" / "manuscript.pdf"

text = MD.read_text(encoding="utf-8")
lines = text.splitlines()

styles = getSampleStyleSheet()
title_style = ParagraphStyle("Title", parent=styles["Title"], fontSize=14, spaceAfter=6)
h1_style = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=13, spaceBefore=12, spaceAfter=4)
h2_style = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=11, spaceBefore=8, spaceAfter=3)
h3_style = ParagraphStyle("H3", parent=styles["Heading3"], fontSize=10, spaceBefore=6, spaceAfter=2)
body_style = ParagraphStyle("Body", parent=styles["BodyText"], fontSize=9.5, leading=12, spaceAfter=4)
code_style = ParagraphStyle("Code", parent=styles["Code"], fontSize=8, leading=10, spaceAfter=4)

story = []
# Simple markdown-ish parser
i = 0
n = len(lines)
while i < n:
    line = lines[i]
    stripped = line.strip()
    if not stripped:
        i += 1
        continue
    # Headings
    if stripped.startswith("# "):
        story.append(Paragraph(stripped[2:].strip(), title_style))
        i += 1
        continue
    if stripped.startswith("## "):
        story.append(Paragraph(stripped[3:].strip(), h1_style))
        i += 1
        continue
    if stripped.startswith("### "):
        story.append(Paragraph(stripped[4:].strip(), h2_style))
        i += 1
        continue
    if stripped.startswith("#### "):
        story.append(Paragraph(stripped[5:].strip(), h3_style))
        i += 1
        continue
    # Horizontal rule
    if stripped.startswith("---") or stripped.startswith("----"):
        story.append(Spacer(1, 6))
        i += 1
        continue
    # Table (collect consecutive lines starting with |)
    if stripped.startswith("|"):
        table_lines = []
        while i < n and lines[i].strip().startswith("|"):
            table_lines.append(lines[i].strip())
            i += 1
        # Parse table
        rows = []
        for tl in table_lines:
            if re.match(r"^\|[-\s|]+\|$", tl):
                continue  # separator
            cells = [c.strip() for c in tl.strip("|").split("|")]
            rows.append(cells)
        if rows:
            # Determine column count
            ncols = max(len(r) for r in rows)
            for r in rows:
                while len(r) < ncols:
                    r.append("")
            # Build table with small font
            tbl = Table(rows, repeatRows=1)
            tbl.setStyle(TableStyle([
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("LEADING", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            story.append(tbl)
            story.append(Spacer(1, 4))
        continue
    # Bullet list
    if stripped.startswith("- ") or stripped.startswith("* "):
        bullet_text = stripped[2:].strip()
        # Convert markdown bold **text** to <b>text</b>
        bullet_text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", bullet_text)
        story.append(Paragraph("• " + bullet_text, body_style))
        i += 1
        continue
    # Numbered list
    if re.match(r"^\d+\.\s", stripped):
        num_text = re.sub(r"^\d+\.\s", "", stripped)
        num_text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", num_text)
        story.append(Paragraph(num_text, body_style))
        i += 1
        continue
    # Code block
    if stripped.startswith("```"):
        i += 1
        code_lines = []
        while i < n and not lines[i].strip().startswith("```"):
            code_lines.append(lines[i])
            i += 1
        i += 1  # skip closing ```
        story.append(Preformatted("\n".join(code_lines), code_style))
        continue
    # Regular paragraph (collect consecutive non-blank, non-special lines)
    para_lines = [stripped]
    i += 1
    while i < n and lines[i].strip() and not lines[i].strip().startswith(("#", "|", "-", "*", "```", "---")) and not re.match(r"^\d+\.\s", lines[i].strip()):
        para_lines.append(lines[i].strip())
        i += 1
    para_text = " ".join(para_lines)
    # Convert markdown bold
    para_text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", para_text)
    # Convert markdown italics
    para_text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", para_text)
    # Escape XML special chars (but not our tags)
    # Simple: just append
    story.append(Paragraph(para_text, body_style))

doc = SimpleDocTemplate(str(OUT), pagesize=letter,
                        leftMargin=0.8*inch, rightMargin=0.8*inch,
                        topMargin=0.8*inch, bottomMargin=0.8*inch)
doc.build(story)
print(f"PDF written: {OUT} ({OUT.stat().st_size} bytes)")