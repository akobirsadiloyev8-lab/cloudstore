"""Custom context processors for the blog app"""
from django.utils import timezone


def food_stats(request):
    """Har bir sahifa uchun ovqatlanish statistikasini qo'shish"""
    from .models import FoodIntake
    
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return {
            'daily_calories': 0,
            'daily_product_count': 0,
            'recommended_kcal': 2500,
            'health_percent': 0,
        }
    
    today = timezone.now().date()
    
    try:
        # Kunlik jami
        daily_totals = FoodIntake.get_daily_totals(request.user, today)
        daily_calories = daily_totals.get('total_calories', 0) or 0
        
        # Mahsulotlar soni (bugungi)
        daily_product_count = FoodIntake.objects.filter(
            user=request.user, 
            date=today
        ).count()
        
        # Meyoriy kcal (o'rtacha - erkak va ayol o'rtasi ~2500)
        recommended_kcal = 2500
        
        # Sog'liq foizi - kunlik iste'mol / meyoriy * 100
        health_percent = min(100, int((daily_calories / recommended_kcal) * 100)) if daily_calories > 0 else 0
        
        return {
            'daily_calories': int(daily_calories),
            'daily_product_count': daily_product_count,
            'recommended_kcal': recommended_kcal,
            'health_percent': health_percent,
        }
    except Exception:
        return {
            'daily_calories': 0,
            'daily_product_count': 0,
            'recommended_kcal': 2500,
            'health_percent': 0,
        }
