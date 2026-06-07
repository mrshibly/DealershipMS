"""
Barcode print sheet generator.
Generates a multi-barcode A4 PDF sheet (3 columns × N rows).
"""
import io
from typing import List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.enums import TA_CENTER

import barcode as barcodelib
from barcode.writer import ImageWriter
from PIL import Image
from reportlab.lib.utils import ImageReader


def _generate_barcode_image(value: str) -> ImageReader:
    """Generate barcode and return as ReportLab ImageReader."""
    code128 = barcodelib.get_barcode_class("code128")
    writer = ImageWriter()
    options = {
        "module_width": 0.35,
        "module_height": 10.0,
        "quiet_zone": 3.0,
        "font_size": 8,
        "text_distance": 2.5,
        "background": "white",
        "foreground": "black",
        "write_text": True,
        "dpi": 150,
    }
    buf = io.BytesIO()
    code128(value, writer=writer).write(buf, options=options)
    buf.seek(0)
    img = Image.open(buf)
    out = io.BytesIO()
    img.save(out, format="PNG")
    out.seek(0)
    return ImageReader(out)


def generate_barcode_sheet_pdf(
    products: List[dict],
    copies: int = 1,
) -> bytes:
    """
    Generate an A4 PDF sheet of barcodes.
    products: list of {"name": str, "sku": str, "barcode": str, "price": str}
    copies: number of copies per product (default 1)
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
        leftMargin=10 * mm,
        rightMargin=10 * mm,
    )

    COLS = 3
    CELL_W = (A4[0] - 20 * mm) / COLS
    CELL_H = 38 * mm

    label_style = ParagraphStyle(
        "Label", fontSize=7, fontName="Helvetica-Bold", alignment=TA_CENTER, leading=9
    )
    sku_style = ParagraphStyle(
        "SKU", fontSize=6, fontName="Helvetica", alignment=TA_CENTER, textColor=colors.HexColor("#6B7280")
    )

    # Expand by copies
    items = []
    for p in products:
        for _ in range(copies):
            items.append(p)

    # Build grid rows
    rows = []
    row = []
    for item in items:
        bc_val = item.get("barcode") or item.get("sku", "000000")
        try:
            bc_img = _generate_barcode_image(bc_val)
            from reportlab.platypus import Image as RLImage
            import tempfile, os
            # Write to temp buffer for RL Image
            tmp_buf = io.BytesIO()
            bc_class = barcodelib.get_barcode_class("code128")
            bc_class(bc_val, writer=ImageWriter()).write(
                tmp_buf,
                options={"module_width": 0.35, "module_height": 10.0, "quiet_zone": 3.0,
                         "font_size": 8, "text_distance": 2.5, "dpi": 150, "write_text": True}
            )
            tmp_buf.seek(0)
            rl_img = RLImage(tmp_buf, width=CELL_W - 6*mm, height=20*mm)
        except Exception:
            rl_img = Paragraph("(barcode error)", sku_style)

        price_str = f"Tk. {item.get('price', '0.00')}" if item.get("price") else ""
        cell_content = Table(
            [
                [Paragraph(item.get("name", ""), label_style)],
                [rl_img],
                [Paragraph(f"{item.get('sku', '')}  {price_str}", sku_style)],
            ],
            colWidths=[CELL_W - 4*mm],
        )
        cell_content.setStyle(TableStyle([
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ]))

        row.append(cell_content)
        if len(row) == COLS:
            rows.append(row)
            row = []

    if row:
        while len(row) < COLS:
            row.append("")
        rows.append(row)

    if not rows:
        from reportlab.platypus import Paragraph as P
        rows = [[P("No products selected", label_style), "", ""]]

    grid = Table(rows, colWidths=[CELL_W] * COLS, rowHeights=[CELL_H] * len(rows))
    grid.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))

    doc.build([grid])
    buffer.seek(0)
    return buffer.read()
