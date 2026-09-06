@echo off
cd /d "%~dp0"
python -m pip install -r requirements.txt pyinstaller
python -m PyInstaller --noconfirm --clean costos_app.spec
echo.
echo Listo. El instalable esta en:
echo   %cd%\dist\CalculadoraCostos-PUBLISTIK.exe
pause
