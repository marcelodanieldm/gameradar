@echo off
echo ============================================
echo GameRadar - Verificacion de Estado
echo ============================================
echo.

cd /d "%~dp0frontend"

echo [Verificando instalacion...]
echo.

REM Verificar Node.js
echo 1. Node.js:
node -v >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    node -v
    echo    [OK]
) else (
    echo    [ERROR] Node.js no instalado
)
echo.

REM Verificar npm
echo 2. npm:
npm -v >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    npm -v
    echo    [OK]
) else (
    echo    [ERROR] npm no instalado
)
echo.

REM Verificar node_modules
echo 3. node_modules:
if exist "node_modules\" (
    echo    [OK] Carpeta existe
) else (
    echo    [ERROR] No existe - ejecuta: npm install
)
echo.

REM Verificar dependencias críticas
echo 4. Dependencias Supabase:
if exist "node_modules\@supabase\auth-helpers-nextjs\" (
    echo    [OK] @supabase/auth-helpers-nextjs
) else (
    echo    [ERROR] @supabase/auth-helpers-nextjs faltante
)

if exist "node_modules\@supabase\supabase-js\" (
    echo    [OK] @supabase/supabase-js
) else (
    echo    [ERROR] @supabase/supabase-js faltante
)
echo.

echo 5. Dependencias Next.js:
if exist "node_modules\next\" (
    echo    [OK] next
) else (
    echo    [ERROR] next faltante
)

if exist "node_modules\react\" (
    echo    [OK] react
) else (
    echo    [ERROR] react faltante
)

if exist "node_modules\zod\" (
    echo    [OK] zod
) else (
    echo    [ERROR] zod faltante
)
echo.

REM Verificar .env.local
echo 6. Configuracion (.env.local):
if exist ".env.local" (
    findstr /C:"NEXT_PUBLIC_SUPABASE_URL=" .env.local >nul
    if %ERRORLEVEL% EQU 0 (
        findstr /C:"your_supabase_url_here" .env.local >nul
        if %ERRORLEVEL% EQU 0 (
            echo    [WARN] Archivo existe pero necesita configuracion
            echo           Edita .env.local con tus credenciales de Supabase
        ) else (
            echo    [OK] Configurado
        )
    ) else (
        echo    [ERROR] Formato invalido
    )
) else (
    echo    [ERROR] No existe - crea .env.local
)
echo.

REM Verificar archivos de autenticacion
echo 7. Archivos de Autenticacion:
if exist "app\[locale]\login\page.tsx" (
    echo    [OK] Login page
) else (
    echo    [ERROR] Login page faltante
)

if exist "app\[locale]\signup\page.tsx" (
    echo    [OK] Signup page
) else (
    echo    [ERROR] Signup page faltante
)

if exist "lib\supabase\client.ts" (
    echo    [OK] Supabase client
) else (
    echo    [ERROR] Supabase client faltante
)
echo.

echo 8. Middleware de Seguridad:
if exist "middleware.ts" (
    findstr /C:"createMiddlewareClient" middleware.ts >nul
    if %ERRORLEVEL% EQU 0 (
        echo    [OK] Middleware configurado
    ) else (
        echo    [WARN] Middleware sin autenticacion
    )
) else (
    echo    [ERROR] Middleware faltante
)
echo.

echo ============================================
echo RESUMEN
echo ============================================
echo.

set ALL_OK=1

if not exist "node_modules\" set ALL_OK=0
if not exist "node_modules\@supabase\auth-helpers-nextjs\" set ALL_OK=0
if not exist "node_modules\next\" set ALL_OK=0
if not exist ".env.local" set ALL_OK=0

if %ALL_OK% EQU 1 (
    echo Estado: LISTO PARA DESARROLLO
    echo.
    echo Proximos pasos:
    echo 1. Verifica .env.local tenga credenciales reales
    echo 2. Ejecuta migracion SQL en Supabase
    echo 3. Ejecuta: npm run dev
) else (
    echo Estado: CONFIGURACION INCOMPLETA
    echo.
    echo Acciones requeridas:
    if not exist "node_modules\" (
        echo - Ejecutar: npm install
    )
    if not exist ".env.local" (
        echo - Crear .env.local con credenciales de Supabase
    )
    echo.
    echo Ver PASOS_FINALES.md para detalles
)

echo ============================================
echo.
pause
