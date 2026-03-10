"""
TASK 4: Document Formatting Module
Blueprint Engine Orchestrator — Exsuvera LLC / LAB

Converts the Markdown business plan into a professionally formatted PDF
with branded cover page, LAB color palette, and Exsuvera styling.
"""

import os
import re
import logging
from datetime import date
from typing import Optional

import markdown2

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Brand constants
# ─────────────────────────────────────────────────────────────

GOLD = "#C9A84C"
BLACK = "#1A1A1A"
DARK_GRAY = "#2D2D2D"
WHITE = "#FFFFFF"
LIGHT_GRAY = "#F5F5F5"
MID_GRAY = "#888888"


# ─────────────────────────────────────────────────────────────
# HTML template builder
# ─────────────────────────────────────────────────────────────

def build_html_document(
    markdown_content: str,
    subject_name: str,
    business_name: str,
    session_date: str,
    last_name: str
) -> str:
    """
    Convert Markdown business plan to a fully branded HTML document.
    This HTML is then converted to PDF via WeasyPrint.
    """

    # Convert Markdown to HTML
    html_body = markdown2.markdown(
        markdown_content,
        extras=[
            "tables",
            "fenced-code-blocks",
            "header-ids",
            "strike",
            "break-on-newline",
            "cuddled-lists"
        ]
    )

    # Post-process: wrap blockquotes with gold left-border class
    html_body = html_body.replace("<blockquote>", '<blockquote class="interview-quote">')

    css = f"""
    @import url('https://fonts.googleapis.com/css2?family=Arial:wght@400;700&display=swap');

    * {{
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }}

    @page {{
        size: letter;
        margin: 1in 0.9in 1in 0.9in;
        @bottom-center {{
            content: "EXSUVERA LLC  |  CONFIDENTIAL";
            font-family: Arial, sans-serif;
            font-size: 8pt;
            color: {MID_GRAY};
            letter-spacing: 1px;
        }}
        @bottom-right {{
            content: counter(page);
            font-family: Arial, sans-serif;
            font-size: 8pt;
            color: {MID_GRAY};
        }}
    }}

    @page cover {{
        margin: 0;
        @bottom-center {{ content: none; }}
        @bottom-right {{ content: none; }}
    }}

    body {{
        font-family: Arial, Helvetica, sans-serif;
        font-size: 11pt;
        color: {DARK_GRAY};
        line-height: 1.7;
        background: {WHITE};
    }}

    /* ── Cover Page ── */
    .cover-page {{
        page: cover;
        width: 100%;
        min-height: 100vh;
        background: {BLACK};
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 80px 60px;
        page-break-after: always;
    }}

    .cover-lab-header {{
        font-family: Arial, Helvetica, sans-serif;
        font-size: 13pt;
        font-weight: 700;
        color: {GOLD};
        letter-spacing: 8px;
        text-transform: uppercase;
        margin-bottom: 20px;
    }}

    .cover-divider {{
        width: 80px;
        height: 2px;
        background: {GOLD};
        margin: 20px auto;
    }}

    .cover-title {{
        font-family: Arial, Helvetica, sans-serif;
        font-size: 42pt;
        font-weight: 700;
        color: {WHITE};
        letter-spacing: 4px;
        text-transform: uppercase;
        margin: 10px 0 30px 0;
        line-height: 1.1;
    }}

    .cover-business-name {{
        font-family: Arial, Helvetica, sans-serif;
        font-size: 22pt;
        font-weight: 700;
        color: {GOLD};
        margin-bottom: 40px;
        letter-spacing: 1px;
    }}

    .cover-prepared-for {{
        font-family: Arial, Helvetica, sans-serif;
        font-size: 12pt;
        color: {MID_GRAY};
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 8px;
    }}

    .cover-subject-name {{
        font-family: Arial, Helvetica, sans-serif;
        font-size: 18pt;
        font-weight: 700;
        color: {WHITE};
        margin-bottom: 50px;
    }}

    .cover-date {{
        font-family: Arial, Helvetica, sans-serif;
        font-size: 10pt;
        color: {MID_GRAY};
        letter-spacing: 1px;
        margin-bottom: 30px;
    }}

    .cover-tagline {{
        font-family: Arial, Helvetica, sans-serif;
        font-size: 10pt;
        color: {GOLD};
        letter-spacing: 3px;
        text-transform: uppercase;
        margin-top: 40px;
    }}

    /* ── Content Styles ── */
    h1 {{
        font-family: Arial, Helvetica, sans-serif;
        font-size: 22pt;
        font-weight: 700;
        color: {BLACK};
        margin: 40px 0 8px 0;
        padding-bottom: 8px;
        border-bottom: 3px solid {GOLD};
        page-break-after: avoid;
    }}

    h2 {{
        font-family: Arial, Helvetica, sans-serif;
        font-size: 15pt;
        font-weight: 700;
        color: {BLACK};
        margin: 30px 0 6px 0;
        padding-bottom: 4px;
        border-bottom: 1px solid {GOLD};
        page-break-after: avoid;
    }}

    h3 {{
        font-family: Arial, Helvetica, sans-serif;
        font-size: 12pt;
        font-weight: 700;
        color: {DARK_GRAY};
        margin: 20px 0 4px 0;
        page-break-after: avoid;
    }}

    h4 {{
        font-family: Arial, Helvetica, sans-serif;
        font-size: 11pt;
        font-weight: 700;
        color: {DARK_GRAY};
        margin: 16px 0 4px 0;
    }}

    p {{
        margin: 0 0 14px 0;
        color: {DARK_GRAY};
    }}

    ul, ol {{
        margin: 0 0 14px 20px;
        color: {DARK_GRAY};
    }}

    li {{
        margin-bottom: 6px;
        line-height: 1.6;
    }}

    strong {{
        color: {BLACK};
        font-weight: 700;
    }}

    em {{
        color: {DARK_GRAY};
        font-style: italic;
    }}

    /* Interview quotes */
    blockquote.interview-quote {{
        border-left: 4px solid {GOLD};
        margin: 20px 0;
        padding: 12px 20px;
        background: {LIGHT_GRAY};
        font-style: italic;
        color: {DARK_GRAY};
        border-radius: 0 4px 4px 0;
    }}

    blockquote.interview-quote p {{
        margin: 0;
        font-size: 11pt;
    }}

    /* Tables */
    table {{
        width: 100%;
        border-collapse: collapse;
        margin: 20px 0;
        font-size: 10pt;
    }}

    thead tr {{
        background: {GOLD};
        color: {WHITE};
    }}

    thead th {{
        padding: 10px 12px;
        font-weight: 700;
        text-align: left;
        border: 1px solid {GOLD};
    }}

    tbody tr:nth-child(even) {{
        background: {LIGHT_GRAY};
    }}

    tbody td {{
        padding: 8px 12px;
        border: 1px solid #ddd;
        color: {DARK_GRAY};
    }}

    /* Horizontal rule */
    hr {{
        border: none;
        border-top: 2px solid {GOLD};
        margin: 40px 0;
    }}

    /* Code blocks */
    code {{
        background: {LIGHT_GRAY};
        padding: 2px 6px;
        border-radius: 3px;
        font-size: 10pt;
        color: {DARK_GRAY};
    }}

    pre {{
        background: {LIGHT_GRAY};
        padding: 16px;
        border-radius: 4px;
        overflow-x: auto;
        margin: 16px 0;
    }}

    /* Section break */
    .section-break {{
        page-break-before: always;
    }}
    """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The Blueprint — {business_name}</title>
    <style>
{css}
    </style>
</head>
<body>

<!-- ═══════════════════════════════════════════════════════════ -->
<!-- COVER PAGE                                                   -->
<!-- ═══════════════════════════════════════════════════════════ -->
<div class="cover-page">
    <div class="cover-lab-header">LION &nbsp; ASS &nbsp; BITCH</div>
    <div class="cover-divider"></div>
    <div class="cover-title">THE<br>BLUEPRINT</div>
    <div class="cover-business-name">{business_name}</div>
    <div class="cover-divider"></div>
    <div class="cover-prepared-for">Prepared for</div>
    <div class="cover-subject-name">{subject_name}</div>
    <div class="cover-date">{session_date}</div>
    <div class="cover-divider"></div>
    <div class="cover-tagline">Exsuvera LLC &nbsp;—&nbsp; Shed The Limitation</div>
</div>

<!-- ═══════════════════════════════════════════════════════════ -->
<!-- BUSINESS PLAN CONTENT                                        -->
<!-- ═══════════════════════════════════════════════════════════ -->
<div class="content">
{html_body}
</div>

</body>
</html>"""

    return html


# ─────────────────────────────────────────────────────────────
# PDF generation
# ─────────────────────────────────────────────────────────────

def generate_pdf(html_content: str, output_path: str) -> bool:
    """
    Convert HTML to PDF using WeasyPrint.
    Returns True on success, False on failure.
    """
    try:
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration

        font_config = FontConfiguration()
        html_doc = HTML(string=html_content)
        html_doc.write_pdf(output_path, font_config=font_config)
        logger.info(f"PDF generated: {output_path}")
        return True
    except Exception as e:
        logger.error(f"WeasyPrint PDF generation failed: {e}")
        return False


def generate_html_fallback(html_content: str, output_path: str) -> bool:
    """Save HTML as fallback if PDF generation fails."""
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        logger.info(f"HTML fallback saved: {output_path}")
        return True
    except Exception as e:
        logger.error(f"HTML fallback save failed: {e}")
        return False


# ─────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────

def run_document_formatter(
    markdown_content: str,
    subject_first_name: str,
    subject_last_name: str,
    business_name: str,
    session_date: str,
    output_dir: str = "/home/ubuntu/blueprint_engine/output"
) -> dict:
    """
    Format the business plan Markdown into a branded PDF document.

    Args:
        markdown_content: Full business plan in Markdown
        subject_first_name: Subject's first name
        subject_last_name: Subject's last name
        business_name: Name of the business
        session_date: Date string (YYYY-MM-DD)
        output_dir: Directory to save output files

    Returns:
        dict with pdf_path, html_path, filename, success
    """
    os.makedirs(output_dir, exist_ok=True)

    subject_name = f"{subject_first_name} {subject_last_name}".strip()
    filename_base = f"Blueprint_{subject_last_name}_{session_date}"
    pdf_path = os.path.join(output_dir, f"{filename_base}.pdf")
    html_path = os.path.join(output_dir, f"{filename_base}.html")

    # Format date for display
    try:
        from datetime import datetime
        display_date = datetime.strptime(session_date, "%Y-%m-%d").strftime("%B %d, %Y")
    except Exception:
        display_date = session_date

    # Build HTML
    logger.info("Building HTML document...")
    html_content = build_html_document(
        markdown_content=markdown_content,
        subject_name=subject_name,
        business_name=business_name,
        session_date=display_date,
        last_name=subject_last_name
    )

    # Save HTML (always)
    generate_html_fallback(html_content, html_path)

    # Attempt PDF
    pdf_success = generate_pdf(html_content, pdf_path)

    return {
        "pdf_path": pdf_path if pdf_success else None,
        "html_path": html_path,
        "filename": f"{filename_base}.pdf",
        "pdf_success": pdf_success,
        "subject_name": subject_name,
        "business_name": business_name
    }


# ─────────────────────────────────────────────────────────────
# Standalone test
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sample_md = """
# I. EXECUTIVE SUMMARY

Marcus Rivera is a 44-year-old Houston-based personal trainer and online fitness coach
who has built a $2,400/month coaching business while working a full-time job.

> "I know the way out and I'd be selfish to keep it to myself."

This plan is built to get you to $78,000 in annual coaching revenue — your stated
replacement salary — within 12 months.

## The Opportunity

The men's health and fitness coaching market is growing rapidly...
"""
    result = run_document_formatter(
        markdown_content=sample_md,
        subject_first_name="Marcus",
        subject_last_name="Rivera",
        business_name="Fit With Marcus",
        session_date="2026-03-10"
    )
    print(result)
