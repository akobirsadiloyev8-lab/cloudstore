"""
LibreOffice yordamida fayl konvertatsiya qilish moduli.
Word, Excel, PowerPoint fayllarini PDF formatiga aylantirish uchun.
"""
import os
import subprocess
import tempfile
from pathlib import Path


def get_libreoffice_path():
    """LibreOffice yo'lini topish"""
    # Docker va Linux uchun
    linux_paths = [
        "/usr/bin/libreoffice",
        "/usr/bin/soffice",
        "/usr/local/bin/libreoffice",
        "/usr/local/bin/soffice",
    ]
    
    # Windows uchun
    windows_paths = [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ]
    
    # Avval Linux yo'llarini tekshirish
    for path in linux_paths:
        if os.path.exists(path):
            return path
    
    # Keyin Windows yo'llarini tekshirish
    for path in windows_paths:
        if os.path.exists(path):
            return path
    
    return None


def convert_to_pdf_with_libreoffice(input_path, output_path=None):
    """
    LibreOffice yordamida faylni PDF formatiga aylantirish.
    
    Qo'llab-quvvatlanadigan formatlar:
    - Word: doc, docx
    - Excel: xls, xlsx
    - PowerPoint: ppt, pptx
    - LibreOffice: odt, ods, odp
    
    Args:
        input_path: Kiruvchi fayl yo'li
        output_path: Chiquvchi PDF fayl yo'li (ixtiyoriy)
    
    Returns:
        str: PDF fayl yo'li yoki None (xato bo'lsa)
    """
    libreoffice_path = get_libreoffice_path()
    
    if not libreoffice_path:
        raise Exception("LibreOffice topilmadi. Iltimos, LibreOffice o'rnating.")
    
    input_path = Path(input_path)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Fayl topilmadi: {input_path}")
    
    # Chiqish papkasini aniqlash
    if output_path:
        output_path = Path(output_path)
        output_dir = output_path.parent
    else:
        output_dir = input_path.parent
        output_path = input_path.with_suffix('.pdf')
    
    # Chiqish papkasini yaratish
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # LibreOffice buyrug'ini ishga tushirish
        cmd = [
            libreoffice_path,
            '--headless',
            '--convert-to', 'pdf',
            '--outdir', str(output_dir),
            str(input_path)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120  # 2 daqiqa timeout
        )
        
        if result.returncode != 0:
            raise Exception(f"LibreOffice xatosi: {result.stderr}")
        
        # LibreOffice standart nom bilan saqlaydi, agar boshqa nom kerak bo'lsa o'zgartirish
        expected_output = output_dir / (input_path.stem + '.pdf')
        
        if expected_output.exists():
            if str(expected_output) != str(output_path):
                os.rename(str(expected_output), str(output_path))
            return str(output_path)
        else:
            raise Exception("PDF fayl yaratilmadi")
            
    except subprocess.TimeoutExpired:
        raise Exception("LibreOffice konvertatsiya vaqti tugadi (timeout)")
    except Exception as e:
        raise Exception(f"Konvertatsiya xatosi: {str(e)}")


def convert_excel_to_pdf_with_libreoffice(input_path, output_path=None):
    """Excel faylini PDF ga aylantirish"""
    return convert_to_pdf_with_libreoffice(input_path, output_path)


def convert_powerpoint_to_pdf_with_libreoffice(input_path, output_path=None):
    """PowerPoint faylini PDF ga aylantirish"""
    return convert_to_pdf_with_libreoffice(input_path, output_path)


def convert_word_to_pdf_with_libreoffice(input_path, output_path=None):
    """Word faylini PDF ga aylantirish"""
    return convert_to_pdf_with_libreoffice(input_path, output_path)


def convert_libreoffice_format(input_path, output_format, output_path=None):
    """
    LibreOffice formatlarini bir-biriga aylantirish.
    
    Args:
        input_path: Kiruvchi fayl yo'li
        output_format: Chiquvchi format (pdf, odt, ods, odp, docx, xlsx, pptx)
        output_path: Chiquvchi fayl yo'li (ixtiyoriy)
    
    Returns:
        str: Chiquvchi fayl yo'li yoki None
    """
    libreoffice_path = get_libreoffice_path()
    
    if not libreoffice_path:
        raise Exception("LibreOffice topilmadi. Iltimos, LibreOffice o'rnating.")
    
    input_path = Path(input_path)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Fayl topilmadi: {input_path}")
    
    # Chiqish papkasini aniqlash
    if output_path:
        output_path = Path(output_path)
        output_dir = output_path.parent
    else:
        output_dir = input_path.parent
        output_path = input_path.with_suffix(f'.{output_format}')
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        cmd = [
            libreoffice_path,
            '--headless',
            '--convert-to', output_format,
            '--outdir', str(output_dir),
            str(input_path)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            raise Exception(f"LibreOffice xatosi: {result.stderr}")
        
        expected_output = output_dir / (input_path.stem + f'.{output_format}')
        
        if expected_output.exists():
            if str(expected_output) != str(output_path):
                os.rename(str(expected_output), str(output_path))
            return str(output_path)
        else:
            raise Exception(f"{output_format.upper()} fayl yaratilmadi")
            
    except subprocess.TimeoutExpired:
        raise Exception("LibreOffice konvertatsiya vaqti tugadi (timeout)")
    except Exception as e:
        raise Exception(f"Konvertatsiya xatosi: {str(e)}")


# Qo'llab-quvvatlanadigan formatlar ro'yxati
LIBREOFFICE_SUPPORTED_FORMATS = {
    'word_to_pdf': ['doc', 'docx', 'odt', 'rtf'],
    'excel_to_pdf': ['xls', 'xlsx', 'ods', 'csv'],
    'powerpoint_to_pdf': ['ppt', 'pptx', 'odp'],
    'libreoffice_formats': ['odt', 'ods', 'odp', 'odg', 'odf']
}


def is_libreoffice_available():
    """LibreOffice mavjudligini tekshirish"""
    return get_libreoffice_path() is not None


def get_supported_extensions():
    """Barcha qo'llab-quvvatlanadigan kengaytmalar ro'yxati"""
    all_extensions = set()
    for formats in LIBREOFFICE_SUPPORTED_FORMATS.values():
        all_extensions.update(formats)
    return list(all_extensions)
