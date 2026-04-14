from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('', views.home, name='home'),
    path('menu/', views.menu, name='menu'),
    path('menu/<slug:slug>/', views.product_detail, name='product_detail'),
    path('specials/', views.specials, name='specials'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/item/<path:item_key>/set/', views.set_cart_quantity, name='set_cart_quantity'),
    path('cart/item/<path:item_key>/<str:action>/', views.change_cart_quantity, name='change_cart_quantity'),
    path('cart/item/<path:item_key>/remove/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('order/success/<str:order_number>/', views.order_success, name='order_success'),
    path('order/<str:order_number>/payment/', views.payment_options, name='payment_options'),
    path('track/', views.track_order, name='track_order'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),

    path('dashboard/', views.dashboard_home, name='dashboard_home'),
    path('dashboard/orders/', views.dashboard_orders, name='dashboard_orders'),
    path('dashboard/orders/feed/', views.dashboard_orders_feed, name='dashboard_orders_feed'),
    path('dashboard/orders/<int:order_id>/status/', views.update_order_status, name='update_order_status'),
    path('dashboard/orders/<int:order_id>/whatsapp/<str:reply_type>/', views.send_order_whatsapp_reply, name='send_order_whatsapp_reply'),
    path('dashboard/orders/<int:order_id>/create-quote/', views.create_quote_from_order, name='create_quote_from_order'),
    path('dashboard/orders/<int:order_id>/create-invoice/', views.create_invoice_from_order, name='create_invoice_from_order'),

    path('dashboard/kitchen/', views.kitchen_screen, name='kitchen_screen'),

    path('dashboard/products/', views.dashboard_products, name='dashboard_products'),
    path('dashboard/products/create/', views.product_create, name='product_create'),
    path('dashboard/products/<int:product_id>/edit/', views.product_edit, name='product_edit'),

    path('dashboard/specials/', views.dashboard_specials, name='dashboard_specials'),
    path('dashboard/specials/create/', views.special_create, name='special_create'),
    path('dashboard/specials/<int:special_id>/edit/', views.special_edit, name='special_edit'),

    path('dashboard/quotes/', views.dashboard_quotes, name='dashboard_quotes'),
    path('dashboard/quotes/create/', views.quote_create, name='quote_create'),
    path('dashboard/quotes/<int:quote_id>/pdf/', views.quote_pdf, name='quote_pdf'),

    path('dashboard/invoices/', views.dashboard_invoices, name='dashboard_invoices'),
    path('dashboard/invoices/create/', views.invoice_create, name='invoice_create'),
    path('dashboard/invoices/<int:invoice_id>/pdf/', views.invoice_pdf, name='invoice_pdf'),

    path('dashboard/settings/', views.dashboard_settings, name='dashboard_settings'),
]
