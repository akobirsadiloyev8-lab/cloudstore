"""
Custom Middleware
Logging, caching, xavfsizlik
"""
import logging
import time
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    """Barcha so'rovlarni log qilish"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Request boshlanish vaqti
        start_time = time.time()
        
        # Response olish
        response = self.get_response(request)
        
        # Vaqtni hisoblash
        duration = time.time() - start_time
        
        # Log qilish (faqat 500ms dan uzoq so'rovlarni yoki xatoliklarni)
        if duration > 0.5 or response.status_code >= 400:
            user = request.user.username if request.user.is_authenticated else 'anonymous'
            logger.info(
                f"REQUEST: {request.method} {request.path} | "
                f"User: {user} | Status: {response.status_code} | "
                f"Duration: {duration:.3f}s"
            )
        
        return response


class OnlineStatusMiddleware:
    """Foydalanuvchi online statusini yangilash"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Faqat authenticated users uchun
        if request.user.is_authenticated:
            try:
                profile = request.user.social_profile
                # Har 5 daqiqada yangilash (performance uchun)
                if not profile.last_seen or (timezone.now() - profile.last_seen).seconds > 300:
                    profile.is_online = True
                    profile.last_seen = timezone.now()
                    profile.save(update_fields=['is_online', 'last_seen'])
            except Exception:
                pass
        
        return response


class SecurityHeadersMiddleware:
    """Xavfsizlik headerlari"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Xavfsizlik headerlari
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # HSTS (faqat production'da)
        if not settings.DEBUG:
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response
