from django.apps import AppConfig


class BlogConfig(AppConfig):
    name = 'blog'
    default_auto_field = 'django.db.models.BigAutoField'
    
    def ready(self):
        """App tayyor bo'lganda signallarni yuklash"""
        import blog.signals  # noqa
