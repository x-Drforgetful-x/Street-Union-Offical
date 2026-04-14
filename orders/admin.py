from django.contrib import admin
from .models import (
    Category, Customer, DeliveryZone, Invoice, InvoiceItem, Order,
    OrderItem, Product, ProductExtra, Quote, QuoteItem, SiteSetting, Special,
)


class ProductExtraInline(admin.TabularInline):
    model = ProductExtra
    extra = 0


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'sort_order')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_featured', 'is_special', 'is_available')
    list_filter = ('category', 'is_featured', 'is_special', 'is_available', 'spice_level')
    search_fields = ('name', 'short_description', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductExtraInline]


@admin.register(Special)
class SpecialAdmin(admin.ModelAdmin):
    list_display = ('title', 'promo_price', 'is_featured', 'is_active', 'start_date', 'end_date')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_name', 'quantity', 'unit_price', 'extras_summary', 'line_total')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer', 'order_type', 'total', 'status', 'created_at')
    search_fields = ('order_number', 'customer__first_name', 'customer__phone_number')
    list_filter = ('order_type', 'status', 'created_at')
    inlines = [OrderItemInline]


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'phone_number', 'email', 'created_at')
    search_fields = ('first_name', 'last_name', 'phone_number', 'email')


@admin.register(DeliveryZone)
class DeliveryZoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'fee', 'minimum_order', 'is_active')


class QuoteItemInline(admin.TabularInline):
    model = QuoteItem
    extra = 0


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ('quote_number', 'customer', 'total', 'status', 'expiry_date', 'created_at')
    inlines = [QuoteItemInline]


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'customer', 'total', 'payment_status', 'due_date', 'created_at')
    inlines = [InvoiceItemInline]


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ('business_name', 'whatsapp_number', 'phone_number')
