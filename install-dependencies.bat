@echo off
echo ============================================
echo GameRadar - Instalacion de Dependencias
echo ============================================
echo.

cd /d "%~dp0frontend"

echo [1/5] Limpiando instalaciones previas...
if exist node_modules (
    echo Eliminando node_modules...
    rmdir /s /q node_modules 2>nul
)
if exist package-lock.json (
    echo Eliminando package-lock.json...
    del /f /q package-lock.json 2>nul
)

echo.
echo [2/5] Limpiando cache de npm...
call npm cache clean --force

echo.
echo [3/5] Instalando dependencias principales...
call npm install next@^14.1.0 react@^18.2.0 react-dom@^18.2.0

echo.
echo [4/5] Instalando dependencias de autenticacion...
call npm install @supabase/supabase-js@^2.39.3 @supabase/auth-helpers-nextjs@^0.10.0 zod@^3.22.4

echo.
echo [5/5] Instalando dependencias restantes...
call npm install --legacy-peer-deps

echo.
echo ============================================
if %ERRORLEVEL% EQU 0 (
    echo ✓ Instalacion completada exitosamente!
    echo.
    echo Proximo paso:
    echo 1. Crear archivo .env.local con credenciales de Supabase
    echo 2. Ejecutar: npm run dev
) else (
    echo ✗ Hubo un error en la instalacion
    echo.
    echo Solucion alternativa:
    echo 1. Cerrar esta ventana
    echo 2. Abrir una nueva terminal
    echo 3. Ejecutar: cd frontend ^&^& npm install --force
)
echo ============================================
echo.
pause
