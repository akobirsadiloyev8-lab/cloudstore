# LibreOffice bloklarini olib tashlash
with open('blog/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# LibreOffice kodlarini olib tashlash
import re

# LibreOffice blokini topish va almashtirish
pattern = r'# LibreOffice orqali konvertatsiya.*?result = f"LibreOffice topilmadi yoki fayl turi qo\'llab-quvvatlanmaydi: {ext}"'

replacement = '''# Python kutubxonalari orqali konvertatsiya (LibreOffice o'rniga)
                if ext == '.docx':
                    try:
                        # docx faylni matn sifatida o'qish va PDF yaratish
                        from docx import Document
                        from reportlab.pdfgen import canvas
                        from reportlab.lib.pagesizes import A4
                        
                        # DOCX'dan matn o'qish
                        doc = Document(input_path)
                        text = "\\n".join([p.text for p in doc.paragraphs])
                        
                        # PDF yaratish
                        c = canvas.Canvas(str(output_path), pagesize=A4)
                        width, height = A4
                        
                        # Matnni PDF'ga yozish
                        y_position = height - 50
                        for line in text.split('\\n'):
                            if y_position < 50:
                                c.showPage()
                                y_position = height - 50
                            if line.strip():  # Bo'sh qatorlarni o'tkazib yuborish
                                c.drawString(50, y_position, line[:100])  # 100 belgigacha
                                y_position -= 20
                        
                        c.save()
                        result = str(output_path)
                        print(f"✓ DOCX dan PDF yaratildi: {result}")
                    except Exception as e:
                        result = f"DOCX konvertatsiya xatosi: {str(e)}"
                        print(f"✗ DOCX konvertatsiya xatosi: {str(e)}")
                else:
                    result = f"LibreOffice o'rnatilmagan. Faqat DOCX -> PDF qo'llab-quvvatlanadi."'''

# Regex bilan almashtirish
content_new = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Agar regex ishlamasa, manual qidirish
if content_new == content:
    # Manual almashtirish
    start_marker = "# LibreOffice orqali konvertatsiya"
    end_marker = 'result = f"LibreOffice topilmadi yoki fayl turi qo\'llab-quvvatlanmaydi: {ext}"'
    
    start_pos = content.find(start_marker)
    end_pos = content.find(end_marker) + len(end_marker)
    
    if start_pos != -1 and end_pos != -1:
        content_new = content[:start_pos] + replacement + content[end_pos:]

with open('blog/views.py', 'w', encoding='utf-8') as f:
    f.write(content_new)

print("LibreOffice bloki o'chirildi va Python alternativ qo'shildi")