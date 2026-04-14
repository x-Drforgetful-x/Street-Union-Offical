from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.db.models import Count, Sum
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    CheckoutForm,
    ManualInvoiceForm,
    ManualQuoteForm,
    OrderStatusForm,
    ProductForm,
    SiteSettingForm,
    SpecialForm,
)
from .models import (
    Category,
    Customer,
    Invoice,
    InvoiceItem,
    Order,
    OrderItem,
    Product,
    ProductExtra,
    Quote,
    QuoteItem,
    SiteSetting,
    Special,
)
from .utils import (
    build_payment_links,
    build_whatsapp_url,
    generate_document_number,
    generate_order_number,
    render_pdf_document,
)


CART_SESSION_KEY = 'futurebite_cart'


def _get_cart(request: HttpRequest) -> dict:
    return request.session.setdefault(CART_SESSION_KEY, {})


def _save_cart(request: HttpRequest, cart: dict) -> None:
    request.session[CART_SESSION_KEY] = cart
    request.session.modified = True


def _build_cart_context(request: HttpRequest) -> dict:
    cart = _get_cart(request)
    items = []
    subtotal = Decimal('0.00')
    for product_id, item in cart.items():
        line_total = Decimal(str(item['unit_price'])) * item['quantity']
        subtotal += line_total
        items.append({
            'item_key': str(product_id),
            'product_id': int(item.get('product_id', str(product_id).split(':')[0])),
            'name': item['name'],
            'quantity': item['quantity'],
            'unit_price': Decimal(str(item['unit_price'])),
            'extras': item.get('extras', []),
            'line_total': line_total,
        })
    return {
        'cart_items': items,
        'cart_count': sum(item['quantity'] for item in cart.values()),
        'cart_subtotal': subtotal,
    }


def _cart_product_quantities(request: HttpRequest) -> dict:
    quantities: dict[int, int] = {}
    for item in _get_cart(request).values():
        product_id = item.get('product_id')
        if product_id:
            quantities[product_id] = quantities.get(product_id, 0) + int(item.get('quantity', 0))
    return quantities


def _get_cart_item(cart: dict, item_key: str) -> dict:
    if item_key not in cart:
        raise Http404('Cart item not found.')
    return cart[item_key]


def _get_or_create_customer(cleaned_data: dict) -> Customer:
    customer, _ = Customer.objects.get_or_create(
        phone_number=cleaned_data['phone_number'],
        defaults={
            'first_name': cleaned_data['first_name'],
            'last_name': cleaned_data.get('last_name', ''),
            'email': cleaned_data.get('email', ''),
        },
    )
    customer.first_name = cleaned_data['first_name']
    customer.last_name = cleaned_data.get('last_name', '')
    customer.email = cleaned_data.get('email', '')
    customer.save()
    return customer


def _status_message(order: Order) -> str:
    pieces = [
        f'Hi {order.customer.first_name},',
        f'Your Street Union Co order {order.order_number} is now {order.get_status_display().lower()}.',
    ]
    if order.status == 'ready':
        pieces.append('Your order is ready for collection or dispatch.')
    elif order.status == 'out-for-delivery':
        pieces.append('Our driver is on the way.')
    elif order.status == 'completed':
        pieces.append('Thank you for ordering with Street Union Co.')
    return ' '.join(pieces)


def home(request: HttpRequest) -> HttpResponse:
    featured_products = Product.objects.filter(is_featured=True, is_available=True)[:8]
    featured_specials = Special.objects.filter(is_active=True, is_featured=True)[:3]
    categories = Category.objects.filter(is_active=True)
    return render(request, 'orders/home.html', {
        'featured_products': featured_products,
        'featured_specials': featured_specials,
        'categories': categories,
        'cart_product_quantities': _cart_product_quantities(request),
    })


def menu(request: HttpRequest) -> HttpResponse:
    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '').strip()
    products = Product.objects.filter(is_available=True).select_related('category')
    categories = Category.objects.filter(is_active=True)
    if query:
        products = products.filter(name__icontains=query)
    if category_slug:
        products = products.filter(category__slug=category_slug)
    return render(request, 'orders/menu.html', {
        'products': products,
        'categories': categories,
        'selected_category': category_slug,
        'search_query': query,
        'cart_product_quantities': _cart_product_quantities(request),
    })


def product_detail(request: HttpRequest, slug: str) -> HttpResponse:
    product = get_object_or_404(Product.objects.prefetch_related('extras'), slug=slug, is_available=True)
    cart_quantities = _cart_product_quantities(request)
    return render(request, 'orders/product_detail.html', {
        'product': product,
        'cart_product_quantities': cart_quantities,
        'product_quantity_in_cart': cart_quantities.get(product.id, 0),
    })


def specials(request: HttpRequest) -> HttpResponse:
    specials_qs = Special.objects.filter(is_active=True)
    return render(request, 'orders/specials.html', {'specials': specials_qs})


def add_to_cart(request: HttpRequest, product_id: int) -> HttpResponse:
    product = get_object_or_404(Product, id=product_id, is_available=True)
    cart = _get_cart(request)
    key = str(product.id)
    selected_extra_ids = request.POST.getlist('extras') if request.method == 'POST' else request.GET.getlist('extras')
    selected_extras = list(ProductExtra.objects.filter(id__in=selected_extra_ids, product=product))
    unit_price = Decimal(product.price)
    extras_names = []
    quantity = max(1, int(request.POST.get('quantity', request.GET.get('quantity', 1))))
    for extra in selected_extras:
        unit_price += Decimal(extra.price)
        extras_names.append(f'{extra.name} (+{settings.CURRENCY_SYMBOL}{extra.price})')

    if key in cart and not extras_names:
        cart[key]['quantity'] += quantity
    else:
        item_key = key
        if extras_names:
            item_key = f"{key}:{'-'.join(str(extra.id) for extra in selected_extras)}"
        if item_key in cart:
            cart[item_key]['quantity'] += quantity
        else:
            cart[item_key] = {
                'product_id': product.id,
                'name': product.name,
                'quantity': quantity,
                'unit_price': str(unit_price),
                'extras': extras_names,
            }
    _save_cart(request, cart)
    messages.success(request, f'{product.name} added to cart.')
    next_url = request.POST.get('next') or request.GET.get('next') or request.META.get('HTTP_REFERER') or 'orders:menu'
    return redirect(next_url)


def set_cart_quantity(request: HttpRequest, item_key: str) -> HttpResponse:
    cart = _get_cart(request)
    item = _get_cart_item(cart, item_key)
    quantity = max(0, int(request.POST.get('quantity', 1)))
    if quantity == 0:
        cart.pop(item_key, None)
        messages.info(request, f"{item['name']} removed from cart.")
    else:
        item['quantity'] = quantity
        messages.success(request, f"{item['name']} quantity updated.")
    _save_cart(request, cart)
    return redirect(request.POST.get('next') or 'orders:cart')


def change_cart_quantity(request: HttpRequest, item_key: str, action: str) -> HttpResponse:
    cart = _get_cart(request)
    item = _get_cart_item(cart, item_key)
    current_qty = int(item.get('quantity', 1))
    if action == 'increase':
        item['quantity'] = current_qty + 1
    elif action == 'decrease':
        if current_qty <= 1:
            cart.pop(item_key, None)
            messages.info(request, f"{item['name']} removed from cart.")
        else:
            item['quantity'] = current_qty - 1
    else:
        raise Http404('Unknown cart action.')
    _save_cart(request, cart)
    return redirect(request.POST.get('next') or request.META.get('HTTP_REFERER') or 'orders:cart')


def remove_from_cart(request: HttpRequest, item_key: str) -> HttpResponse:
    cart = _get_cart(request)
    item = cart.pop(item_key, None)
    _save_cart(request, cart)
    if item:
        messages.info(request, f"{item['name']} removed from cart.")
    return redirect(request.POST.get('next') or 'orders:cart')


def cart_view(request: HttpRequest) -> HttpResponse:
    context = _build_cart_context(request)
    return render(request, 'orders/cart.html', context)


def checkout(request: HttpRequest) -> HttpResponse:
    cart_context = _build_cart_context(request)
    if not cart_context['cart_items']:
        messages.warning(request, 'Your cart is empty.')
        return redirect('orders:menu')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            customer = _get_or_create_customer(form.cleaned_data)
            delivery_zone = form.cleaned_data.get('delivery_zone')
            delivery_fee = Decimal(delivery_zone.fee) if delivery_zone else Decimal('0.00')
            subtotal = cart_context['cart_subtotal']
            total = subtotal + delivery_fee
            order_number = generate_order_number(
                form.cleaned_data['first_name'],
                form.cleaned_data['phone_number']
            )
            order = Order.objects.create(
                customer=customer,
                order_number=order_number,
                order_type=form.cleaned_data['order_type'],
                delivery_zone=delivery_zone,
                delivery_address=form.cleaned_data['delivery_address'],
                note=form.cleaned_data['note'],
                subtotal=subtotal,
                delivery_fee=delivery_fee,
                total=total,
            )
            lines = [
                'Hello, I would like to place an order.',
                '',
                f'Order Number: {order.order_number}',
                f'Customer Name: {customer.first_name} {customer.last_name}'.strip(),
                f'Phone Number: {customer.phone_number}',
                f'Order Type: {order.get_order_type_display()}',
                '',
                'Items Ordered:',
            ]
            for item in cart_context['cart_items']:
                extras = f" | Extras: {', '.join(item['extras'])}" if item['extras'] else ''
                OrderItem.objects.create(
                    order=order,
                    product_id=item['product_id'],
                    product_name=item['name'],
                    quantity=item['quantity'],
                    unit_price=item['unit_price'],
                    extras_summary=', '.join(item['extras']),
                    line_total=item['line_total'],
                )
                lines.append(
                    f"{item['quantity']} x {item['name']} - {settings.CURRENCY_SYMBOL}{item['line_total']}{extras}"
                )

            if order.delivery_address:
                lines.extend(['', 'Delivery Address:', order.delivery_address])
            lines.extend([
                '',
                f'Subtotal: {settings.CURRENCY_SYMBOL}{subtotal}',
                f'Delivery Fee: {settings.CURRENCY_SYMBOL}{delivery_fee}',
                f'Total: {settings.CURRENCY_SYMBOL}{total}',
            ])
            if order.note:
                lines.extend(['', f'Order Notes: {order.note}'])

            whatsapp_url = build_whatsapp_url(settings.WHATSAPP_NUMBER, '\n'.join(lines))
            request.session[CART_SESSION_KEY] = {}
            request.session['last_whatsapp_url'] = whatsapp_url
            request.session['last_order_number'] = order.order_number
            return redirect('orders:order_success', order_number=order.order_number)
    else:
        form = CheckoutForm()

    return render(request, 'orders/checkout.html', {
        'form': form,
        **cart_context,
    })


def order_success(request: HttpRequest, order_number: str) -> HttpResponse:
    order = get_object_or_404(Order.objects.select_related('customer'), order_number=order_number)
    whatsapp_url = request.session.get('last_whatsapp_url', '')
    payment_links = build_payment_links(order.order_number, order.total)
    return render(request, 'orders/order_success.html', {
        'order': order,
        'whatsapp_url': whatsapp_url,
        'payment_links': payment_links,
    })


def payment_options(request: HttpRequest, order_number: str) -> HttpResponse:
    order = get_object_or_404(Order.objects.select_related('customer'), order_number=order_number)
    payment_links = build_payment_links(order.order_number, order.total)
    return render(request, 'orders/payment_options.html', {
        'order': order,
        'payment_links': payment_links,
    })


def track_order(request: HttpRequest) -> HttpResponse:
    order = None
    search = request.GET.get('order_number', '').strip()
    if search:
        order = Order.objects.filter(order_number=search).select_related('customer').first()
    return render(request, 'orders/track_order.html', {'order': order, 'search': search})


def about(request: HttpRequest) -> HttpResponse:
    return render(request, 'orders/about.html')


def contact(request: HttpRequest) -> HttpResponse:
    return render(request, 'orders/contact.html')


def dashboard_home(request: HttpRequest) -> HttpResponse:
    stats = {
        'orders_count': Order.objects.count(),
        'products_count': Product.objects.count(),
        'quotes_count': Quote.objects.count(),
        'invoices_count': Invoice.objects.count(),
        'sales_total': Order.objects.aggregate(total=Sum('total'))['total'] or Decimal('0.00'),
        'featured_count': Product.objects.filter(is_featured=True).count(),
    }
    recent_orders = Order.objects.select_related('customer')[:5]
    top_categories = Category.objects.annotate(item_count=Count('products')).order_by('-item_count')[:5]
    status_form = OrderStatusForm()
    return render(request, 'orders/dashboard/home.html', {
        'stats': stats,
        'recent_orders': recent_orders,
        'top_categories': top_categories,
        'status_form': status_form,
    })


def dashboard_orders(request: HttpRequest) -> HttpResponse:
    orders = Order.objects.select_related('customer', 'delivery_zone').prefetch_related('items')
    return render(request, 'orders/dashboard/orders.html', {
        'orders': orders,
        'status_form': OrderStatusForm(),
    })


def dashboard_orders_feed(request: HttpRequest) -> JsonResponse:
    orders = Order.objects.select_related('customer').prefetch_related('items')[:25]
    payload = {
        'timestamp': timezone.now().isoformat(),
        'orders': [
            {
                'id': order.id,
                'order_number': order.order_number,
                'customer_name': str(order.customer),
                'phone_number': order.customer.phone_number,
                'order_type': order.get_order_type_display(),
                'status': order.status,
                'status_label': order.get_status_display(),
                'total': f'{order.total:.2f}',
                'created_at': timezone.localtime(order.created_at).strftime('%d %b %Y %H:%M'),
                'items': [
                    {
                        'name': item.product_name,
                        'quantity': item.quantity,
                        'extras': item.extras_summary,
                    }
                    for item in order.items.all()
                ],
            }
            for order in orders
        ],
    }
    return JsonResponse(payload)


def kitchen_screen(request: HttpRequest) -> HttpResponse:
    orders = Order.objects.select_related('customer').prefetch_related('items').exclude(status__in=['completed', 'cancelled'])
    return render(request, 'orders/dashboard/kitchen.html', {
        'orders': orders,
        'status_form': OrderStatusForm(),
    })


def update_order_status(request: HttpRequest, order_id: int) -> HttpResponse:
    order = get_object_or_404(Order.objects.select_related('customer'), id=order_id)
    if request.method != 'POST':
        return redirect('orders:dashboard_orders')

    form = OrderStatusForm(request.POST)
    if form.is_valid():
        order.status = form.cleaned_data['status']
        order.save(update_fields=['status', 'updated_at'])
        messages.success(request, f'Order {order.order_number} updated to {order.get_status_display()}.')
    else:
        messages.error(request, 'Could not update the order status.')

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or 'orders:dashboard_orders'
    return redirect(next_url)


def send_order_whatsapp_reply(request: HttpRequest, order_id: int, reply_type: str) -> HttpResponse:
    order = get_object_or_404(Order.objects.select_related('customer'), id=order_id)
    if reply_type == 'confirm':
        message = (
            f'Hi {order.customer.first_name}, your Street Union Co order {order.order_number} '
            f'has been received. Total: {settings.CURRENCY_SYMBOL}{order.total}. '
            'We will keep you updated.'
        )
    elif reply_type == 'status':
        message = _status_message(order)
    else:
        raise Http404('Unknown WhatsApp reply type.')
    whatsapp_url = build_whatsapp_url(order.customer.phone_number, message)
    return redirect(whatsapp_url)


def dashboard_products(request: HttpRequest) -> HttpResponse:
    return render(request, 'orders/dashboard/products.html', {'products': Product.objects.select_related('category')})


def product_create(request: HttpRequest) -> HttpResponse:
    form = ProductForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Product created successfully.')
        return redirect('orders:dashboard_products')
    return render(request, 'orders/dashboard/product_form.html', {
        'form': form,
        'page_title': 'Create product',
        'submit_label': 'Create product',
    })


def product_edit(request: HttpRequest, product_id: int) -> HttpResponse:
    product = get_object_or_404(Product, id=product_id)
    form = ProductForm(request.POST or None, instance=product)
    if form.is_valid():
        form.save()
        messages.success(request, 'Product updated successfully.')
        return redirect('orders:dashboard_products')
    return render(request, 'orders/dashboard/product_form.html', {
        'form': form,
        'product': product,
        'page_title': f'Edit {product.name}',
        'submit_label': 'Save changes',
    })


def dashboard_quotes(request: HttpRequest) -> HttpResponse:
    return render(request, 'orders/dashboard/quotes.html', {'quotes': Quote.objects.select_related('customer')})


def quote_create(request: HttpRequest) -> HttpResponse:
    form = ManualQuoteForm(request.POST or None)
    if form.is_valid():
        customer = _get_or_create_customer(form.cleaned_data)
        items = form.cleaned_data['items_text']
        subtotal = sum((item['line_total'] for item in items), Decimal('0.00'))
        delivery_fee = form.cleaned_data['delivery_fee']
        quote = Quote.objects.create(
            customer=customer,
            quote_number=generate_document_number('QUO'),
            expiry_date=form.cleaned_data['expiry_date'],
            note=form.cleaned_data['note'],
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            total=subtotal + delivery_fee,
            status=form.cleaned_data['status'],
        )
        for item in items:
            QuoteItem.objects.create(
                quote=quote,
                item_name=item['name'],
                quantity=item['quantity'],
                unit_price=item['unit_price'],
                line_total=item['line_total'],
            )
        messages.success(request, f'Quote {quote.quote_number} created successfully.')
        return redirect('orders:dashboard_quotes')
    return render(request, 'orders/dashboard/quote_form.html', {
        'form': form,
        'page_title': 'Create manual quote',
        'submit_label': 'Create quote',
    })


def dashboard_invoices(request: HttpRequest) -> HttpResponse:
    return render(request, 'orders/dashboard/invoices.html', {'invoices': Invoice.objects.select_related('customer')})


def invoice_create(request: HttpRequest) -> HttpResponse:
    form = ManualInvoiceForm(request.POST or None)
    if form.is_valid():
        customer = _get_or_create_customer(form.cleaned_data)
        items = form.cleaned_data['items_text']
        subtotal = sum((item['line_total'] for item in items), Decimal('0.00'))
        delivery_fee = form.cleaned_data['delivery_fee']
        invoice = Invoice.objects.create(
            customer=customer,
            invoice_number=generate_document_number('INV'),
            due_date=form.cleaned_data['due_date'],
            note=form.cleaned_data['note'],
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            total=subtotal + delivery_fee,
            payment_status=form.cleaned_data['payment_status'],
        )
        for item in items:
            InvoiceItem.objects.create(
                invoice=invoice,
                item_name=item['name'],
                quantity=item['quantity'],
                unit_price=item['unit_price'],
                line_total=item['line_total'],
            )
        messages.success(request, f'Invoice {invoice.invoice_number} created successfully.')
        return redirect('orders:dashboard_invoices')
    return render(request, 'orders/dashboard/invoice_form.html', {
        'form': form,
        'page_title': 'Create manual invoice',
        'submit_label': 'Create invoice',
    })


def dashboard_specials(request: HttpRequest) -> HttpResponse:
    return render(request, 'orders/dashboard/specials.html', {'specials': Special.objects.all()})


def special_create(request: HttpRequest) -> HttpResponse:
    form = SpecialForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Special created successfully.')
        return redirect('orders:dashboard_specials')
    return render(request, 'orders/dashboard/special_form.html', {
        'form': form,
        'page_title': 'Create special',
        'submit_label': 'Create special',
    })


def special_edit(request: HttpRequest, special_id: int) -> HttpResponse:
    special = get_object_or_404(Special, id=special_id)
    form = SpecialForm(request.POST or None, instance=special)
    if form.is_valid():
        form.save()
        messages.success(request, 'Special updated successfully.')
        return redirect('orders:dashboard_specials')
    return render(request, 'orders/dashboard/special_form.html', {
        'form': form,
        'special': special,
        'page_title': f'Edit {special.title}',
        'submit_label': 'Save changes',
    })


def dashboard_settings(request: HttpRequest) -> HttpResponse:
    site_settings = SiteSetting.objects.first() or SiteSetting.objects.create(business_name=settings.BUSINESS_NAME)
    form = SiteSettingForm(request.POST or None, instance=site_settings)
    if form.is_valid():
        form.save()
        messages.success(request, 'Brand and contact settings updated.')
        return redirect('orders:dashboard_settings')
    return render(request, 'orders/dashboard/settings.html', {'form': form})


def invoice_pdf(request: HttpRequest, invoice_id: int) -> HttpResponse:
    invoice = get_object_or_404(Invoice.objects.select_related('customer', 'order', 'quote').prefetch_related('items'), id=invoice_id)
    meta_lines = [
        f'Customer: {invoice.customer}',
        f'Payment status: {invoice.get_payment_status_display()}',
        f'Due date: {invoice.due_date or "-"}',
    ]
    if invoice.order:
        meta_lines.append(f'Order ref: {invoice.order.order_number}')
    if invoice.quote:
        meta_lines.append(f'Quote ref: {invoice.quote.quote_number}')
    line_items = [
        {
            'name': item.item_name,
            'quantity': item.quantity,
            'unit_price': item.unit_price,
            'line_total': item.line_total,
        }
        for item in invoice.items.all()
    ]
    site_settings = SiteSetting.objects.first()
    return render_pdf_document(
        title='INVOICE',
        document_number=invoice.invoice_number,
        business_name=(site_settings.business_name if site_settings else settings.BUSINESS_NAME),
        meta_lines=meta_lines,
        line_items=line_items,
        subtotal=invoice.subtotal,
        delivery_fee=invoice.delivery_fee,
        total=invoice.total,
        note=invoice.note,
        filename=f'invoice-{invoice.invoice_number}.pdf',
    )


def quote_pdf(request: HttpRequest, quote_id: int) -> HttpResponse:
    quote = get_object_or_404(Quote.objects.select_related('customer').prefetch_related('items'), id=quote_id)
    meta_lines = [
        f'Customer: {quote.customer}',
        f'Status: {quote.get_status_display()}',
        f'Expiry date: {quote.expiry_date or "-"}',
    ]
    line_items = [
        {
            'name': item.item_name,
            'quantity': item.quantity,
            'unit_price': item.unit_price,
            'line_total': item.line_total,
        }
        for item in quote.items.all()
    ]
    site_settings = SiteSetting.objects.first()
    return render_pdf_document(
        title='QUOTE',
        document_number=quote.quote_number,
        business_name=(site_settings.business_name if site_settings else settings.BUSINESS_NAME),
        meta_lines=meta_lines,
        line_items=line_items,
        subtotal=quote.subtotal,
        delivery_fee=quote.delivery_fee,
        total=quote.total,
        note=quote.note,
        filename=f'quote-{quote.quote_number}.pdf',
    )


def create_quote_from_order(request: HttpRequest, order_id: int) -> HttpResponse:
    order = get_object_or_404(Order.objects.select_related('customer').prefetch_related('items'), id=order_id)
    today = timezone.now().date()
    quote = Quote.objects.create(
        customer=order.customer,
        quote_number=generate_document_number('QUO'),
        expiry_date=today + timedelta(days=7),
        note=f'Created from order {order.order_number}.',
        subtotal=order.subtotal,
        delivery_fee=order.delivery_fee,
        total=order.total,
        status='sent',
    )
    for item in order.items.all():
        QuoteItem.objects.create(
            quote=quote,
            item_name=item.product_name,
            quantity=item.quantity,
            unit_price=item.unit_price,
            line_total=item.line_total,
        )
    messages.success(request, f'Quote {quote.quote_number} created from order {order.order_number}.')
    return redirect('orders:dashboard_quotes')


def create_invoice_from_order(request: HttpRequest, order_id: int) -> HttpResponse:
    order = get_object_or_404(Order.objects.select_related('customer').prefetch_related('items'), id=order_id)
    invoice = Invoice.objects.create(
        customer=order.customer,
        order=order,
        invoice_number=generate_document_number('INV'),
        due_date=timezone.now().date(),
        note=f'Created from order {order.order_number}.',
        subtotal=order.subtotal,
        delivery_fee=order.delivery_fee,
        total=order.total,
        payment_status='unpaid',
    )
    for item in order.items.all():
        InvoiceItem.objects.create(
            invoice=invoice,
            item_name=item.product_name,
            quantity=item.quantity,
            unit_price=item.unit_price,
            line_total=item.line_total,
        )
    messages.success(request, f'Invoice {invoice.invoice_number} created from order {order.order_number}.')
    return redirect('orders:dashboard_invoices')
