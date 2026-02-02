from django.contrib import admin
from django.utils.html import format_html
from django import forms
from .models import (Image, File, Feedback, Author, Book, BookPage, 
                     Category, BookRating, Favorite, ReadingProgress, SearchQuery, BookSummary,
                     Product, ProductScanHistory)

# Premium Obuna Admin'larini import qilish
from .admin_subscription import *

# Register your models here.

class BookCategoryInline(admin.TabularInline):
    """Kategoriya ichida kitoblarni ko'rsatish"""
    model = Book.categories.through
    extra = 0
    verbose_name = "Kategoriya kitobi"
    verbose_name_plural = "Kategoriya kitoblari"
    autocomplete_fields = ['book']


class CategoryAdminForm(forms.ModelForm):
    """Kategoriyaga kitob qo'shish uchun forma"""
    books_to_add = forms.ModelMultipleChoiceField(
        queryset=Book.objects.all(),
        required=False,
        widget=admin.widgets.FilteredSelectMultiple("Kitoblar", is_stacked=False),
        label="Kitoblar qo'shish/o'chirish"
    )
    
    class Meta:
        model = Category
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # Barcha kitoblarni ko'rsatish
            self.fields['books_to_add'].queryset = Book.objects.all()
            self.fields['books_to_add'].initial = self.instance.books.all()


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    form = CategoryAdminForm
    list_display = ('name', 'slug', 'icon', 'book_count', 'show_books')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    inlines = [BookCategoryInline]
    
    fieldsets = (
        ('Kategoriya ma\'lumotlari', {
            'fields': ('name', 'slug', 'icon', 'description')
        }),
        ('Kitoblarni boshqarish', {
            'fields': ('books_to_add',),
            'description': 'Kitoblarni tanlang va saqlash tugmasini bosing'
        }),
    )
    
    def book_count(self, obj):
        count = obj.books.count()
        return format_html('<span style="color: green; font-weight: bold;">{}</span>', count)
    book_count.short_description = "Kitoblar soni"
    
    def show_books(self, obj):
        books = obj.books.all()[:3]
        if books:
            names = ", ".join([b.title[:20] for b in books])
            if obj.books.count() > 3:
                names += f" ... (+{obj.books.count() - 3})"
            return names
        return "-"
    show_books.short_description = "Kitoblar"
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
    
    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        
        # Tanlangan kitoblarni kategoriyaga qo'shish (ManyToMany)
        if 'books_to_add' in form.cleaned_data:
            selected_books = form.cleaned_data['books_to_add']
            # ManyToMany munosabatini yangilash
            form.instance.books.set(selected_books)
    
    actions = ['remove_all_books']
    
    @admin.action(description="Barcha kitoblarni kategoriyadan o'chirish")
    def remove_all_books(self, request, queryset):
        count = 0
        for category in queryset:
            count += category.books.count()
            category.books.clear()  # ManyToMany uchun clear() ishlatamiz
        self.message_user(request, f"{count} ta kitob kategoriyadan o'chirildi.")


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('title',)


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ('file', 'user', 'uploaded_at')
    list_filter = ('uploaded_at',)


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_message', 'user', 'created_at', 'is_read')
    list_filter = ('created_at', 'is_read')
    search_fields = ('name', 'message', 'user__username')
    list_editable = ('is_read',)
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    def short_message(self, obj):
        return obj.message[:50] + "..." if len(obj.message) > 50 else obj.message
    short_message.short_description = "Xabar"
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
        self.message_user(request, f"{queryset.count()} ta fikr o'qilgan deb belgilandi.")
    mark_as_read.short_description = "O'qilgan deb belgilash"
    
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
        self.message_user(request, f"{queryset.count()} ta fikr o'qilmagan deb belgilandi.")
    mark_as_unread.short_description = "O'qilmagan deb belgilash"


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('name', 'book_count', 'birth_year', 'death_year', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'bio')
    ordering = ('name',)
    
    def book_count(self, obj):
        return obj.books.count()
    book_count.short_description = "Kitoblar soni"


class BookPageInline(admin.TabularInline):
    model = BookPage
    extra = 0
    readonly_fields = ('page_number', 'text_preview')
    fields = ('page_number', 'text_preview')
    can_delete = True
    
    def text_preview(self, obj):
        if obj.text:
            return obj.text[:100] + "..." if len(obj.text) > 100 else obj.text
        return "-"
    text_preview.short_description = "Matn"


class BookInline(admin.TabularInline):
    model = Book
    extra = 1


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'year_written', 'page_count', 'has_content', 'created_at')
    list_filter = ('author', 'created_at')
    search_fields = ('title', 'description', 'author__name', 'content')
    ordering = ('title',)
    readonly_fields = ('content_preview', 'page_count')
    inlines = [BookPageInline]
    actions = ['delete_selected', 'regenerate_pages']
    
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('author', 'title', 'description', 'year_written', 'file')
        }),
        ('Kitob matni', {
            'fields': ('content', 'content_preview', 'page_count'),
            'classes': ('collapse',),
            'description': 'Fayl yuklanganda matn avtomatik o\'qib olinadi'
        }),
    )
    
    def page_count(self, obj):
        return obj.pages.count()
    page_count.short_description = "Sahifalar"
    
    def has_content(self, obj):
        """Kitob matnini borligini ko'rsatish"""
        if obj.content:
            return f"✓ ({len(obj.content)} belgi)"
        return "✗"
    has_content.short_description = "Matn"
    
    def content_preview(self, obj):
        """Matnning qisqa ko'rinishi"""
        if obj.content:
            preview = obj.content[:500] + "..." if len(obj.content) > 500 else obj.content
            return preview
        return "Matn mavjud emas"
    content_preview.short_description = "Matn ko'rinishi"
    
    def save_model(self, request, obj, form, change):
        """Kitobni saqlashda fayldan matnni avtomatik o'qib olish"""
        # Avval obyektni saqlaymiz (fayl saqlanishi uchun)
        super().save_model(request, obj, form, change)
        
        # Agar fayl mavjud bo'lsa va yangi yuklangan bo'lsa
        if obj.file:
            # Fayldan matnni o'qib olamiz
            extracted_text = obj.extract_text_from_file()
            if extracted_text:
                obj.content = extracted_text
                obj.save(update_fields=['content'])
            # Sahifalarni ham saqlash
            try:
                obj.save_pages_from_file()
            except:
                pass
    
    @admin.action(description="Sahifalarni qayta generatsiya qilish")
    def regenerate_pages(self, request, queryset):
        count = 0
        for book in queryset:
            if book.file:
                try:
                    book.save_pages_from_file()
                    count += 1
                except:
                    pass
        self.message_user(request, f"{count} ta kitob sahifalari qayta yaratildi.")


@admin.register(BookPage)
class BookPageAdmin(admin.ModelAdmin):
    list_display = ('book', 'page_number', 'text_preview')
    list_filter = ('book',)
    search_fields = ('book__title', 'text')
    ordering = ('book', 'page_number')
    
    def text_preview(self, obj):
        if obj.text:
            return obj.text[:80] + "..." if len(obj.text) > 80 else obj.text
        return "-"
    text_preview.short_description = "Matn"


@admin.register(BookRating)
class BookRatingAdmin(admin.ModelAdmin):
    list_display = ('book', 'name', 'rating', 'comment_preview', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('book__title', 'name', 'comment')
    
    def comment_preview(self, obj):
        if obj.comment:
            return obj.comment[:50] + "..." if len(obj.comment) > 50 else obj.comment
        return "-"
    comment_preview.short_description = "Sharh"


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'book__title')


@admin.register(ReadingProgress)
class ReadingProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'current_page', 'total_pages', 'progress_percent', 'is_completed', 'last_read')
    list_filter = ('is_completed', 'last_read')
    search_fields = ('user__username', 'book__title')
    
    def progress_percent(self, obj):
        return f"{obj.progress_percent}%"
    progress_percent.short_description = "Progress"


@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ('query', 'count', 'last_searched')
    list_filter = ('last_searched',)
    search_fields = ('query',)
    ordering = ('-count',)


@admin.register(BookSummary)
class BookSummaryAdmin(admin.ModelAdmin):
    list_display = ('book', 'summary_preview', 'updated_at')
    search_fields = ('book__title', 'short_summary')
    
    def summary_preview(self, obj):
        return obj.short_summary[:100] + "..." if len(obj.short_summary) > 100 else obj.short_summary
    summary_preview.short_description = "Xulosa"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('barcode', 'name', 'brand', 'price', 'currency', 'category', 'scan_count', 'is_active')
    list_filter = ('is_active', 'category', 'brand', 'country')
    search_fields = ('barcode', 'name', 'brand', 'manufacturer')
    list_editable = ('is_active', 'price')
    ordering = ('-scan_count', '-created_at')
    readonly_fields = ('scan_count', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('barcode', 'name', 'description', 'image')
        }),
        ('Narx', {
            'fields': ('price', 'currency')
        }),
        ('Kategoriya', {
            'fields': ('category', 'brand', 'manufacturer', 'country')
        }),
        ('Tarkib va qo\'shimcha', {
            'fields': ('weight', 'ingredients', 'nutrition_info', 'expiry_info'),
            'classes': ('collapse',)
        }),
        ('Statistika', {
            'fields': ('is_active', 'scan_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProductScanHistory)
class ProductScanHistoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'scanned_at')
    list_filter = ('scanned_at',)
    search_fields = ('product__name', 'product__barcode', 'user__username')
    date_hierarchy = 'scanned_at'
    ordering = ('-scanned_at',)
