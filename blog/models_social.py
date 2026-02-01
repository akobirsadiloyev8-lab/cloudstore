"""
Ijtimoiy Tarmoq Modellari
Foydalanuvchilarni qidirish, kuzatish va do'stlik tizimi
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UserProfile(models.Model):
    """Foydalanuvchi profili - kengaytirilgan ma'lumotlar"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='social_profile')
    bio = models.TextField(max_length=500, blank=True, verbose_name="Bio")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="Profil rasmi")
    location = models.CharField(max_length=100, blank=True, verbose_name="Joylashuv")
    website = models.URLField(blank=True, verbose_name="Veb sayt")
    
    # Qiziqishlar
    favorite_genres = models.CharField(max_length=300, blank=True, verbose_name="Sevimli janrlar")
    favorite_author = models.CharField(max_length=200, blank=True, verbose_name="Sevimli muallif")
    
    # Statistika
    books_read = models.PositiveIntegerField(default=0, verbose_name="O'qilgan kitoblar")
    reviews_count = models.PositiveIntegerField(default=0, verbose_name="Sharhlar soni")
    
    # Online status
    is_online = models.BooleanField(default=False, verbose_name="Online")
    last_seen = models.DateTimeField(null=True, blank=True, verbose_name="Oxirgi faollik")
    
    # Typing status (yozmoqda...)
    is_typing_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                      related_name='typing_users', verbose_name="Kimga yozmoqda")
    typing_started_at = models.DateTimeField(null=True, blank=True)
    
    # Sozlamalar
    is_public = models.BooleanField(default=True, verbose_name="Profil ochiq")
    show_reading_activity = models.BooleanField(default=True, verbose_name="O'qish faoliyatini ko'rsatish")
    allow_messages = models.BooleanField(default=True, verbose_name="Xabarlarga ruxsat")
    show_online_status = models.BooleanField(default=True, verbose_name="Online statusni ko'rsatish")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Foydalanuvchi profili"
        verbose_name_plural = "Foydalanuvchi profillari"
    
    def __str__(self):
        return f"{self.user.username} profili"
    
    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return "/static/blog/default-avatar.png"
    
    def followers_count(self):
        return self.user.followers.count()
    
    def following_count(self):
        return self.user.following.count()
    
    def update_online_status(self):
        """Online statusni yangilash"""
        self.is_online = True
        self.last_seen = timezone.now()
        self.save(update_fields=['is_online', 'last_seen'])
    
    def set_offline(self):
        """Offline qilish"""
        self.is_online = False
        self.last_seen = timezone.now()
        self.is_typing_to = None
        self.save(update_fields=['is_online', 'last_seen', 'is_typing_to'])
    
    def get_online_status_display(self):
        """Online statusni ko'rsatish"""
        if not self.show_online_status:
            return ""
        if self.is_online:
            return "Online"
        if self.last_seen:
            now = timezone.now()
            diff = now - self.last_seen
            if diff.seconds < 60:
                return "Hozirgina"
            elif diff.seconds < 3600:
                minutes = diff.seconds // 60
                return f"{minutes} daqiqa oldin"
            elif diff.seconds < 86400:
                hours = diff.seconds // 3600
                return f"{hours} soat oldin"
            else:
                days = diff.days
                return f"{days} kun oldin"
        return "Uzoq vaqt oldin"
    
    def start_typing(self, to_user):
        """Yozmoqda statusini boshlash"""
        self.is_typing_to = to_user
        self.typing_started_at = timezone.now()
        self.save(update_fields=['is_typing_to', 'typing_started_at'])
    
    def stop_typing(self):
        """Yozmoqda statusini to'xtatish"""
        self.is_typing_to = None
        self.typing_started_at = None
        self.save(update_fields=['is_typing_to', 'typing_started_at'])


class Follow(models.Model):
    """Kuzatish tizimi"""
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following', verbose_name="Kuzatuvchi")
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers', verbose_name="Kuzatilayotgan")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Kuzatish"
        verbose_name_plural = "Kuzatishlar"
        unique_together = ('follower', 'following')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.follower.username} → {self.following.username}"


class Message(models.Model):
    """Xabar tizimi - kengaytirilgan"""
    MESSAGE_TYPES = [
        ('text', 'Matn'),
        ('image', 'Rasm'),
        ('file', 'Fayl'),
        ('voice', 'Ovozli xabar'),
    ]
    
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages', verbose_name="Jo'natuvchi")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages', verbose_name="Qabul qiluvchi")
    content = models.TextField(verbose_name="Xabar matni", blank=True)
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text', verbose_name="Xabar turi")
    
    # Fayl/Rasm uchun
    file = models.FileField(upload_to='chat_files/', blank=True, null=True, verbose_name="Fayl")
    file_name = models.CharField(max_length=255, blank=True, verbose_name="Fayl nomi")
    file_size = models.PositiveIntegerField(default=0, verbose_name="Fayl hajmi (bytes)")
    
    # Status
    is_read = models.BooleanField(default=False, verbose_name="O'qilgan")
    is_deleted_by_sender = models.BooleanField(default=False, verbose_name="Jo'natuvchi o'chirgan")
    is_deleted_by_receiver = models.BooleanField(default=False, verbose_name="Qabul qiluvchi o'chirgan")
    is_deleted_for_everyone = models.BooleanField(default=False, verbose_name="Hammadan o'chirilgan")
    
    # Reply (javob)
    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies', verbose_name="Javob")
    
    # Vaqt
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True, verbose_name="Tahrirlangan")
    
    class Meta:
        verbose_name = "Xabar"
        verbose_name_plural = "Xabarlar"
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender.username} → {self.receiver.username}: {self.content[:50] if self.content else self.message_type}"
    
    def is_visible_to(self, user):
        """Xabar foydalanuvchiga ko'rinadimi"""
        if self.is_deleted_for_everyone:
            return False
        if user == self.sender and self.is_deleted_by_sender:
            return False
        if user == self.receiver and self.is_deleted_by_receiver:
            return False
        return True
    
    def get_file_extension(self):
        """Fayl kengaytmasini olish"""
        if self.file:
            return self.file.name.split('.')[-1].lower()
        return ''
    
    def is_image(self):
        """Rasm ekanligini tekshirish"""
        return self.get_file_extension() in ['jpg', 'jpeg', 'png', 'gif', 'webp']
    
    def format_file_size(self):
        """Fayl hajmini formatlash"""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        else:
            return f"{self.file_size / (1024 * 1024):.1f} MB"


class ReadingActivity(models.Model):
    """O'qish faoliyati - nima o'qiyotganini ko'rsatish"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reading_activities')
    book = models.ForeignKey('Book', on_delete=models.CASCADE, related_name='social_readers')
    status = models.CharField(max_length=20, choices=[
        ('reading', "O'qiyapman"),
        ('completed', "Tugatdim"),
        ('want_to_read', "O'qimoqchiman"),
        ('paused', "To'xtatilgan"),
    ], default='reading')
    progress = models.PositiveIntegerField(default=0, verbose_name="Foiz")  # 0-100
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "O'qish faoliyati"
        verbose_name_plural = "O'qish faoliyatlari"
        unique_together = ('user', 'book')
    
    def __str__(self):
        return f"{self.user.username}: {self.book.title} ({self.status})"


class BookReview(models.Model):
    """Kitob sharhlari"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='book_reviews')
    book = models.ForeignKey('Book', on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(choices=[(i, str(i)) for i in range(1, 6)], verbose_name="Baho")
    content = models.TextField(verbose_name="Sharh matni")
    likes_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Kitob sharhi"
        verbose_name_plural = "Kitob sharhlari"
        unique_together = ('user', 'book')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username}: {self.book.title} - {self.rating}⭐"


class ReviewLike(models.Model):
    """Sharh like"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    review = models.ForeignKey(BookReview, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'review')
