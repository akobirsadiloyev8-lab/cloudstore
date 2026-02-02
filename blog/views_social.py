"""
Ijtimoiy Tarmoq Views
Foydalanuvchilarni qidirish, kuzatish, xabar yuborish
"""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from django.db.models import Q, Count, F, Prefetch, OuterRef, Subquery
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib import messages
from django.core.cache import cache
import json

from .models_social import UserProfile, Follow, Message, ReadingActivity, BookReview, ReviewLike
from .models import Book
from .utils import rate_limit, validate_uploaded_file, sanitize_filename, log_user_action

logger = logging.getLogger(__name__)


def get_or_create_profile(user):
    """Profil olish yoki yaratish"""
    try:
        return user.social_profile
    except UserProfile.DoesNotExist:
        profile, _ = UserProfile.objects.get_or_create(user=user)
        return profile


# ===== USER SEARCH & DISCOVERY =====

def search_users(request):
    """Foydalanuvchilarni qidirish - Optimized va birlashtirilgan"""
    query = request.GET.get('q', '').strip()
    filter_by = request.GET.get('filter', 'all')
    current_tab = request.GET.get('tab', 'all')
    
    # Tab tizimi bilan birlashtirish
    if current_tab == 'followers' and request.user.is_authenticated:
        # Mening kuzatuvchilarim
        follower_ids = Follow.objects.filter(following=request.user).values_list('follower_id', flat=True)
        users = User.objects.filter(id__in=follower_ids, is_active=True).select_related('social_profile')
    elif current_tab == 'following' and request.user.is_authenticated:
        # Men kuzatayotganlar
        following_ids_list = Follow.objects.filter(follower=request.user).values_list('following_id', flat=True)
        users = User.objects.filter(id__in=following_ids_list, is_active=True).select_related('social_profile')
    elif current_tab == 'discover' and request.user.is_authenticated:
        # Tavsiya qilinganlar - o'xshash qiziqishlar asosida
        # Foydalanuvchi o'qigan kitoblar
        my_books = set(ReadingActivity.objects.filter(user=request.user).values_list('book_id', flat=True))
        # Shu kitoblarni o'qigan boshqa foydalanuvchilar
        similar_users = ReadingActivity.objects.filter(
            book_id__in=my_books
        ).exclude(user=request.user).values_list('user_id', flat=True)
        # Men kuzatmaganlarni olish
        following_ids_list = Follow.objects.filter(follower=request.user).values_list('following_id', flat=True)
        users = User.objects.filter(
            id__in=similar_users, is_active=True
        ).exclude(id__in=following_ids_list).exclude(is_superuser=True).select_related('social_profile')
    else:
        # Barcha foydalanuvchilar
        users = User.objects.filter(is_active=True).exclude(is_superuser=True).select_related('social_profile')
    
    # Qidiruv
    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(social_profile__bio__icontains=query) |
            Q(social_profile__location__icontains=query)
        ).distinct()
    
    # Annotate follower/following counts bir marta
    users = users.annotate(
        annotated_follower_count=Count('followers', distinct=True),
        annotated_following_count=Count('following', distinct=True),
    )
    
    # Filter
    if filter_by == 'active':
        week_ago = timezone.now() - timezone.timedelta(days=7)
        users = users.filter(last_login__gte=week_ago)
    elif filter_by == 'top_readers':
        users = users.annotate(
            books_count=Count('reading_activities', distinct=True)
        ).order_by('-books_count')
    elif filter_by == 'most_followed':
        users = users.order_by('-annotated_follower_count')
    else:
        users = users.order_by('-date_joined')
    
    # Pagination
    paginator = Paginator(users, 20)
    page = request.GET.get('page', 1)
    users_page = paginator.get_page(page)
    
    # Kuzatish holatini bir marta olish (faqat authenticated users uchun)
    following_ids = set()
    if request.user.is_authenticated:
        following_ids = set(Follow.objects.filter(
            follower=request.user
        ).values_list('following_id', flat=True))
    
    # Natijalarni tayyorlash - N+1 yo'q
    users_with_profiles = []
    for user in users_page:
        try:
            profile = user.social_profile
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(user=user)
        
        users_with_profiles.append({
            'user': user,
            'profile': profile,
            'is_following': user.id in following_ids,
            'followers_count': user.annotated_follower_count,
            'following_count': user.annotated_following_count,
        })
    
    context = {
        'users': users_with_profiles,
        'query': query,
        'filter_by': filter_by,
        'page_obj': users_page,
        'total_count': paginator.count,
        'current_tab': current_tab,
    }
    return render(request, 'blog/social/search_users.html', context)


def user_profile_view(request, username):
    """Foydalanuvchi profilini ko'rish"""
    user = get_object_or_404(User, username=username, is_active=True)
    profile = get_or_create_profile(user)
    
    # Maxfiylik tekshirish
    is_owner = request.user == user
    can_view = profile.is_public or is_owner
    
    if not can_view and request.user.is_authenticated:
        # Kuzatayotganlar ko'ra oladi
        can_view = Follow.objects.filter(follower=request.user, following=user).exists()
    
    # Statistika
    is_following = False
    if request.user.is_authenticated and request.user != user:
        is_following = Follow.objects.filter(follower=request.user, following=user).exists()
    
    # O'qish faoliyati
    reading_activities = []
    if can_view and profile.show_reading_activity:
        reading_activities = ReadingActivity.objects.filter(user=user).select_related('book').order_by('-started_at')[:10]
    
    # Sharhlar
    reviews = BookReview.objects.filter(user=user).select_related('book').order_by('-created_at')[:5]
    
    # Kuzatuvchilar va kuzatilayotganlar
    followers = Follow.objects.filter(following=user).select_related('follower')[:12]
    following = Follow.objects.filter(follower=user).select_related('following')[:12]
    
    # O'xshash qiziqishlar
    mutual_books = []
    if request.user.is_authenticated and request.user != user:
        user_books = set(ReadingActivity.objects.filter(user=request.user).values_list('book_id', flat=True))
        other_books = set(ReadingActivity.objects.filter(user=user).values_list('book_id', flat=True))
        mutual_ids = user_books & other_books
        if mutual_ids:
            mutual_books = Book.objects.filter(id__in=list(mutual_ids)[:5])
    
    context = {
        'profile_user': user,
        'profile': profile,
        'is_owner': is_owner,
        'can_view': can_view,
        'is_following': is_following,
        'followers_count': user.followers.count(),
        'following_count': user.following.count(),
        'reading_activities': reading_activities,
        'reviews': reviews,
        'followers': followers,
        'following_list': following,
        'mutual_books': mutual_books,
    }
    return render(request, 'blog/social/user_profile.html', context)


@login_required
@require_POST
def toggle_follow(request, username):
    """Kuzatishni yoqish/o'chirish"""
    user_to_follow = get_object_or_404(User, username=username)
    
    if request.user == user_to_follow:
        return JsonResponse({'error': "O'zingizni kuzata olmaysiz"}, status=400)
    
    follow, created = Follow.objects.get_or_create(
        follower=request.user,
        following=user_to_follow
    )
    
    if not created:
        # Allaqachon kuzatyapti - bekor qilish
        follow.delete()
        is_following = False
        message = f"{user_to_follow.username}ni kuzatishni to'xtatdingiz"
    else:
        is_following = True
        message = f"{user_to_follow.username}ni kuzatyapsiz"
    
    return JsonResponse({
        'success': True,
        'is_following': is_following,
        'followers_count': user_to_follow.followers.count(),
        'message': message
    })


@login_required
def my_followers(request):
    """search_users ga yo'naltirish"""
    return redirect('/users/?tab=followers')


@login_required
def my_following(request):
    """search_users ga yo'naltirish"""
    return redirect('/users/?tab=following')


def discover_users(request):
    """search_users ga yo'naltirish"""
    return redirect('/users/?tab=discover')


# ===== MESSAGES =====

@login_required
def messages_inbox(request):
    """telegram_chat ga yo'naltirish"""
    return redirect('telegram_chat')


@login_required
def telegram_chat(request, username=None):
    """Telegram uslubida chat interfeysi - Optimized"""
    # Barcha suhbatlar ro'yxatini olish - Optimized query
    # Subquery orqali oxirgi xabar va o'qilmaganlar sonini olish
    
    # Oxirgi xabar uchun subquery
    last_message_subquery = Message.objects.filter(
        Q(sender=request.user, receiver=OuterRef('pk')) |
        Q(sender=OuterRef('pk'), receiver=request.user)
    ).order_by('-created_at')
    
    # Xabar almashgan foydalanuvchilarni topish
    sent_to = Message.objects.filter(sender=request.user).values_list('receiver_id', flat=True)
    received_from = Message.objects.filter(receiver=request.user).values_list('sender_id', flat=True)
    chat_user_ids = set(sent_to) | set(received_from)
    
    # Foydalanuvchilarni profil bilan birga olish
    chat_users_qs = User.objects.filter(id__in=chat_user_ids).select_related('social_profile')
    
    # O'qilmagan xabarlar sonini hisoblash - bir queryda
    unread_counts = dict(
        Message.objects.filter(
            receiver=request.user,
            sender_id__in=chat_user_ids,
            is_read=False
        ).values('sender_id').annotate(count=Count('id')).values_list('sender_id', 'count')
    )
    
    # Oxirgi xabarlarni olish - bir queryda
    last_messages = {}
    for user_id in chat_user_ids:
        last_msg = Message.objects.filter(
            Q(sender=request.user, receiver_id=user_id) |
            Q(sender_id=user_id, receiver=request.user)
        ).order_by('-created_at').first()
        if last_msg:
            last_messages[user_id] = last_msg
    
    chats = []
    for chat_user in chat_users_qs:
        try:
            profile = chat_user.social_profile
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(user=chat_user)
        
        chats.append({
            'user': chat_user,
            'profile': profile,
            'last_message': last_messages.get(chat_user.id),
            'unread_count': unread_counts.get(chat_user.id, 0),
        })
    
    # Oxirgi xabar vaqtiga ko'ra saralash
    chats.sort(key=lambda x: x['last_message'].created_at if x['last_message'] else timezone.datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    
    context = {
        'chats': chats,
        'total_unread': sum(c['unread_count'] for c in chats),
    }
    
    # Agar username berilgan bo'lsa, shu suhbatni ochish
    if username:
        active_user = get_object_or_404(User.objects.select_related('social_profile'), username=username)
        try:
            active_profile = active_user.social_profile
        except UserProfile.DoesNotExist:
            active_profile = UserProfile.objects.create(user=active_user)
        
        # Xabarlarni o'qilgan deb belgilash
        Message.objects.filter(sender=active_user, receiver=request.user, is_read=False).update(is_read=True)
        
        # Xabarlar (o'chirilmaganlar) - select_related bilan
        messages_list = Message.objects.filter(
            Q(sender=request.user, receiver=active_user) | Q(sender=active_user, receiver=request.user)
        ).exclude(
            Q(is_deleted_for_everyone=True) |
            Q(sender=request.user, is_deleted_by_sender=True) |
            Q(receiver=request.user, is_deleted_by_receiver=True)
        ).select_related('sender', 'receiver', 'reply_to').order_by('created_at')
        
        # Online status yangilash
        my_profile = get_or_create_profile(request.user)
        my_profile.update_online_status()
        
        context['active_user'] = active_user
        context['active_profile'] = active_profile
        context['active_chat'] = username
        context['messages'] = messages_list
        
        log_user_action(request.user, 'chat_opened', {'with_user': username})
    
    return render(request, 'blog/social/telegram_chat.html', context)


@login_required
def chat_view(request, username):
    """Suhbat ko'rish"""
    other_user = get_object_or_404(User, username=username)
    other_profile = get_or_create_profile(other_user)
    
    # Xabarlarni o'qilgan deb belgilash
    Message.objects.filter(sender=other_user, receiver=request.user, is_read=False).update(is_read=True)
    
    # Xabarlar (o'chirilmaganlar)
    messages_list = Message.objects.filter(
        (Q(sender=request.user, receiver=other_user) | Q(sender=other_user, receiver=request.user))
    ).exclude(
        Q(is_deleted_for_everyone=True) |
        Q(sender=request.user, is_deleted_by_sender=True) |
        Q(receiver=request.user, is_deleted_by_receiver=True)
    ).order_by('created_at')
    
    # Online status yangilash
    my_profile = get_or_create_profile(request.user)
    my_profile.update_online_status()
    
    context = {
        'other_user': other_user,
        'other_profile': other_profile,
        'messages': messages_list,
    }
    return render(request, 'blog/social/chat.html', context)


@login_required
@require_POST
@rate_limit('send_message', limit=30, period=60)  # 30 xabar/daqiqa
def send_message(request, username):
    """Xabar yuborish (matn, rasm, fayl) - Xavfsiz va optimizatsiyalangan"""
    receiver = get_object_or_404(User.objects.select_related('social_profile'), username=username)
    
    # Xabar yuborish ruxsati
    try:
        receiver_profile = receiver.social_profile
    except UserProfile.DoesNotExist:
        receiver_profile = UserProfile.objects.create(user=receiver)
    
    if not receiver_profile.allow_messages:
        return JsonResponse({'error': "Bu foydalanuvchi xabarlarga ruxsat bermagan"}, status=403)
    
    # Content type tekshirish
    content_type = request.content_type
    
    if 'multipart/form-data' in content_type:
        # Fayl yuklash
        content = request.POST.get('content', '').strip()
        message_type = request.POST.get('message_type', 'text')
        reply_to_id = request.POST.get('reply_to')
        uploaded_file = request.FILES.get('file')
        
        if not content and not uploaded_file:
            return JsonResponse({'error': "Xabar yoki fayl yuborishingiz kerak"}, status=400)
        
        # Matn uzunligini tekshirish
        if len(content) > 2000:
            return JsonResponse({'error': "Xabar 2000 belgidan oshmasligi kerak"}, status=400)
        
        message = Message.objects.create(
            sender=request.user,
            receiver=receiver,
            content=content,
            message_type=message_type if uploaded_file else 'text',
        )
        
        if uploaded_file:
            # Fayl xavfsizligini tekshirish
            is_valid, error = validate_uploaded_file(uploaded_file, 'chat')
            if not is_valid:
                message.delete()
                return JsonResponse({'error': error}, status=400)
            
            # Fayl nomini xavfsiz qilish
            safe_filename = sanitize_filename(uploaded_file.name)
            uploaded_file.name = safe_filename
            
            message.file = uploaded_file
            message.file_name = safe_filename
            message.file_size = uploaded_file.size
            
            # Rasm yoki fayl ekanini aniqlash
            ext = safe_filename.split('.')[-1].lower() if '.' in safe_filename else ''
            if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                message.message_type = 'image'
            else:
                message.message_type = 'file'
            message.save()
            
            log_user_action(request.user, 'file_uploaded', {
                'filename': safe_filename,
                'size': uploaded_file.size,
                'to_user': username
            })
        
        if reply_to_id:
            try:
                reply_to = Message.objects.get(id=reply_to_id)
                message.reply_to = reply_to
                message.save()
            except Message.DoesNotExist:
                pass
    else:
        # JSON xabar
        data = json.loads(request.body)
        content = data.get('content', '').strip()
        reply_to_id = data.get('reply_to')
        
        if not content:
            return JsonResponse({'error': "Xabar bo'sh bo'lmasligi kerak"}, status=400)
        
        if len(content) > 2000:
            return JsonResponse({'error': "Xabar juda uzun"}, status=400)
        
        message = Message.objects.create(
            sender=request.user,
            receiver=receiver,
            content=content,
            message_type='text'
        )
        
        if reply_to_id:
            try:
                reply_to = Message.objects.get(id=reply_to_id)
                message.reply_to = reply_to
                message.save()
            except Message.DoesNotExist:
                pass
    
    # Typing statusini to'xtatish
    my_profile = get_or_create_profile(request.user)
    my_profile.stop_typing()
    
    return JsonResponse({
        'success': True,
        'message': {
            'id': message.id,
            'content': message.content,
            'message_type': message.message_type,
            'file_url': message.file.url if message.file else None,
            'file_name': message.file_name,
            'file_size': message.format_file_size() if message.file else None,
            'file_size_bytes': message.file_size,  # Local saqlash uchun
            'is_image': message.is_image(),
            'created_at': message.created_at.strftime('%H:%M'),
        }
    })


@login_required
@require_POST
def delete_message(request, message_id):
    """Xabarni o'chirish"""
    message = get_object_or_404(Message, id=message_id)
    
    # Faqat jo'natuvchi o'chira oladi
    if message.sender != request.user and message.receiver != request.user:
        return JsonResponse({'error': "Sizda ruxsat yo'q"}, status=403)
    
    data = json.loads(request.body)
    delete_for_everyone = data.get('delete_for_everyone', False)
    
    if delete_for_everyone and message.sender == request.user:
        # 15 daqiqa ichida hammadan o'chirish mumkin
        time_diff = timezone.now() - message.created_at
        if time_diff.seconds <= 900:  # 15 daqiqa
            message.is_deleted_for_everyone = True
            message.content = ""
            if message.file:
                message.file.delete()
            message.save()
            return JsonResponse({'success': True, 'deleted_for_everyone': True})
        else:
            return JsonResponse({'error': "15 daqiqadan keyin hammadan o'chirib bo'lmaydi"}, status=400)
    else:
        # Faqat o'zimdan o'chirish
        if message.sender == request.user:
            message.is_deleted_by_sender = True
        else:
            message.is_deleted_by_receiver = True
        message.save()
        return JsonResponse({'success': True, 'deleted_for_everyone': False})


@login_required
@require_POST
def edit_message(request, message_id):
    """Xabarni tahrirlash"""
    message = get_object_or_404(Message, id=message_id, sender=request.user)
    
    # Faqat matnli xabarlarni tahrirlash mumkin
    if message.message_type != 'text':
        return JsonResponse({'error': "Faqat matnli xabarlarni tahrirlash mumkin"}, status=400)
    
    # 15 daqiqa ichida tahrirlash mumkin
    time_diff = timezone.now() - message.created_at
    if time_diff.seconds > 900:
        return JsonResponse({'error': "15 daqiqadan keyin tahrirlash mumkin emas"}, status=400)
    
    data = json.loads(request.body)
    new_content = data.get('content', '').strip()
    
    if not new_content:
        return JsonResponse({'error': "Xabar bo'sh bo'lmasligi kerak"}, status=400)
    
    if len(new_content) > 2000:
        return JsonResponse({'error': "Xabar juda uzun"}, status=400)
    
    message.content = new_content
    message.edited_at = timezone.now()
    message.save()
    
    return JsonResponse({
        'success': True,
        'message': {
            'id': message.id,
            'content': message.content,
            'edited': True,
        }
    })


@login_required
def get_new_messages(request, username):
    """Yangi xabarlarni olish (polling uchun)"""
    other_user = get_object_or_404(User, username=username)
    last_id = request.GET.get('last_id', 0)
    
    try:
        last_id = int(last_id)
    except:
        last_id = 0
    
    # Yangi xabarlar
    new_messages = Message.objects.filter(
        sender=other_user,
        receiver=request.user,
        id__gt=last_id
    ).exclude(
        Q(is_deleted_for_everyone=True) |
        Q(is_deleted_by_receiver=True)
    ).order_by('created_at')
    
    # Xabarlarni o'qilgan deb belgilash
    new_messages.update(is_read=True)
    
    # Online status yangilash
    my_profile = get_or_create_profile(request.user)
    my_profile.update_online_status()
    
    # Boshqa foydalanuvchi holati
    other_profile = get_or_create_profile(other_user)
    is_typing = other_profile.is_typing_to == request.user
    # Typing 10 sekunddan eski bo'lsa reset
    if is_typing and other_profile.typing_started_at:
        if (timezone.now() - other_profile.typing_started_at).seconds > 10:
            is_typing = False
    
    messages_data = []
    for msg in new_messages:
        messages_data.append({
            'id': msg.id,
            'content': msg.content,
            'message_type': msg.message_type,
            'file_url': msg.file.url if msg.file else None,
            'file_name': msg.file_name,
            'is_image': msg.is_image(),
            'created_at': msg.created_at.strftime('%H:%M'),
            'is_mine': False,
        })
    
    return JsonResponse({
        'messages': messages_data,
        'other_user': {
            'is_online': other_profile.is_online if other_profile.show_online_status else None,
            'last_seen': other_profile.get_online_status_display() if other_profile.show_online_status else None,
            'is_typing': is_typing,
        }
    })


@login_required
@require_POST
def set_typing_status(request, username):
    """Yozmoqda statusini o'rnatish"""
    other_user = get_object_or_404(User, username=username)
    
    data = json.loads(request.body)
    is_typing = data.get('is_typing', False)
    
    my_profile = get_or_create_profile(request.user)
    
    if is_typing:
        my_profile.start_typing(other_user)
    else:
        my_profile.stop_typing()
    
    return JsonResponse({'success': True})


@login_required
def update_online_status(request):
    """Online statusni yangilash (heartbeat)"""
    my_profile = get_or_create_profile(request.user)
    my_profile.update_online_status()
    
    # O'qilmagan xabarlar soni
    unread_count = Message.objects.filter(
        receiver=request.user,
        is_read=False,
        is_deleted_for_everyone=False,
        is_deleted_by_receiver=False
    ).count()
    
    return JsonResponse({
        'success': True,
        'unread_count': unread_count
    })


# ===== PROFILE EDIT =====

@login_required
def edit_profile(request):
    """Profilni tahrirlash"""
    profile = get_or_create_profile(request.user)
    
    if request.method == 'POST':
        # Ma'lumotlarni yangilash
        profile.bio = request.POST.get('bio', '')[:500]
        profile.location = request.POST.get('location', '')[:100]
        profile.website = request.POST.get('website', '')
        profile.favorite_genres = request.POST.get('favorite_genres', '')[:300]
        profile.favorite_author = request.POST.get('favorite_author', '')[:200]
        profile.is_public = request.POST.get('is_public') == 'on'
        profile.show_reading_activity = request.POST.get('show_reading_activity') == 'on'
        profile.allow_messages = request.POST.get('allow_messages') == 'on'
        profile.show_online_status = request.POST.get('show_online_status') == 'on'
        
        # Avatar
        if 'avatar' in request.FILES:
            profile.avatar = request.FILES['avatar']
        
        # User info
        request.user.first_name = request.POST.get('first_name', '')[:30]
        request.user.last_name = request.POST.get('last_name', '')[:30]
        request.user.save()
        
        profile.save()
        messages.success(request, "Profil muvaffaqiyatli yangilandi!")
        return redirect('user_profile', username=request.user.username)
    
    context = {
        'profile': profile,
    }
    return render(request, 'blog/social/edit_profile.html', context)


# ===== DISCOVER USERS =====

def discover_users(request):
    """Tavsiya etilgan foydalanuvchilar"""
    suggested_users = []
    
    if request.user.is_authenticated:
        # Kuzatmayotgan faol foydalanuvchilar
        following_ids = Follow.objects.filter(follower=request.user).values_list('following_id', flat=True)
        
        suggested = User.objects.filter(is_active=True).exclude(
            Q(id=request.user.id) | Q(id__in=following_ids) | Q(is_superuser=True)
        ).annotate(
            follower_count=Count('followers')
        ).order_by('-follower_count', '-date_joined')[:20]
        
        for user in suggested:
            profile = get_or_create_profile(user)
            
            # O'xshash kitoblar soni
            user_books = set(ReadingActivity.objects.filter(user=request.user).values_list('book_id', flat=True))
            other_books = set(ReadingActivity.objects.filter(user=user).values_list('book_id', flat=True))
            common_books = len(user_books & other_books)
            
            suggested_users.append({
                'user': user,
                'profile': profile,
                'followers_count': user.followers.count(),
                'common_books': common_books,
            })
        
        # O'xshash kitoblar bo'yicha saralash
        suggested_users.sort(key=lambda x: x['common_books'], reverse=True)
    else:
        # Mehmon uchun eng mashhur foydalanuvchilar
        popular = User.objects.filter(is_active=True, is_superuser=False).annotate(
            follower_count=Count('followers')
        ).order_by('-follower_count')[:20]
        
        for user in popular:
            profile = get_or_create_profile(user)
            suggested_users.append({
                'user': user,
                'profile': profile,
                'followers_count': user.followers.count(),
                'common_books': 0,
            })
    
    context = {
        'suggested_users': suggested_users,
    }
    return render(request, 'blog/social/discover.html', context)
