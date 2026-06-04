"""
PDF generation utilities.
Generates NBR-compliant invoice PDFs using ReportLab.
"""
import io
from decimal import Decimal
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


def _currency(value) -> str:
    try:
        return f"৳{Decimal(str(value)):,.2f}"
    except Exception:
        return f"৳0.00"


def generate_invoice_pdf(invoice_data: dict) -> bytes:
    """
    Generate an NBR-compliant A4 invoice PDF.
    invoice_data keys:
        invoice_no, date, dealer_name, dealer_address, dealer_phone,
        dsr_name, shop_name,
        items: [{name, total_pieces, unit_price, vat_rate, vat_amount, line_total, is_free_item}],
        subtotal, discount, vat_amount, grand_total, paid_amount, status,
        company_name, company_address, company_phone, company_vat_bin
    """
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
    )

    styles = getSampleStyleSheet()
    w, _ = A4

    PRIMARY = colors.HexColor("#2563EB")
    LIGHT_GRAY = colors.HexColor("#F3F4F6")
    DARK = colors.HexColor("#111827")
    MUTED = colors.HexColor("#6B7280")

    story = []

    # ── Header ──────────────────────────────────────────────────────────────────
    company_name = invoice_data.get("company_name", "Dealership Management System")
    company_address = invoice_data.get("company_address", "Dhaka, Bangladesh")
    company_phone = invoice_data.get("company_phone", "")
    company_vat = invoice_data.get("company_vat_bin", "")

    header_style = ParagraphStyle("CompanyName", fontSize=16, fontName="Helvetica-Bold",
                                   textColor=PRIMARY, alignment=TA_LEFT)
    sub_style = ParagraphStyle("CompanySub", fontSize=8, fontName="Helvetica",
                               textColor=MUTED, alignment=TA_LEFT, leading=12)
    inv_title_style = ParagraphStyle("InvTitle", fontSize=20, fontName="Helvetica-Bold",
                                      textColor=DARK, alignment=TA_RIGHT)
    inv_meta_style = ParagraphStyle("InvMeta", fontSize=8, fontName="Helvetica",
                                     textColor=MUTED, alignment=TA_RIGHT, leading=12)

    header_data = [
        [
            Paragraph(company_name, header_style),
            Paragraph("INVOICE", inv_title_style)
        ],
        [
            Paragraph(f"{company_address}<br/>{company_phone}<br/>VAT BIN: {company_vat}", sub_style),
            Paragraph(
                f"Invoice No: <b>{invoice_data.get('invoice_no', '')}</b><br/>"
                f"Date: <b>{invoice_data.get('date', '')}</b><br/>"
                f"Status: <b>{invoice_data.get('status', '')}</b>",
                inv_meta_style
            )
        ]
    ]
    header_table = Table(header_data, colWidths=[(w - 30*mm) * 0.55, (w - 30*mm) * 0.45])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(header_table)
    story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY, spaceAfter=6))

    # ── Bill To / DSR ────────────────────────────────────────────────────────────
    label_style = ParagraphStyle("Label", fontSize=7, fontName="Helvetica-Bold",
                                  textColor=MUTED, spaceAfter=2)
    value_style = ParagraphStyle("Value", fontSize=9, fontName="Helvetica-Bold",
                                  textColor=DARK, leading=13)
    value_normal = ParagraphStyle("ValueNorm", fontSize=8, fontName="Helvetica",
                                   textColor=DARK, leading=12)

    bill_data = [
        [
            Paragraph("BILL TO", label_style),
            Paragraph("DSR", label_style),
            Paragraph("SHOP", label_style),
        ],
        [
            Paragraph(
                f"<b>{invoice_data.get('dealer_name', '-')}</b><br/>"
                f"{invoice_data.get('dealer_address', '')}<br/>"
                f"{invoice_data.get('dealer_phone', '')}",
                value_normal
            ),
            Paragraph(invoice_data.get("dsr_name", "-"), value_style),
            Paragraph(invoice_data.get("shop_name", "-"), value_style),
        ]
    ]
    bill_table = Table(bill_data, colWidths=[(w - 30*mm) / 3] * 3)
    bill_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT_GRAY),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
    ]))
    story.append(Spacer(1, 4 * mm))
    story.append(bill_table)
    story.append(Spacer(1, 5 * mm))

    # ── Line Items ──────────────────────────────────────────────────────────────
    col_label = ParagraphStyle("ColLabel", fontSize=8, fontName="Helvetica-Bold",
                                textColor=colors.white, alignment=TA_CENTER)
    cell_style = ParagraphStyle("Cell", fontSize=8, fontName="Helvetica",
                                 textColor=DARK, alignment=TA_LEFT)
    cell_right = ParagraphStyle("CellR", fontSize=8, fontName="Helvetica",
                                 textColor=DARK, alignment=TA_RIGHT)

    item_header = [
        Paragraph("#", col_label),
        Paragraph("Product", col_label),
        Paragraph("Qty (Pcs)", col_label),
        Paragraph("Unit Price", col_label),
        Paragraph("VAT", col_label),
        Paragraph("Amount", col_label),
    ]

    col_widths = [8*mm, None, 22*mm, 28*mm, 24*mm, 30*mm]
    available_w = w - 30*mm
    fixed = sum(c for c in col_widths if c)
    col_widths[1] = available_w - fixed

    rows = [item_header]
    for i, item in enumerate(invoice_data.get("items", []), 1):
        free_tag = " [FREE]" if item.get("is_free_item") else ""
        rows.append([
            Paragraph(str(i), cell_right),
            Paragraph(f"{item.get('name', '')}{free_tag}", cell_style),
            Paragraph(str(item.get("total_pieces", 0)), cell_right),
            Paragraph(_currency(item.get("unit_price", 0)), cell_right),
            Paragraph(
                f"{_currency(item.get('vat_amount', 0))}<br/><font size=7 color=gray>({item.get('vat_rate', 0)}%)</font>",
                cell_right
            ),
            Paragraph(_currency(item.get("line_total", 0)), cell_right),
        ])

    items_table = Table(rows, colWidths=col_widths, repeatRows=1)
    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#E5E7EB")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 5 * mm))

    # ── Totals ──────────────────────────────────────────────────────────────────
    total_label = ParagraphStyle("TotLabel", fontSize=9, fontName="Helvetica",
                                  textColor=MUTED, alignment=TA_RIGHT)
    total_value = ParagraphStyle("TotVal", fontSize=9, fontName="Helvetica",
                                  textColor=DARK, alignment=TA_RIGHT)
    grand_label = ParagraphStyle("GrandL", fontSize=11, fontName="Helvetica-Bold",
                                  textColor=DARK, alignment=TA_RIGHT)
    grand_value = ParagraphStyle("GrandV", fontSize=11, fontName="Helvetica-Bold",
                                  textColor=PRIMARY, alignment=TA_RIGHT)

    outstanding = Decimal(str(invoice_data.get("grand_total", 0))) - Decimal(str(invoice_data.get("paid_amount", 0)))
    totals_rows = [
        [Paragraph("Subtotal:", total_label), Paragraph(_currency(invoice_data.get("subtotal", 0)), total_value)],
        [Paragraph("Discount:", total_label), Paragraph(f"-{_currency(invoice_data.get('discount', 0))}", total_value)],
        [Paragraph("VAT:", total_label), Paragraph(_currency(invoice_data.get("vat_amount", 0)), total_value)],
        [Paragraph("Grand Total:", grand_label), Paragraph(_currency(invoice_data.get("grand_total", 0)), grand_value)],
        [Paragraph("Paid:", total_label), Paragraph(_currency(invoice_data.get("paid_amount", 0)), total_value)],
        [Paragraph("Outstanding:", grand_label), Paragraph(_currency(outstanding), ParagraphStyle("Out", fontSize=11, fontName="Helvetica-Bold", textColor=colors.HexColor("#DC2626"), alignment=TA_RIGHT))],
    ]

    totals_col = available_w * 0.38
    totals_table = Table(totals_rows, colWidths=[totals_col * 0.55, totals_col * 0.45])
    totals_table.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LINEABOVE", (0, 3), (-1, 3), 1, PRIMARY),
        ("LINEABOVE", (0, -1), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ]))

    # Right-align the totals block
    wrapper = Table([[Paragraph(""), totals_table]], colWidths=[available_w - totals_col, totals_col])
    wrapper.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(wrapper)

    story.append(Spacer(1, 10 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E5E7EB")))
    story.append(Spacer(1, 4 * mm))

    # ── Footer ──────────────────────────────────────────────────────────────────
    footer_style = ParagraphStyle("Footer", fontSize=7, fontName="Helvetica",
                                   textColor=MUTED, alignment=TA_CENTER)
    sig_style = ParagraphStyle("Sig", fontSize=8, fontName="Helvetica",
                                textColor=DARK, alignment=TA_CENTER)

    sig_table = Table(
        [[Paragraph("_____________________", sig_style), Paragraph("_____________________", sig_style)],
         [Paragraph("Authorised Signatory", footer_style), Paragraph("Receiver Signature", footer_style)]],
        colWidths=[available_w / 2, available_w / 2]
    )
    story.append(sig_table)
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("This is a computer-generated invoice. No physical signature required.", footer_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
