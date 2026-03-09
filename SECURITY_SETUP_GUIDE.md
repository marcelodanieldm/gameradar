# 🚀 Guía Rápida: Completar Implementación de Seguridad

## ⚠️ Estado Actual

✅ **COMPLETADO**: Todo el código de seguridad ha sido implementado
- Login/Signup pages
- Middleware de autenticación  
- Protección de Dashboard
- Protección de APIs
- Helpers de Supabase
- Schema de base de datos

🔴 **PENDIENTE**: Configuración y dependencias
1. Instalar dependencias npm
2. Configurar variables de entorno
3. Ejecutar migración SQL en Supabase

---

## 📦 Paso 1: Instalar Dependencias

### Opción A: Script Automático (Recomendado)

```bash
# Ejecutar el script de instalación
install-dependencies.bat
```

### Opción B: Manual

```bash
# 1. Abrir terminal NUEVA (importante)
cd frontend

# 2. Limpiar instalaciones previas
Remove-Item node_modules -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item package-lock.json -Force -ErrorAction SilentlyContinue

# 3. Limpiar cache
npm cache clean --force

# 4. Instalar todo con --force
npm install --force

# Si falla, intenta:
npm install --legacy-peer-deps
```

### ⚠️ Si sigue fallando

El error "Invalid Version" es causado por una dependencia de `canvg`. Soluciones:

```bash
# Solución 1: Usar Yarn (si está instalado)
yarn install

# Solución 2: Instalar sin jspdf temporalmente
# Editar package.json y remover:
# - "jspdf": "^2.5.1",
# - "jspdf-autotable": "^3.8.2",
# Luego:
npm install --legacy-peer-deps

# Solución 3: Usar Node 18 (si tienes Node 22)
nvm use 18
npm install
```

---

## 🔐 Paso 2: Configurar Variables de Entorno

### 1. Crear archivo .env.local

```bash
cd frontend
copy .env.example .env.local
```

### 2. Obtener credenciales de Supabase

1. Ir a https://app.supabase.com
2. Abrir tu proyecto "GameRadar"
3. Ir a **Settings** → **API**

### 3. Copiar valores

Editar `frontend/.env.local` con los valores reales:

```bash
# Project URL (Settings → API → Project URL)
NEXT_PUBLIC_SUPABASE_URL=https://xxxxxxxxxxx.supabase.co

# Anon Key (Settings → API → anon public)
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGc...

# Service Role Key (Settings → API → service_role **secret**)
# ⚠️ SECRETO - NO COMPARTIR
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...

# Backend (usar localhost por ahora)
BACKEND_URL=http://localhost:8000

# Environment
NODE_ENV=development
```

---

## 🗄️ Paso 3: Ejecutar Migración de Base de Datos

### 1. Abrir SQL Editor en Supabase

1. Ve a https://app.supabase.com
2. Abre tu proyecto
3. Ve a **SQL Editor**
4. Click en **New query**

### 2. Ejecutar Script

1. Abre el archivo: `supabase/migrations/002_subscription_security.sql`
2. Copia **todo el contenido**
3. Pégalo en el SQL Editor
4. Click en **Run** (botón verde)

### 3. Verificar Tablas Creadas

Ejecuta esta query para verificar:

```sql
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public'
  AND tablename IN (
    'subscription_plans',
    'subscriptions', 
    'payment_history',
    'subscription_usage',
    'search_logs'
  );
```

Deberías ver 5 tablas con `rowsecurity = true`.

### 4. Verificar Funciones RPC

```sql
SELECT routine_name 
FROM information_schema.routines 
WHERE routine_schema = 'public'
  AND routine_name IN (
    'get_active_subscription',
    'can_user_search',
    'increment_search_count'
  );
```

Deberías ver las 3 funciones listadas.

---

## 🔧 Paso 4: Configurar Autenticación en Supabase

### 1. Ir a Authentication Settings

1. Ve a **Authentication** → **URL Configuration**

### 2. Configurar URLs

**Site URL** (desarrollo):
```
http://localhost:3000
```

**Redirect URLs** (agrega estas):
```
http://localhost:3000/auth/callback
https://tu-dominio.com/auth/callback
```

### 3. Habilitar Email Auth

1. Ve a **Authentication** → **Providers**
2. Verifica que **Email** esté habilitado
3. Configura opciones:
   - ✅ Enable email confirmations
   - ✅ Secure email change
   - ⏱️ Email confirm expiry: 86400 (24 horas)

---

## 🧪 Paso 5: Probar Implementación

### 1. Iniciar Servidor

```bash
cd frontend
npm run dev
```

### 2. Flujo de Prueba

#### Test 1: Dashboard Protegido
```
1. Abrir: http://localhost:3000/dashboard
2. ✅ Debe redirigir a /login
3. ❌ NO debe mostrar el dashboard sin auth
```

#### Test 2: Registro
```
1. Ir a: http://localhost:3000/signup
2. Llenar form con:
   - Nombre completo
   - Email válido
   - Password (mín 8 caracteres)
   - Confirmar password
3. Click en "Sign up"
4. ✅ Debe mostrar mensaje: "Verify your email"
5. ✅ Debe recibir email de confirmación
```

#### Test 3: Confirmar Email
```
1. Abrir email de Supabase
2. Click en "Confirm your email"
3. ✅ Debe redirigir a /login
```

#### Test 4: Login
```
1. Ir a http://localhost:3000/login
2. Ingresar email y password
3. Click en "Sign in"
4. ✅ Debe redirigir a /dashboard OR /subscribe
   - Si NO tiene suscripción → /subscribe/street-scout
   - Si tiene suscripción → /dashboard
```

#### Test 5: Acceso sin Suscripción
```
1. Login exitoso (usuario sin subscription)
2. Intentar ir a /dashboard
3. ✅ Debe redirigir a /subscribe/street-scout
```

#### Test 6: API Protegida
```
1. Sin login, hacer request a API:
   fetch('http://localhost:3000/api/semantic-search', {
     method: 'POST',
     body: JSON.stringify({ query: 'test' })
   })
2. ✅ Debe retornar: 401 Unauthorized
```

### 3. Crear Suscripción de Prueba

Para probar el dashboard completo, inserta una suscripción manual:

```sql
-- 1. Obtener tu user_id
SELECT id, email FROM auth.users;

-- 2. Insertar plan (si no existe)
INSERT INTO subscription_plans (
  name, price, currency, interval_unit, interval_count,
  search_limit, markets_limit, pdf_export_enabled, analytics_enabled
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

-- 3. Insertar suscripción activa
INSERT INTO subscriptions (
  user_id,
  plan_id,
  status,
  current_period_start,
  current_period_end,
  selected_markets
) VALUES (
  'tu-user-id-aqui', -- Reemplaza con el ID del paso 1
  (SELECT id FROM subscription_plans WHERE name = 'Street Scout'),
  'active',
  NOW(),
  NOW() + INTERVAL '30 days',
  ARRAY['KR', 'JP']::TEXT[]
);
```

#### Test 7: Dashboard con Suscripción
```
1. Hacer login
2. Ir a /dashboard
3. ✅ Debe mostrar:
   - Stats de uso (searches: 0/50)
   - Días restantes (30)
   - Mercados seleccionados (KR, JP)
   - Botón de logout
```

#### Test 8: Límite de Búsquedas
```
1. En dashboard, hacer 50 búsquedas
2. Intentar búsqueda #51
3. ✅ Debe retornar: 429 Too Many Requests
4. ✅ Dashboard debe mostrar: 50/50 searches used
```

---

## 🐛 Troubleshooting

### Error: "Invalid Version" en npm install

**Causa**: Conflicto con canvg dependency

**Solución**:
```bash
# Ya agregamos overrides en package.json
npm install --force

# O remover jspdf temporalmente
# Editar package.json y comentar:
# "jspdf": "^2.5.1",
# "jspdf-autotable": "^3.8.2",
```

### Error: "Unauthorized" al hacer login

**Causa**: Variables de entorno incorrectas

**Solución**:
1. Verificar que `.env.local` existe
2. Verificar que las keys son correctas
3. Reiniciar servidor: `npm run dev`

### Error: "Could not find subscription"

**Causa**: No existe registro en tabla `subscriptions`

**Solución**:
1. Verificar que la migración SQL se ejecutó
2. Insertar suscripción de prueba (ver Paso 5.3)
3. Verificar que `user_id` coincide con `auth.users.id`

### Error: "RLS policy violation"

**Causa**: Row Level Security mal configurado

**Solución**:
1. Verificar que RLS está habilitado:
   ```sql
   ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
   ALTER TABLE subscription_usage ENABLE ROW LEVEL SECURITY;
   ```
2. Verificar que las policies existen:
   ```sql
   SELECT tablename, policyname 
   FROM pg_policies 
   WHERE schemaname = 'public';
   ```

### Dashboard muestra datos mock (23/50 searches)

**Causa**: Dashboard no está recibiendo datos reales

**Solución**:
1. Verificar que `requireActiveSubscription()` se está llamando en la page
2. Verificar que props se están pasando al componente
3. Verificar logs de console en browser

---

## 📋 Checklist Final

Antes de considerar la implementación completa:

### Backend
- [ ] npm install exitoso (sin errores)
- [ ] `.env.local` creado y configurado
- [ ] Servidor dev inicia sin errores: `npm run dev`

### Supabase
- [ ] Proyecto creado y configurado
- [ ] Migración SQL ejecutada (5 tablas + 3 funciones)
- [ ] RLS habilitado en todas las tablas
- [ ] Email auth configurado
- [ ] Redirect URLs configuradas

### Funcionalidad
- [ ] `/dashboard` redirige a `/login` sin auth
- [ ] Registro funciona y envía email
- [ ] Confirmación de email funciona
- [ ] Login exitoso redirige correctamente
- [ ] Dashboard muestra datos reales (no mock)
- [ ] API search retorna 401 sin auth
- [ ] Límite de búsquedas funciona
- [ ] Logout funciona correctamente

### Seguridad
- [ ] Todas las rutas protegidas requieren auth
- [ ] APIs verifican autenticación
- [ ] RLS previene acceso a datos de otros usuarios
- [ ] Service Role Key NO está en código cliente
- [ ] Passwords tienen validación mínima

---

## 📚 Archivos de Referencia

- **Estado de implementación**: [SECURITY_IMPLEMENTATION_STATUS.md](SECURITY_IMPLEMENTATION_STATUS.md)
- **Análisis de seguridad**: [SECURITY_ANALYSIS_DASHBOARD.md](SECURITY_ANALYSIS_DASHBOARD.md)
- **Guía de implementación**: [SECURITY_IMPLEMENTATION_GUIDE.md](SECURITY_IMPLEMENTATION_GUIDE.md)
- **Schema SQL**: [supabase/migrations/002_subscription_security.sql](supabase/migrations/002_subscription_security.sql)

---

## ✨ Próximos Pasos (Después de Seguridad Básica)

1. **Integrar Payment Gateway** (Stripe/Razorpay)
   - Crear checkout flow
   - Webhook para activar suscripciones
   - Manejo de pagos fallidos

2. **Proteger Más APIs**
   - `/api/payment/*` routes
   - Otras APIs sensibles

3. **Rate Limiting**
   - Instalar Upstash Redis
   - Implementar límites por IP

4. **Email Templates**
   - Personalizar emails de Supabase
   - Agregar branding

5. **Audit Logging**
   - Extender logs a más eventos
   - Dashboard de admin

---

## 🆘 ¿Necesitas Ayuda?

Si encuentras problemas:

1. Revisa la sección de Troubleshooting arriba
2. Verifica los logs en browser console: `F12 → Console`
3. Verifica logs en terminal donde corre `npm run dev`
4. Revisa logs en Supabase: Dashboard → Logs

**Logs importantes a verificar:**
- Supabase auth errors
- API route errors (401, 403, 500)
- Database query errors
- Middleware redirect loops

---

**¡Éxito con la implementación! 🚀**
