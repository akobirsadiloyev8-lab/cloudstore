"""
Boshlang'ich obuna rejalarini yaratish
Ishga tushirish: python manage.py shell < setup_plans.py
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from blog.models_subscription import SubscriptionPlan

# Mavjud rejalarni o'chirish (agar kerak bo'lsa)
# SubscriptionPlan.objects.all().delete()

# Bepul reja
free_plan, created = SubscriptionPlan.objects.get_or_create(
    plan_type='free',
    defaults={
        'name': 'Bepul',
        'duration_type': 'monthly',
        'price': 0,
        'original_price': 0,
        'daily_book_limit': 2,
        'daily_ai_limit': 3,
        'can_download': False,
        'can_read_premium': False,
        'ads_free': False,
        'offline_reading': False,
        'referral_bonus': 3,
        'order': 1,
        'is_popular': False,
        'is_active': True,
        'description': 'Asosiy funksiyalar bilan tanishing',
        'features': [
            'Kuniga 2 ta kitob o\'qish',
            'Kuniga 3 ta AI so\'rov',
            'Kategoriyalar bo\'yicha qidirish',
            'Kitoblarni baholash'
        ]
    }
)
print(f"Bepul reja: {'yaratildi' if created else 'mavjud'}")

# Standart reja
standard_plan, created = SubscriptionPlan.objects.get_or_create(
    plan_type='standard',
    defaults={
        'name': 'Standart',
        'duration_type': 'monthly',
        'price': 19900,  # 19,900 so'm
        'original_price': 29900,
        'daily_book_limit': 10,
        'daily_ai_limit': 20,
        'can_download': True,
        'can_read_premium': False,
        'ads_free': True,
        'offline_reading': False,
        'referral_bonus': 7,
        'order': 2,
        'is_popular': False,
        'is_active': True,
        'description': 'Ko\'proq kitob va AI imkoniyatlari',
        'features': [
            'Kuniga 10 ta kitob',
            'Kuniga 20 ta AI so\'rov',
            'Kitoblarni yuklab olish',
            'Reklmasiz tajriba',
            'Ustuvor yordam'
        ]
    }
)
print(f"Standart reja: {'yaratildi' if created else 'mavjud'}")

# Premium reja
premium_plan, created = SubscriptionPlan.objects.get_or_create(
    plan_type='premium',
    defaults={
        'name': 'Premium',
        'duration_type': 'monthly',
        'price': 39900,  # 39,900 so'm
        'original_price': 59900,
        'daily_book_limit': 50,
        'daily_ai_limit': 100,
        'can_download': True,
        'can_read_premium': True,
        'ads_free': True,
        'offline_reading': True,
        'referral_bonus': 14,
        'order': 3,
        'is_popular': True,  # Mashhur
        'is_active': True,
        'description': 'To\'liq imkoniyatlar!',
        'features': [
            'Kuniga 50 ta kitob',
            'Cheksiz AI so\'rovlar',
            'Premium kitoblar',
            'Offline o\'qish',
            'Yuklash cheksiz',
            'VIP yordam'
        ]
    }
)
print(f"Premium reja: {'yaratildi' if created else 'mavjud'}")

# VIP reja (yillik)
vip_plan, created = SubscriptionPlan.objects.get_or_create(
    plan_type='vip',
    defaults={
        'name': 'VIP Yillik',
        'duration_type': 'yearly',
        'price': 299000,  # 299,000 so'm (yillik)
        'original_price': 479000,
        'daily_book_limit': 999,  # Cheksiz
        'daily_ai_limit': 999,
        'can_download': True,
        'can_read_premium': True,
        'ads_free': True,
        'offline_reading': True,
        'referral_bonus': 30,
        'order': 4,
        'is_popular': False,
        'is_active': True,
        'description': 'Eng yaxshi tanlov - 40% tejang!',
        'features': [
            'CHEKSIZ kitoblar',
            'CHEKSIZ AI',
            'Barcha premium xususiyatlar',
            '40% chegirma',
            'Birinchi navbatda yangiliklar',
            'Shaxsiy menejer'
        ]
    }
)
print(f"VIP reja: {'yaratildi' if created else 'mavjud'}")

print("\n✅ Barcha obuna rejalari tayyor!")
print(f"Jami rejalar: {SubscriptionPlan.objects.count()}")
