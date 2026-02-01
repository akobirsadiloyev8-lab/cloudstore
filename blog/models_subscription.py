"""
Premium Obuna Tizimi - Subscription Models
Zamonaviy Freemium model uchun barcha modellar
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import uuid
import hashlib


class SubscriptionPlan(models.Model):
    """Obuna rejalari"""
    PLAN_TYPES = [
        ('free', 'Bepul'),
        ('standard', 'Standart'),
        ('premium', 'Premium'),
        ('vip', 'VIP'),
    ]
    
    DURATION_TYPES = [
        ('monthly', 'Oylik'),
        ('quarterly', 'Choraklik (3 oy)'),
        ('yearly', 'Yillik'),
        ('lifetime', 'Umrbod'),
    ]
    
    name = models.CharField(max_length=50, verbose_name="Reja nomi")
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES, unique=True)
    duration_type = models.CharField(max_length=20, choices=DURATION_TYPES, default='monthly')
    
    # Narxlar (so'mda)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Narxi (so'm)")
    original_price = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Asl narxi (chegirma uchun)")
    
    # Cheklovlar
    daily_book_limit = models.PositiveIntegerField(default=3, verbose_name="Kunlik kitob limiti")
    daily_ai_limit = models.PositiveIntegerField(default=5, verbose_name="Kunlik AI so'rov limiti")
    can_download = models.BooleanField(default=False, verbose_name="Yuklab olish")
    can_read_premium = models.BooleanField(default=False, verbose_name="Premium kitoblarni o'qish")
    ads_free = models.BooleanField(default=False, verbose_name="Reklmasiz")
    offline_reading = models.BooleanField(default=False, verbose_name="Offline o'qish")
    
    # Bonus
    referral_bonus = models.PositiveIntegerField(default=0, verbose_name="Referral bonus (kun)")
    
    # Tavsif
    description = models.TextField(blank=True, verbose_name="Tavsif")
    features = models.JSONField(default=list, verbose_name="Xususiyatlar ro'yxati")
    
    # Tartib
    order = models.PositiveIntegerField(default=0, verbose_name="Tartib raqami")
    is_popular = models.BooleanField(default=False, verbose_name="Mashhur (badge)")
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    
    class Meta:
        verbose_name = "Obuna rejasi"
        verbose_name_plural = "Obuna rejalari"
        ordering = ['order', 'price']
    
    def __str__(self):
        return f"{self.name} - {self.get_price_display()}"
    
    def get_price_display(self):
        if self.price == 0:
            return "Bepul"
        return f"{self.price:,.0f} so'm"
    
    def get_duration_days(self):
        """Obuna davomiyligini kunlarda qaytarish"""
        durations = {
            'monthly': 30,
            'quarterly': 90,
            'yearly': 365,
            'lifetime': 36500,  # 100 yil
        }
        return durations.get(self.duration_type, 30)


class UserSubscription(models.Model):
    """Foydalanuvchi obunasi"""
    STATUS_CHOICES = [
        ('active', 'Faol'),
        ('expired', 'Muddati tugagan'),
        ('cancelled', 'Bekor qilingan'),
        ('pending', 'Kutilmoqda'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    started_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Kunlik foydalanish
    daily_books_read = models.PositiveIntegerField(default=0)
    daily_ai_requests = models.PositiveIntegerField(default=0)
    last_reset_date = models.DateField(auto_now_add=True)
    
    # Bonus kunlar (referral va promo)
    bonus_days = models.PositiveIntegerField(default=0)
    
    # To'lov ma'lumotlari
    auto_renew = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Foydalanuvchi obunasi"
        verbose_name_plural = "Foydalanuvchi obunalari"
    
    def __str__(self):
        return f"{self.user.username} - {self.plan.name if self.plan else 'Bepul'}"
    
    def is_active(self):
        """Obuna faolmi?"""
        if not self.plan:
            return True  # Bepul reja
        if self.status != 'active':
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True
    
    def is_premium(self):
        """Premium obunami?"""
        if not self.plan:
            return False
        return self.plan.plan_type in ['standard', 'premium', 'vip']
    
    def reset_daily_limits(self):
        """Kunlik limitlarni yangilash"""
        today = timezone.now().date()
        if self.last_reset_date != today:
            self.daily_books_read = 0
            self.daily_ai_requests = 0
            self.last_reset_date = today
            self.save()
    
    def can_read_book(self):
        """Kitob o'qish mumkinmi?"""
        self.reset_daily_limits()
        if not self.plan:
            return self.daily_books_read < 2  # Bepul: 2 ta kitob
        return self.daily_books_read < self.plan.daily_book_limit
    
    def can_use_ai(self):
        """AI ishlatish mumkinmi?"""
        self.reset_daily_limits()
        if not self.plan:
            return self.daily_ai_requests < 3  # Bepul: 3 ta
        return self.daily_ai_requests < self.plan.daily_ai_limit
    
    def increment_book_read(self):
        """Kitob o'qish hisoblagichini oshirish"""
        self.reset_daily_limits()
        self.daily_books_read += 1
        self.save()
    
    def increment_ai_request(self):
        """AI so'rov hisoblagichini oshirish"""
        self.reset_daily_limits()
        self.daily_ai_requests += 1
        self.save()
    
    def days_remaining(self):
        """Qolgan kunlar"""
        if not self.expires_at:
            return float('inf')
        delta = self.expires_at - timezone.now()
        return max(0, delta.days)
    
    def add_bonus_days(self, days):
        """Bonus kun qo'shish"""
        self.bonus_days += days
        if self.expires_at:
            self.expires_at += timedelta(days=days)
        self.save()


class Payment(models.Model):
    """To'lovlar tarixi"""
    PAYMENT_METHODS = [
        ('click', 'Click'),
        ('payme', 'Payme'),
        ('uzum', 'Uzum Bank'),
        ('stripe', 'Stripe'),
        ('promo', 'Promo kod'),
        ('referral', 'Referral bonus'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('completed', 'Yakunlangan'),
        ('failed', 'Muvaffaqiyatsiz'),
        ('refunded', 'Qaytarilgan'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    
    transaction_id = models.CharField(max_length=100, unique=True, editable=False)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # To'lov tizimi ma'lumotlari
    external_id = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = "To'lov"
        verbose_name_plural = "To'lovlar"
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.transaction_id} - {self.amount} so'm"


class PromoCode(models.Model):
    """Promo kodlar"""
    CODE_TYPES = [
        ('percentage', 'Foiz chegirma'),
        ('fixed', 'Belgilangan summa'),
        ('days', 'Bonus kunlar'),
        ('trial', 'Sinov muddati'),
    ]
    
    code = models.CharField(max_length=50, unique=True, verbose_name="Kod")
    code_type = models.CharField(max_length=20, choices=CODE_TYPES, default='percentage')
    value = models.PositiveIntegerField(default=0, verbose_name="Qiymat")
    
    # Qaysi rejaga tegishli
    applicable_plans = models.ManyToManyField(SubscriptionPlan, blank=True)
    
    # Cheklovlar
    max_uses = models.PositiveIntegerField(default=100, verbose_name="Maksimal foydalanish")
    used_count = models.PositiveIntegerField(default=0, verbose_name="Ishlatilgan")
    
    # Muddati
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Promo kod"
        verbose_name_plural = "Promo kodlar"
    
    def __str__(self):
        return self.code
    
    def is_valid(self):
        """Kod hali amalda mi?"""
        if not self.is_active:
            return False
        if self.used_count >= self.max_uses:
            return False
        now = timezone.now()
        if self.valid_from > now:
            return False
        if self.valid_until and self.valid_until < now:
            return False
        return True
    
    def apply(self, price):
        """Kodni qo'llash"""
        if self.code_type == 'percentage':
            return price * (100 - self.value) / 100
        elif self.code_type == 'fixed':
            return max(0, price - self.value)
        return price


class ReferralCode(models.Model):
    """Referral (do'stni taklif qilish) kodlari"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='referral_code')
    code = models.CharField(max_length=20, unique=True)
    
    # Statistika
    total_invites = models.PositiveIntegerField(default=0, verbose_name="Jami takliflar")
    successful_invites = models.PositiveIntegerField(default=0, verbose_name="Muvaffaqiyatli")
    earned_days = models.PositiveIntegerField(default=0, verbose_name="Yutilgan kunlar")
    earned_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Referral kod"
        verbose_name_plural = "Referral kodlar"
    
    def save(self, *args, **kwargs):
        if not self.code:
            # Unikal kod generatsiya
            base = f"{self.user.username}{self.user.id}"
            hash_code = hashlib.md5(base.encode()).hexdigest()[:6].upper()
            self.code = f"REF{hash_code}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.username}: {self.code}"
    
    def get_share_link(self):
        """Ulashish havolasi"""
        return f"?ref={self.code}"


class ReferralInvite(models.Model):
    """Referral takliflar tarixi"""
    referrer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invites')
    invited_user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='invited_by')
    referral_code = models.ForeignKey(ReferralCode, on_delete=models.CASCADE)
    
    # Bonus berildi mi?
    referrer_bonus_given = models.BooleanField(default=False)
    invited_bonus_given = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    converted_at = models.DateTimeField(null=True, blank=True)  # Premium bo'lsa
    
    class Meta:
        verbose_name = "Referral taklif"
        verbose_name_plural = "Referral takliflar"
    
    def __str__(self):
        return f"{self.referrer.username} → {self.invited_user.username}"


class DailyQuote(models.Model):
    """Kundalik iqtiboslar (viral content uchun)"""
    quote = models.TextField(verbose_name="Iqtibos")
    author = models.CharField(max_length=200, verbose_name="Muallif")
    book_title = models.CharField(max_length=300, blank=True, verbose_name="Kitob nomi")
    book = models.ForeignKey('Book', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Ulashish statistikasi
    share_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)
    
    # Qachon ko'rsatilsin
    show_date = models.DateField(null=True, blank=True, verbose_name="Ko'rsatish sanasi")
    is_featured = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Kundalik iqtibos"
        verbose_name_plural = "Kundalik iqtiboslar"
        ordering = ['-show_date', '-created_at']
    
    def __str__(self):
        return f'"{self.quote[:50]}..." - {self.author}'


class UserActivity(models.Model):
    """Foydalanuvchi faoliyati (gamifikatsiya uchun)"""
    ACTIVITY_TYPES = [
        ('read_book', 'Kitob o\'qish'),
        ('finish_book', 'Kitob tugatish'),
        ('rate_book', 'Baho berish'),
        ('share', 'Ulashish'),
        ('invite', 'Taklif qilish'),
        ('login_streak', 'Ketma-ket kirish'),
        ('first_book', 'Birinchi kitob'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=30, choices=ACTIVITY_TYPES)
    points = models.PositiveIntegerField(default=0)
    description = models.CharField(max_length=255, blank=True)
    
    # Bog'liq ma'lumot
    related_book = models.ForeignKey('Book', on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Faoliyat"
        verbose_name_plural = "Faoliyatlar"
        ordering = ['-created_at']


class UserBadge(models.Model):
    """Yutuqlar/Badge'lar"""
    BADGE_TYPES = [
        ('reader_1', 'Boshlang\'ich o\'quvchi'),
        ('reader_10', '10 ta kitob'),
        ('reader_50', '50 ta kitob'),
        ('reader_100', 'Kitobxon ustasi'),
        ('sharer', 'Faol ulashuvchi'),
        ('reviewer', 'Sharh ustasi'),
        ('inviter_5', '5 do\'st taklifi'),
        ('inviter_20', 'Influencer'),
        ('streak_7', 'Haftalik streak'),
        ('streak_30', 'Oylik streak'),
        ('first_premium', 'Premium a\'zo'),
        ('vip', 'VIP a\'zo'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badges')
    badge_type = models.CharField(max_length=30, choices=BADGE_TYPES)
    earned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Yutuq"
        verbose_name_plural = "Yutuqlar"
        unique_together = ('user', 'badge_type')
    
    def __str__(self):
        return f"{self.user.username} - {self.get_badge_type_display()}"
    
    @staticmethod
    def get_badge_icon(badge_type):
        """Badge ikonkasi"""
        icons = {
            'reader_1': '📖',
            'reader_10': '📚',
            'reader_50': '🏆',
            'reader_100': '👑',
            'sharer': '🔗',
            'reviewer': '✍️',
            'inviter_5': '👥',
            'inviter_20': '🌟',
            'streak_7': '🔥',
            'streak_30': '💪',
            'first_premium': '💎',
            'vip': '👑',
        }
        return icons.get(badge_type, '🏅')


class UserStats(models.Model):
    """Foydalanuvchi statistikasi"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='stats')
    
    # O'qish statistikasi
    total_books_read = models.PositiveIntegerField(default=0)
    total_pages_read = models.PositiveIntegerField(default=0)
    total_reading_time = models.PositiveIntegerField(default=0)  # minutlarda
    
    # Faollik
    total_points = models.PositiveIntegerField(default=0)
    current_streak = models.PositiveIntegerField(default=0)  # ketma-ket kirish kunlari
    longest_streak = models.PositiveIntegerField(default=0)
    last_active_date = models.DateField(null=True, blank=True)
    
    # Ijtimoiy
    total_shares = models.PositiveIntegerField(default=0)
    total_reviews = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = "Foydalanuvchi statistikasi"
        verbose_name_plural = "Foydalanuvchi statistikalari"
    
    def __str__(self):
        return f"{self.user.username} stats"
    
    def update_streak(self):
        """Streak yangilash"""
        today = timezone.now().date()
        if self.last_active_date:
            delta = (today - self.last_active_date).days
            if delta == 1:
                self.current_streak += 1
            elif delta > 1:
                self.current_streak = 1
            # Agar bugun bo'lsa, o'zgartirmaslik
        else:
            self.current_streak = 1
        
        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak
        
        self.last_active_date = today
        self.save()
    
    def add_points(self, points):
        """Ball qo'shish"""
        self.total_points += points
        self.save()
