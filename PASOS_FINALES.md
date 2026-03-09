# 🎯 PASOS FINALES - Configuración Completa

## ✅ Estado Actual

- ✅ **TODO el código implementado** (14 archivos nuevos/modificados)
- ✅ **`.env.local` creado** - Necesita tus credenciales
- ⚠️ **npm install pendiente** - Bug de npm 11.4.1
- ⏳ **Migración SQL pendiente** - Ejecutar en Supabase

---

## 🔴 PASO 1: Resolver npm install

### Problema Identificado
npm v11.4.1 tiene un bug crítico que impide instalar dependencias.

### ✅ Solución Manual Más Rápida (5 minutos)

**Opción A: Descargar e Instalar Node.js v20 LTS**

1. Ve a: https://nodejs.org/
2. Descarga **Node.js v20 LTS** (incluye npm 10 sin el bug)
3. Ejecuta el instalador
4. Cierra todas las terminales de VS Code
5. Abre una terminal nueva y ejecuta:

```powershell
node -v  # Debe mostrar v20.x.x
npm -v   # Debe mostrar 10.x.x

cd D:\gameradar\gameradar\frontend
npm install
```

**Opción B: Usar Yarn (si tienes instalado)**

```powershell
npm install -g yarn
cd D:\gameradar\gameradar\frontend
yarn install
```

**Opción C: Instalar npm 10 manualmente desde PowerShell como Admin**

1. Click derecho en el icono de PowerShell → "Ejecutar como administrador"
2. Ejecuta:

```powershell
npm install -g npm@10.9.2
npm -v  # Verificar que sea 10.x

cd D:\gameradar\gameradar\frontend
npm install
```

### Verificar Instalación Exitosa

```powershell
# Debe retornar True para todas:
Test-Path node_modules\next
Test-Path node_modules\@supabase\auth-helpers-nextjs
Test-Path node_modules\zod
```

---

## 🔐 PASO 2: Configurar Supabase Credentials

### 2.1 Abrir Supabase Dashboard

1. Ve a: https://app.supabase.com
2. Inicia sesión
3. Abre tu proyecto **GameRadar** (o créalo si no existe)

### 2.2 Crear Proyecto (si es nuevo)

1. Click en "New Project"
2. Nombre: **GameRadar**
3. Database Password: **(guarda esta contraseña)**
4. Region: Elige la más cercana
5. Plan: **Free** (suficiente para desarrollo)
6. Click "Create new project"
7. Espera 2-3 minutos a que el proyecto se inicialice

### 2.3 Obtener API Keys

1. Ve a **Settings** → **API**
2. Encontrarás:
   - **Project URL**: `https://xxxxxxxxxxx.supabase.co`
   - **anon public key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
   - **service_role key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` ⚠️

### 2.4 Editar `.env.local`

Abre `frontend\.env.local` y reemplaza los valores:

```bash
# Ejemplo con valores reales:
NEXT_PUBLIC_SUPABASE_URL=https://abcdefgh12345678.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFiY2RlZmdoMTIzNDU2NzgiLCJyb2xlIjoiYW5vbiIsImlhdCI6MTYzOTU4NjQwMCwiZXhwIjoxOTU1MTYyNDAwfQ.abc123...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFiY2RlZmdoMTIzNDU2NzgiLCJyb2xlIjoic2VydmljZV9yb2xlIiwiaWF0IjoxNjM5NTg2NDAwLCJleHAiOjE5NTUxNjI0MDB9.xyz789...
```

⚠️ **IMPORTANTE**: 
- NO subas `.env.local` a Git (ya está en `.gitignore`)
- El `service_role` key es SECRETO - nunca lo compartas

---

## 🗄️ PASO 3: Ejecutar Migración SQL

### 3.1 Abrir SQL Editor en Supabase

1. En tu proyecto Supabase, ve a **SQL Editor** (ícono de base de datos en el menú izquierdo)
2. Click en **"+ New query"**

### 3.2 Copiar y Ejecutar Script

1. Abre el archivo: `supabase\migrations\002_subscription_security.sql`
2. Copia **TODO el contenido** (tiene ~600 líneas)
3. Pégalo en el SQL Editor de Supabase
4. Click en el botón **"Run"** (▶️ verde en la esquina inferior derecha)
5. Espera a que termine (puede tomar 10-15 segundos)

### 3.3 Verificar Tablas Creadas

Ejecuta este query en el SQL Editor:

```sql
SELECT 
  tablename, 
  rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public'
  AND tablename IN (
    'subscription_plans',
    'subscriptions',
    'payment_history',
    'subscription_usage',
    'search_logs'
  )
ORDER BY tablename;
```

**Resultado esperado**: 5 tablas con `rowsecurity = true`

```
tablename             | rowsecurity
----------------------|-------------
payment_history       | true
search_logs           | true
subscription_plans    | true
subscription_usage    | true
subscriptions         | true
```

### 3.4 Verificar Funciones RPC

```sql
SELECT 
  routine_name,
  routine_type
FROM information_schema.routines 
WHERE routine_schema = 'public'
  AND routine_name IN (
    'get_active_subscription',
    'can_user_search',
    'increment_search_count'
  )
ORDER BY routine_name;
```

**Resultado esperado**: 3 funciones

```
routine_name              | routine_type
--------------------------|-------------
can_user_search           | FUNCTION
get_active_subscription   | FUNCTION
increment_search_count    | FUNCTION
```

### 3.5 Configurar Authentication

1. Ve a **Authentication** → **URL Configuration**
2. **Site URL**: `http://localhost:3000`
3. **Redirect URLs** (agregar):
   ```
   http://localhost:3000/auth/callback
   http://localhost:3000/*
   ```
4. Click **"Save"**

5. Ve a **Authentication** → **Providers**
6. Verifica que **Email** esté habilitado (verde)
7. Configuración recomendada:
   - ✅ Enable email confirmations
   - ✅ Secure email change
   - ⏱️ Email confirm expiry: 86400 (24 horas)

---

## 🚀 PASO 4: Iniciar Aplicación

### 4.1 Iniciar Dev Server

```powershell
cd D:\gameradar\gameradar\frontend
npm run dev
```

**Salida esperada**:
```
▲ Next.js 14.1.0
- Local:        http://localhost:3000
- Environments: .env.local

✓ Ready in 2.5s
```

### 4.2 Abrir en Navegador

Visita: http://localhost:3000

---

## 🧪 PASO 5: Testing del Sistema

### Test 1: Dashboard Protegido ✅

```
1. Ir a: http://localhost:3000/dashboard
2. ✅ DEBE redirigir automáticamente a /login
3. ❌ NO debe mostrar el dashboard
```

### Test 2: Registro de Usuario ✅

```
1. Ir a: http://localhost:3000/signup
2. Llenar formulario:
   - Full Name: Test User
   - Email: test@example.com
   - Password: password123
   - Confirm Password: password123
3. Click "Sign up"
4. ✅ Debe mostrar: "Please check your email to verify your account"
5. ✅ Recibir email de confirmación de Supabase
```

### Test 3: Confirmar Email ✅

```
1. Abrir email de Supabase
2. Click en "Confirm your email"
3. ✅ Debe redirigir a /login
4. ✅ URL debe contener: ?confirmed=true
```

### Test 4: Login ✅

```
1. Ir a: http://localhost:3000/login
2. Ingresar:
   - Email: test@example.com
   - Password: password123
3. Click "Sign in"
4. ✅ Debe redirigir a /subscribe/street-scout
   (porque el usuario no tiene suscripción activa)
```

### Test 5: Crear Suscripción de Prueba ✅

Para continuar testing, necesitas crear una suscripción manual en Supabase:

```sql
-- 1. Obtener tu user_id
SELECT id, email FROM auth.users;

-- 2. Insertar plan Street Scout (si no existe)
INSERT INTO subscription_plans (
  name, price, currency, 
  interval_unit, interval_count,
  search_limit, markets_limit, 
  pdf_export_enabled, analytics_enabled
) VALUES (
  'Street Scout',
  99.00,
  'USD',
  'month',
  1,
  50,
  2,
  true,
  false
) ON CONFLICT (name) DO NOTHING;

-- 3. Insertar suscripción activa para tu usuario
INSERT INTO subscriptions (
  user_id,
  plan_id,
  status,
  current_period_start,
  current_period_end,
  selected_markets
) VALUES (
  'REEMPLAZAR-CON-TU-USER-ID',  -- <-- ID del paso 1
  (SELECT id FROM subscription_plans WHERE name = 'Street Scout'),
  'active',
  NOW(),
  NOW() + INTERVAL '30 days',
  ARRAY['KR', 'JP']::TEXT[]
);

-- 4. Verificar que se creó
SELECT * FROM subscriptions WHERE user_id = 'TU-USER-ID';
```

### Test 6: Dashboard con Suscripción ✅

```
1. Hacer login de nuevo
2. ✅ DEBE redirigir a /dashboard (ahora con suscripción)
3. ✅ Ver stats reales:
   - Searches: 0/50
   - Days remaining: 30
   - Selected markets: South Korea 🇰🇷, Japan 🇯🇵
4. ✅ Ver botón de Logout
```

### Test 7: API Protegida ✅

Abrir DevTools (F12) y ejecutar en Console:

```javascript
// Sin auth - debe fallar
fetch('/api/semantic-search', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: 'striker korea' })
}).then(r => r.json()).then(console.log)

// ✅ Debe retornar: { error: 'Unauthorized' }
```

### Test 8: Búsqueda con Límite ✅

```
1. En dashboard, hacer búsquedas múltiples
2. ✅ Contador debe incrementar: 1/50, 2/50, etc.
3. ✅ Al llegar a 50/50, debe mostrar límite alcanzado
```

### Test 9: Logout ✅

```
1. Click en botón "Logout"
2. ✅ Debe redirigir a /login
3. ✅ Session debe estar limpia
4. ✅ Intentar ir a /dashboard de nuevo debe redirigir a /login
```

---

## 📊 Checklist Final

Marca cada item cuando esté completo:

### npm Install
- [ ] Node.js v20 instalado OR npm 10 instalado OR Yarn configurado
- [ ] `npm install` completado sin errores
- [ ] Existen `node_modules/@supabase/auth-helpers-nextjs`
- [ ] Existen `node_modules/next`
- [ ] Existen `node_modules/zod`

### Configuración
- [ ] `.env.local` creado con valores reales de Supabase
- [ ] NEXT_PUBLIC_SUPABASE_URL configurado
- [ ] NEXT_PUBLIC_SUPABASE_ANON_KEY configurado
- [ ] SUPABASE_SERVICE_ROLE_KEY configurado

### Base de Datos
- [ ] Migración SQL ejecutada en Supabase
- [ ] 5 tablas creadas con RLS habilitado
- [ ] 3 funciones RPC creadas
- [ ] Authentication habilitado con Email provider
- [ ] Redirect URLs configuradas

### Testing
- [ ] `npm run dev` inicia sin errores
- [ ] Dashboard protegido (redirige a login)
- [ ] Registro funciona y envía email
- [ ] Confirmación de email funciona
- [ ] Login funciona correctamente
- [ ] Dashboard muestra datos reales (no mock)
- [ ] API rechaza requests sin auth
- [ ] Logout funciona

---

## 🎉 ¡Listo!

Una vez completes todos los items, tendrás:

✅ **Autenticación completa** con Supabase Auth  
✅ **Dashboard protegido** que requiere login y suscripción  
✅ **APIs seguras** con verificación de auth y límites  
✅ **Base de datos con RLS** que protege datos por usuario  
✅ **Sistema de suscripciones** funcionando  

## 📚 Documentos de Referencia

- [NPM_INSTALL_PROBLEM.md](NPM_INSTALL_PROBLEM.md) - Soluciones detalladas para npm
- [SECURITY_SETUP_GUIDE.md](SECURITY_SETUP_GUIDE.md) - Guía completa de seguridad
- [SECURITY_IMPLEMENTATION_STATUS.md](SECURITY_IMPLEMENTATION_STATUS.md) - Estado actual
- `supabase/migrations/002_subscription_security.sql` - Script SQL completo

## 🆘 ¿Necesitas Ayuda?

Si algo no funciona, revisa los logs:

- **Browser Console**: F12 → Console (errores de frontend)
- **Terminal**: Donde corre `npm run dev` (errores de backend)
- **Supabase Logs**: Dashboard → Logs → API/Auth/Database

---

**¡Todo el código está listo! Solo falta ejecutar estos pasos de configuración.** 🚀
