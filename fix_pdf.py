# PDF extraction code ni o'zgartirish
with open('blog/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Eski kodini topib o'zgartirish
old_code = """                # Faqat PyMuPDF (fitz) orqali PDF matnini o'qish
                try:
                    import fitz
                    doc = fitz.open(filepath)
                    text = "\\n".join([page.get_text() for page in doc])
                    if text and text.strip():
                        result['content'] = text
                    else:
                        result['content'] = 'PDF faylidan matn o'qib bo'lmadi yoki fayl bo'sh.'
                except Exception as e:
                    result['content'] = f'PDF matnini o'qishda xatolik: {str(e)}'"""

new_code = """                # Advanced PDF text extraction
                result['content'] = extract_pdf_text_advanced(filepath)"""

# O'zgartirish
content = content.replace(old_code, new_code)

with open('blog/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("PDF extraction updated successfully!")