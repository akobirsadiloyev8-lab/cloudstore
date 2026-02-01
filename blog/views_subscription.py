"""
Premium Obuna Tizimi - Views
Subscription, Payment va Marketing uchun viewlar
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.contrib import messages
from datetime import timedelta
from functools import wraps
import json
import hashlib
import uuid

from .models_subscription import (
    SubscriptionPlan, UserSubscription, Payment, PromoCode,
    ReferralCode, ReferralInvite, DailyQuote, UserActivity,
    UserBadge, UserStats
)


def get_or_create_subscription(user):
    """Foydalanuvchi obunasini olish yoki yaratish"""
    subscription, created = UserSubscription.objects.get_or_create(
        user=user,
        defaults={
            'plan': SubscriptionPlan.objects.filter(plan_type='free').first(),
            'status': 'active'
        }
    )
    return subscription


def get_or_create_stats(user):
    """Foydalanuvchi statistikasini olish yoki yaratish"""
    stats, created = UserStats.objects.get_or_create(user=user)
    return stats


def get_or_create_referral_code(user):
    """Referral kod olish yoki yaratish"""
    referral, created = ReferralCode.objects.get_or_create(user=user)
    return referral


# ===== DECORATORS =====

def premium_required(view_func):
    """Premium obuna kerak bo'lgan viewlar uchun decorator"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        subscription = get_or_create_subscription(request.user)
        if not subscription.is_premium():
            messages.warning(request, "Bu funksiya uchun Premium obuna kerak!")
            return redirect('subscription_plans')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def check_book_limit(view_func):
    """Kitob o'qish limitini tekshirish"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            subscription = get_or_create_subscription(request.user)
            if not subscription.can_read_book():
                return JsonResponse({
                    'success': False,
                    'limit_reached': True,
                    'message': f"Kunlik limitingiz tugadi! Premium obunaga o'ting yoki ertaga qaytib keling.",
                    'upgrade_url': '/obuna/'
                }, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


def check_ai_limit(view_func):
    """AI so'rov limitini tekshirish"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            subscription = get_or_create_subscription(request.user)
            if not subscription.can_use_ai():
                return JsonResponse({
                    'success': False,
                    'limit_reached': True,
                    'message': "AI so'rovlar limitingiz tugadi! Premium obunaga o'ting.",
                    'upgrade_url': '/obuna/'
                }, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


# ===== SUBSCRIPTION VIEWS =====

def subscription_plans(request):
    """Obuna rejalarini ko'rsatish"""
    plans = SubscriptionPlan.objects.filter(is_active=True).order_by('order')
    
    user_subscription = None
    if request.user.is_authenticated:
        user_subscription = get_or_create_subscription(request.user)
    
    # Referral kodi (agar URL'da bo'lsa)
    ref_code = request.GET.get('ref', '')
    if ref_code and request.user.is_authenticated:
        # Referral kodini session'ga saqlash
        request.session['referral_code'] = ref_code
    
    context = {
        'plans': plans,
        'user_subscription': user_subscription,
        'referral_code': ref_code,
    }
    return render(request, 'blog/subscription/plans.html', context)


@login_required
def checkout(request, plan_id):
    """To'lov sahifasi"""
    plan = get_object_or_404(SubscriptionPlan, id=plan_id, is_active=True)
    
    if plan.price == 0:
        # Bepul rejaga o'tish
        subscription = get_or_create_subscription(request.user)
        subscription.plan = plan
        subscription.status = 'active'
        subscription.save()
        messages.success(request, f"{plan.name} rejasiga o'tdingiz!")
        return redirect('profile')
    
    # Promo kod tekshirish
    promo_code = request.GET.get('promo', '')
    discount = 0
    promo = None
    
    if promo_code:
        try:
            promo = PromoCode.objects.get(code=promo_code.upper(), is_active=True)
            if promo.is_valid():
                if promo.code_type == 'percentage':
                    discount = float(plan.price) * promo.value / 100
                elif promo.code_type == 'fixed':
                    discount = promo.value
        except PromoCode.DoesNotExist:
            pass
    
    final_price = max(0, float(plan.price) - discount)
    
    context = {
        'plan': plan,
        'promo': promo,
        'discount': discount,
        'final_price': final_price,
    }
    return render(request, 'blog/subscription/checkout.html', context)


@login_required
@require_POST
def apply_promo_code(request):
    """Promo kodni tekshirish va qo'llash"""
    data = json.loads(request.body)
    code = data.get('code', '').upper().strip()
    plan_id = data.get('plan_id')
    
    if not code:
        return JsonResponse({'success': False, 'message': 'Kodni kiriting'})
    
    try:
        promo = PromoCode.objects.get(code=code, is_active=True)
        
        if not promo.is_valid():
            return JsonResponse({'success': False, 'message': 'Bu kod amal qilmaydi'})
        
        # Reja bo'yicha tekshirish
        if promo.applicable_plans.exists() and plan_id:
            if not promo.applicable_plans.filter(id=plan_id).exists():
                return JsonResponse({'success': False, 'message': 'Bu kod ushbu reja uchun yaroqsiz'})
        
        return JsonResponse({
            'success': True,
            'code_type': promo.code_type,
            'value': promo.value,
            'message': f'{promo.value}% chegirma qo\'llandi!' if promo.code_type == 'percentage' else f'{promo.value:,} so\'m chegirma!'
        })
        
    except PromoCode.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Noto\'g\'ri kod'})


@login_required
@csrf_exempt
def create_payment(request):
    """To'lov yaratish"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST kerak'}, status=400)
    
    data = json.loads(request.body)
    plan_id = data.get('plan_id')
    payment_method = data.get('payment_method', 'click')
    promo_code = data.get('promo_code', '')
    
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    
    # Narxni hisoblash
    final_price = float(plan.price)
    
    if promo_code:
        try:
            promo = PromoCode.objects.get(code=promo_code.upper(), is_active=True)
            if promo.is_valid():
                final_price = promo.apply(final_price)
                promo.used_count += 1
                promo.save()
        except PromoCode.DoesNotExist:
            pass
    
    # Payment yaratish
    payment = Payment.objects.create(
        user=request.user,
        plan=plan,
        amount=final_price,
        payment_method=payment_method,
        status='pending',
        metadata={'promo_code': promo_code}
    )
    
    # To'lov tizimiga yo'naltirish URL'ini yaratish
    if payment_method == 'click':
        payment_url = generate_click_url(payment)
    elif payment_method == 'payme':
        payment_url = generate_payme_url(payment)
    else:
        payment_url = f'/payment/manual/{payment.transaction_id}/'
    
    return JsonResponse({
        'success': True,
        'transaction_id': payment.transaction_id,
        'payment_url': payment_url,
        'amount': float(payment.amount)
    })


def generate_click_url(payment):
    """Click to'lov URL'ini yaratish"""
    # Click API parametrlari (sozlamalardan olish kerak)
    merchant_id = "YOUR_CLICK_MERCHANT_ID"
    service_id = "YOUR_CLICK_SERVICE_ID"
    
    return f"https://my.click.uz/services/pay?merchant_id={merchant_id}&service_id={service_id}&transaction_param={payment.transaction_id}&amount={payment.amount}"


def generate_payme_url(payment):
    """Payme to'lov URL'ini yaratish"""
    # Payme API parametrlari
    merchant_id = "YOUR_PAYME_MERCHANT_ID"
    
    import base64
    data = f"m={merchant_id};ac.order_id={payment.transaction_id};a={int(payment.amount * 100)}"
    encoded = base64.b64encode(data.encode()).decode()
    
    return f"https://checkout.paycom.uz/{encoded}"


@csrf_exempt
def payment_callback(request, provider):
    """To'lov callback (Click/Payme)"""
    # Bu yerda to'lov tizimlaridan kelgan ma'lumotlarni tekshirish
    # Har bir to'lov tizimining o'z formati bor
    
    if provider == 'click':
        return handle_click_callback(request)
    elif provider == 'payme':
        return handle_payme_callback(request)
    
    return JsonResponse({'error': 'Unknown provider'}, status=400)


def handle_click_callback(request):
    """Click callback handler"""
    # Click'dan kelgan ma'lumotlarni tekshirish
    transaction_id = request.POST.get('merchant_trans_id')
    status = request.POST.get('error')
    
    if transaction_id:
        try:
            payment = Payment.objects.get(transaction_id=transaction_id)
            
            if status == '0':  # Muvaffaqiyatli
                payment.status = 'completed'
                payment.completed_at = timezone.now()
                payment.save()
                
                # Obunani faollashtirish
                activate_subscription(payment.user, payment.plan)
                
                return JsonResponse({'error': '0', 'error_note': 'Success'})
            
        except Payment.DoesNotExist:
            pass
    
    return JsonResponse({'error': '-1', 'error_note': 'Transaction not found'})


def handle_payme_callback(request):
    """Payme callback handler"""
    # Payme'dan kelgan JSON so'rovni tekshirish
    try:
        data = json.loads(request.body)
        method = data.get('method')
        
        if method == 'CheckPerformTransaction':
            # To'lovni tekshirish
            order_id = data['params']['account']['order_id']
            payment = Payment.objects.get(transaction_id=order_id)
            
            return JsonResponse({
                'result': {
                    'allow': True,
                    'additional': {'order_id': order_id}
                }
            })
        
        elif method == 'PerformTransaction':
            # To'lovni amalga oshirish
            order_id = data['params']['account']['order_id']
            payment = Payment.objects.get(transaction_id=order_id)
            payment.status = 'completed'
            payment.completed_at = timezone.now()
            payment.external_id = data['params']['id']
            payment.save()
            
            activate_subscription(payment.user, payment.plan)
            
            return JsonResponse({
                'result': {
                    'transaction': payment.transaction_id,
                    'state': 2,
                    'perform_time': int(timezone.now().timestamp() * 1000)
                }
            })
            
    except Exception as e:
        return JsonResponse({'error': {'code': -1, 'message': str(e)}})
    
    return JsonResponse({'error': {'code': -1, 'message': 'Unknown method'}})


def activate_subscription(user, plan):
    """Obunani faollashtirish"""
    subscription = get_or_create_subscription(user)
    
    subscription.plan = plan
    subscription.status = 'active'
    subscription.started_at = timezone.now()
    subscription.expires_at = timezone.now() + timedelta(days=plan.get_duration_days())
    subscription.save()
    
    # Referral bonusni berish
    try:
        invite = ReferralInvite.objects.get(invited_user=user, referrer_bonus_given=False)
        if plan.plan_type != 'free':
            # Taklif qiluvchiga bonus
            referrer_subscription = get_or_create_subscription(invite.referrer)
            referrer_subscription.add_bonus_days(7)  # 7 kun bonus
            
            invite.referrer_bonus_given = True
            invite.converted_at = timezone.now()
            invite.save()
            
            # Referral statistikasini yangilash
            invite.referral_code.successful_invites += 1
            invite.referral_code.earned_days += 7
            invite.referral_code.save()
            
            # Badge berish
            if invite.referral_code.successful_invites >= 5:
                UserBadge.objects.get_or_create(
                    user=invite.referrer,
                    badge_type='inviter_5'
                )
            if invite.referral_code.successful_invites >= 20:
                UserBadge.objects.get_or_create(
                    user=invite.referrer,
                    badge_type='inviter_20'
                )
    except ReferralInvite.DoesNotExist:
        pass
    
    # Premium badge
    if plan.plan_type in ['premium', 'vip']:
        badge_type = 'vip' if plan.plan_type == 'vip' else 'first_premium'
        UserBadge.objects.get_or_create(user=user, badge_type=badge_type)


@login_required
def my_subscription(request):
    """Mening obunalarim"""
    subscription = get_or_create_subscription(request.user)
    payments = Payment.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    context = {
        'subscription': subscription,
        'payments': payments,
    }
    return render(request, 'blog/subscription/my_subscription.html', context)


# ===== REFERRAL VIEWS =====

@login_required
def referral_dashboard(request):
    """Referral boshqaruv paneli"""
    referral_code = get_or_create_referral_code(request.user)
    invites = ReferralInvite.objects.filter(referrer=request.user).order_by('-created_at')
    
    context = {
        'referral_code': referral_code,
        'invites': invites,
        'share_link': request.build_absolute_uri(f'/register/?ref={referral_code.code}')
    }
    return render(request, 'blog/subscription/referral.html', context)


def track_referral(request, user):
    """Yangi foydalanuvchi uchun referral tracking"""
    ref_code = request.session.get('referral_code') or request.GET.get('ref')
    
    if ref_code:
        try:
            referral = ReferralCode.objects.get(code=ref_code.upper())
            
            # O'zini o'zi taklif qila olmaydi
            if referral.user != user:
                ReferralInvite.objects.create(
                    referrer=referral.user,
                    invited_user=user,
                    referral_code=referral
                )
                
                referral.total_invites += 1
                referral.save()
                
                # Yangi foydalanuvchiga bonus
                subscription = get_or_create_subscription(user)
                subscription.add_bonus_days(3)  # 3 kun bepul premium
                
                # Session'dan o'chirish
                if 'referral_code' in request.session:
                    del request.session['referral_code']
                    
        except ReferralCode.DoesNotExist:
            pass


# ===== MARKETING VIEWS =====

def daily_quote(request):
    """Bugungi iqtibos"""
    today = timezone.now().date()
    
    quote = DailyQuote.objects.filter(show_date=today).first()
    if not quote:
        quote = DailyQuote.objects.filter(is_featured=True).order_by('?').first()
    if not quote:
        quote = DailyQuote.objects.order_by('?').first()
    
    if request.headers.get('Accept') == 'application/json':
        if quote:
            return JsonResponse({
                'quote': quote.quote,
                'author': quote.author,
                'book': quote.book_title,
                'book_id': quote.book_id
            })
        return JsonResponse({'quote': '', 'author': ''})
    
    return render(request, 'blog/daily_quote.html', {'quote': quote})


@require_POST
def share_quote(request):
    """Iqtibosni ulashish statistikasi"""
    quote_id = request.POST.get('quote_id')
    platform = request.POST.get('platform', 'other')
    
    try:
        quote = DailyQuote.objects.get(id=quote_id)
        quote.share_count += 1
        quote.save()
        
        if request.user.is_authenticated:
            UserActivity.objects.create(
                user=request.user,
                activity_type='share',
                points=5,
                description=f"Iqtibos ulashildi ({platform})"
            )
            
            stats = get_or_create_stats(request.user)
            stats.total_shares += 1
            stats.add_points(5)
        
        return JsonResponse({'success': True})
    except:
        return JsonResponse({'success': False})


# ===== GAMIFICATION VIEWS =====

@login_required
def leaderboard(request):
    """Eng faol o'quvchilar reytingi"""
    # Haftalik
    week_ago = timezone.now() - timedelta(days=7)
    
    weekly_leaders = UserStats.objects.filter(
        last_active_date__gte=week_ago.date()
    ).order_by('-total_points')[:20]
    
    # Umumiy
    all_time_leaders = UserStats.objects.order_by('-total_points')[:20]
    
    # Streak bo'yicha
    streak_leaders = UserStats.objects.order_by('-current_streak')[:10]
    
    context = {
        'weekly_leaders': weekly_leaders,
        'all_time_leaders': all_time_leaders,
        'streak_leaders': streak_leaders,
    }
    return render(request, 'blog/leaderboard.html', context)


@login_required
def my_badges(request):
    """Mening yutuqlarim"""
    badges = UserBadge.objects.filter(user=request.user).order_by('-earned_at')
    stats = get_or_create_stats(request.user)
    
    # Mavjud barcha badge turlari
    all_badge_types = dict(UserBadge.BADGE_TYPES)
    earned_types = set(badges.values_list('badge_type', flat=True))
    
    context = {
        'badges': badges,
        'stats': stats,
        'all_badges': all_badge_types,
        'earned_types': earned_types,
    }
    return render(request, 'blog/my_badges.html', context)


def check_and_award_badges(user):
    """Badge'larni tekshirish va berish"""
    stats = get_or_create_stats(user)
    
    badge_conditions = {
        'reader_1': stats.total_books_read >= 1,
        'reader_10': stats.total_books_read >= 10,
        'reader_50': stats.total_books_read >= 50,
        'reader_100': stats.total_books_read >= 100,
        'reviewer': stats.total_reviews >= 10,
        'sharer': stats.total_shares >= 20,
        'streak_7': stats.longest_streak >= 7,
        'streak_30': stats.longest_streak >= 30,
    }
    
    for badge_type, condition in badge_conditions.items():
        if condition:
            UserBadge.objects.get_or_create(user=user, badge_type=badge_type)


# ===== UTILITY FUNCTIONS =====

def subscription_context_processor(request):
    """Template context processor - barcha sahifalarda obuna ma'lumoti"""
    context = {
        'user_subscription': None,
        'is_premium': False,
        'can_read': True,
        'can_use_ai': True,
    }
    
    if request.user.is_authenticated:
        subscription = get_or_create_subscription(request.user)
        context['user_subscription'] = subscription
        context['is_premium'] = subscription.is_premium()
        context['can_read'] = subscription.can_read_book()
        context['can_use_ai'] = subscription.can_use_ai()
    
    return context
