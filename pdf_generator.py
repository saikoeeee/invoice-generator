# pdf_generator.py

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_RIGHT, TA_LEFT, TA_CENTER
import config
import database


# ── Colour Palette ─────────────────────────────────────────────
PRIMARY = colors.HexColor("#1a1a2e")
ACCENT = colors.HexColor("#4f8ef7")
LIGHT_GREY = colors.HexColor("#f7fafc")
MID_GREY = colors.HexColor("#e2e8f0")
TEXT_GREY = colors.HexColor("#718096")
WHITE = colors.white
BLACK = colors.HexColor("#1a1a2e")

STATUS_COLOURS = {
    "paid": colors.HexColor("#28a745"),
    "unpaid": colors.HexColor("#dc3545"),
    "overdue": colors.HexColor("#fd7e14")
}


def build_styles():
    """Returns a dict of paragraph styles used throughout the PDF."""
    styles = getSampleStyleSheet()

    return {
        "business_name": ParagraphStyle(
            "BusinessName",
            fontSize=22,
            textColor=WHITE,
            fontName="Helvetica-Bold",
            alignment=TA_LEFT
        ),
        "business_detail": ParagraphStyle(
            "BusinessDetail",
            fontSize=9,
            textColor=colors.HexColor("#a0aec0"),
            fontName="Helvetica",
            alignment=TA_LEFT,
            leading=14
        ),
        "invoice_title": ParagraphStyle(
            "InvoiceTitle",
            fontSize=28,
            textColor=WHITE,
            fontName="Helvetica-Bold",
            alignment=TA_RIGHT
        ),
        "invoice_meta": ParagraphStyle(
            "InvoiceMeta",
            fontSize=9,
            textColor=colors.HexColor("#a0aec0"),
            fontName="Helvetica",
            alignment=TA_RIGHT,
            leading=14
        ),
        "section_label": ParagraphStyle(
            "SectionLabel",
            fontSize=8,
            textColor=TEXT_GREY,
            fontName="Helvetica-Bold",
            alignment=TA_LEFT,
            spaceAfter=2
        ),
        "section_value": ParagraphStyle(
            "SectionValue",
            fontSize=10,
            textColor=BLACK,
            fontName="Helvetica",
            alignment=TA_LEFT,
            leading=15
        ),
        "table_header": ParagraphStyle(
            "TableHeader",
            fontSize=9,
            textColor=WHITE,
            fontName="Helvetica-Bold",
            alignment=TA_LEFT
        ),
        "table_cell": ParagraphStyle(
            "TableCell",
            fontSize=9,
            textColor=BLACK,
            fontName="Helvetica",
            alignment=TA_LEFT
        ),
        "table_cell_right": ParagraphStyle(
            "TableCellRight",
            fontSize=9,
            textColor=BLACK,
            fontName="Helvetica",
            alignment=TA_RIGHT
        ),
        "total_label": ParagraphStyle(
            "TotalLabel",
            fontSize=10,
            textColor=TEXT_GREY,
            fontName="Helvetica",
            alignment=TA_RIGHT
        ),
        "total_value": ParagraphStyle(
            "TotalValue",
            fontSize=10,
            textColor=BLACK,
            fontName="Helvetica-Bold",
            alignment=TA_RIGHT
        ),
        "grand_total_label": ParagraphStyle(
            "GrandTotalLabel",
            fontSize=13,
            textColor=WHITE,
            fontName="Helvetica-Bold",
            alignment=TA_RIGHT
        ),
        "grand_total_value": ParagraphStyle(
            "GrandTotalValue",
            fontSize=13,
            textColor=WHITE,
            fontName="Helvetica-Bold",
            alignment=TA_RIGHT
        ),
        "notes_label": ParagraphStyle(
            "NotesLabel",
            fontSize=9,
            textColor=TEXT_GREY,
            fontName="Helvetica-Bold",
            spaceAfter=4
        ),
        "notes_text": ParagraphStyle(
            "NotesText",
            fontSize=9,
            textColor=BLACK,
            fontName="Helvetica",
            leading=14
        ),
        "footer": ParagraphStyle(
            "Footer",
            fontSize=8,
            textColor=TEXT_GREY,
            fontName="Helvetica",
            alignment=TA_CENTER
        ),
        "status_paid": ParagraphStyle(
            "StatusPaid",
            fontSize=9,
            textColor=colors.HexColor("#28a745"),
            fontName="Helvetica-Bold",
            alignment=TA_RIGHT
        ),
        "status_unpaid": ParagraphStyle(
            "StatusUnpaid",
            fontSize=9,
            textColor=colors.HexColor("#dc3545"),
            fontName="Helvetica-Bold",
            alignment=TA_RIGHT
        ),
        "status_overdue": ParagraphStyle(
            "StatusOverdue",
            fontSize=9,
            textColor=colors.HexColor("#fd7e14"),
            fontName="Helvetica-Bold",
            alignment=TA_RIGHT
        ),
    }


def generate_pdf(invoice_id):
    """
    Generates a professional PDF invoice for the given invoice ID.
    Saves it to static/invoices/ and returns the filename.
    """
    invoice = database.get_invoice(invoice_id)
    items = database.get_invoice_items(invoice_id)
    items_as_dicts = [dict(item) for item in items]
    totals = database.get_invoice_totals(
        items_as_dicts,
        invoice["tax_rate"],
        invoice["discount"]
    )

    output_dir = os.path.join("static", "invoices")
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{invoice['invoice_number']}.pdf"
    filepath = os.path.join(output_dir, filename)

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=0,
        bottomMargin=15 * mm
    )

    styles = build_styles()
    story = []
    page_width = A4[0] - 30 * mm

    # ── Header Banner ───────────────────────────────────────────
    header_data = [[
        Paragraph(config.BUSINESS_NAME, styles["business_name"]),
        Paragraph("INVOICE", styles["invoice_title"])
    ]]

    header_table = Table(header_data, colWidths=[page_width * 0.6, page_width * 0.4])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PRIMARY),
        ("TOPPADDING", (0, 0), (-1, -1), 10 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8 * mm),
        ("LEFTPADDING", (0, 0), (0, -1), 8 * mm),
        ("RIGHTPADDING", (1, 0), (1, -1), 8 * mm),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(header_table)

    # ── Business Details and Invoice Meta ───────────────────────
    status_style = styles.get(f"status_{invoice['status']}", styles["status_unpaid"])
    status_text = invoice["status"].upper()

    meta_data = [[
        Paragraph(
            f"{config.BUSINESS_ADDRESS}<br/>"
            f"{config.BUSINESS_EMAIL}<br/>"
            f"{config.BUSINESS_PHONE}",
            styles["business_detail"]
        ),
        Paragraph(
            f"<b>Invoice No:</b> {invoice['invoice_number']}<br/>"
            f"<b>Issue Date:</b> {invoice['issue_date']}<br/>"
            f"<b>Due Date:</b> {invoice['due_date']}<br/>",
            styles["invoice_meta"]
        )
    ]]

    meta_table = Table(meta_data, colWidths=[page_width * 0.6, page_width * 0.4])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PRIMARY),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8 * mm),
        ("LEFTPADDING", (0, 0), (0, -1), 8 * mm),
        ("RIGHTPADDING", (1, 0), (1, -1), 8 * mm),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 6 * mm))

    # ── Bill To ─────────────────────────────────────────────────
    bill_data = [[
        Paragraph("BILL TO", styles["section_label"]),
        Paragraph("STATUS", styles["section_label"])
    ], [
        Paragraph(
            f"{invoice['client_name']}<br/>"
            f"{invoice['client_email']}<br/>"
            f"{invoice['client_address'] or ''}<br/>"
            f"{invoice['client_phone'] or ''}",
            styles["section_value"]
        ),
        Paragraph(status_text, status_style)
    ]]

    bill_table = Table(bill_data, colWidths=[page_width * 0.6, page_width * 0.4])
    bill_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
    ]))
    story.append(bill_table)
    story.append(Spacer(1, 6 * mm))
    story.append(HRFlowable(width="100%", thickness=1, color=MID_GREY))
    story.append(Spacer(1, 4 * mm))

    # ── Line Items Table ─────────────────────────────────────────
    item_rows = [[
        Paragraph("DESCRIPTION", styles["table_header"]),
        Paragraph("QTY", styles["table_header"]),
        Paragraph("UNIT PRICE", styles["table_header"]),
        Paragraph("AMOUNT", styles["table_header"])
    ]]

    for item in items:
        amount = item["quantity"] * item["unit_price"]
        item_rows.append([
            Paragraph(item["description"], styles["table_cell"]),
            Paragraph(str(item["quantity"]), styles["table_cell"]),
            Paragraph(f"${item['unit_price']:.2f}", styles["table_cell_right"]),
            Paragraph(f"${amount:.2f}", styles["table_cell_right"])
        ])

    col_widths = [
        page_width * 0.50,
        page_width * 0.10,
        page_width * 0.20,
        page_width * 0.20
    ]

    items_table = Table(item_rows, colWidths=col_widths, repeatRows=1)
    items_table.setStyle(TableStyle([
        # Header row
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("LEFTPADDING", (0, 0), (-1, 0), 8),
        ("RIGHTPADDING", (0, 0), (-1, 0), 8),
        # Data rows
        ("BACKGROUND", (0, 1), (-1, -1), WHITE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GREY]),
        ("TOPPADDING", (0, 1), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 7),
        ("LEFTPADDING", (0, 1), (-1, -1), 8),
        ("RIGHTPADDING", (0, 1), (-1, -1), 8),
        # Alignment
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        # Border
        ("LINEBELOW", (0, -1), (-1, -1), 1, MID_GREY),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 5 * mm))

    # ── Totals ───────────────────────────────────────────────────
    totals_data = [
        [
            Paragraph("Subtotal", styles["total_label"]),
            Paragraph(f"${totals['subtotal']:.2f}", styles["total_value"])
        ],
    ]

    if invoice["discount"] > 0:
        totals_data.append([
            Paragraph(f"Discount ({invoice['discount']:.0f}%)", styles["total_label"]),
            Paragraph(f"-${totals['discount_amount']:.2f}", styles["total_value"])
        ])

    if invoice["tax_rate"] > 0:
        totals_data.append([
            Paragraph(f"Tax ({invoice['tax_rate']:.0f}%)", styles["total_label"]),
            Paragraph(f"${totals['tax_amount']:.2f}", styles["total_value"])
        ])

    totals_table = Table(
        totals_data,
        colWidths=[page_width * 0.8, page_width * 0.2]
    )
    totals_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(totals_table)
    story.append(Spacer(1, 3 * mm))

    # ── Grand Total Banner ───────────────────────────────────────
    grand_total_data = [[
        Paragraph("TOTAL DUE", styles["grand_total_label"]),
        Paragraph(f"${totals['total']:.2f}", styles["grand_total_value"])
    ]]

    grand_total_table = Table(
        grand_total_data,
        colWidths=[page_width * 0.75, page_width * 0.25]
    )
    grand_total_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), ACCENT),
        ("TOPPADDING", (0, 0), (-1, -1), 5 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5 * mm),
        ("LEFTPADDING", (0, 0), (-1, -1), 8 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8 * mm),
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))
    story.append(Spacer(1, 2 * mm))
    story.append(grand_total_table)

    # ── Notes ────────────────────────────────────────────────────
    if invoice["notes"]:
        story.append(Spacer(1, 6 * mm))
        story.append(HRFlowable(width="100%", thickness=1, color=MID_GREY))
        story.append(Spacer(1, 4 * mm))
        story.append(Paragraph("NOTES", styles["notes_label"]))
        story.append(Paragraph(invoice["notes"], styles["notes_text"]))

    # ── Footer ───────────────────────────────────────────────────
    story.append(Spacer(1, 8 * mm))
    story.append(HRFlowable(width="100%", thickness=1, color=MID_GREY))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(
        f"Thank you for your business. "
        f"Please make payment by {invoice['due_date']}. "
        f"Questions? Contact us at {config.BUSINESS_EMAIL}.",
        styles["footer"]
    ))

    doc.build(story)
    return filename