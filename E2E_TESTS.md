# GameRadar AI - E2E Tests Guide

## 🎯 Estructura de Tests

### Backend Tests (Python + Playwright)
- **Archivo**: `test_e2e_playwright.py`
- **Tests**: 11 tests end-to-end
- **Coverage**:
  - Bronze Ingestion (Liquipedia, OP.GG)
  - Supabase Integration (Bronze/Silver/Gold)
  - Country Detection
  - Character Detection (Asian chars)
  - Error Handling
  - Performance

### Frontend Tests (TypeScript + Playwright)
- **Archivo**: `frontend/tests/e2e.spec.ts`
- **Tests**: 17 tests end-to-end
- **Coverage**:
  - TransculturalDashboard rendering
  - PlayerCard adaptativo (Mobile vs Technical)
  - View mode toggle
  - Region filter
  - Sorting & filtering
  - Responsive design
  - Accessibility
  - Performance

## 🚀 Ejecutar Tests

### Backend Tests

```bash
# Instalar dependencias
pip install pytest pytest-asyncio playwright
playwright install chromium

# Ejecutar todos los tests
python test_e2e_playwright.py

# Ejecutar con pytest
pytest test_e2e_playwright.py -v

# Ejecutar test específico
pytest test_e2e_playwright.py::test_bronze_ingestion_liquipedia -v
```

### Frontend Tests

```bash
# Instalar Playwright
cd frontend
npm install --save-dev @playwright/test

# Instalar browsers
npx playwright install

# Ejecutar tests
npm run test:e2e

# Ejecutar en modo headed (ver navegador)
npm run test:e2e:headed

# Ejecutar en modo debug
npm run test:e2e:debug

# Ejecutar en UI mode (interactivo)
npm run test:e2e:ui

# Ejecutar solo en Chrome
npm run test:e2e:chromium

# Ver reporte HTML
npm run test:e2e:report
```

## 📋 Tests Backend Detallados

### TEST 1: Bronze Ingestion - Liquipedia
- Scrapea datos de Liquipedia
- Verifica estructura de datos
- Detecta caracteres asiáticos
- ✅ Assertion: `len(players_data) > 0`

### TEST 2: Bronze Ingestion - OP.GG
- Scrapea ranking de OP.GG Korea
- Verifica región y fuente
- ✅ Assertion: `region == "KR"`

### TEST 3: Country Detection
- Detección por bandera (🇰🇷 → KR)
- Detección por servidor (mumbai → IN)
- Detección por URL (vn.op.gg → VN)
- Detección por texto (China Server → CN)
- ✅ Assertion: Todos los métodos funcionan

### TEST 4: Supabase - Bronze Insert
- Inserta datos de prueba en Bronze
- Verifica inserción exitosa
- ✅ Assertion: `result is not None`

### TEST 5: Supabase - Silver Normalization
- Verifica normalización automática Bronze → Silver
- Espera trigger de PostgreSQL
- ✅ Assertion: Datos en Silver con talent_score

### TEST 6: Supabase - Gold Score Calculation
- Consulta jugadores en Gold con gameradar_score
- Verifica rango 0-100
- ✅ Assertion: `0 <= score <= 100`

### TEST 7: Full Pipeline
- Ejecuta pipeline completo
- Bronze → Silver → Gold
- ✅ Assertion: `players_processed > 0`

### TEST 8: Asian Character Detection
- Coreano: 페이커 (Faker)
- Chino: 中国玩家
- Japonés: プレイヤー
- ✅ Assertion: Todos detectados correctamente

### TEST 9: Error Handling
- Intenta scrapear URL inválida
- Verifica que no lanza excepción
- ✅ Assertion: `error_count >= 0`

### TEST 10: Search & Queries
- Query por región (KR)
- Estadísticas regionales
- ✅ Assertion: Resultados correctos

### TEST 11: Performance
- Mide tiempo de scraping + insert
- ✅ Assertion: `elapsed < 30s`

## 📋 Tests Frontend Detallados

### TEST 1: Dashboard Rendering
- Verifica que carga correctamente
- Sin errores visibles
- ✅ Assertion: Título "GameRadar" visible

### TEST 2: Stats Cards
- Total Players, Top Talent, Regions
- ✅ Assertion: Cards visibles

### TEST 3: Region Filter
- Dropdown de regiones
- Selección funciona
- ✅ Assertion: Valor cambia

### TEST 4: View Mode Toggle
- Botones Auto/Cards/Table
- Cambia layout correctamente
- ✅ Assertion: Clase CSS activa

### TEST 5: Mobile-Heavy Cards
- Botón WhatsApp visible
- Color verde característico
- ✅ Assertion: WhatsApp button presente

### TEST 6: Technical Cards
- Tabla con múltiples columnas
- Filas de datos
- ✅ Assertion: `columns > 5`

### TEST 7: Sorting
- Click en headers
- Icono de sort aparece
- ✅ Assertion: Sort icon visible

### TEST 8: Card Interactions
- Hover effects
- Botones de acción
- ✅ Assertion: `buttons > 0`

### TEST 9: Verified Badge
- Badge "Verified" o "✓"
- ✅ Assertion: Badges encontrados

### TEST 10: Score Badges
- Valores 0-100
- ✅ Assertion: Rango válido

### TEST 11: Responsive Design
- Desktop (1920x1080)
- Tablet (768x1024)
- Mobile (375x667)
- ✅ Assertion: Visible en todos

### TEST 12: Dark Mode
- Background oscuro
- ✅ Assertion: Color RGB oscuro

### TEST 13: Loading States
- Spinner durante carga
- ✅ Assertion: Loading visible

### TEST 14: Error Handling
- Simula error de red
- Mensaje de error visible
- ✅ Assertion: Error message mostrado

### TEST 15: Accessibility
- Botones focuseables
- Imágenes con alt text
- ✅ Assertion: Accesibilidad OK

### TEST 16: Performance
- Load time < 5s
- ✅ Assertion: `loadTime < 5000ms`

### TEST 17: Supabase Data Fetching
- API calls interceptadas
- ✅ Assertion: Supabase llamado

## 🎨 Output Esperado

### Backend Tests
```
==============================================================
🚀 GAMERADAR AI - E2E TESTS
==============================================================

🧪 TEST 1: Bronze Ingestion - Liquipedia
   ✓ Scraped 50 jugadores de Liquipedia

🧪 TEST 2: Bronze Ingestion - OP.GG
   ✓ Scraped 10 jugadores de OP.GG

🧪 TEST 3: Country Detection
   ✓ Detección por bandera: 🇰🇷 → KR
   ✓ Detección por servidor: mumbai → IN
   ✓ Detección por URL: vn.op.gg → VN
   ✓ Detección por texto: China Server → CN

...

==============================================================
📊 RESUMEN DE TESTS
==============================================================
✅ Passed: 11/11
❌ Failed: 0/11
==============================================================
```

### Frontend Tests
```
Running 17 tests using 4 workers

  ✓ [chromium] › e2e.spec.ts:15:7 › Dashboard debe renderizar correctamente (2.5s)
  ✓ [chromium] › e2e.spec.ts:30:7 › Stats cards deben mostrar datos (1.8s)
  ✓ [chromium] › e2e.spec.ts:45:7 › Region filter debe funcionar (2.1s)
  ...
  ✓ [chromium] › e2e.spec.ts:350:7 › Datos de Supabase deben cargarse (3.2s)

  17 passed (45s)
```

## 🔧 Configuración

### Variables de Entorno

```bash
# Backend (.env)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-key

# Frontend (.env.local)
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
FRONTEND_URL=http://localhost:3000
```

## 📝 Comandos Útiles

```bash
# Backend: Ejecutar tests con coverage
pytest test_e2e_playwright.py --cov=. --cov-report=html

# Frontend: Ejecutar tests en paralelo
npx playwright test --workers=4

# Frontend: Generar screenshots
npx playwright test --screenshot=on

# Frontend: Generar videos
npx playwright test --video=on

# Frontend: Test específico
npx playwright test e2e.spec.ts:15

# Frontend: Modo interactivo
npx playwright test --ui
```

## 🐛 Debugging

### Backend
```python
# Agregar breakpoint
import pdb; pdb.set_trace()

# Ejecutar con verbose
pytest test_e2e_playwright.py -v -s
```

### Frontend
```bash
# Modo debug (pausa en cada paso)
npx playwright test --debug

# Modo headed (ver navegador)
npx playwright test --headed --slowMo=500

# Trace viewer
npx playwright show-trace trace.zip
```

## 🚀 CI/CD Integration

### GitHub Actions

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          playwright install chromium
      - name: Run backend tests
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
        run: python test_e2e_playwright.py

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install dependencies
        run: |
          cd frontend
          npm install
          npx playwright install --with-deps
      - name: Run frontend tests
        run: |
          cd frontend
          npm run test:e2e
      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: frontend/playwright-report/
```

## 📊 Coverage Actual

- **Backend**: 11 tests cubriendo ingesta, normalización, y scores
- **Frontend**: 17 tests cubriendo rendering, interacciones, y UX
- **Total**: 28 tests E2E end-to-end

## 🎯 Próximos Tests

- [ ] Tests de integración con Airtable
- [ ] Tests de GitHub Actions workflows
- [ ] Tests de gold_analytics.sql
- [ ] Tests de proxy rotation
- [ ] Visual regression tests
- [ ] Load testing con k6

---

**Nota**: Todos los tests están diseñados para ejecutarse en CI/CD y localmente sin modificaciones.
