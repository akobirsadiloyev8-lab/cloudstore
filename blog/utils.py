"""
Utility functions va xavfsizlik
"""
import os
import logging
from functools import wraps
from django.core.cache import cache
from django.http import JsonResponse
from django.conf import settings

# python-magic optional
try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False

logger = logging.getLogger(__name__)


# ===== RATE LIMITING =====

def rate_limit(key_prefix, limit=10, period=60):
    """
    Rate limiting dekoratori
    :param key_prefix: Cache kaliti prefiksi
    :param limit: Ruxsat berilgan so'rovlar soni
    :param period: Vaqt oynasi (sekundlarda)
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # IP yoki foydalanuvchi asosida kalit
            if request.user.is_authenticated:
                identifier = f"user_{request.user.id}"
            else:
                identifier = f"ip_{get_client_ip(request)}"
            
            cache_key = f"ratelimit:{key_prefix}:{identifier}"
            
            # Joriy so'rovlar sonini olish
            current = cache.get(cache_key, 0)
            
            if current >= limit:
                logger.warning(f"Rate limit exceeded for {identifier} on {key_prefix}")
                return JsonResponse({
                    'error': "Juda ko'p so'rov. Biroz kuting.",
                    'retry_after': period
                }, status=429)
            
            # Sonni oshirish
            cache.set(cache_key, current + 1, period)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def get_client_ip(request):
    """Mijoz IP manzilini olish"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip


# ===== FILE SECURITY =====

# Ruxsat berilgan fayl turlari
ALLOWED_IMAGE_TYPES = {
    'image/jpeg': ['.jpg', '.jpeg'],
    'image/png': ['.png'],
    'image/gif': ['.gif'],
    'image/webp': ['.webp'],
}

ALLOWED_DOCUMENT_TYPES = {
    'application/pdf': ['.pdf'],
    'application/msword': ['.doc'],
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    'application/vnd.ms-excel': ['.xls'],
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
    'application/vnd.ms-powerpoint': ['.ppt'],
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
    'text/plain': ['.txt'],
    'application/zip': ['.zip'],
    'application/x-rar-compressed': ['.rar'],
}

ALLOWED_CHAT_FILES = {**ALLOWED_IMAGE_TYPES, **ALLOWED_DOCUMENT_TYPES}

# Maksimal fayl hajmlari (bytes)
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_DOCUMENT_SIZE = 50 * 1024 * 1024  # 50MB
MAX_CHAT_FILE_SIZE = 20 * 1024 * 1024  # 20MB


def validate_file_type(file, allowed_types=None):
    """
    Fayl turini tekshirish (MIME type va kengaytma)
    :param file: UploadedFile
    :param allowed_types: Ruxsat berilgan MIME turlari dict
    :return: (is_valid, error_message)
    """
    if allowed_types is None:
        allowed_types = ALLOWED_CHAT_FILES
    
    # Fayl kengaytmasini olish
    file_ext = os.path.splitext(file.name)[1].lower()
    
    # MIME turini tekshirish (file signature orqali)
    try:
        # Faylning boshini o'qish
        file.seek(0)
        file_header = file.read(2048)
        file.seek(0)
        
        # python-magic yordamida haqiqiy turni aniqlash (agar mavjud bo'lsa)
        if HAS_MAGIC:
            try:
                mime = magic.from_buffer(file_header, mime=True)
            except Exception:
                mime = file.content_type
        else:
            # magic kutubxonasi yo'q, content_type dan foydalanish
            mime = file.content_type
        
        # MIME turi ruxsat berilganlar ichidami
        if mime not in allowed_types:
            logger.warning(f"Invalid file type: {mime} for file {file.name}")
            return False, f"Bu fayl turi ruxsat berilmagan: {mime}"
        
        # Kengaytma MIME turiga mosmi
        allowed_extensions = allowed_types.get(mime, [])
        if file_ext not in allowed_extensions:
            logger.warning(f"Extension mismatch: {file_ext} vs {allowed_extensions}")
            return False, f"Fayl kengaytmasi mos emas"
        
        return True, None
        
    except Exception as e:
        logger.error(f"File validation error: {e}")
        return False, "Faylni tekshirishda xatolik"


def validate_file_size(file, max_size=None):
    """
    Fayl hajmini tekshirish
    :param file: UploadedFile
    :param max_size: Maksimal hajm (bytes)
    :return: (is_valid, error_message)
    """
    if max_size is None:
        max_size = MAX_CHAT_FILE_SIZE
    
    if file.size > max_size:
        max_mb = max_size / (1024 * 1024)
        file_mb = file.size / (1024 * 1024)
        return False, f"Fayl juda katta: {file_mb:.1f}MB (max: {max_mb:.0f}MB)"
    
    return True, None


def validate_uploaded_file(file, file_type='chat'):
    """
    To'liq fayl validatsiyasi
    :param file: UploadedFile
    :param file_type: 'image', 'document', 'chat'
    :return: (is_valid, error_message)
    """
    if not file:
        return False, "Fayl topilmadi"
    
    # Fayl turi va hajmini belgilash
    if file_type == 'image':
        allowed_types = ALLOWED_IMAGE_TYPES
        max_size = MAX_IMAGE_SIZE
    elif file_type == 'document':
        allowed_types = ALLOWED_DOCUMENT_TYPES
        max_size = MAX_DOCUMENT_SIZE
    else:
        allowed_types = ALLOWED_CHAT_FILES
        max_size = MAX_CHAT_FILE_SIZE
    
    # Hajmni tekshirish
    is_valid, error = validate_file_size(file, max_size)
    if not is_valid:
        return False, error
    
    # Turni tekshirish
    is_valid, error = validate_file_type(file, allowed_types)
    if not is_valid:
        return False, error
    
    return True, None


def sanitize_filename(filename):
    """Fayl nomini xavfsiz qilish"""
    import re
    import unicodedata
    
    # Unicode normalizatsiya
    filename = unicodedata.normalize('NFKD', filename)
    
    # Xavfli belgilarni olib tashlash
    filename = re.sub(r'[^\w\s\-\.]', '', filename)
    
    # Bo'shliqlarni _ bilan almashtirish
    filename = re.sub(r'\s+', '_', filename)
    
    # Boshida va oxirida nuqtalarni olib tashlash
    filename = filename.strip('.')
    
    # Maksimal uzunlik
    if len(filename) > 100:
        name, ext = os.path.splitext(filename)
        filename = name[:95] + ext
    
    return filename or 'file'


# ===== LOGGING HELPERS =====

def log_user_action(user, action, details=None):
    """Foydalanuvchi harakatini log qilish"""
    log_data = {
        'user_id': user.id if user and user.is_authenticated else None,
        'username': user.username if user and user.is_authenticated else 'anonymous',
        'action': action,
    }
    if details:
        log_data['details'] = details
    
    logger.info(f"USER_ACTION: {log_data}")


# ===== CACHE HELPERS =====

def cache_user_data(user_id, data, timeout=300):
    """Foydalanuvchi ma'lumotlarini cache qilish"""
    cache_key = f"user_data:{user_id}"
    cache.set(cache_key, data, timeout)


def get_cached_user_data(user_id):
    """Cache'dan foydalanuvchi ma'lumotlarini olish"""
    cache_key = f"user_data:{user_id}"
    return cache.get(cache_key)


def invalidate_user_cache(user_id):
    """Foydalanuvchi cache'ini tozalash"""
    cache_key = f"user_data:{user_id}"
    cache.delete(cache_key)
