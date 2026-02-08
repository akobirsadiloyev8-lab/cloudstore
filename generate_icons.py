"""
Cloudstore AI uchun chiroyli bulut ikonkasi yaratish
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_cloud_icon(size):
    """Chiroyli gradient bulut ikonkasi yaratish"""
    # Yangi rasm yaratish (RGBA - shaffof fon uchun)
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Gradient fon (ko'k-binafsha)
    for y in range(size):
        # Gradient: yuqoridan pastga
        ratio = y / size
        r = int(102 + (103 - 102) * ratio)  # 667eea -> 6366f1
        g = int(126 + (102 - 126) * ratio)
        b = int(234 + (241 - 234) * ratio)
        draw.line([(0, y), (size, y)], fill=(r, g, b, 255))
    
    # Yumaloq burchaklar
    margin = size // 8
    radius = size // 5
    
    # Oq bulut shakli
    cloud_color = (255, 255, 255, 240)
    
    # Bulut parametrlari
    cx, cy = size // 2, size // 2 + size // 10
    
    # Asosiy bulut doiralari
    circles = [
        (cx - size//5, cy, size//4),      # Chap
        (cx + size//5, cy, size//4),      # O'ng
        (cx, cy - size//8, size//3.5),    # Markaziy (katta)
        (cx - size//8, cy + size//12, size//5),  # Pastki chap
        (cx + size//8, cy + size//12, size//5),  # Pastki o'ng
    ]
    
    for x, y, r in circles:
        r = int(r)
        draw.ellipse([x-r, y-r, x+r, y+r], fill=cloud_color)
    
    # Pastki tekis qism
    rect_height = size // 6
    rect_y = cy + size // 20
    draw.rectangle([
        cx - size//3.5, rect_y,
        cx + size//3.5, rect_y + rect_height
    ], fill=cloud_color)
    
    # AI yozuvi (bulut ichida)
    try:
        font_size = size // 5
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    # AI matn
    text = "AI"
    text_color = (102, 126, 234, 255)  # Ko'k rang
    
    # Matn joylashuvi
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = (size - text_width) // 2
    text_y = cy - text_height // 2
    
    draw.text((text_x, text_y), text, fill=text_color, font=font)
    
    return img

def create_modern_cloud_icon(size):
    """Zamonaviy flat dizaynli bulut ikonkasi - Qora tema"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Qora gradient fon
    for y in range(size):
        ratio = y / size
        # Qora gradient (yuqoridan pastga)
        r = int(25 * (1 - ratio) + 15 * ratio)
        g = int(25 * (1 - ratio) + 15 * ratio)  
        b = int(25 * (1 - ratio) + 15 * ratio)
        draw.line([(0, y), (size, y)], fill=(r, g, b, 255))
    
    # Rounded rectangle mask
    mask = Image.new('L', (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    radius = size // 5
    mask_draw.rounded_rectangle([0, 0, size-1, size-1], radius=radius, fill=255)
    
    # Apply mask
    result = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    result.paste(img, mask=mask)
    img = result
    draw = ImageDraw.Draw(img)
    
    # Oq bulut
    cx, cy = size // 2, size // 2 + size // 15
    cloud_color = (255, 255, 255, 250)
    
    # Bulut shakli - soddalashtirilgan
    s = size / 512  # Scale factor
    
    # Katta doiralar
    circles = [
        (cx, cy - int(30*s), int(80*s)),           # Tepa
        (cx - int(70*s), cy + int(20*s), int(60*s)),  # Chap
        (cx + int(70*s), cy + int(20*s), int(60*s)),  # O'ng
        (cx, cy + int(30*s), int(70*s)),           # Markaz past
    ]
    
    for x, y, r in circles:
        draw.ellipse([x-r, y-r, x+r, y+r], fill=cloud_color)
    
    # To'rtburchak birlashtiruvchi
    draw.rectangle([
        cx - int(90*s), cy - int(10*s),
        cx + int(90*s), cy + int(60*s)
    ], fill=cloud_color)
    
    # AI yozuvi
    try:
        font_size = int(80 * s)
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        try:
            font_size = int(80 * s)
            font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", font_size)
        except:
            font = ImageFont.load_default()
    
    text = "AI"
    text_color = (25, 25, 25, 255)  # Qora rang
    
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = (size - text_width) // 2
    text_y = cy - text_height // 2 + int(10*s)
    
    draw.text((text_x, text_y), text, fill=text_color, font=font)
    
    return img

def create_splash_screen(width, height):
    """iOS Splash Screen yaratish - Qora tema"""
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Qora gradient fon
    for y in range(height):
        ratio = y / height
        r = int(25 * (1 - ratio) + 15 * ratio)
        g = int(25 * (1 - ratio) + 15 * ratio)  
        b = int(25 * (1 - ratio) + 15 * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))
    
    # Markazda ikonka
    icon_size = min(width, height) // 4
    icon = create_modern_cloud_icon(icon_size)
    
    # Ikonkani markazga joylashtirish
    x = (width - icon_size) // 2
    y = (height - icon_size) // 2 - height // 10
    img.paste(icon, (x, y), icon)
    
    # Cloudstore yozuvi
    try:
        font_size = min(width, height) // 15
        font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    text = "Cloudstore"
    text_color = (255, 255, 255, 255)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_x = (width - text_width) // 2
    text_y = y + icon_size + height // 20
    draw.text((text_x, text_y), text, fill=text_color, font=font)
    
    return img

# Ikonkalar papkasi
icons_dir = "blog/static/icons"
os.makedirs(icons_dir, exist_ok=True)

# Barcha o'lchamlarda yaratish
sizes = [16, 32, 72, 96, 128, 144, 152, 167, 180, 192, 384, 512]

print("Cloudstore AI ikonkalari yaratilmoqda...")

for size in sizes:
    icon = create_modern_cloud_icon(size)
    filename = f"icon-{size}x{size}.png"
    filepath = os.path.join(icons_dir, filename)
    icon.save(filepath, 'PNG')
    print(f"✓ {filename} yaratildi")

# iOS Splash Screens
splash_sizes = [
    (750, 1334),    # iPhone 8, SE
    (828, 1792),    # iPhone 11, XR
    (1125, 2436),   # iPhone 12/13 Mini
    (1170, 2532),   # iPhone 13/14
    (1179, 2556),   # iPhone 14 Pro
    (1242, 2208),   # iPhone 8 Plus
    (1242, 2688),   # iPhone 11 Pro Max
    (1290, 2796),   # iPhone 14 Pro Max
    (1536, 2048),   # iPad Air, Mini
    (1668, 2388),   # iPad Pro 11"
    (2048, 2732),   # iPad Pro 12.9"
]

print("\niOS Splash Screen'lar yaratilmoqda...")

for width, height in splash_sizes:
    splash = create_splash_screen(width, height)
    filename = f"splash-{width}x{height}.png"
    filepath = os.path.join(icons_dir, filename)
    splash.save(filepath, 'PNG')
    print(f"✓ {filename} yaratildi")

print("\nBarcha ikonkalar va splash screen'lar muvaffaqiyatli yaratildi!")
print("Endi 'python manage.py collectstatic' buyrug'ini ishga tushiring.")
