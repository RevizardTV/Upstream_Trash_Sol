import io
from typing import Any, Dict, Union
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_receipt_pdf(data: Union[Dict[str, Any], Any]) -> bytes:
    """
    Generates a PDF receipt dynamically handling both dictionary payloads 
    and SQLAlchemy model instance objects safely.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter, 
        rightMargin=36, 
        leftMargin=36, 
        topMargin=36, 
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        textColor=colors.HexColor("#065F46"),
        spaceAfter=12
    )
    
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor("#1F2937"),
        leading=14
    )

    # Safely resolve attributes regardless of Dict or ORM Model input
    def get_val(key: str, default: Any = "N/A") -> Any:
        if isinstance(data, dict):
            val = data.get(key, default)
        else:
            val = getattr(data, key, default)
        return val if val is not None else default

    entry_id = get_val("entry_id", "0000")
    user_name = get_val("user_name", get_val("full_name", "Valued Customer"))
    user_email = get_val("user_email", get_val("email", "N/A"))
    waste_category = str(get_val("waste_category", "General Waste")).capitalize()
    
    # Safe numerical formatting for Decimal/Float/Int
    try:
        weight_kg = f"{float(get_val('weight_kg', 0.0)):.2f} kg"
    except (ValueError, TypeError):
        weight_kg = "0.00 kg"

    try:
        # Use standard ASCII 'Rs. ' to prevent Helvetica font glyph box rendering issues
        payout_amount = f"Rs. {float(get_val('payout_amount', 0.0)):.2f}"
    except (ValueError, TypeError):
        payout_amount = "Rs. 0.00"

    status = str(get_val("status", "Pending")).capitalize()
    station_id = get_val("station_id", "BIN-LOCAL-01")
    
    created_at_val = get_val("created_at", None)
    if hasattr(created_at_val, "strftime"):
        created_at = created_at_val.strftime("%Y-%m-%d %H:%M:%S")
    else:
        created_at = str(created_at_val) if created_at_val else "N/A"

    elements = []

    # Title & Header
    elements.append(Paragraph("EcoRecycle - Official Transaction Receipt", title_style))
    elements.append(Paragraph(f"<b>Receipt ID:</b> REC-{entry_id} | <b>Date:</b> {created_at}", body_style))
    elements.append(Spacer(1, 15))

    # User Details
    elements.append(Paragraph(f"<b>Customer Name:</b> {user_name}", body_style))
    elements.append(Paragraph(f"<b>Email Address:</b> {user_email}", body_style))
    elements.append(Paragraph(f"<b>Processing Station:</b> {station_id}", body_style))
    elements.append(Spacer(1, 15))

    # Transaction Table
    table_data = [
        [Paragraph("<b>Item Description</b>", body_style), Paragraph("<b>Details</b>", body_style)],
        ["Waste Category", waste_category],
        ["Measured Weight", weight_kg],
        ["Payout Status", status],
        ["Total Earnings", payout_amount]
    ]

    t = Table(table_data, colWidths=[200, 300])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#D1FAE5")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#065F46")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor("#047857")),
    ]))
    elements.append(t)
    
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Thank you for contributing to a cleaner environment!", body_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()