@echo off
title SPK Hibrida AHP-TOPSIS Futsal
cd /d "%~dp0"

echo ============================================================
echo   SPK Hibrida AHP-TOPSIS - Penentuan Posisi Pemain Futsal
echo ============================================================
echo.

rem 1. Cek Python
where python >nul 2>nul
if errorlevel 1 (
  echo [X] Python belum terpasang.
  echo     Unduh dari https://www.python.org/downloads/ lalu centang
  echo     "Add python.exe to PATH" saat instalasi, kemudian jalankan file ini lagi.
  echo.
  pause
  exit /b 1
)

rem 2. Pasang library yang dibutuhkan (hanya saat pertama kali)
python -c "import flask, openpyxl, reportlab" >nul 2>nul
if errorlevel 1 (
  echo [..] Menyiapkan library untuk pertama kali, mohon tunggu...
  python -m pip install -q -r requirements.txt
  if errorlevel 1 (
    echo [X] Gagal memasang library. Periksa koneksi internet lalu coba lagi.
    pause
    exit /b 1
  )
)

rem 3. Buka browser setelah server siap (sekitar 3 detik)
echo [OK] Aplikasi berjalan di http://localhost:5000
echo      Browser akan terbuka otomatis.
echo.
echo      JANGAN TUTUP jendela ini selama aplikasi dipakai.
echo      Untuk berhenti: tutup jendela ini atau tekan Ctrl+C.
echo.
start "" /b cmd /c "timeout /t 3 /nobreak >nul & start "" http://localhost:5000"

rem 4. Jalankan aplikasi
python app.py
echo.
echo Aplikasi berhenti.
pause
