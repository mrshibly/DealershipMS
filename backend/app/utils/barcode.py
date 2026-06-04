"""
Barcode utility — generates Code128 barcodes as PNG bytes.
Used by GET /products/{id}/barcode endpoint.
"""
import io

import barcode
from barcode.writer import ImageWriter
from PIL import Image


def generate_barcode_png(value: str, width_mm: int = 80, height_mm: int = 20) -> bytes:
    """
    Generate a Code128 barcode PNG.
    Returns raw PNG bytes.
    """
    code128 = barcode.get_barcode_class("code128")
    writer = ImageWriter()

    options = {
        "module_width": 0.4,
        "module_height": 12.0,
        "quiet_zone": 4.0,
        "font_size": 10,
        "text_distance": 3.0,
        "background": "white",
        "foreground": "black",
        "write_text": True,
        "dpi": 200,
    }

    buffer = io.BytesIO()
    code = code128(value, writer=writer)
    code.write(buffer, options=options)
    buffer.seek(0)
    return buffer.read()


def generate_sku(prefix: str = "PRD") -> str:
    """
    Generate a unique SKU candidate: PREFIX-XXXXXXXX (8 random uppercase hex chars).
    Uniqueness must be verified in the service layer.
    """
    import secrets
    return f"{prefix.upper()}-{secrets.token_hex(4).upper()}"
