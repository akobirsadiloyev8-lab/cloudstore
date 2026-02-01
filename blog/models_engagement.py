"""
Foydalanuvchi Jalb Qilish Tizimi - Models
Kunlik bonus, omad g'ildiragi, topshiriqlar
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import random


class DailyBonus(models.Model):
    """Kunlik kirish bonusi"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_bonuses')
    date = models.DateField(auto_now_add=True)
    points = models.PositiveIntegerField(default=10)
    streak_day = models.PositiveIntegerField(default=1)  # Ketma-ket nechanchi kun
    streak_multiplier = models.FloatField(default=1.0)  # Ko'paytiruvchi
    
    class Meta:
        verbose_name = "Kunlik bonus"
        verbose_name_plural = "Kunlik bonuslar"
        unique_together = ('user', 'date')
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.user.username} - {self.date} - {self.points} ball"


class SpinWheel(models.Model):
    """Omad g'ildiragi"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='spin_wheels')
    date = models.DateField(auto_now_add=True)
    prize_type = models.CharField(max_length=50, choices=[
        ('points_10', '10 ball'),
        ('points_25', '25 ball'),
        ('points_50', '50 ball'),
        ('points_100', '100 ball'),
        ('premium_1', '1 kun Premium'),
        ('premium_3', '3 kun Premium'),
        ('premium_7', '7 kun Premium'),
        ('book_access', 'Premium kitob'),
        ('nothing', 'Keyingi safar omad!'),
        ('double_next', 'Keyingi 2x bonus'),
    ])
    prize_value = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Omad g'ildiragi"
        verbose_name_plural = "Omad g'ildiraklari"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_prize_type_display()}"


class DailyTask(models.Model):
    """Kunlik topshiriq turi"""
    title = models.CharField(max_length=200, verbose_name="Sarlavha")
    description = models.TextField(verbose_name="Tavsif")
    task_type = models.CharField(max_length=50, choices=[
        ('read_book', 'Kitob o\'qish'),
        ('read_pages', 'Sahifalar o\'qish'),
        ('rate_book', 'Kitob baholash'),
        ('add_favorite', 'Sevimlilarga qo\'shish'),
        ('send_message', 'Xabar yuborish'),
        ('follow_user', 'Foydalanuvchi kuzatish'),
        ('share_book', 'Kitob ulashish'),
        ('login', 'Saytga kirish'),
        ('profile_complete', 'Profilni to\'ldirish'),
        ('ai_chat', 'AI bilan suhbat'),
    ])
    points_reward = models.PositiveIntegerField(default=20, verbose_name="Ball mukofoti")
    target_count = models.PositiveIntegerField(default=1, verbose_name="Maqsad soni")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Kunlik topshiriq"
        verbose_name_plural = "Kunlik topshiriqlar"
    
    def __str__(self):
        return self.title


class UserDailyTask(models.Model):
    """Foydalanuvchining kunlik topshirig'i"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_tasks')
    task = models.ForeignKey(DailyTask, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    progress = models.PositiveIntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    is_claimed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Foydalanuvchi topshirig'i"
        verbose_name_plural = "Foydalanuvchi topshiriqlari"
        unique_together = ('user', 'task', 'date')
    
    def __str__(self):
        status = "✅" if self.is_completed else f"{self.progress}/{self.task.target_count}"
        return f"{self.user.username} - {self.task.title} - {status}"
    
    def check_completion(self):
        if self.progress >= self.task.target_count and not self.is_completed:
            self.is_completed = True
            self.completed_at = timezone.now()
            self.save()
        return self.is_completed


class UserStreak(models.Model):
    """Foydalanuvchi streak (ketma-ket kunlar)"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='streak')
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)
    total_points = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = "Foydalanuvchi streak"
        verbose_name_plural = "Foydalanuvchi streaklari"
    
    def __str__(self):
        return f"{self.user.username} - {self.current_streak} kun"
    
    def update_streak(self):
        today = timezone.now().date()
        
        if self.last_activity_date is None:
            # Birinchi marta
            self.current_streak = 1
        elif self.last_activity_date == today:
            # Bugun allaqachon kirilgan
            return self.current_streak
        elif self.last_activity_date == today - timedelta(days=1):
            # Ketma-ket kun
            self.current_streak += 1
        else:
            # Streak uzildi
            self.current_streak = 1
        
        self.last_activity_date = today
        
        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak
        
        self.save()
        return self.current_streak
    
    def get_multiplier(self):
        """Streak bo'yicha ko'paytiruvchi"""
        if self.current_streak >= 30:
            return 3.0  # 30+ kun - 3x
        elif self.current_streak >= 14:
            return 2.0  # 14+ kun - 2x
        elif self.current_streak >= 7:
            return 1.5  # 7+ kun - 1.5x
        return 1.0


class Notification(models.Model):
    """Bildirishnomalar"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=50, choices=[
        ('bonus', 'Bonus'),
        ('streak', 'Streak'),
        ('task', 'Topshiriq'),
        ('spin', 'Omad g\'ildiragi'),
        ('follow', 'Yangi kuzatuvchi'),
        ('message', 'Yangi xabar'),
        ('system', 'Tizim'),
    ])
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    link = models.CharField(max_length=200, blank=True)
    
    class Meta:
        verbose_name = "Bildirishnoma"
        verbose_name_plural = "Bildirishnomalar"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
