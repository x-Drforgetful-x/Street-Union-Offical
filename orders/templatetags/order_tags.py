from decimal import Decimal
from django import template

register = template.Library()


@register.filter
def multiply(value, arg):
    return Decimal(value) * Decimal(arg)


@register.filter
def get_item(mapping, key):
    if isinstance(mapping, dict):
        return mapping.get(key)
    return None
