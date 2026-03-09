# 📂 GameRadar AI - Índice del Proyecto

## 🎯 Descripción
SaaS de scouting de jugadores de e-sports para regiones de Asia e India con motor de ingesta automatizado.

---

## 📁 Estructura del Proyecto

```
gameradar/
│
├── 📄 Core Python Files
│   ├── models.py                    # 🏗️ Modelos Pydantic (PlayerProfile, Stats, Champion)
│   ├── config.py                    # ⚙️ Configuración centralizada
│   ├── country_detector.py          # 🌍 Detección de país (banderas, servidores, URLs)
│   ├── scrapers.py                  # 🕷️ Scrapers para OP.GG y Liquipedia
│   ├── cnn_brasil_scraper.py        # 🥷 Ninja scraper para CNN Brasil
│   ├── proxy_rotator.py             # 🔄 Sistema de rotación de proxies
│   ├── supabase_client.py           # 💾 Cliente de Supabase (Bronze/Silver/Gold)
│   ├── airtable_client.py           # 📤 Cliente de Airtable
│   ├── pipeline.py                  # 🚀 Orquestación del flujo completo
│   ├── payment_gateway.py           # 💳 Sprint 3: Razorpay + Stripe
│   ├── notification_service.py      # 🔔 Sprint 3: WhatsApp/Telegram/Email
│   └── api_routes_sprint3.py        # 🌐 Sprint 3: FastAPI endpoints
│
├── 🧪 Testing & Examples
│   ├── test_ninja_scraper.py        # 🧪 Tests del scraper ninja
│   └── examples.py                  # 📝 7 ejemplos de uso
│
├── 🗄️ Database
│   └── database_schema.sql          # 🏛️ Schema PostgreSQL (Bronze/Silver/Gold + Sprint 3)
│
├── ⚙️ GitHub Actions
│   └── .github/workflows/
│       └── ninja_scraper.yml        # 🤖 Workflow automático (cada 6 horas)
│
├── 📚 Documentación
│   ├── README.md                    # 📖 Documentación principal
│   ├── NINJA_SCRAPER.md            # 🥷 Guía del scraper ninja
│   ├── NINJA_SUMMARY.md            # 📊 Resumen ejecutivo
│   ├── GITHUB_SETUP.md             # 🚀 Setup de GitHub Actions
│   ├── COMMANDS.md                  # 💻 Comandos útiles
│   ├── SPRINT3_CASHFLOW_ENGAGEMENT.md  # 💰 Sprint 3: Pagos & Alertas
│   ├── SPRINT3_QUICK_REFERENCE.md  # ⚡ Sprint 3: Quick Reference
│   └── INDEX.md                     # 📂 Este archivo
│
├── 🎨 Frontend (Next.js)
│   ├── components/
│   │   ├── RegionalPayment.tsx     # 💳 Sprint 3: Payment UI
│   │   └── TalentPingSubscription.tsx  # 🔔 Sprint 3: Alert subscriptions
│   └── app/api/
│       ├── payment/                 # 💳 Payment endpoints
│       └── talent-ping/             # 🔔 Notification endpoints
│
└── 🔧 Configuración
    ├── requirements.txt             # 📦 Dependencias Python (+ Sprint 3)
    ├── .env.example                 # 🔐 Template de variables de entorno
    ├── setup_sprint3.sh            # 🚀 Setup script (Linux/Mac)
    ├── setup_sprint3.bat           # 🚀 Setup script (Windows)
    └── .gitignore                   # 🚫 Archivos ignorados por Git
```

---

## 📖 Guía de Lectura

### 🚀 Para empezar:
1. **README.md** - Overview del proyecto
2. **GITHUB_SETUP.md** - Configuración paso a paso
3. **NINJA_SUMMARY.md** - Resumen ejecutivo

### 💻 Para desarrolladores:
1. **models.py** - Entender estructura de datos
2. **scrapers.py** - Lógica de scraping
3. **cnn_brasil_scraper.py** - Scraper ninja
4. **pipeline.py** - Flujo completo
5. **payment_gateway.py** - Sprint 3: Pagos regionales
6. **notification_service.py** - Sprint 3: Sistema de alertas

### 💳 Para Sprint 3 (Cashflow & Engagement):
1. **SPRINT3_CASHFLOW_ENGAGEMENT.md** - Documentación completa
2. **SPRINT3_QUICK_REFERENCE.md** - Quick reference
3. **setup_sprint3.sh / .bat** - Setup automatizado

### 🧪 Para testing:
1. **test_ninja_scraper.py** - Ejecutar tests
2. **examples.py** - Ver casos de uso
3. **COMMANDS.md** - Comandos útiles

### 🗄️ Para base de datos:
1. **database_schema.sql** - Schema SQL completo
2. **supabase_client.py** - Queries y operaciones

### 🥷 Para scraper ninja:
1. **NINJA_SCRAPER.md** - Guía completa
2. **cnn_brasil_scraper.py** - Código principal
3. **proxy_rotator.py** - Configuración de proxies

---

## 🎯 Flujos Principales

### Flujo 1: Setup Inicial
```
GITHUB_SETUP.md → Crear repo → Configurar secrets → Push código → Activar workflow
```

### Flujo 2: Scraping Manual
```
scrapers.py → Ejecutar script → Bronze → Silver (auto) → Airtable (opcional)
```

### Flujo 3: Scraping Ninja (Automatizado)
```
GitHub Actions (cron) → cnn_brasil_scraper.py → Bronze → Silver (auto)
```

### Flujo 4: Pipeline Completo
```
pipeline.py → Scraping → Bronze → Silver → Gold → Airtable
```

### Flujo 5: Consultas
```
supabase_client.py → Queries → Visualización
```

### Flujo 6: Sprint 3 - Cashflow & Engagement
```
User → RegionalPayment → Payment Gateway (Razorpay/Stripe) → Database
User → TalentPingSubscription → Notification Service → WhatsApp/Telegram/Email
Backend → Talent Alert → Multi-channel Delivery → PDF Reports (Professional)
```

---

## 🔑 Archivos Clave por Funcionalidad

### 🕷️ Web Scraping
- `scrapers.py` - Base scrapers (OP.GG, Liquipedia)
- `cnn_brasil_scraper.py` - Ninja scraper
- `proxy_rotator.py` - Proxy management

### 📊 Datos y Validación
- `models.py` - Schemas con Pydantic
- `country_detector.py` - Detección de región

### 💾 Persistencia
- `supabase_client.py` - Operaciones CRUD
- `airtable_client.py` - Exportación
- `database_schema.sql` - Schema SQL

### 🚀 Automatización
- `.github/workflows/ninja_scraper.yml` - GitHub Actions
- `pipeline.py` - Orquestación

### 🧪 Testing
- `test_ninja_scraper.py` - Tests automatizados
- `examples.py` - Ejemplos de uso

### 💳 Sprint 3: Cashflow
- `payment_gateway.py` - Razorpay + Stripe integration
- `frontend/components/RegionalPayment.tsx` - Payment UI
- `frontend/app/api/payment/` - Payment endpoints

### 🔔 Sprint 3: Engagement
- `notification_service.py` - WhatsApp/Telegram/Email + PDF
- `frontend/components/TalentPingSubscription.tsx` - Alert subscription UI
- `frontend/app/api/talent-ping/` - Notification endpoints

---

## 🎨 Características por Archivo

### models.py
- ✅ Soporte Unicode (Hindi, Chino, Coreano)
- ✅ Validación con Pydantic
- ✅ Enums para países y juegos
- ✅ Modelos Bronze/Silver/Gold
- ✅ Conversión a Airtable

### cnn_brasil_scraper.py
- ✅ Playwright asíncrono
- ✅ Anti-detección (stealth)
- ✅ Proxy rotation
- ✅ User-agent rotation
- ✅ Retry logic (3 intentos)
- ✅ Error handling silencioso
- ✅ Detección de India automática
- ✅ Upsert a Supabase

### database_schema.sql
- ✅ Arquitectura Bronze/Silver/Gold
- ✅ Triggers automáticos
- ✅ Funciones SQL
- ✅ Vistas de estadísticas
- ✅ Row Level Security
- ✅ Soporte Unicode completo

### .github/workflows/ninja_scraper.yml
- ✅ Ejecución cada 6 horas
- ✅ Secrets management
- ✅ Artifact upload
- ✅ Summary reports
- ✅ Continue on error

---

## 📊 Estadísticas del Proyecto

```
📦 Archivos Python: 11
🧪 Tests: 2
📖 Docs: 6
⚙️ Config: 4
🗄️ SQL: 1
---
📝 Líneas de código: ~3,500
📚 Líneas de docs: ~2,000
🎯 Total: ~5,500 líneas
```

---

## 🚀 Quick Access

### Para ejecutar:
```bash
# Scraper ninja
python cnn_brasil_scraper.py

# Tests
python test_ninja_scraper.py

# Ejemplos
python examples.py

# Pipeline completo
python pipeline.py
```

### Para documentación:
```bash
# Abrir README
cat README.md

# Abrir guía ninja
cat NINJA_SCRAPER.md

# Ver comandos
cat COMMANDS.md
```

---

## 🎯 Casos de Uso

### 1. Setup desde cero
→ **GITHUB_SETUP.md**

### 2. Scrapear jugadores manualmente
→ **examples.py** (Ejemplo 1-2)

### 3. Automatizar scraping
→ **NINJA_SCRAPER.md**

### 4. Consultar datos
→ **examples.py** (Ejemplo 3)

### 5. Configurar proxies
→ **proxy_rotator.py** + **NINJA_SCRAPER.md**

### 6. Debugging
→ **COMMANDS.md** (Sección Debugging)

### 7. Deploy a producción
→ **GITHUB_SETUP.md** + **NINJA_SUMMARY.md**

---

## 🔄 Ciclo de Vida de los Datos

```
1. 🕷️ Scraping
   └─> cnn_brasil_scraper.py / scrapers.py

2. 📥 Ingesta Bronze
   └─> supabase_client.insert_bronze_raw()

3. 🔄 Normalización Silver (automática)
   └─> Trigger SQL: normalize_bronze_to_silver()

4. ⭐ Promoción Gold (manual/automática)
   └─> supabase_client.promote_to_gold()

5. 📤 Exportación Airtable (opcional)
   └─> airtable_client.send_player()
```

---

## 🎓 Nivel de Dificultad

### Principiante
- README.md
- GITHUB_SETUP.md
- examples.py

### Intermedio
- scrapers.py
- models.py
- pipeline.py

### Avanzado
- cnn_brasil_scraper.py
- proxy_rotator.py
- database_schema.sql

---

## 🆘 Ayuda Rápida

### ¿Cómo empezar?
→ **README.md** sección "Setup Inicial"

### ¿Cómo configurar GitHub Actions?
→ **GITHUB_SETUP.md** completo

### ¿Cómo funciona el scraper ninja?
→ **NINJA_SCRAPER.md** + **NINJA_SUMMARY.md**

### ¿Qué comandos usar?
→ **COMMANDS.md**

### ¿Cómo hacer testing?
→ **test_ninja_scraper.py**

### ¿Ejemplos de código?
→ **examples.py**

---

## 🔐 Archivos Sensibles

⚠️ **NUNCA commitear:**
- `.env` (credenciales reales)
- `*.log` (logs con datos)
- `__pycache__/` (cache Python)

✅ **Sí commitear:**
- `.env.example` (template)
- `.gitignore` (configurado)
- Todos los `.py` y `.md`

---

## 📝 Versiones

```
v1.0.0 - Initial release
├─ ✅ Base scrapers (OP.GG, Liquipedia)

v2.0.0 - Sprint 3: Cashflow & Engagement
├─ ✅ Regional payment gateways (Razorpay/Stripe)
├─ ✅ UPI integration for India (80% of transactions)
├─ ✅ Multi-channel notifications (WhatsApp/Telegram/Email)
├─ ✅ Cultural UX/UI adaptation
├─ ✅ PDF reports for professional markets
├─ ✅ Payment & subscription database schema
└─ ✅ FastAPI backend + Next.js frontend integration
├─ ✅ Supabase integration
├─ ✅ Airtable export
└─ ✅ Pipeline orchestration

v1.1.0 - Ninja scraper
├─ ✅ CNN Brasil scraper
├─ ✅ GitHub Actions workflow
├─ ✅ Proxy rotation
├─ ✅ Anti-detection
└─ ✅ India tagging
```

---

## 🎉 ¡Listo para usar!

Todo el sistema está completamente funcional. Para empezar:

1. Lee **README.md**
2. Sigue **GITHUB_SETUP.md**
3. Ejecuta **test_ninja_scraper.py**
4. Push a GitHub y activa el workflow

**¡Que empiece el scouting! 🥷🎮**

---

*GameRadar AI - Scouting de e-sports en Asia e India*
*Creado con ❤️ para el equipo de Data Science & Backend*
