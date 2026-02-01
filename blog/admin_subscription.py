"""
Premium Obuna Tizimi - Admin Panel
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models_subscription import (
    SubscriptionPlan, UserSubscription, Payment, PromoCode,
    ReferralCode, ReferralInvite, DailyQuote, UserActivity,
    UserBadge, UserStats
)


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'plan_type', 'price_display', 'duration_type', 
                    'daily_book_limit', 'daily_ai_limit', 'is_popular', 'is_active', 'order')
    list_filter = ('plan_type', 'duration_type', 'is_active', 'is_popular')
    list_editable = ('order', 'is_active', 'is_popular')
    search_fields = ('name',)
    ordering = ('order',)
    
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('name', 'plan_type', 'duration_type', 'order')
        }),
        ('Narxlar', {
            'fields': ('price', 'original_price')
        }),
        ('Cheklovlar', {
            'fields': ('daily_book_limit', 'daily_ai_limit', 'can_download', 
                      'can_read_premium', 'ads_free', 'offline_reading')
        }),
        ('Qo\'shimcha', {
            'fields': ('referral_bonus', 'description', 'features', 'is_popular', 'is_active')
        }),
    )
    
    def price_display(self, obj):
        if obj.price == 0:
            return format_html('<span style="color: green; font-weight: bold;">Bepul</span>')
        return format_html('<span style="color: #667eea; font-weight: bold;">{:,.0f} so\'m</span>', obj.price)
    price_display.short_description = "Narxi"


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'status_badge', 'expires_at', 'daily_books_read', 
                    'daily_ai_requests', 'days_remaining_display')
    list_filter = ('status', 'plan')
    search_fields = ('user__username', 'user__email')
    raw_id_fields = ('user', 'plan')
    readonly_fields = ('started_at', 'last_reset_date')
    
    def status_badge(self, obj):
        colors = {
            'active': 'green',
            'expired': 'red',
            'cancelled': 'gray',
            'pending': 'orange'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; border-radius: 10px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Status"
    
    def days_remaining_display(self, obj):
        days = obj.days_remaining()
        if days == float('inf'):
            return "∞"
        if days <= 3:
            return format_html('<span style="color: red; font-weight: bold;">{} kun</span>', days)
        return f"{days} kun"
    days_remaining_display.short_description = "Qolgan"


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'user', 'plan', 'amount_display', 
                    'payment_method', 'status_badge', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('transaction_id', 'user__username', 'external_id')
    raw_id_fields = ('user', 'plan')
    readonly_fields = ('transaction_id', 'created_at', 'completed_at')
    date_hierarchy = 'created_at'
    
    def amount_display(self, obj):
        return format_html('<strong>{:,.0f} so\'m</strong>', obj.amount)
    amount_display.short_description = "Summa"
    
    def status_badge(self, obj):
        colors = {
            'pending': '#f59e0b',
            'completed': '#10b981',
            'failed': '#ef4444',
            'refunded': '#6366f1'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; border-radius: 10px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Status"
    
    actions = ['mark_as_completed', 'mark_as_refunded']
    
    def mark_as_completed(self, request, queryset):
        for payment in queryset.filter(status='pending'):
            payment.status = 'completed'
            payment.completed_at = timezone.now()
            payment.save()
            
            # Obunani faollashtirish
            from .views_subscription import activate_subscription
            activate_subscription(payment.user, payment.plan)
        
        self.message_user(request, f"{queryset.count()} ta to'lov tasdiqlandi")
    mark_as_completed.short_description = "To'lovni tasdiqlash"
    
    def mark_as_refunded(self, request, queryset):
        queryset.update(status='refunded')
        self.message_user(request, f"{queryset.count()} ta to'lov qaytarildi")
    mark_as_refunded.short_description = "To'lovni qaytarish"


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'code_type', 'value', 'usage_display', 'valid_until', 'is_valid_display', 'is_active')
    list_filter = ('code_type', 'is_active')
    search_fields = ('code',)
    list_editable = ('is_active',)
    filter_horizontal = ('applicable_plans',)
    
    def usage_display(self, obj):
        percent = (obj.used_count / obj.max_uses * 100) if obj.max_uses > 0 else 0
        color = 'green' if percent < 50 else 'orange' if percent < 90 else 'red'
        return format_html(
            '<span style="color: {};">{} / {}</span>',
            color, obj.used_count, obj.max_uses
        )
    usage_display.short_description = "Foydalanish"
    
    def is_valid_display(self, obj):
        if obj.is_valid():
            return format_html('<span style="color: green;">✓ Amal qilmoqda</span>')
        return format_html('<span style="color: red;">✗ Yaroqsiz</span>')
    is_valid_display.short_description = "Holati"


@admin.register(ReferralCode)
class ReferralCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'user', 'total_invites', 'successful_invites', 'earned_days', 'created_at')
    search_fields = ('code', 'user__username')
    raw_id_fields = ('user',)
    readonly_fields = ('code', 'created_at')
    
    def has_add_permission(self, request):
        return False  # Faqat avtomatik yaratiladi


@admin.register(ReferralInvite)
class ReferralInviteAdmin(admin.ModelAdmin):
    list_display = ('referrer', 'invited_user', 'referrer_bonus_given', 'converted_at', 'created_at')
    list_filter = ('referrer_bonus_given', 'created_at')
    search_fields = ('referrer__username', 'invited_user__username')
    raw_id_fields = ('referrer', 'invited_user', 'referral_code')


@admin.register(DailyQuote)
class DailyQuoteAdmin(admin.ModelAdmin):
    list_display = ('quote_preview', 'author', 'book_title', 'show_date', 'share_count', 'is_featured')
    list_filter = ('is_featured', 'show_date')
    search_fields = ('quote', 'author', 'book_title')
    list_editable = ('show_date', 'is_featured')
    raw_id_fields = ('book',)
    
    def quote_preview(self, obj):
        return obj.quote[:80] + "..." if len(obj.quote) > 80 else obj.quote
    quote_preview.short_description = "Iqtibos"


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'points', 'description', 'created_at')
    list_filter = ('activity_type', 'created_at')
    search_fields = ('user__username', 'description')
    raw_id_fields = ('user', 'related_book')
    date_hierarchy = 'created_at'


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ('user', 'badge_icon', 'badge_type', 'earned_at')
    list_filter = ('badge_type', 'earned_at')
    search_fields = ('user__username',)
    raw_id_fields = ('user',)
    
    def badge_icon(self, obj):
        return UserBadge.get_badge_icon(obj.badge_type)
    badge_icon.short_description = "🏅"


@admin.register(UserStats)
class UserStatsAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_books_read', 'total_pages_read', 'total_points', 
                    'current_streak', 'longest_streak', 'last_active_date')
    list_filter = ('last_active_date',)
    search_fields = ('user__username',)
    raw_id_fields = ('user',)
    
    def has_add_permission(self, request):
        return False  # Faqat avtomatik yaratiladi
