@echo off
chcp 65001 >nul
title Kitap Köşkü - exe derleme
cd /d "%~dp0"

tasklist /FI "IMAGENAME eq KitapKosku.exe" | find /I "KitapKosku.exe" >nul && (echo Once acik olan Kitap Kosku uygulamasini kapatin. & pause & exit /b 1)

echo [1/4] Python paketleri kontrol ediliyor...
python -m pip install -q -r requirements.txt pyinstaller || (echo Paket kurulumu basarisiz. & pause & exit /b 1)

echo [2/4] Kitaplar, sozluk ve ceviri modeli kontrol ediliyor (eksikse bir kez internet gerekir)...
if not exist "%~dp0books\catalog.json" (python tools\build_library.py || (echo Kutuphane kurulamadi. & pause & exit /b 1))
if not exist "%~dp0books\dict-en-tr.json.gz" (python tools\build_dict.py || (echo Sozluk kurulamadi. & pause & exit /b 1))
if not exist "%~dp0tools\_models\en-tr-big\model.bin" (
  python -m pip install -q "transformers>=4.40" sacremoses || (echo Donusturucu kurulamadi. & pause & exit /b 1)
  ct2-transformers-converter --model Helsinki-NLP/opus-mt-tc-big-en-tr --output_dir "%~dp0tools\_models\en-tr-big" --quantization int8 --copy_files source.spm target.spm || (echo Ceviri modeli hazirlanamadi. & pause & exit /b 1)
)

echo [3/4] KitapKosku olusturuluyor (klasor halinde, hizli acilsin diye)...
set "BUILD=%TEMP%\kitap-kosku-build"
python -m PyInstaller --noconfirm --onedir --windowed --name KitapKosku --icon "%~dp0icon.ico" ^
  --add-data "%~dp0web;web" --add-data "%~dp0books;books" --add-data "%~dp0tools\_models\en-tr-big;mt-model" ^
  --hidden-import ceviri --hidden-import mt --collect-binaries ctranslate2 ^
  --exclude-module torch --exclude-module transformers --exclude-module tokenizers --exclude-module safetensors ^
  --exclude-module huggingface_hub --exclude-module sacremoses --exclude-module pandas --exclude-module matplotlib ^
  --exclude-module IPython --exclude-module PIL ^
  --distpath "%~dp0dist" --workpath "%BUILD%\work" --specpath "%BUILD%" "%~dp0app.py" || (echo Derleme basarisiz. & pause & exit /b 1)

echo [4/4] Masaustune kisayol koyuluyor...
powershell -NoProfile -Command "$d=[Environment]::GetFolderPath('Desktop'); $s=(New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $d 'Kitap Köşkü.lnk')); $s.TargetPath='%~dp0dist\KitapKosku\KitapKosku.exe'; $s.WorkingDirectory='%~dp0dist\KitapKosku'; $s.IconLocation='%~dp0dist\KitapKosku\KitapKosku.exe,0'; $s.Save()"
echo.
echo Tamamlandi: dist\KitapKosku\KitapKosku.exe (masaustunde "Kitap Köşkü" kisayolu)
pause
