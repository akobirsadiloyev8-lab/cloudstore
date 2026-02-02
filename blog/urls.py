from django.urls import path, include
from . import views
from . import views_subscription
from . import views_social

urlpatterns = [
    path('', views.boshlash, name='boshlash'),
    path('preview/', views.preview_files, name='preview'),
    path('preview-content/', views.preview_file_content, name='preview_content'),
    path('upload/', views.upload_file, name='upload'),
    path('convert/', views.convert_to_format, name='convert_format'),
    path('convert-folder-zip/', views.convert_folder_to_pdf_zip, name='convert_folder_zip'),
    path('download/<str:filename>/', views.download_file, name='download'),
    path('delete-file/', views.delete_file, name='delete_file'),
    path('edit-file/', views.edit_file_page, name='edit_file'),
    path('file-stats/', views.get_file_stats, name='file_stats'),
    path('image_list/', views.image_list, name='image_list'),
    path('convert/<path:filename>/<str:to_format>/', views.convert_file, name='convert_file'),
    path('feedback/', views.feedback_list, name='feedback_list'),
    path('submit_feedback/', views.submit_feedback, name='submit_feedback'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('accounts/', include('django.contrib.auth.urls')),
    
    # AI Chat
    path('ai-chat/', views.ai_chat, name='ai_chat'),
    path('api/get-file-content/', views.get_file_content, name='get_file_content'),
    path('api/ai-ask/', views.ai_ask, name='ai_ask'),
    
    # Kitoblar - Birlashtirilgan
    path('adabiyotlar/', views.adabiyotlar, name='adabiyotlar'),
    path('kitoblar/', views.all_books, name='all_books'),
    path('api/search-books/', views.ai_search_books, name='ai_search_books'),
    path('kitob-yuklash/', views.kitob_yuklash, name='kitob_yuklash'),
    path('api/get-authors/', views.get_authors, name='get_authors'),
    path('api/upload-zip/', views.upload_zip_books, name='upload_zip_books'),
    path('kitob/<int:book_id>/', views.book_detail, name='book_detail'),
    path('kitob/<int:book_id>/read/', views.read_book, name='read_book'),
    path('rate-book/', views.rate_book, name='rate_book'),
    path('toggle-favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('save-progress/', views.save_reading_progress, name='save_reading_progress'),
    path('get-summary/', views.get_book_summary, name='get_book_summary'),
    path('ask-book/', views.ask_about_book, name='ask_about_book'),
    path('similar-books/', views.get_similar_books, name='get_similar_books'),
    path('kategoriyalar/', views.categories_list, name='categories'),
    path('delete-account/', views.delete_account, name='delete_account'),
    
    # ===== PREMIUM OBUNA TIZIMI =====
    path('obuna/', views_subscription.subscription_plans, name='subscription_plans'),
    path('obuna/checkout/<int:plan_id>/', views_subscription.checkout, name='checkout'),
    path('obuna/mening/', views_subscription.my_subscription, name='my_subscription'),
    path('api/apply-promo/', views_subscription.apply_promo_code, name='apply_promo'),
    path('api/create-payment/', views_subscription.create_payment, name='create_payment'),
    path('payment/callback/<str:provider>/', views_subscription.payment_callback, name='payment_callback'),
    path('referral/', views_subscription.referral_dashboard, name='referral'),
    path('kunlik-iqtibos/', views_subscription.daily_quote, name='daily_quote'),
    path('api/share-quote/', views_subscription.share_quote, name='share_quote'),
    path('liderlar/', views_subscription.leaderboard, name='leaderboard'),
    path('yutuqlar/', views_subscription.my_badges, name='my_badges'),
    
    # PWA / Offline
    path('offline/', views.offline_page, name='offline'),
    
    # ===== IJTIMOIY TARMOQ - Birlashtirilgan =====
    path('users/', views_social.search_users, name='search_users'),
    path('users/<str:username>/', views_social.user_profile_view, name='user_profile'),
    path('users/<str:username>/follow/', views_social.toggle_follow, name='toggle_follow'),
    path('users/<str:username>/message/', views_social.send_message, name='send_message'),
    
    # Xabarlar - Birlashtirilgan (telegram_chat)
    path('telegram-chat/', views_social.telegram_chat, name='telegram_chat'),
    path('telegram-chat/<str:username>/', views_social.telegram_chat, name='telegram_chat_with_user'),
    path('api/messages/<int:message_id>/delete/', views_social.delete_message, name='delete_message'),
    path('api/messages/<int:message_id>/edit/', views_social.edit_message, name='edit_message'),
    path('api/chat/<str:username>/new/', views_social.get_new_messages, name='get_new_messages'),
    path('api/chat/<str:username>/typing/', views_social.set_typing_status, name='set_typing_status'),
    path('api/online-status/', views_social.update_online_status, name='update_online_status'),
    
    # Profil
    path('profil/tahrirlash/', views_social.edit_profile, name='edit_profile'),
    
    # ===== PWA =====
    path('manifest.json', views.pwa_manifest, name='pwa_manifest'),
    path('sw.js', views.pwa_service_worker, name='pwa_sw'),
    path('offline/', views.pwa_offline, name='pwa_offline'),
    # path('pwa-icon/<str:size>/', views.pwa_icon, name='pwa_icon'),  # TODO: pwa_icon funksiyasini yaratish kerak
    
    # ===== BARCODE SCANNER =====
    path('scanner/', views.barcode_scanner, name='barcode_scanner'),
    path('api/barcode/lookup/', views.barcode_lookup, name='barcode_lookup'),
    path('api/barcode/add/', views.barcode_add_product, name='barcode_add_product'),
    path('scanner/tarix/', views.barcode_history, name='barcode_history'),
    
    # ===== HUQUQIY SAHIFALAR =====
    path('maxfiylik-siyosati/', views.privacy_policy, name='privacy_policy'),
    path('foydalanish-shartlari/', views.terms_of_service, name='terms_of_service'),
    path('biz-haqimizda/', views.about, name='about'),
]


