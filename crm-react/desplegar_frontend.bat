@echo off
echo ========================================
echo   DESPLIEGUE FRONTEND EN VERCEL
echo ========================================
echo.

REM Verificar que Vercel CLI está instalado
where vercel >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Vercel CLI no está instalado.
    echo.
    echo Instalando Vercel CLI...
    call npm install -g vercel
    echo.
)

echo [INFO] IMPORTANTE: Necesitas la URL de tu backend desplegado.
echo.
set /p BACKEND_URL="Ingresa la URL de tu backend (ej: https://tu-backend-xxxxx.vercel.app): "

if "%BACKEND_URL%"=="" (
    echo [ERROR] No ingresaste la URL del backend.
    echo.
    echo Sigue estos pasos:
    echo 1. Despliega primero el backend usando desplegar_backend.bat
    echo 2. Anota la URL que te da Vercel
    echo 3. Vuelve a ejecutar este script
    echo.
    pause
    exit /b 1
)

echo.
echo [1/3] Iniciando sesion en Vercel...
cd /d "%~dp0frontend"
call vercel login

echo.
echo [2/3] Desplegando frontend...
call vercel

echo.
echo [3/3] Configurando variable de entorno VITE_API_URL...
echo.
echo IMPORTANTE: Debes configurar manualmente la variable de entorno:
echo.
echo 1. Ve a Vercel Dashboard
echo 2. Ve a tu proyecto frontend
echo 3. Settings -^> Environment Variables
echo 4. Agrega: VITE_API_URL=%BACKEND_URL%/api
echo 5. Haz clic en "Save"
echo 6. Ve a Deployments -^> Latest -^> ... -^> Redeploy
echo.
echo O ejecuta este comando desde el directorio frontend:
echo vercel env add VITE_API_URL production
echo.
echo Cuando te pregunte el valor, ingresa: %BACKEND_URL%/api
echo.

pause
