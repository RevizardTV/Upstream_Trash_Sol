import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_receipt_pdf(entry_data: dict) -> bytes:
    """
    Generates a PDF receipt buffer for a given recycling entry.
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
    
    # Custom Palette
    PRIMARY_COLOR = colors.HexColor("#059669")  # Emerald Green
    DARK_BG = colors.HexColor("#0f172a")        # Slate 900
    TEXT_MUTED = colors.HexColor("#64748b")     # Slate 500

    # Custom Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Title'],
        fontName='Helvetica-Bold',
        fontSize=22,
        textColor=PRIMARY_COLOR,
        alignment=0,
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=TEXT_MUTED,
        spaceAfter=15
    )

    label_style = ParagraphStyle(
        'Label',
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=TEXT_MUTED
    )

    value_style = ParagraphStyle(
        'Value',
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.black
    )

    story = []

    # Header Section
    story.append(Paragraph("EcoRecycle Payment Receipt", title_style))
    story.append(Paragraph("Official Material Verification & Payout Statement", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY_COLOR, spaceAfter=20))

    # Key Metadata Grid
    entry_id = entry_data.get("entry_id", "N/A")
    status = str(entry_data.get("status", "N/A")).upper()
    created_at = str(entry_data.get("created_at", "N/A"))
    user_name = entry_data.get("user_name", "Registered User")

    meta_table_data = [
        [
            Paragraph("Transaction Reference:", label_style),
            Paragraph(f"#{entry_id}", value_style),
            Paragraph("Verification Status:", label_style),
            Paragraph(status, value_style)
        ],
        [
            Paragraph("Issued To:", label_style),
            Paragraph(user_name, value_style),
            Paragraph("Transaction Date:", label_style),
            Paragraph(created_at, value_style)
        ]
    ]

    meta_table = Table(meta_table_data, colWidths=[120, 150, 120, 150])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 20))

    # Recycling Breakdown Table
    category = str(entry_data.get("waste_category", "N/A")).capitalize()
    weight = f"{float(entry_data.get('weight_kg', 0)):.2f} kg"
    payout = f"₹{float(entry_data.get('payout_amount', 0)):.2f}"
    station = entry_data.get("station_id") or "BIN-DEFAULT-01"

    breakdown_data = [
        [Paragraph("<b>Item Description / Category</b>", label_style), 
         Paragraph("<b>Station ID</b>", label_style), 
         Paragraph("<b>Measured Weight</b>", label_style), 
         Paragraph("<b>Payout Amount</b>", label_style)],
        [Paragraph(category, value_style), 
         Paragraph(station, value_style), 
         Paragraph(weight, value_style), 
         Paragraph(payout, value_style)]
    ]

    breakdown_table = Table(breakdown_data, colWidths=[180, 120, 120, 120])
    breakdown_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
    ]))
    story.append(breakdown_table)
    story.append(Spacer(1, 30))

    # Total Summary Box
    summary_data = [
        [Paragraph("<b>Total Approved Settlement:</b>", label_style), Paragraph(f"<b>{payout}</b>", title_style)]
    ]
    summary_table = Table(summary_data, colWidths=[200, 340])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(summary_table)

    # Footer Disclaimer
    story.append(Spacer(1, 40))
    story.append(HRFlowable(width="100%", thickness=0.5, color=TEXT_MUTED, spaceAfter=10))
    disclaimer = (
        "This is an electronically generated receipt issued under the EcoRecycle Pay-As-You-Throw (PAYT) "
        "initiative. Disbursement is processed directly to your registered UPI ID or IMPS bank account. "
        "For compliance or audit support, please contact support@ecorecycle.org."
    )
    story.append(Paragraph(disclaimer, subtitle_style))

    # Build PDF
    doc.build(story)
    pdf_value = buffer.getvalue()
    buffer.close()
    return pdf_value