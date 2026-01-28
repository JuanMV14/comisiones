@echo off
echo ========================================
echo   INICIANDO CRM - Backend y Frontend
echo ========================================
echo.

REM Verificar que existe el archivo .env en backend
if not exist "backend\.env" (
    echo [ADVERTENCIA] No se encontro backend\.env
    echo.
    echo Por favor crea el archivo backend\.env con:
    echo SUPABASE_URL=tu_url_de_supabase
    echo SUPABASE_KEY=tu_key_de_supabase
    echo.
    echo Puedes copiar env.example como base:
    echo copy backend\env.example backend\.env
    echo.
    pause
    exit /b 1
)

echo [1/2] Iniciando Backend en nueva ventana...
start "CRM Backend" cmd /k "cd /d %~dp0backend && python main.py"
timeout /t 3 /nobreak >nul

echo [2/2] Iniciando Frontend en nueva ventana...
start "CRM Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ========================================
echo   CRM INICIADO
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173 (o el puerto que muestre Vite)
echo.
echo Presiona cualquier tecla para cerrar esta ventana...
pause >nul
