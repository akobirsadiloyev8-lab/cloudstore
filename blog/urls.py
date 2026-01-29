from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.boshlash, name='boshlash'),
    path('boshlash/', views.boshlash, name='boshlash'),
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
    path('adabiyotlar/', views.adabiyotlar, name='adabiyotlar'),
    path('kitoblar/', views.all_books, name='all_books'),
    path('book-list/<int:author_id>/', views.book_list, name='book_list'),
    path('api/search-books/', views.ai_search_books, name='ai_search_books'),
    path('kitob-yuklash/', views.kitob_yuklash, name='kitob_yuklash'),
    path('api/get-authors/', views.get_authors, name='get_authors'),
    path('api/upload-zip/', views.upload_zip_books, name='upload_zip_books'),
    
    # Yangi funksiyalar
    path('kitob/<int:book_id>/', views.book_detail, name='book_detail'),
    path('kitob/<int:book_id>/read/', views.read_book, name='read_book'),
    path('rate-book/', views.rate_book, name='rate_book'),
    path('toggle-favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('save-progress/', views.save_reading_progress, name='save_reading_progress'),
    path('get-summary/', views.get_book_summary, name='get_book_summary'),
    path('ask-book/', views.ask_about_book, name='ask_about_book'),
    path('similar-books/', views.get_similar_books, name='get_similar_books'),
    path('kategoriyalar/', views.categories_list, name='categories'),
    path('kategoriya/<slug:slug>/', views.category_books, name='category_books'),
    path('top-kitoblar/', views.top_books, name='top_books'),
    path('yangi-kitoblar/', views.new_books, name='new_books'),
    path('sevimlilar/', views.favorites_list, name='favorites'),
    path('profil/', views.user_profile, name='profile'),
    path('delete-account/', views.delete_account, name='delete_account'),
]


