@echo off
echo Iniciando Frontend CRM...
cd /d "%~dp0frontend"

REM Verificar que node_modules existe
if not exist "node_modules" (
    echo.
    echo [INFO] Instalando dependencias por primera vez...
    call npm.cmd install
    echo.
)

call npm.cmd run dev
