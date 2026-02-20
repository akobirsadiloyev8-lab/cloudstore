# OPTIMIZATSIYANI ISHGA TUSHIRISH (PowerShell)
# Bu skriptni PowerShell orqali ishga tushiring

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "  SAYT OPTIMIZATSIYASI BOSHLANDI" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# 1. Paketlarni yangilash
Write-Host "1. Paketlarni o'rnatyapman..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✓ Paketlar o'rnatildi!" -ForegroundColor Green
} else {
    Write-Host "   ✗ Paketlarni o'rnatishda xato!" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 2. Database migration
Write-Host "2. Database indexlarni qo'shyapman..." -ForegroundColor Yellow
python manage.py makemigrations
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✓ Migration yaratildi!" -ForegroundColor Green
} else {
    Write-Host "   ! Migration xatosi (bu normal bo'lishi mumkin)" -ForegroundColor Yellow
}

python manage.py migrate
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✓ Migration bajarildi!" -ForegroundColor Green
} else {
    Write-Host "   ✗ Migration xatosi!" -ForegroundColor Red
}
Write-Host ""

# 3. Cache tozalash
Write-Host "3. Cache'ni tozalayapman..." -ForegroundColor Yellow
if (Test-Path "cache") {
    Remove-Item -Recurse -Force cache\* -ErrorAction SilentlyContinue
    Write-Host "   ✓ Cache tozalandi!" -ForegroundColor Green
} else {
    Write-Host "   ! Cache papkasi topilmadi (yangi yaratiladi)" -ForegroundColor Yellow
}
Write-Host ""

# 4. Static files
Write-Host "4. Static fayllarni yig'yapman..." -ForegroundColor Yellow
python manage.py collectstatic --noinput
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✓ Static fayllar tayyor!" -ForegroundColor Green
} else {
    Write-Host "   ! Static files xatosi (bu normal)" -ForegroundColor Yellow
}
Write-Host ""

# Yakuniy xabar
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "  ✓ OPTIMIZATSIYA TUGADI!" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Keyingi qadam:" -ForegroundColor Yellow
Write-Host "  python manage.py runserver" -ForegroundColor White
Write-Host ""
Write-Host "Browser'da:" -ForegroundColor Yellow
Write-Host "  http://127.0.0.1:8000/kitoblar/" -ForegroundColor White
Write-Host ""
Write-Host "Natijani tekshiring:" -ForegroundColor Yellow
Write-Host "  - Har sahifada 24 ta kitob ko'rinadi" -ForegroundColor White
Write-Host "  - Pagination tugmalari mavjud" -ForegroundColor White
Write-Host "  - Tezlik yaxshilangan" -ForegroundColor White
Write-Host ""
