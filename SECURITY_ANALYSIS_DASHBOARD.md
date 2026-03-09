# 🔒 Análisis de Seguridad - Dashboard Street Scout

**Fecha de análisis:** 9 de marzo de 2026  
**Componentes analizados:** Dashboard, Subscription, Success Page, API Routes  
**Nivel de riesgo actual:** ⚠️ **CRÍTICO**

---

## 📊 Resumen Ejecutivo

El dashboard de Street Scout actualmente **NO tiene implementada ninguna capa de seguridad**. Cualquier usuario, autenticado o no, puede acceder al dashboard y ver información que debería ser privada. Los datos mostrados son estáticos (mock data) y no están conectados a una base de datos ni a un sistema de autenticación.

### Vulnerabilidades Críticas Identificadas

| # | Vulnerabilidad | Severidad | Impacto |
|---|---|---|---|
| 1 | Sin autenticación en dashboard | 🔴 CRÍTICA | Acceso público a datos privados |
| 2 | Sin verificación de suscripción | 🔴 CRÍTICA | Usuarios sin pagar pueden usar el servicio |
| 3 | Sin protección de rutas | 🔴 CRÍTICA | Bypass completo de seguridad |
| 4 | Sin gestión de sesiones | 🔴 CRÍTICA | No se identifica al usuario |
| 5 | API sin validación de tokens | 🟠 ALTA | Cualquiera puede llamar las APIs |
| 6 | Sin rate limiting | 🟠 ALTA | Vulnerable a ataques DDoS |
| 7 | Sin protección CSRF | 🟠 ALTA | Ataques cross-site posibles |
| 8 | Datos hardcoded en frontend | 🟡 MEDIA | No refleja estado real |

---

## 🔍 Análisis Detallado

### 1. **Dashboard Component** (`StreetScoutDashboard.tsx`)

#### ❌ Problemas de Seguridad

```typescript
export default function StreetScoutDashboard() {
  const [stats, setStats] = useState<UsageStats>({
    searchesUsed: 23,
    searchesLimit: 50,
    // ... datos hardcoded, NO viene de API autenticada
  });
```

**Problemas:**
- ✗ No valida si el usuario está autenticado
- ✗ No verifica si tiene suscripción activa
- ✗ Datos estáticos (no consulta DB)
- ✗ No hay session/token verification
- ✗ Cualquiera puede acceder a `/dashboard`

**Riesgo:** Un usuario malicioso puede:
1. Acceder al dashboard sin pagar
2. Ver la interfaz completa sin restricciones
3. Intentar explotar las APIs si las descubre

---

### 2. **Dashboard Page** (`app/[locale]/dashboard/page.tsx`)

#### ❌ Problemas de Seguridad

```typescript
export default function DashboardPage() {
  return <StreetScoutDashboard />;
}
```

**Problemas:**
- ✗ NO es un Server Component con verificación
- ✗ No usa `getServerSideProps` o Server Actions
- ✗ No redirige a login si no autenticado
- ✗ No valida permisos en el servidor

**Impacto:** La ruta está completamente desprotegida

---

### 3. **Middleware** (`middleware.ts`)

#### ⚠️ Configuración Actual

```typescript
export default createMiddleware({
  locales: ['en', 'ko', 'zh', 'hi', 'vi', 'th', 'ja'],
  defaultLocale: 'en',
  localeDetection: true
})

export const config = {
  matcher: ['/', '/(ko|zh|hi|vi|th|ja|en)/:path*']
}
```

**Problemas:**
- ✗ Solo maneja internacionalización (i18n)
- ✗ NO verifica autenticación
- ✗ NO protege rutas privadas
- ✗ NO valida tokens/sesiones

**Lo que DEBERÍA hacer:**
- ✓ Verificar JWT/session token
- ✓ Redirigir a login si no autenticado
- ✓ Validar permisos por ruta
- ✓ Bloquear acceso a recursos protegidos

---

### 4. **API Routes de Pago**

#### `/api/payment/create/route.ts`

```typescript
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { amount, currency, userId, email, region, paymentMethod, metadata } = body;

    // Validate input
    if (!amount || !userId || !email || !region) {
      return NextResponse.json(
        { success: false, error_message: 'Missing required fields' },
        { status: 400 }
      );
    }
```

**Problemas:**
- ✗ Acepta `userId` del cliente (puede ser manipulado)
- ✗ No valida que el `userId` corresponda al usuario autenticado
- ✗ No verifica token de sesión
- ✗ No hay rate limiting (vulnerable a abuso)
- ✗ No hay logging de intentos sospechosos

**Riesgo:**
- Un atacante puede enviar `userId` de otra persona
- Puede crear suscripciones para otros usuarios
- Puede hacer spam de requests

#### `/api/payment/verify/route.ts`

```typescript
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { gateway, userId } = body;

    // Validate input
    if (!gateway || !userId) {
      return NextResponse.json(
        { success: false, error: 'Missing required fields' },
        { status: 400 }
      );
    }
```

**Mismo problema:** Acepta `userId` del cliente sin validación

---

### 5. **Subscription Success Page**

#### `SubscriptionSuccess.tsx`

```typescript
useEffect(() => {
  const sessionId = searchParams.get('sessionId');
  
  if (!sessionId) {
    setError('No se encontró información de la suscripción');
    setLoading(false);
    return;
  }

  // Fetch subscription details
  fetch(`/api/payment/verify?sessionId=${sessionId}`)
```

**Problemas:**
- ✗ Confía en el `sessionId` de la URL (puede ser manipulado)
- ✗ No verifica que el sessionId pertenezca al usuario actual
- ✗ API `/api/payment/verify` no valida ownership
- ✗ Cualquiera con un sessionId válido puede ver detalles de otro

**Ataque posible:**
1. Usuario A completa suscripción → obtiene sessionId=ABC123
2. Usuario B adivina o intercepta sessionId=ABC123
3. Usuario B accede a `/subscription/success?sessionId=ABC123`
4. Usuario B ve los detalles de la suscripción de Usuario A

---

## 🛡️ Componentes de Seguridad FALTANTES

### ❌ No Implementado Actualmente

1. **Authentication Provider**
   - No hay Supabase Auth, NextAuth, Clerk, o similar
   - No hay login/signup flows
   - No hay password management

2. **Session Management**
   - No hay cookies de sesión
   - No hay JWT tokens
   - No hay refresh token mechanism

3. **Authorization Layer**
   - No hay verificación de roles
   - No hay subscription status checks
   - No hay feature flags por plan

4. **API Security**
   - No hay API authentication middleware
   - No hay rate limiting
   - No hay request validation
   - No hay CORS configuration

5. **Database Security**
   - No hay Row Level Security (RLS) en Supabase
   - No hay políticas de acceso
   - No hay encriptación de datos sensibles

6. **Audit Logging**
   - No se registran accesos
   - No se rastrean cambios
   - No hay alertas de seguridad

---

## 🎯 Impacto por Usuario

### Usuario No Pagador (Atacante)
- ✓ Puede acceder al dashboard sin pagar
- ✓ Puede ver la interfaz completa
- ✓ Puede intentar usar las funciones (si APIs no protegidas)
- ✓ Puede ver datos de otros usuarios (sessionId leak)

### Usuario Legítimo (Pagador)
- ✗ Sus datos no están protegidos
- ✗ Otros pueden acceder a su dashboard
- ✗ Su sessionId puede ser robado
- ✗ No tiene garantía de privacidad

---

## 🚨 Escenarios de Ataque

### Escenario 1: Acceso No Autorizado
```
1. Atacante navega a https://gameradar.com/dashboard
2. Dashboard se carga sin restricciones
3. Atacante ve toda la interfaz del plan Street Scout
4. Puede intentar llamar APIs si las descubre
```

### Escenario 2: Session ID Hijacking
```
1. Usuario A subscribe, URL: /subscription/success?sessionId=ABC123
2. Atacante intercepta URL (shoulder surfing, browser history, etc.)
3. Atacante accede a /subscription/success?sessionId=ABC123
4. Ve email, monto, plan del Usuario A
```

### Escenario 3: API Abuse
```
1. Atacante inspecciona Network tab
2. Descubre POST /api/payment/create
3. Envía requests masivos con diferentes userId
4. Crea caos en el sistema de pagos
```

### Escenario 4: Payment Manipulation
```
1. Atacante modifica request de pago
2. Cambia amount: 99 → amount: 1
3. Cambia userId a uno de otra persona
4. Crea suscripción fraudulenta
```

---

## 📋 Recomendaciones Prioritarias

### 🔴 URGENTE (Implementar ANTES de producción)

#### 1. Implementar Autenticación con Supabase Auth
```typescript
// lib/supabase/auth.ts
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs'

export const supabase = createClientComponentClient()

export async function signUp(email: string, password: string) {
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
  })
  return { data, error }
}

export async function signIn(email: string, password: string) {
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  })
  return { data, error }
}

export async function signOut() {
  const { error } = await supabase.auth.signOut()
  return { error }
}

export async function getSession() {
  const { data: { session } } = await supabase.auth.getSession()
  return session
}
```

#### 2. Proteger Dashboard con Auth Check
```typescript
// app/[locale]/dashboard/page.tsx
import { createServerComponentClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'

export default async function DashboardPage() {
  const supabase = createServerComponentClient({ cookies })
  
  const { data: { session } } = await supabase.auth.getSession()
  
  if (!session) {
    redirect('/login')
  }

  // Verificar suscripción activa
  const { data: subscription } = await supabase
    .from('subscriptions')
    .select('*')
    .eq('user_id', session.user.id)
    .eq('status', 'active')
    .single()

  if (!subscription) {
    redirect('/subscribe')
  }

  return <StreetScoutDashboard userId={session.user.id} />
}
```

#### 3. Actualizar Middleware para Auth
```typescript
// middleware.ts
import { createMiddlewareClient } from '@supabase/auth-helpers-nextjs'
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
import createIntlMiddleware from 'next-intl/middleware'

const intlMiddleware = createIntlMiddleware({
  locales: ['en', 'ko', 'zh', 'hi', 'vi', 'th', 'ja'],
  defaultLocale: 'en',
  localeDetection: true
})

export async function middleware(req: NextRequest) {
  // Handle i18n
  const intlResponse = intlMiddleware(req)
  
  // Protected routes
  const protectedPaths = ['/dashboard', '/settings', '/analytics', '/search']
  const isProtectedPath = protectedPaths.some(path => 
    req.nextUrl.pathname.includes(path)
  )

  if (isProtectedPath) {
    const res = NextResponse.next()
    const supabase = createMiddlewareClient({ req, res })
    const { data: { session } } = await supabase.auth.getSession()

    if (!session) {
      const redirectUrl = req.nextUrl.clone()
      redirectUrl.pathname = '/login'
      redirectUrl.searchParams.set('redirectTo', req.nextUrl.pathname)
      return NextResponse.redirect(redirectUrl)
    }

    // Verificar suscripción activa
    const { data: subscription } = await supabase
      .from('subscriptions')
      .select('status')
      .eq('user_id', session.user.id)
      .single()

    if (!subscription || subscription.status !== 'active') {
      return NextResponse.redirect(new URL('/subscribe', req.url))
    }
  }

  return intlResponse
}

export const config = {
  matcher: ['/', '/(ko|zh|hi|vi|th|ja|en)/:path*']
}
```

#### 4. Proteger APIs con Auth Middleware
```typescript
// lib/api-auth.ts
import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { NextResponse } from 'next/server'

export async function withAuth(handler: Function) {
  return async (request: Request) => {
    const supabase = createRouteHandlerClient({ cookies })
    
    const { data: { session } } = await supabase.auth.getSession()
    
    if (!session) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      )
    }

    return handler(request, session)
  }
}

// Uso en API route
// app/api/payment/create/route.ts
import { withAuth } from '@/lib/api-auth'

export const POST = withAuth(async (request: Request, session: any) => {
  const body = await request.json()
  
  // userId viene de la sesión, NO del cliente
  const userId = session.user.id
  
  // Continuar con lógica de pago...
})
```

#### 5. Fetch Real Data en Dashboard
```typescript
// components/StreetScoutDashboard.tsx
'use client'

import { useEffect, useState } from 'react'
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs'

export default function StreetScoutDashboard({ userId }: { userId: string }) {
  const [stats, setStats] = useState<UsageStats | null>(null)
  const [loading, setLoading] = useState(true)
  const supabase = createClientComponentClient()

  useEffect(() => {
    async function fetchStats() {
      // Fetch del backend con Row Level Security
      const { data: subscription } = await supabase
        .from('subscriptions')
        .select(`
          *,
          usage:subscription_usage(*)
        `)
        .eq('user_id', userId)
        .eq('status', 'active')
        .single()

      if (subscription) {
        setStats({
          searchesUsed: subscription.usage?.searches_used || 0,
          searchesLimit: subscription.plan_limits.searches_per_month,
          marketsUsed: subscription.selected_markets?.length || 0,
          marketsLimit: subscription.plan_limits.max_markets,
          currentPeriodStart: subscription.current_period_start,
          currentPeriodEnd: subscription.current_period_end,
          subscriptionStatus: subscription.status,
          daysRemaining: calculateDaysRemaining(subscription.current_period_end)
        })
      }
      
      setLoading(false)
    }

    fetchStats()
  }, [userId])

  if (loading) return <LoadingSpinner />
  if (!stats) return <ErrorState />

  return (
    // Render dashboard con datos reales...
  )
}
```

#### 6. Row Level Security en Supabase
```sql
-- Enable RLS en tabla subscriptions
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;

-- Policy: usuarios solo ven sus propias suscripciones
CREATE POLICY "Users can view own subscriptions"
ON subscriptions FOR SELECT
USING (auth.uid() = user_id);

-- Policy: solo backend puede crear suscripciones
CREATE POLICY "Service role can insert subscriptions"
ON subscriptions FOR INSERT
WITH CHECK (auth.role() = 'service_role');

-- Policy: usuarios pueden actualizar sus mercados seleccionados
CREATE POLICY "Users can update own selected markets"
ON subscriptions FOR UPDATE
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- Enable RLS en subscription_usage
ALTER TABLE subscription_usage ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own usage"
ON subscription_usage FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM subscriptions
    WHERE subscriptions.id = subscription_usage.subscription_id
    AND subscriptions.user_id = auth.uid()
  )
);
```

---

### 🟠 ALTA PRIORIDAD

#### 7. Rate Limiting
```typescript
// lib/rate-limit.ts
import { Ratelimit } from '@upstash/ratelimit'
import { Redis } from '@upstash/redis'

const redis = new Redis({
  url: process.env.UPSTASH_REDIS_REST_URL!,
  token: process.env.UPSTASH_REDIS_REST_TOKEN!,
})

export const ratelimit = new Ratelimit({
  redis,
  limiter: Ratelimit.slidingWindow(10, '10 s'),
  analytics: true,
})

// Uso en API
export async function POST(request: Request) {
  const ip = request.headers.get('x-forwarded-for') ?? 'anonymous'
  const { success } = await ratelimit.limit(ip)

  if (!success) {
    return NextResponse.json(
      { error: 'Too many requests' },
      { status: 429 }
    )
  }

  // Continuar...
}
```

#### 8. CSRF Protection
```typescript
// lib/csrf.ts
import { cookies } from 'next/headers'
import crypto from 'crypto'

export function generateCsrfToken(): string {
  return crypto.randomBytes(32).toString('hex')
}

export function setCsrfCookie(token: string) {
  cookies().set('csrf-token', token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'strict',
    maxAge: 60 * 60 * 24 // 24 horas
  })
}

export function verifyCsrfToken(requestToken: string): boolean {
  const storedToken = cookies().get('csrf-token')?.value
  return storedToken === requestToken
}
```

#### 9. Input Validation con Zod
```typescript
// lib/validations/payment.ts
import { z } from 'zod'

export const paymentSchema = z.object({
  email: z.string().email('Email inválido'),
  cardNumber: z.string().regex(/^\d{16}$/, 'Tarjeta debe tener 16 dígitos'),
  cardName: z.string().min(2, 'Nombre muy corto'),
  expiryDate: z.string().regex(/^\d{2}\/\d{2}$/, 'Formato MM/YY'),
  cvv: z.string().regex(/^\d{3}$/, 'CVV debe ser 3 dígitos'),
  country: z.string().min(2, 'País requerido'),
})

// Uso en API
export async function POST(request: Request) {
  const body = await request.json()
  
  const validation = paymentSchema.safeParse(body)
  
  if (!validation.success) {
    return NextResponse.json(
      { error: 'Validación fallida', details: validation.error.errors },
      { status: 400 }
    )
  }

  const data = validation.data
  // Continuar con datos validados...
}
```

---

### 🟡 MEDIA PRIORIDAD

#### 10. Audit Logging
```typescript
// lib/audit-log.ts
export async function logAuditEvent(
  userId: string,
  action: string,
  resource: string,
  metadata?: any
) {
  await supabase.from('audit_logs').insert({
    user_id: userId,
    action,
    resource,
    metadata,
    ip_address: getClientIp(),
    user_agent: getUserAgent(),
    created_at: new Date().toISOString()
  })
}

// Uso
await logAuditEvent(
  session.user.id,
  'subscription.created',
  'subscriptions',
  { plan: 'street-scout', amount: 99 }
)
```

#### 11. Security Headers
```typescript
// next.config.js
const securityHeaders = [
  {
    key: 'X-DNS-Prefetch-Control',
    value: 'on'
  },
  {
    key: 'Strict-Transport-Security',
    value: 'max-age=63072000; includeSubDomains; preload'
  },
  {
    key: 'X-Frame-Options',
    value: 'SAMEORIGIN'
  },
  {
    key: 'X-Content-Type-Options',
    value: 'nosniff'
  },
  {
    key: 'X-XSS-Protection',
    value: '1; mode=block'
  },
  {
    key: 'Referrer-Policy',
    value: 'strict-origin-when-cross-origin'
  },
  {
    key: 'Permissions-Policy',
    value: 'camera=(), microphone=(), geolocation=()'
  }
]

module.exports = {
  async headers() {
    return [
      {
        source: '/:path*',
        headers: securityHeaders,
      },
    ]
  },
}
```

#### 12. Environment Variables Security
```bash
# .env.local (NUNCA commitear)
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJxxxxx (público, está bien)
SUPABASE_SERVICE_ROLE_KEY=eyJxxxxx (SECRETO, solo server-side)
DATABASE_URL=postgresql://xxxxx (SECRETO)
STRIPE_SECRET_KEY=sk_xxxxx (SECRETO)
RAZORPAY_KEY_SECRET=xxxxx (SECRETO)
```

**Agregar a `.gitignore`:**
```
.env.local
.env.development.local
.env.production.local
```

---

## ✅ Checklist de Implementación

### Fase 1: Autenticación (Semana 1)
- [ ] Instalar `@supabase/auth-helpers-nextjs`
- [ ] Crear tablas de usuarios en Supabase
- [ ] Implementar signup/login/logout flows
- [ ] Crear páginas de login y registro
- [ ] Configurar email templates
- [ ] Implementar password reset

### Fase 2: Autorización (Semana 2)
- [ ] Actualizar middleware con auth checks
- [ ] Proteger todas las rutas privadas
- [ ] Implementar Row Level Security en Supabase
- [ ] Crear políticas de acceso por tabla
- [ ] Validar tokens en todas las APIs

### Fase 3: Dashboard Real (Semana 2-3)
- [ ] Crear schema de subscriptions en DB
- [ ] Migrar de datos mock a queries reales
- [ ] Implementar tracking de usage
- [ ] Conectar con payment gateway
- [ ] Sync de estado de suscripción

### Fase 4: API Security (Semana 3)
- [ ] Implementar rate limiting
- [ ] Agregar CSRF protection
- [ ] Validar inputs con Zod
- [ ] Sanitizar outputs
- [ ] Configurar CORS

### Fase 5: Monitoring (Semana 4)
- [ ] Implementar audit logging
- [ ] Configurar alertas de seguridad
- [ ] Dashboard de admin para monitoreo
- [ ] Logs de accesos sospechosos
- [ ] Testing de penetración

---

## 🔒 Arquitectura de Seguridad Recomendada

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js)                   │
├─────────────────────────────────────────────────────────────┤
│  Browser → Middleware (Auth Check) → Protected Page         │
│            ↓                              ↓                  │
│       [Redirect to /login]          [Render with data]      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     SUPABASE AUTH                           │
├─────────────────────────────────────────────────────────────┤
│  - JWT Token Management                                     │
│  - Session Handling                                         │
│  - User Identity                                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     API ROUTES (Next.js)                    │
├─────────────────────────────────────────────────────────────┤
│  withAuth Middleware → Validate Session → Execute Logic     │
│                     ↓                      ↓                 │
│              [Return 401]             [Return data]         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  SUPABASE DATABASE                          │
├─────────────────────────────────────────────────────────────┤
│  Row Level Security (RLS)                                   │
│  ↓                                                           │
│  auth.uid() = user_id → Allow                              │
│  auth.uid() ≠ user_id → Deny                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 📚 Referencias

- [Supabase Auth Documentation](https://supabase.com/docs/guides/auth)
- [Next.js Authentication](https://nextjs.org/docs/authentication)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [Row Level Security Guide](https://supabase.com/docs/guides/auth/row-level-security)

---

## 🎯 Conclusión

**Estado actual:** ⚠️ Sistema completamente inseguro, NO está listo para producción

**Prioridad #1:** Implementar autenticación con Supabase Auth  
**Prioridad #2:** Proteger todas las rutas con middleware  
**Prioridad #3:** Conectar dashboard con datos reales de DB  
**Prioridad #4:** Asegurar APIs con validación de tokens  

**Tiempo estimado para seguridad básica:** 2-3 semanas  
**Tiempo estimado para seguridad empresarial:** 4-6 semanas

**Recomendación:** NO lanzar a producción hasta completar al menos Fase 1 y Fase 2.
