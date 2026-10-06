@echo off
title Reset Data Awal - SPK Futsal
cd /d "%~dp0"
echo ============================================================
echo   RESET DATA AWAL
echo ============================================================
echo.
echo Semua data akan dikembalikan ke kondisi awal (16 pemain dummy):
echo pemain, skill, kriteria, matriks AHP, hasil tersimpan, akun, dan log.
echo Data yang sudah Anda ubah atau tambahkan akan HILANG.
echo.
echo Pastikan aplikasi sedang TIDAK berjalan (tutup jendela "Jalankan Aplikasi").
echo.
set /p OK=Ketik YA lalu Enter untuk melanjutkan:
if /i not "%OK%"=="YA" (
  echo Dibatalkan. Tidak ada data yang diubah.
  pause
  exit /b 0
)
if exist sppk_futsal.db python -c "import shutil,datetime; shutil.copy('sppk_futsal.db','sppk_futsal.cadangan-'+datetime.datetime.now().strftime('%%Y%%m%%d-%%H%%M')+'.db')"
python -c "from db import init_db; init_db(reset=True)"
if errorlevel 1 (
  echo [X] Reset gagal. Pastikan aplikasi tidak sedang berjalan.
) else (
  echo [OK] Data sudah dikembalikan ke kondisi awal.
  echo      Cadangan data lama disimpan sebagai sppk_futsal.cadangan-*.db
)
pause
