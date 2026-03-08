from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib import colors
from io import BytesIO
from datetime import datetime, timezone
from decimal import Decimal
from num2words import num2words

IGST_RATE = Decimal("0.05")

styles = getSampleStyleSheet()
title_style = styles["Heading1"]
normal = styles["Normal"]
bold = styles["Heading4"]


def format_currency(v):
    return f"{Decimal(v):,.2f}"


def number_to_words(amount):
    words = num2words(amount, lang="en_IN")
    return f"Indian Rupee {words.title()} Only"


def build_invoice_pdf(order):

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=30,
        rightMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    elements = []

    # ====================================================
    # HEADER SECTION
    # ====================================================

    company = Paragraph(
        """
        <b>XSNAPSTER</b><br/>
        H.No. 1015, Akbarpur Sarai Gagh<br/>
        Kannauj, Uttar Pradesh 209727<br/>
        India<br/>
        Email: xsnapster.store@gmail.com
        """,
        normal
    )

    invoice_date = (
        order.created_at.astimezone(timezone.utc).strftime("%d/%m/%Y")
        if order.created_at else datetime.now().strftime("%d/%m/%Y")
    )

    invoice_info = Paragraph(
        f"""
        <b>TAX INVOICE</b><br/><br/>
        Invoice Date : {invoice_date}<br/>
        Due Date : {invoice_date}<br/>
        Invoice # : {order.invoice_number}
        """,
        normal
    )

    header_table = Table(
        [[company, invoice_info]],
        colWidths=[280, 250]
    )

    header_table.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP")
    ]))

    elements.append(header_table)
    elements.append(Spacer(1, 20))

    # ====================================================
    # BILL TO
    # ====================================================

    bill_to = Paragraph(
        f"""
        <b>Bill To</b><br/>
        {order.delivery_name}<br/>
        {order.delivery_address_line}<br/>
        {order.delivery_city}, {order.delivery_state} - {order.delivery_zip_code}
        """,
        normal
    )

    elements.append(bill_to)
    elements.append(Spacer(1, 20))

    # ====================================================
    # ITEMS TABLE
    # ====================================================

    data = [
        ["#", "Item & Description", "Qty", "Rate", "IGST", "Amount"]
    ]

    subtotal = Decimal("0.00")

    for i, item in enumerate(order.items, start=1):

        qty = Decimal(item.quantity)
        rate = Decimal(str(item.price))
        amount = qty * rate

        subtotal += amount

        title = item.product.title if item.product else "Product"
        dimension = f" ({item.dimension})" if item.dimension else ""

        description = Paragraph(f"{title}{dimension}", normal)

        data.append([
            i,
            description,
            item.quantity,
            format_currency(rate),
            "5%",
            format_currency(amount)
        ])

    table = Table(
        data,
        colWidths=[30, 260, 60, 70, 60, 80]
    )

    table.setStyle(TableStyle([

        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),

        ("ALIGN", (2,1), (-1,-1), "RIGHT"),

        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),

        ("VALIGN", (0,0), (-1,-1), "MIDDLE")
    ]))

    elements.append(table)
    elements.append(Spacer(1, 20))

    # ====================================================
    # TOTALS
    # ====================================================

    igst = subtotal * IGST_RATE
    total = subtotal + igst

    totals_table = Table(
        [
            ["Sub Total", format_currency(subtotal)],
            ["IGST (5%)", format_currency(igst)],
            ["Total", format_currency(total)],
            ["Balance Due", format_currency(total)]
        ],
        colWidths=[400, 120]
    )

    totals_table.setStyle(TableStyle([

        ("ALIGN", (1,0), (1,-1), "RIGHT"),
        ("FONTNAME", (0,-2), (-1,-2), "Helvetica-Bold"),
        ("FONTNAME", (0,-1), (-1,-1), "Helvetica-Bold"),

        ("LINEABOVE", (0,-2), (-1,-2), 1, colors.black)
    ]))

    elements.append(totals_table)
    elements.append(Spacer(1, 20))

    # ====================================================
    # TOTAL IN WORDS
    # ====================================================

    elements.append(
        Paragraph(
            f"<b>Total In Words:</b> {number_to_words(total)}",
            normal
        )
    )

    elements.append(Spacer(1, 30))

    # ====================================================
    # BANK DETAILS
    # ====================================================

    bank = Paragraph(
        """
        <b>Company's Bank Details</b><br/>
        Bank Name: Central Bank of India<br/>
        A/c No: 5931529847<br/>
        IFSC Code: CBIN0283150
        """,
        normal
    )

    elements.append(bank)

    elements.append(Spacer(1, 40))

    # ====================================================
    # FOOTER
    # ====================================================

    footer = Table(
        [
            ["Notes: Thanks for your business.", "Authorized Signature"]
        ],
        colWidths=[400, 150]
    )

    footer.setStyle(TableStyle([
        ("ALIGN", (1,0), (1,0), "RIGHT")
    ]))

    elements.append(footer)

    doc.build(elements)

    buffer.seek(0)
    return buffer.read()

def generate_invoice_number(order_id: int) -> str:
    print(f"Generating invoice number for order {order_id}")
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    print(f"Generated invoice number: INV-{today}-{order_id}")
    return f"INV-{today}-{order_id}"
