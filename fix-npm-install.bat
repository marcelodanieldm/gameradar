@echo off
setlocal

echo ============================================
echo GameRadar - Fix npm install
echo ============================================
echo.

cd /d "%~dp0frontend"

echo [1/6] Limpiando archivos anteriores...
if exist node_modules rmdir /s /q node_modules 2>nul
if exist package-lock.json del /f /q package-lock.json 2>nul
echo OK.

echo.
echo [2/6] Limpiando cache de npm...
call npm cache clean --force 2>nul
echo OK.

echo.
echo [3/6] Instalando Next.js y React...
call npm install next@14.1.0 react@18.2.0 react-dom@18.2.0 --save --legacy-peer-deps
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: No se pudo instalar Next.js y React
    pause
    exit /b 1
)
echo OK.

echo.
echo [4/6] Instalando Supabase...
call npm install @supabase/supabase-js@2.39.8 @supabase/auth-helpers-nextjs@0.10.0 --save --legacy-peer-deps
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: No se pudo instalar Supabase
    pause
    exit /b 1
)
echo OK.

echo.
echo [5/6] Instalando otras dependencias...
call npm install next-intl@3.9.0 clsx@2.1.0 lucide-react@0.323.0 zod@3.22.4 --save --legacy-peer-deps
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: No se pudo instalar dependencias adicionales
    pause
    exit /b 1
)
echo OK.

echo.
echo [6/6] Instalando devDependencies...
call npm install --save-dev @types/node@20.11.16 @types/react@18.2.52 @types/react-dom@18.2.18 typescript@5.3.3 tailwindcss@3.4.1 postcss@8.4.35 autoprefixer@10.4.17 eslint@8.56.0 eslint-config-next@14.1.0 --legacy-peer-deps
if %ERRORLEVEL% NEQ 0 (
    echo ADVERTENCIA: Algunas devDependencies no se instalaron
)
echo OK.

echo.
echo ============================================
echo ✓ Instalacion completada!
echo ============================================
echo.
echo Verificando instalacion...
if exist "node_modules\@supabase\auth-helpers-nextjs" (
    echo ✓ Supabase Auth instalado correctamente
) else (
    echo ✗ Supabase Auth no encontrado
)

if exist "node_modules\next" (
    echo ✓ Next.js instalado correctamente
) else (
    echo ✗ Next.js no encontrado
)

echo.
echo Proximos pasos:
echo 1. Crear .env.local con credenciales de Supabase
echo 2. Ejecutar: cd frontend ^&^& npm run dev
echo.
pause
