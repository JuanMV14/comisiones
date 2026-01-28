@echo off
echo ========================================
echo   DESPLIEGUE BACKEND EN VERCEL
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

REM Verificar que existe el archivo .env o env.example
if not exist "backend\.env" (
    if exist "backend\env.example" (
        echo [ADVERTENCIA] No se encontro backend\.env
        echo.
        echo Por favor crea el archivo backend\.env con:
        echo SUPABASE_URL=tu_url_de_supabase
        echo SUPABASE_KEY=tu_key_de_supabase
        echo ENVIRONMENT=production
        echo.
        echo Puedes copiar env.example como base:
        echo copy backend\env.example backend\.env
        echo.
        pause
    )
)

echo [1/2] Iniciando sesion en Vercel...
cd /d "%~dp0backend"
call vercel login

echo.
echo [2/2] Desplegando backend...
call vercel

echo.
echo ========================================
echo   DESPLIEGUE COMPLETADO
echo ========================================
echo.
echo IMPORTANTE: Anota la URL que te dio Vercel
echo La necesitaras para configurar el frontend.
echo.
echo Siguiente paso:
echo 1. Ve a Vercel Dashboard
echo 2. Ve a tu proyecto backend
echo 3. Settings -^> Environment Variables
echo 4. Agrega las variables de entorno necesarias
echo.
pause
