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
]


