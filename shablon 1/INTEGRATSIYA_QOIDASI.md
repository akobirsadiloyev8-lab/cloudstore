# AdminUX Shablonini Django ga Integratsiya Qilish

## 📁 Yaratilgan Fayllar:

1. **django_base.html** - Django uchun tayyor base template
2. **misol_kitoblar_sahifa.html** - Qanday ishlatishga misol

## 🚀 Integratsiya Qadamlari:

### 1. Static Fayllarni Ko'chirish

AdminUX assets papkasidagi fayllarni Django static papkaga ko'chiring:

```bash
# PowerShell buyruqlari:
cd "D:\study_file\mysite\shablon 1\cloudstore2\adminuiux.com\adminuiux\adminux-mobile\html"

# CSS fayllarni ko'chirish
Copy-Item -Path "assets\css\*" -Destination "D:\study_file\mysite\blog\static\adminux\css\" -Recurse -Force

# JavaScript fayllarni ko'chirish
Copy-Item -Path "assets\js\*" -Destination "D:\study_file\mysite\blog\static\adminux\js\" -Recurse -Force

# Rasm fayllarni ko'chirish
Copy-Item -Path "assets\img\*" -Destination "D:\study_file\mysite\blog\static\adminux\img\" -Recurse -Force
```

### 2. Template Fayllarni Ko'chirish

```bash
# django_base.html ni blog/templates/blog/ ga ko'chirish
Copy-Item -Path "D:\study_file\mysite\shablon 1\django_base.html" -Destination "D:\study_file\mysite\blog\templates\blog\base.html"
```

### 3. URL Marshrutlarini Sozlash

**blog/urls.py** da quyidagi URL'larni qo'shing:

```python
from django.urls import path
from . import views

urlpatterns = [
    path('', views.bosh_sahifa, name='bosh_sahifa'),
    path('kitoblar/', views.kitoblar, name='kitoblar'),
    path('kitob/<int:pk>/', views.kitob_detail, name='kitob_detail'),
    path('mualliflar/', views.mualliflar, name='mualliflar'),
    path('kategoriyalar/', views.kategoriyalar, name='kategoriyalar'),
    path('my-library/', views.my_library, name='my_library'),
    path('downloads/', views.downloads, name='downloads'),
    path('food-diary/', views.food_diary, name='food_diary'),
    path('yordam/', views.yordam, name='yordam'),
    path('aloqa/', views.aloqa, name='aloqa'),
    path('maxfiylik/', views.maxfiylik, name='maxfiylik'),
    
    # Admin
    path('kitob/qoshish/', views.kitob_qoshish, name='kitob_qoshish'),
    path('kitob/<int:pk>/download/', views.download_book, name='download_book'),
    
    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
]
```

### 4. Context Processor Qo'shish

**mysite/settings.py** da `current_year` uchun context processor qo'shing:

```python
# settings.py
TEMPLATES = [
    {
        'OPTIONS': {
            'context_processors': [
                # ... mavjud processorlar
                'blog.context_processors.current_year',
            ],
        },
    },
]
```

**blog/context_processors.py** yarating:

```python
from datetime import datetime

def current_year(request):
    return {
        'current_year': datetime.now().year
    }
```

### 5. Static Papka Strukturasi

Ko'chirishdan keyin struktura:

```
blog/static/
├── adminux/
│   ├── css/
│   │   └── app.css
│   ├── js/
│   │   └── app.js
│   └── img/
│       ├── logo.svg
│       ├── logo-light.svg
│       └── favicon.png
└── blog/
    ├── css/
    │   ├── base.css (eski - olib tashlash mumkin)
    │   └── food_diary.css
    └── js/
        └── ... (eski fayllar)
```

### 6. Yangi Sahifa Yaratish

Yangi sahifa uchun (masalan, kitoblar.html):

```django
{% extends 'blog/base.html' %}
{% load static %}

{% block title %}Kitoblar - Cloudstore{% endblock %}

{% block extra_css %}
<style>
    /* Sahifa uchun maxsus CSS */
</style>
{% endblock %}

{% block content %}
<div class="row">
    <div class="col-12">
        <h1>Kitoblar</h1>
        <!-- Sahifa contenti -->
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
    // Sahifa uchun maxsus JavaScript
</script>
{% endblock %}
```

## ⚙️ Sozlamalar

### Bootstrap Icons Qo'shish

AdminUX Bootstrap Icons ishlatadi. CDN qo'shing yoki local yuklab oling:

**base.html** `<head>` qismiga qo'shing:

```html
<!-- Bootstrap Icons -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
```

### Django Messages Tag Mapping

**settings.py** ga qo'shing:

```python
from django.contrib.messages import constants as messages

MESSAGE_TAGS = {
    messages.DEBUG: 'info',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}
```

## 🎨 Mavzularni Sozlash

AdminUX 14+ rang sxemalari bilan keladi:

```html
<body class="theme-blue">     <!-- Ko'k (default) -->
<body class="theme-green">    <!-- Yashil -->
<body class="theme-purple">   <!-- Binafsha -->
<body class="theme-red">      <!-- Qizil -->
<body class="theme-orange">   <!-- To'q sariq -->
```

## 📝 Muhim Eslatmalar:

1. **Static fayllar hajmi:** ~5-10 MB
2. **AdminUX CSS/JS ishlatadi:** Bootstrap 5 + Admin komponentlar
3. **PWA qo'llab-quvvatlash:** Service Worker bilan
4. **Dark/Light mode:** Avtomatik
5. **Responsive:** Mobile-first dizayn

## 🔧 Muammolarni Hal Qilish:

### Static fayllar yuklanmayapti:

```bash
python manage.py collectstatic --noinput
```

### CSS/JS ishlmayapti:

`settings.py` da tekshiring:

```python
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'blog' / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

### URL xatolari:

Barcha URL'lar `blog/urls.py` da mavjudligini tekshiring.

## ✅ Integratsiya Checklist:

- [ ] Static fayllar ko'chirildi (css, js, img)
- [ ] django_base.html → blog/templates/blog/base.html
- [ ] URL marshrutlari qo'shildi
- [ ] Context processor sozlandi
- [ ] Bootstrap Icons qo'shildi
- [ ] MESSAGE_TAGS sozlandi
- [ ] collectstatic bajarildi
- [ ] Server qayta ishga tushirildi
- [ ] Test qilindi

## 🎯 Keyingi Qadamlar:

1. Logo va favicon rasmlarini almashtiring
2. Rang sxemasini tanlang (theme-blue, theme-green, ...)
3. Sidebar menyusini o'z ehtiyojingizga moslashtiring
4. Har bir sahifa uchun view yarating
5. Kitoblar, mualliflar sahifalarini tuzing

---

**Muallif:** AI Assistant  
**Sana:** 2026-02-19  
**Versiya:** 1.0
