"""
Foydalanuvchi Jalb Qilish Tizimi - Views
Kunlik bonus, omad g'ildiragi, topshiriqlar
"""
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.contrib import messages
from datetime import timedelta
import random
import json

from .models_engagement import (
    DailyBonus, SpinWheel, DailyTask, UserDailyTask, 
    UserStreak, Notification
)
from .models_subscription import UserSubscription


def get_or_create_streak(user):
    """Streak olish yoki yaratish"""
    streak, created = UserStreak.objects.get_or_create(user=user)
    return streak


@login_required
def daily_rewards(request):
    """Kunlik mukofotlar sahifasi"""
    today = timezone.now().date()
    streak = get_or_create_streak(request.user)
    
    # Bugun bonus olindimi?
    daily_bonus = DailyBonus.objects.filter(user=request.user, date=today).first()
    can_claim_bonus = daily_bonus is None
    
    # Bugun g'ildirak aylantirilganmi?
    spin_today = SpinWheel.objects.filter(user=request.user, date=today).first()
    can_spin = spin_today is None
    
    # Kunlik topshiriqlar
    user_tasks = UserDailyTask.objects.filter(user=request.user, date=today).select_related('task')
    
    # Agar topshiriqlar yo'q bo'lsa, tasodifiy 3 ta topshiriq tanlash
    if not user_tasks.exists():
        all_tasks = list(DailyTask.objects.filter(is_active=True))
        if all_tasks:
            selected_tasks = random.sample(all_tasks, min(3, len(all_tasks)))
            for task in selected_tasks:
                UserDailyTask.objects.create(user=request.user, task=task, date=today)
            user_tasks = UserDailyTask.objects.filter(user=request.user, date=today).select_related('task')
    
    # Jami topshiriq progressi
    completed_tasks = user_tasks.filter(is_completed=True).count()
    total_tasks = user_tasks.count()
    
    # Oxirgi 7 kunlik bonus tarixi
    bonus_history = DailyBonus.objects.filter(user=request.user).order_by('-date')[:7]
    
    # Oxirgi spin natijalari
    recent_spins = SpinWheel.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    context = {
        'streak': streak,
        'can_claim_bonus': can_claim_bonus,
        'daily_bonus': daily_bonus,
        'can_spin': can_spin,
        'spin_today': spin_today,
        'user_tasks': user_tasks,
        'completed_tasks': completed_tasks,
        'total_tasks': total_tasks,
        'bonus_history': bonus_history,
        'recent_spins': recent_spins,
    }
    return render(request, 'blog/engagement/daily_rewards.html', context)


@login_required
@require_POST
def claim_daily_bonus(request):
    """Kunlik bonusni olish"""
    today = timezone.now().date()
    
    # Allaqachon olindimi?
    if DailyBonus.objects.filter(user=request.user, date=today).exists():
        return JsonResponse({'success': False, 'message': 'Bugun bonus allaqachon olindi!'})
    
    # Streak yangilash
    streak = get_or_create_streak(request.user)
    streak_day = streak.update_streak()
    multiplier = streak.get_multiplier()
    
    # Bonus hisoblash (asosiy + streak bonus)
    base_points = 10
    streak_bonus = min(streak_day, 7) * 2  # Har kun +2, maks 14
    total_points = int((base_points + streak_bonus) * multiplier)
    
    # Bonus yaratish
    bonus = DailyBonus.objects.create(
        user=request.user,
        points=total_points,
        streak_day=streak_day,
        streak_multiplier=multiplier
    )
    
    # Jami ballni yangilash
    streak.total_points += total_points
    streak.save()
    
    # Bildirishnoma
    Notification.objects.create(
        user=request.user,
        title="Kunlik bonus olindi! 🎁",
        message=f"{total_points} ball qo'shildi. Streak: {streak_day} kun!",
        notification_type='bonus'
    )
    
    return JsonResponse({
        'success': True,
        'points': total_points,
        'streak_day': streak_day,
        'multiplier': multiplier,
        'total_points': streak.total_points,
        'message': f"🎉 {total_points} ball oldingiz! Streak: {streak_day} kun"
    })


@login_required
@require_POST
def spin_wheel(request):
    """Omad g'ildiragini aylantirish"""
    today = timezone.now().date()
    
    # Bugun aylantirilganmi?
    if SpinWheel.objects.filter(user=request.user, date=today).exists():
        return JsonResponse({'success': False, 'message': 'Bugun allaqachon aylantirilgan!'})
    
    # Sovg'alar va ehtimollar
    prizes = [
        ('points_10', 10, 25),      # 25% - 10 ball
        ('points_25', 25, 20),      # 20% - 25 ball
        ('points_50', 50, 15),      # 15% - 50 ball
        ('points_100', 100, 5),     # 5% - 100 ball
        ('premium_1', 1, 10),       # 10% - 1 kun premium
        ('premium_3', 3, 5),        # 5% - 3 kun premium
        ('premium_7', 7, 2),        # 2% - 7 kun premium
        ('nothing', 0, 15),         # 15% - hech narsa
        ('double_next', 2, 3),      # 3% - keyingi 2x
    ]
    
    # Tasodifiy tanlash (og'irlikli)
    total_weight = sum(p[2] for p in prizes)
    r = random.randint(1, total_weight)
    
    current_weight = 0
    selected_prize = prizes[0]
    for prize in prizes:
        current_weight += prize[2]
        if r <= current_weight:
            selected_prize = prize
            break
    
    prize_type, prize_value, _ = selected_prize
    
    # Spin yaratish
    spin = SpinWheel.objects.create(
        user=request.user,
        prize_type=prize_type,
        prize_value=prize_value
    )
    
    # Mukofotni qo'llash
    streak = get_or_create_streak(request.user)
    message = ""
    
    if prize_type.startswith('points_'):
        streak.total_points += prize_value
        streak.save()
        message = f"🎉 {prize_value} ball yutdingiz!"
    
    elif prize_type.startswith('premium_'):
        # Premium kunlar qo'shish
        try:
            subscription = UserSubscription.objects.get(user=request.user)
            if subscription.expires_at:
                subscription.expires_at += timedelta(days=prize_value)
            else:
                subscription.expires_at = timezone.now() + timedelta(days=prize_value)
            subscription.save()
            message = f"🌟 {prize_value} kun Premium yutdingiz!"
        except UserSubscription.DoesNotExist:
            streak.total_points += prize_value * 10
            streak.save()
            message = f"🎁 {prize_value * 10} ball yutdingiz!"
    
    elif prize_type == 'nothing':
        message = "😅 Keyingi safar omad! Ertaga yana urinib ko'ring."
    
    elif prize_type == 'double_next':
        message = "⚡ Keyingi bonus 2x bo'ladi!"
    
    # Bildirishnoma
    Notification.objects.create(
        user=request.user,
        title="Omad g'ildiragi! 🎰",
        message=message,
        notification_type='spin'
    )
    
    return JsonResponse({
        'success': True,
        'prize_type': prize_type,
        'prize_value': prize_value,
        'prize_display': spin.get_prize_type_display(),
        'message': message,
        'total_points': streak.total_points
    })


@login_required
@require_POST
def claim_task_reward(request):
    """Topshiriq mukofotini olish"""
    data = json.loads(request.body)
    task_id = data.get('task_id')
    
    try:
        user_task = UserDailyTask.objects.get(
            id=task_id, 
            user=request.user,
            is_completed=True,
            is_claimed=False
        )
        
        # Mukofotni berish
        streak = get_or_create_streak(request.user)
        points = user_task.task.points_reward
        streak.total_points += points
        streak.save()
        
        user_task.is_claimed = True
        user_task.save()
        
        return JsonResponse({
            'success': True,
            'points': points,
            'total_points': streak.total_points,
            'message': f"🎁 {points} ball oldingiz!"
        })
        
    except UserDailyTask.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Topshiriq topilmadi'})


def update_task_progress(user, task_type, count=1):
    """Topshiriq progressini yangilash (boshqa viewlardan chaqiriladi)"""
    today = timezone.now().date()
    
    user_tasks = UserDailyTask.objects.filter(
        user=user,
        date=today,
        task__task_type=task_type,
        is_completed=False
    )
    
    for user_task in user_tasks:
        user_task.progress += count
        user_task.check_completion()
        user_task.save()
        
        if user_task.is_completed:
            Notification.objects.create(
                user=user,
                title="Topshiriq bajarildi! ✅",
                message=f"{user_task.task.title} - {user_task.task.points_reward} ball kutmoqda!",
                notification_type='task',
                link='/kunlik-mukofotlar/'
            )


@login_required
def notifications_list(request):
    """Bildirishnomalar ro'yxati"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:50]
    unread_count = notifications.filter(is_read=False).count()
    
    context = {
        'notifications': notifications,
        'unread_count': unread_count,
    }
    return render(request, 'blog/engagement/notifications.html', context)


@login_required
@require_POST
def mark_notification_read(request):
    """Bildirishnomani o'qilgan deb belgilash"""
    data = json.loads(request.body)
    notification_id = data.get('notification_id')
    
    if notification_id == 'all':
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    else:
        Notification.objects.filter(id=notification_id, user=request.user).update(is_read=True)
    
    return JsonResponse({'success': True})


@login_required
def get_unread_count(request):
    """O'qilmagan bildirishnomalar soni"""
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})
