from decimal import Decimal

from django.conf import settings
from django.db.utils import OperationalError, ProgrammingError

from .models import Special, SiteSetting


def site_context(request):
    cart = request.session.get('futurebite_cart', {})
    cart_count = sum(item.get('quantity', 0) for item in cart.values())
    cart_subtotal = Decimal('0.00')
    cart_preview_items = []
    for item_key, item in cart.items():
        line_total = Decimal(str(item.get('unit_price', '0'))) * int(item.get('quantity', 0))
        cart_subtotal += line_total
        cart_preview_items.append({
            'item_key': item_key,
            'product_id': item.get('product_id'),
            'name': item.get('name', ''),
            'quantity': item.get('quantity', 0),
            'unit_price': Decimal(str(item.get('unit_price', '0'))),
            'extras': item.get('extras', []),
            'line_total': line_total,
        })
    try:
        active_specials = Special.objects.filter(is_active=True)[:5]
        settings_obj = SiteSetting.objects.first()
    except (OperationalError, ProgrammingError):
        active_specials = []
        settings_obj = None
    return {
        'active_specials': active_specials,
        'business_name': getattr(settings_obj, 'business_name', None) or getattr(settings, 'BUSINESS_NAME', 'Street Union Co'),
        'whatsapp_number': getattr(settings, 'WHATSAPP_NUMBER', ''),
        'currency_symbol': getattr(settings, 'CURRENCY_SYMBOL', 'R'),
        'site_settings': settings_obj,
        'cart_count': cart_count,
        'cart_subtotal': cart_subtotal,
        'cart_preview_items': cart_preview_items,
    }
