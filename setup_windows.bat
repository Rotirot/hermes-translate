@echo off
REM ─────────────────────────────────────────────────────────────────
REM  Hermes Translate — Windows Setup
REM  Run once after cloning. Re-run quarterly to update language packs.
REM ─────────────────────────────────────────────────────────────────

echo.
echo  Hermes Translate — Setup
echo  ═══════════════════════
echo.

python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo  [ERROR] Python not found.
    echo         Download from https://python.org — tick "Add to PATH"
    pause & exit /b 1
)

echo  [1/3] Installing Python dependencies...
pip install -r requirements.txt
echo.

echo  [2/3] Downloading language packs (~1-2 GB total)...
python -c "
import argostranslate.package as pkg

PAIRS = [
    ('en','fr'),('fr','en'),
    ('en','de'),('de','en'),
    ('en','tr'),('tr','en'),
    ('fr','de'),('de','fr'),
]

print('  Fetching package index...')
pkg.update_package_index()
available  = pkg.get_available_packages()
installed  = {(p.from_code, p.to_code) for p in pkg.get_installed_packages()}

for fc, tc in PAIRS:
    if (fc, tc) in installed:
        print(f'  Already installed: {fc} -> {tc}')
        continue
    match = next((p for p in available if p.from_code==fc and p.to_code==tc), None)
    if match:
        print(f'  Installing {fc} -> {tc}...')
        try:
            pkg.install_from_path(match.download())
            print(f'    OK')
        except Exception as e:
            print(f'    FAILED: {e}')
    else:
        print(f'  Not found: {fc} -> {tc}')
"

echo.
echo  [3/3] Creating desktop shortcut...
set "DIR=%~dp0"
set "LINK=%USERPROFILE%\Desktop\Hermes Translate.lnk"
powershell -Command ^
  "$ws=$env:WSCRIPTSHELL; if(!$ws){$ws=(New-Object -ComObject WScript.Shell)}; $s=$ws.CreateShortcut('%LINK%'); $s.TargetPath='pythonw'; $s.Arguments='\"%DIR%hermes.py\"'; $s.WorkingDirectory='%DIR%'; $s.IconLocation='python.exe,0'; $s.Save()"

echo.
echo  ═══════════════════════════════════════════════
echo   Done! Launch via desktop shortcut or:
echo     python hermes.py
echo  ═══════════════════════════════════════════════
echo.
pause
