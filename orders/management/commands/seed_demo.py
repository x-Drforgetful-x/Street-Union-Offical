from decimal import Decimal
from django.core.management.base import BaseCommand
from orders.models import Category, DeliveryZone, Product, ProductExtra, SiteSetting, Special


class Command(BaseCommand):
    help = 'Seeds demo categories, products, specials, and delivery zones.'

    def handle(self, *args, **options):
        SiteSetting.objects.get_or_create(
            business_name='Street Union Co',
            defaults={
                'tagline': 'Bold street food. Fast ordering. Big flavour.',
                'whatsapp_number': '27670000000',
                'phone_number': '067 000 0000',
                'promo_text': 'Street Union Co weekly specials live now',
                'delivery_note': 'Delivery fees can be adjusted in admin later.',
            },
        )

        category_names = ['Burgers', 'Meals', 'Chips & Sides', 'Drinks', 'Specials']
        categories = {}
        for index, name in enumerate(category_names, start=1):
            categories[name], _ = Category.objects.get_or_create(name=name, defaults={'sort_order': index})

        items = [
            ('Smash Burger Deluxe', 'Burgers', Decimal('79.00'), True, False),
            ('Hot Chicken Crunch', 'Burgers', Decimal('85.00'), True, False),
            ('Loaded Chips Supreme', 'Chips & Sides', Decimal('55.00'), False, True),
            ('Street Combo Meal', 'Meals', Decimal('129.00'), True, True),
            ('Cream Soda 440ml', 'Drinks', Decimal('18.00'), False, False),
        ]
        for name, category_name, price, featured, special in items:
            product, _ = Product.objects.get_or_create(
                name=name,
                defaults={
                    'category': categories[category_name],
                    'price': price,
                    'short_description': 'Built for speed, flavor, and bold presentation.',
                    'description': 'A premium demo item for your fast-food ordering platform.',
                    'is_featured': featured,
                    'is_special': special,
                    'image_url': 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=900&q=80',
                },
            )
            ProductExtra.objects.get_or_create(product=product, name='Extra Cheese', defaults={'price': Decimal('12.00')})
            ProductExtra.objects.get_or_create(product=product, name='Extra Sauce', defaults={'price': Decimal('8.00')})

        Special.objects.get_or_create(
            title='Monday Madness Combo',
            defaults={
                'description': '2 burgers + chips + drink for one promo price.',
                'promo_price': Decimal('149.00'),
                'old_price': Decimal('185.00'),
                'is_active': True,
                'is_featured': True,
                'banner_url': 'https://images.unsplash.com/photo-1513104890138-7c749659a591?auto=format&fit=crop&w=1200&q=80',
            },
        )

        for zone_name, fee in [('Pretoria Central', Decimal('20.00')), ('Mamelodi', Decimal('35.00')), ('Centurion', Decimal('45.00'))]:
            DeliveryZone.objects.get_or_create(name=zone_name, defaults={'fee': fee, 'minimum_order': Decimal('80.00')})

        self.stdout.write(self.style.SUCCESS('Demo data seeded successfully.'))
