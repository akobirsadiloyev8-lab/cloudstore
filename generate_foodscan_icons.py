"""
FoodScan ikonkalarini yaratish - logo.png asosida
"""
from PIL import Image
import os

def generate_icons():
    """Logo faylidan turli o'lchamdagi ikonkalar yaratish"""
    
    # Logo faylini o'qish
    logo_path = os.path.join('blog', 'static', 'assets', 'img', 'logo.png')
    
    if not os.path.exists(logo_path):
        print(f"❌ Logo fayli topilmadi: {logo_path}")
        print("Iltimos, avval logo.png faylini yuklang")
        return
    
    logo = Image.open(logo_path)
    
    # RGBA formatga o'tkazish
    if logo.mode != 'RGBA':
        logo = logo.convert('RGBA')
    
    # Ikonka o'lchamlari
    icon_sizes = [16, 32, 72, 96, 128, 144, 152, 167, 180, 192, 384, 512]
    
    # Icons papkasi
    icons_dir = os.path.join('blog', 'static', 'icons')
    os.makedirs(icons_dir, exist_ok=True)
    
    print("🔄 Ikonkalar yaratilmoqda...")
    
    for size in icon_sizes:
        # O'lchamni o'zgartirish
        resized = logo.resize((size, size), Image.Resampling.LANCZOS)
        
        # Saqlash
        icon_path = os.path.join(icons_dir, f'icon-{size}x{size}.png')
        resized.save(icon_path, 'PNG', optimize=True)
        print(f"  ✅ {icon_path}")
    
    # Favicon yaratish (32x32)
    favicon = logo.resize((32, 32), Image.Resampling.LANCZOS)
    favicon_path = os.path.join('blog', 'static', 'assets', 'img', 'favicon.png')
    favicon.save(favicon_path, 'PNG', optimize=True)
    print(f"  ✅ {favicon_path}")
    
    # Mobile app uchun logo nusxa ko'chirish
    mobile_logo_path = os.path.join('..', 'cloudstore-mobile', 'www', 'img', 'logo.png')
    if os.path.exists(os.path.dirname(mobile_logo_path)):
        logo.save(mobile_logo_path, 'PNG', optimize=True)
        print(f"  ✅ {mobile_logo_path}")
    
    print("\n✅ Barcha ikonkalar yaratildi!")
    print("\n⚠️ Endi quyidagini ishga tushiring:")
    print("   python manage.py collectstatic --no-input")

if __name__ == '__main__':
    generate_icons()
