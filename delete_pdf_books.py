"""
PDF kitoblarni bazadan va diskdan o'chirish skripti
"""
import os
import django

# Django sozlamalarini yuklash
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from blog.models import Book, BookPage

def delete_pdf_books():
    """Barcha PDF formatdagi kitoblarni o'chirish"""
    
    # PDF kitoblarni topish
    pdf_books = Book.objects.filter(file__iendswith='.pdf')
    count = pdf_books.count()
    
    print(f"📚 {count} ta PDF kitob topildi")
    
    if count == 0:
        print("✅ PDF kitoblar yo'q, o'chirishga hojat yo'q.")
        return
    
    deleted_files = []
    deleted_books = []
    
    for book in pdf_books:
        book_title = book.title
        file_path = book.file.path if book.file else None
        
        # Kitob sahifalarini o'chirish
        pages_count = BookPage.objects.filter(book=book).count()
        BookPage.objects.filter(book=book).delete()
        
        # Faylni diskdan o'chirish
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                deleted_files.append(file_path)
                print(f"  🗑️ Fayl o'chirildi: {file_path}")
            except Exception as e:
                print(f"  ⚠️ Faylni o'chirishda xato: {e}")
        
        # Kitobni bazadan o'chirish
        book.delete()
        deleted_books.append(book_title)
        print(f"  📖 Kitob o'chirildi: {book_title} ({pages_count} sahifa)")
    
    print(f"\n✅ Jami {len(deleted_books)} ta PDF kitob o'chirildi:")
    for title in deleted_books:
        print(f"   - {title}")
    
    print(f"\n📁 Jami {len(deleted_files)} ta fayl diskdan o'chirildi")

if __name__ == '__main__':
    confirm = input("⚠️ Barcha PDF kitoblarni o'chirishni xohlaysizmi? (yes/no): ")
    if confirm.lower() == 'yes':
        delete_pdf_books()
    else:
        print("❌ Bekor qilindi.")
