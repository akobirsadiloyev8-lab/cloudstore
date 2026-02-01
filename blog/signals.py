"""
Django Signals
Avtomatik profile yaratish va boshqa hodisalar
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

from .models_social import UserProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Yangi foydalanuvchi yaratilganda avtomatik profil yaratish"""
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Foydalanuvchi saqlanganida profilni ham saqlash"""
    try:
        instance.social_profile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=instance)
