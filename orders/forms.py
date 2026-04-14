from __future__ import annotations

from decimal import Decimal, InvalidOperation

from django import forms

from .models import Category, DeliveryZone, Product, SiteSetting, Special


ORDER_TYPE_CHOICES = [
    ('collection', 'Collection'),
    ('delivery', 'Delivery'),
]


class CheckoutForm(forms.Form):
    first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    order_type = forms.ChoiceField(choices=ORDER_TYPE_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    delivery_zone = forms.ModelChoiceField(
        queryset=DeliveryZone.objects.filter(is_active=True),
        required=False,
        empty_label='Select delivery area',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    delivery_address = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}), required=False
    )
    note = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}), required=False
    )

    def clean(self):
        cleaned_data = super().clean()
        order_type = cleaned_data.get('order_type')
        zone = cleaned_data.get('delivery_zone')
        address = cleaned_data.get('delivery_address')
        if order_type == 'delivery':
            if not zone:
                self.add_error('delivery_zone', 'Please choose a delivery area.')
            if not address:
                self.add_error('delivery_address', 'Please enter a delivery address.')
        return cleaned_data


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'category', 'name', 'slug', 'short_description', 'description', 'price',
            'image_url', 'spice_level', 'prep_time_minutes', 'is_featured', 'is_special',
            'is_available',
        ]
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'short_description': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'image_url': forms.URLInput(attrs={'class': 'form-control'}),
            'spice_level': forms.Select(attrs={'class': 'form-select'}),
            'prep_time_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_special': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class SpecialForm(forms.ModelForm):
    class Meta:
        model = Special
        fields = [
            'title', 'description', 'banner_url', 'promo_price', 'old_price',
            'start_date', 'end_date', 'is_active', 'is_featured',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'banner_url': forms.URLInput(attrs={'class': 'form-control'}),
            'promo_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'old_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CustomerMiniFormMixin(forms.Form):
    first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))


class ManualQuoteForm(CustomerMiniFormMixin):
    expiry_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    delivery_fee = forms.DecimalField(initial=0, min_value=0, decimal_places=2, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}))
    status = forms.ChoiceField(
        choices=[('draft', 'Draft'), ('sent', 'Sent'), ('approved', 'Approved'), ('expired', 'Expired')],
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='draft',
    )
    note = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}))
    items_text = forms.CharField(
        help_text='One item per line in this format: Item Name | Qty | Price',
        widget=forms.Textarea(attrs={'class': 'form-control font-monospace', 'rows': 8, 'placeholder': 'Classic Union Burger | 2 | 65\nLoaded Fries | 1 | 50'}),
    )

    def clean_items_text(self):
        return validate_item_lines(self.cleaned_data['items_text'])


class ManualInvoiceForm(CustomerMiniFormMixin):
    due_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    delivery_fee = forms.DecimalField(initial=0, min_value=0, decimal_places=2, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}))
    payment_status = forms.ChoiceField(
        choices=[('unpaid', 'Unpaid'), ('partial', 'Partial'), ('paid', 'Paid')],
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='unpaid',
    )
    note = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}))
    items_text = forms.CharField(
        help_text='One item per line in this format: Item Name | Qty | Price',
        widget=forms.Textarea(attrs={'class': 'form-control font-monospace', 'rows': 8, 'placeholder': 'Street Tacos | 3 | 60\nHomemade Lemonade | 2 | 25'}),
    )

    def clean_items_text(self):
        return validate_item_lines(self.cleaned_data['items_text'])


class OrderStatusForm(forms.Form):
    status = forms.ChoiceField(
        choices=[
            ('received', 'Received'),
            ('preparing', 'Preparing'),
            ('ready', 'Ready'),
            ('out-for-delivery', 'Out for Delivery'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
    )


class SiteSettingForm(forms.ModelForm):
    class Meta:
        model = SiteSetting
        fields = [
            'business_name', 'tagline', 'whatsapp_number', 'support_email',
            'phone_number', 'address', 'delivery_note', 'promo_text',
        ]
        widgets = {
            'business_name': forms.TextInput(attrs={'class': 'form-control'}),
            'tagline': forms.TextInput(attrs={'class': 'form-control'}),
            'whatsapp_number': forms.TextInput(attrs={'class': 'form-control'}),
            'support_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'delivery_note': forms.TextInput(attrs={'class': 'form-control'}),
            'promo_text': forms.TextInput(attrs={'class': 'form-control'}),
        }


def validate_item_lines(value: str) -> list[dict]:
    lines = [line.strip() for line in value.splitlines() if line.strip()]
    parsed: list[dict] = []
    if not lines:
        raise forms.ValidationError('Please add at least one line item.')
    for idx, line in enumerate(lines, start=1):
        parts = [part.strip() for part in line.split('|')]
        if len(parts) != 3:
            raise forms.ValidationError(
                f'Line {idx} must follow: Item Name | Qty | Price'
            )
        name, qty_raw, price_raw = parts
        try:
            qty = int(qty_raw)
            price = Decimal(price_raw)
        except (ValueError, InvalidOperation):
            raise forms.ValidationError(f'Line {idx} has an invalid quantity or price.')
        if qty < 1 or price < 0:
            raise forms.ValidationError(f'Line {idx} must have a quantity above 0 and a non-negative price.')
        parsed.append({
            'name': name,
            'quantity': qty,
            'unit_price': price,
            'line_total': price * qty,
        })
    return parsed
