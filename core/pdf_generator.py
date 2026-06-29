import io
import os
from datetime import date, timedelta
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

BRAND_DARK = colors.HexColor("#1A1A2E")
BRAND_ACCENT = colors.HexColor("#E94560")
LIGHT_GRAY = colors.HexColor("#F5F5F5")
MID_GRAY = colors.HexColor("#CCCCCC")

COUNTER_FILE = Path(__file__).parent.parent / "quotes_counter.txt"


def _next_quote_number() -> str:
    if COUNTER_FILE.exists():
        n = int(COUNTER_FILE.read_text().strip()) + 1
    else:
        n = 1
    COUNTER_FILE.write_text(str(n))
    return f"Q-{date.today().year}-{n:04d}"


def _styles():
    base = getSampleStyleSheet()
    return {
        "company_name": ParagraphStyle(
            "company_name",
            fontSize=16,
            fontName="Helvetica-Bold",
            textColor=BRAND_DARK,
            leading=20,
        ),
        "company_sub": ParagraphStyle(
            "company_sub",
            fontSize=8,
            fontName="Helvetica",
            textColor=colors.HexColor("#555555"),
            leading=12,
        ),
        "doc_title": ParagraphStyle(
            "doc_title",
            fontSize=22,
            fontName="Helvetica-Bold",
            textColor=BRAND_ACCENT,
            leading=28,
        ),
        "section_header": ParagraphStyle(
            "section_header",
            fontSize=9,
            fontName="Helvetica-Bold",
            textColor=colors.HexColor("#888888"),
            leading=14,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "body",
            fontSize=10,
            fontName="Helvetica",
            textColor=BRAND_DARK,
            leading=14,
        ),
        "body_bold": ParagraphStyle(
            "body_bold",
            fontSize=10,
            fontName="Helvetica-Bold",
            textColor=BRAND_DARK,
            leading=14,
        ),
        "small": ParagraphStyle(
            "small",
            fontSize=8,
            fontName="Helvetica",
            textColor=colors.HexColor("#555555"),
            leading=12,
        ),
        "total_label": ParagraphStyle(
            "total_label",
            fontSize=12,
            fontName="Helvetica-Bold",
            textColor=BRAND_DARK,
        ),
        "total_value": ParagraphStyle(
            "total_value",
            fontSize=14,
            fontName="Helvetica-Bold",
            textColor=BRAND_ACCENT,
        ),
    }


def _divider():
    return HRFlowable(width="100%", thickness=1, color=MID_GRAY, spaceAfter=12, spaceBefore=12)


def generate_pdf(
    client_name: str,
    address: str,
    phone: str,
    email: str,
    result: dict,
    sop: dict,
) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    s = _styles()
    story = []
    quote_num = _next_quote_number()
    today = date.today()
    valid_until = today + timedelta(days=sop["validity_days"])
    company = sop["company"]

    # ── Header: logo left, company info right ──────────────────────────────
    logo_path = Path(__file__).parent.parent / company["logo_path"]
    if logo_path.exists():
        logo = Image(str(logo_path), width=1.4 * inch, height=1.4 * inch)
    else:
        logo = Paragraph("<b>L&amp;J</b>", ParagraphStyle(
            "logo_fallback", fontSize=28, fontName="Helvetica-Bold",
            textColor=BRAND_ACCENT,
        ))

    company_block = [
        Paragraph(company["name"], s["company_name"]),
        Paragraph(company["phone"], s["company_sub"]),
        Paragraph(company["email"], s["company_sub"]),
        Paragraph(company["website"], s["company_sub"]),
    ]

    header_table = Table(
        [[logo, company_block]],
        colWidths=[1.6 * inch, None],
    )
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
    ]))
    story.append(header_table)
    story.append(_divider())

    # ── Quote title + meta ─────────────────────────────────────────────────
    meta_data = [
        [Paragraph("PAINTING QUOTE", s["doc_title"]),
         Table([
             [Paragraph("Quote #:", s["section_header"]), Paragraph(quote_num, s["body_bold"])],
             [Paragraph("Date:", s["section_header"]), Paragraph(today.strftime("%B %d, %Y"), s["body"])],
             [Paragraph("Valid Until:", s["section_header"]), Paragraph(valid_until.strftime("%B %d, %Y"), s["body"])],
         ], colWidths=[0.8 * inch, 1.5 * inch],
            style=TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))]
    ]
    meta_table = Table(meta_data, colWidths=[3.5 * inch, None])
    meta_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 0.2 * inch))

    # ── Client info ────────────────────────────────────────────────────────
    story.append(Paragraph("PREPARED FOR", s["section_header"]))
    story.append(Paragraph(client_name, s["body_bold"]))
    story.append(Paragraph(address, s["body"]))
    if phone:
        story.append(Paragraph(phone, s["body"]))
    if email:
        story.append(Paragraph(email, s["body"]))

    story.append(_divider())

    # ── Scope blurb ────────────────────────────────────────────────────────
    story.append(Paragraph("SCOPE OF WORK", s["section_header"]))
    scope_text = (
        f"Dear {client_name}, thank you for choosing {company['name']}. "
        f"We are pleased to provide this quote for painting services at "
        f"<b>{address}</b>. "
        f"This proposal covers a total of <b>{result['sqft']:,.0f} sq ft</b> "
        f"under <b>Tier {result['tier']} — {result['tier_label']}</b> preparation. "
        f"{result['tier_description']} "
        f"Our team will handle all necessary preparation and application to ensure "
        f"a professional, long-lasting finish."
    )
    story.append(Paragraph(scope_text, s["body"]))
    story.append(_divider())

    # ── Itemized estimate ──────────────────────────────────────────────────
    story.append(Paragraph("ITEMIZED ESTIMATE", s["section_header"]))
    story.append(Spacer(1, 0.08 * inch))

    table_data = [
        [
            Paragraph("Description", s["body_bold"]),
            Paragraph("Sq Ft", s["body_bold"]),
            Paragraph("Rate / Sq Ft", s["body_bold"]),
            Paragraph("Total", s["body_bold"]),
        ],
        [
            Paragraph(f"Tier {result['tier']} — {result['tier_label']}", s["body"]),
            Paragraph(f"{result['sqft']:,.0f}", s["body"]),
            Paragraph(f"${result['rate_per_sqft']:.2f}", s["body"]),
            Paragraph(f"${result['total']:,.2f}", s["body_bold"]),
        ],
        # Blank spacer row
        ["", "", "", ""],
        [
            Paragraph("", s["body"]),
            Paragraph("", s["body"]),
            Paragraph("TOTAL", s["total_label"]),
            Paragraph(f"${result['total']:,.2f}", s["total_value"]),
        ],
    ]

    col_widths = [3.0 * inch, 1.0 * inch, 1.3 * inch, 1.3 * inch]
    est_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    est_table.setStyle(TableStyle([
        # Header row
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, 1), [LIGHT_GRAY]),
        # Total row
        ("LINEABOVE", (2, 3), (-1, 3), 1.5, BRAND_DARK),
        ("TOPPADDING", (0, 3), (-1, 3), 8),
        # General
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWHEIGHT", (0, 0), (-1, -1), 22),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, 1), 0.5, MID_GRAY),
    ]))
    story.append(est_table)
    story.append(_divider())

    # ── Terms ──────────────────────────────────────────────────────────────
    story.append(Paragraph("TERMS & CONDITIONS", s["section_header"]))
    story.append(Paragraph(sop["payment_terms"], s["body"]))
    story.append(Paragraph(
        f"This quote is valid for {sop['validity_days']} days from the date above.",
        s["small"],
    ))
    story.append(_divider())

    # ── Acceptance ─────────────────────────────────────────────────────────
    story.append(Paragraph("ACCEPTANCE", s["section_header"]))
    story.append(Paragraph(
        f"By signing below, you authorize {company['name']} to proceed with the "
        "scope of work described above at the quoted price.",
        s["body"],
    ))
    story.append(Spacer(1, 0.3 * inch))

    sig_table = Table(
        [
            [
                "Client Signature: _______________________________",
                "Date: ________________",
            ],
            ["", ""],
            [
                "Print Name:  _______________________________",
                "",
            ],
        ],
        colWidths=[4 * inch, 2.6 * inch],
    )
    sig_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (-1, -1), BRAND_DARK),
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(sig_table)

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
