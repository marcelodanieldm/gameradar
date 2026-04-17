@echo off
:: ============================================================
:: GameRadar AI — Power BI Bridge  |  start_api.bat
:: ============================================================
:: Inicia la API en el puerto 8000 (fijo y persistente).
:: Power BI puede conectarse en: http://127.0.0.1:8000/export/players
::
:: USO:
::   Doble clic en este archivo  → ventana de consola abierta
::   Ctrl+C en la consola        → detiene la API
::
:: INICIO AUTOMÁTICO (opcional):
::   Para que arranque sola al iniciar Windows:
::   1. Win+R → shell:startup
::   2. Crea un acceso directo de este .bat en esa carpeta
::   3. En el acceso directo → Propiedades → Ejecutar: Minimizada
:: ============================================================

title GameRadar AI — Power BI Bridge  [Puerto 8000]

:: Ir al directorio del proyecto
cd /d "%~dp0"

:: Verificar que el entorno virtual existe
IF NOT EXIST ".venv\Scripts\python.exe" (
    echo.
    echo  [ERROR] No se encontro el entorno virtual .venv
    echo  Crea el entorno con:  python -m venv .venv
    echo  Instala deps con:     .venv\Scripts\pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

:: Verificar silver_data.json
IF NOT EXIST "silver\silver_data.json" (
    echo.
    echo  [INFO] silver_data.json no encontrado.
    echo  Ejecuta POST http://127.0.0.1:8000/sync despues de iniciar la API
    echo  para descargar y procesar los datos de GitHub.
    echo.
)

echo.
echo  ============================================================
echo   GameRadar AI — Power BI Bridge
echo  ============================================================
echo   Puerto    : http://127.0.0.1:8000
echo   Power BI  : http://127.0.0.1:8000/export/players
echo   Docs      : http://127.0.0.1:8000/docs
echo   Sync      : POST http://127.0.0.1:8000/sync
echo  ============================================================
echo   Presiona Ctrl+C para detener la API
echo  ============================================================
echo.

:: Iniciar uvicorn con puerto fijo
:: reload=False garantiza que el puerto no cambie entre recargas
.venv\Scripts\uvicorn.exe api_powerbi:app --host 127.0.0.1 --port 8000 --log-level info

:: Si uvicorn falla, intentar con python directamente
IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo  [FALLBACK] Intentando con python directamente...
    .venv\Scripts\python.exe api_powerbi.py
)

echo.
echo  API detenida.
pause
