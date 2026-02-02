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
    """Zamonaviy flat dizaynli bulut ikonkasi"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Gradient fon
    for y in range(size):
        ratio = y / size
        # Ko'k-binafsha gradient
        r = int(99 * (1 - ratio) + 139 * ratio)
        g = int(102 * (1 - ratio) + 92 * ratio)  
        b = int(241 * (1 - ratio) + 246 * ratio)
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
    text_color = (99, 102, 241, 255)  # Indigo
    
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = (size - text_width) // 2
    text_y = cy - text_height // 2 + int(10*s)
    
    draw.text((text_x, text_y), text, fill=text_color, font=font)
    
    return img

# Ikonkalar papkasi
icons_dir = "blog/static/icons"

# Barcha o'lchamlarda yaratish
sizes = [72, 96, 128, 144, 152, 192, 384, 512]

print("Cloudstore AI ikonkalari yaratilmoqda...")

for size in sizes:
    icon = create_modern_cloud_icon(size)
    filename = f"icon-{size}x{size}.png"
    filepath = os.path.join(icons_dir, filename)
    icon.save(filepath, 'PNG')
    print(f"✓ {filename} yaratildi")

print("\nBarcha ikonkalar muvaffaqiyatli yaratildi!")
print("Endi 'python manage.py collectstatic' buyrug'ini ishga tushiring.")
