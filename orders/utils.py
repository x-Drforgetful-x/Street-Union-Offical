from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from io import BytesIO
from urllib.parse import quote

from django.conf import settings

from django.http import HttpResponse


def generate_order_number(first_name: str, phone_number: str) -> str:
    first_letter = (first_name.strip()[:1] or 'X').upper()
    digits = ''.join(char for char in phone_number if char.isdigit())
    last_four = digits[-4:] if len(digits) >= 4 else digits.zfill(4)
    time_code = datetime.now().strftime('%d%m%y-%H%M')
    return f'{first_letter}{last_four}-{time_code}'


def generate_document_number(prefix: str) -> str:
    return f"{prefix}-{datetime.now().strftime('%d%m%y-%H%M%S')}"


def build_whatsapp_url(number: str, message: str) -> str:
    sanitized = ''.join(ch for ch in number if ch.isdigit())
    return f'https://wa.me/{sanitized}?text={quote(message)}'


def render_pdf_document(
    *,
    title: str,
    document_number: str,
    business_name: str,
    meta_lines: list[str],
    line_items: list[dict],
    subtotal: Decimal,
    delivery_fee: Decimal,
    total: Decimal,
    note: str = '',
    filename: str = 'document.pdf',
) -> HttpResponse:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50

    def draw_line(text: str, size: int = 11, gap: int = 18, bold: bool = False):
        nonlocal y
        pdf.setFont('Helvetica-Bold' if bold else 'Helvetica', size)
        pdf.drawString(50, y, text)
        y -= gap

    draw_line(business_name, size=20, gap=26, bold=True)
    draw_line(title, size=16, gap=22, bold=True)
    draw_line(f'Number: {document_number}')
    draw_line(f'Date: {datetime.now().strftime("%d %b %Y %H:%M")}')
    y -= 6

    for line in meta_lines:
        draw_line(line)

    y -= 10
    draw_line('Items', size=13, gap=20, bold=True)
    draw_line('Qty   Item                                      Unit Price         Total', bold=True)
    pdf.line(50, y + 6, width - 50, y + 6)
    y -= 6

    for item in line_items:
        name = str(item['name'])[:38]
        qty = str(item['quantity'])
        unit_price = f"R{Decimal(item['unit_price']):.2f}"
        line_total = f"R{Decimal(item['line_total']):.2f}"
        draw_line(f'{qty:<5}{name:<42}{unit_price:<18}{line_total}')
        if y < 120:
            pdf.showPage()
            y = height - 50

    y -= 10
    draw_line(f'Subtotal: R{Decimal(subtotal):.2f}', bold=True)
    draw_line(f'Delivery fee: R{Decimal(delivery_fee):.2f}', bold=True)
    draw_line(f'Total: R{Decimal(total):.2f}', size=13, gap=22, bold=True)

    if note:
        y -= 8
        draw_line('Note', size=13, gap=20, bold=True)
        for raw_line in str(note).splitlines():
            draw_line(raw_line[:95])

    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response


def build_payment_links(order_number: str, total: Decimal) -> dict:
    amount = f"{Decimal(total):.2f}"
    payfast_base = getattr(settings, 'PAYFAST_URL', '').strip()
    payshap_handle = getattr(settings, 'PAYSHAP_HANDLE', '').strip()
    payfast_link = ''
    if payfast_base:
        separator = '&' if '?' in payfast_base else '?'
        payfast_link = f"{payfast_base}{separator}reference={quote(order_number)}&amount={quote(amount)}"
    payshap_message = f"Street Union Co order {order_number} payment reference. Amount: R{amount}"
    payshap_link = ''
    if payshap_handle:
        payshap_link = build_whatsapp_url(payshap_handle, payshap_message)
    return {
        'payfast_link': payfast_link,
        'payshap_link': payshap_link,
        'amount': amount,
    }
