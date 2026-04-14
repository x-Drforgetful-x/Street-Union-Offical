# Street Union Co Food Ordering Platform

A Django-based fast food ordering platform with:
- customer-facing ordering website
- weekly specials banner/tabs
- searchable menu by category
- session-based cart
- delivery/collection checkout
- WhatsApp order handoff
- manual quotes and invoices
- live dashboard and kitchen screen

## Core features included
- Home page with hero, specials, featured items, and promo strip
- Menu page with category filters and search
- Product detail page with optional extras
- Session cart with quantity updates and a cart drawer
- Checkout flow with delivery or collection
- Order number format based on first letter + last 4 digits + timestamp
- WhatsApp redirect with prefilled order text
- Live orders dashboard with auto refresh
- Kitchen tablet screen with fast status updates
- Dashboard CRUD pages for products and specials
- Manual quote creation with PDF export
- Manual invoice creation with PDF export
- WhatsApp confirm/status message links from the dashboard
- Payment options screen with PayFast and PayShap placeholders

## Suggested stack
- Python 3.12+
- Django 6.0 or compatible
- SQLite for quick start
- MariaDB/MySQL in production

## Quick start
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo
python manage.py runserver
```

Open:
- Website: http://127.0.0.1:8000/
- Dashboard: http://127.0.0.1:8000/dashboard/
- Kitchen screen: http://127.0.0.1:8000/dashboard/kitchen/
- Admin: http://127.0.0.1:8000/admin/

## Environment variables
Create a `.env` file or set variables another way:
```env
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
WHATSAPP_NUMBER=27670000000
BUSINESS_NAME=Street Union Co
CURRENCY_SYMBOL=R
PAYFAST_URL=
PAYSHAP_HANDLE=
```

## Notes on integrations
- The project creates prefilled WhatsApp links for orders and order updates.
- Automatic sending of WhatsApp messages still needs a real WhatsApp Business API setup and credentials.
- PayFast and PayShap buttons are scaffolded through environment variables so you can plug in your live payment flow later.

## Project structure
```text
street_union_co_project/
├── manage.py
├── requirements.txt
├── futurebite/
│   ├── settings.py
│   ├── urls.py
│   └── ...
├── orders/
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── admin.py
│   ├── context_processors.py
│   ├── templatetags/
│   ├── management/commands/seed_demo.py
│   └── templates/
└── static/
    ├── css/
    └── js/
```

## Production notes
- Switch the database engine to MariaDB/MySQL in `settings.py`
- Collect static files with `python manage.py collectstatic`
- Add proper authentication and permissions around dashboard views
- Replace placeholder payment links with your live PayFast or bank/PayShap flow
- Connect a real WhatsApp Business API provider for true automated sends
