@echo off
REM Script para cerrar el proceso que está usando el puerto 8000

echo ========================================
echo   CERRANDO PROCESO EN PUERTO 8000
echo ========================================
echo.

REM Buscar el proceso que usa el puerto 8000
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    set PID=%%a
    echo [INFO] Proceso encontrado en puerto 8000: PID %%a
    echo.
    echo [INFO] Cerrando proceso...
    taskkill /PID %%a /F
    if errorlevel 1 (
        echo [ERROR] No se pudo cerrar el proceso. Puede requerir permisos de administrador.
    ) else (
        echo [OK] Proceso cerrado correctamente.
    )
)

echo.
echo ========================================
echo   PROCESO CERRADO
echo ========================================
echo.
echo Ahora puedes iniciar el backend nuevamente:
echo   cd crm-react\backend
echo   python main.py
echo.
pause
