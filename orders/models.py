from django.db import models
from django.utils.text import slugify


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Category(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name_plural = 'Categories'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(TimeStampedModel):
    SPICE_CHOICES = [
        ('mild', 'Mild'),
        ('medium', 'Medium'),
        ('hot', 'Hot'),
        ('extra-hot', 'Extra Hot'),
    ]

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=160, unique=True, blank=True)
    short_description = models.CharField(max_length=220, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image_url = models.URLField(blank=True)
    spice_level = models.CharField(max_length=20, choices=SPICE_CHOICES, default='mild')
    prep_time_minutes = models.PositiveIntegerField(default=15)
    is_featured = models.BooleanField(default=False)
    is_special = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProductExtra(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='extras')
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        unique_together = ('product', 'name')
        ordering = ['name']

    def __str__(self):
        return f'{self.product.name} - {self.name}'


class Special(TimeStampedModel):
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    banner_url = models.URLField(blank=True)
    promo_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    old_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    class Meta:
        ordering = ['-is_featured', '-created_at']

    def __str__(self):
        return self.title


class Customer(TimeStampedModel):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True)

    class Meta:
        ordering = ['first_name', 'last_name']

    def __str__(self):
        return f'{self.first_name} {self.last_name}'.strip()


class DeliveryZone(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    minimum_order = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Order(TimeStampedModel):
    STATUS_CHOICES = [
        ('received', 'Received'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
        ('out-for-delivery', 'Out for Delivery'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    TYPE_CHOICES = [('collection', 'Collection'), ('delivery', 'Delivery')]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=40, unique=True)
    order_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='collection')
    delivery_zone = models.ForeignKey(
        DeliveryZone, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders'
    )
    delivery_address = models.TextField(blank=True)
    note = models.TextField(blank=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='received')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.order_number


class OrderItem(TimeStampedModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=150)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    extras_summary = models.TextField(blank=True)
    line_total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'{self.quantity} x {self.product_name}'


class Quote(TimeStampedModel):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('approved', 'Approved'),
        ('expired', 'Expired'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='quotes')
    quote_number = models.CharField(max_length=40, unique=True)
    expiry_date = models.DateField(null=True, blank=True)
    note = models.TextField(blank=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.quote_number


class QuoteItem(TimeStampedModel):
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name='items')
    item_name = models.CharField(max_length=150)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'{self.quantity} x {self.item_name}'


class Invoice(TimeStampedModel):
    PAYMENT_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('partial', 'Partial'),
        ('paid', 'Paid'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='invoices')
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True)
    quote = models.ForeignKey(Quote, on_delete=models.SET_NULL, null=True, blank=True)
    invoice_number = models.CharField(max_length=40, unique=True)
    due_date = models.DateField(null=True, blank=True)
    note = models.TextField(blank=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='unpaid')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.invoice_number


class InvoiceItem(TimeStampedModel):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    item_name = models.CharField(max_length=150)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'{self.quantity} x {self.item_name}'


class SiteSetting(TimeStampedModel):
    business_name = models.CharField(max_length=150, default='Street Union Co')
    tagline = models.CharField(max_length=220, blank=True)
    whatsapp_number = models.CharField(max_length=20, blank=True)
    support_email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    delivery_note = models.CharField(max_length=220, blank=True)
    promo_text = models.CharField(max_length=220, blank=True)

    def __str__(self):
        return self.business_name
