# 🔐 Implementación de Seguridad - Guía Paso a Paso

Esta guía te lleva desde el estado actual (sin seguridad) hasta un sistema completamente seguro.

---

## 📦 Paso 1: Instalar Dependencias

```bash
cd frontend
npm install @supabase/auth-helpers-nextjs @supabase/supabase-js
npm install @upstash/ratelimit @upstash/redis  # Para rate limiting
npm install zod  # Para validación de inputs
npm install jose  # Para JWT verification
```

---

## 🔧 Paso 2: Configurar Variables de Entorno

Crear `frontend/.env.local`:

```bash
# Supabase (públicas, OK para exponer)
NEXT_PUBLIC_SUPABASE_URL=https://tu-proyecto.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJI...

# Supabase (SECRETAS, solo server-side)
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Rate Limiting (opcional)
UPSTASH_REDIS_REST_URL=https://xxx.upstash.io
UPSTASH_REDIS_REST_TOKEN=AbCdEf123...

# Backend
BACKEND_URL=http://localhost:8000

# Environment
NODE_ENV=development
```

Agregar a `.gitignore`:
```
.env.local
.env*.local
```

---

## 🗄️ Paso 3: Ejecutar Migración de Base de Datos

1. Ir a Supabase Dashboard → SQL Editor
2. Ejecutar el script `supabase/migrations/002_subscription_security.sql`
3. Verificar que se crearon las tablas:
   - `subscription_plans`
   - `subscriptions`
   - `payment_history`
   - `subscription_usage`
   - `search_logs`

---

## 🔐 Paso 4: Crear Utilidades de Autenticación

### `lib/supabase/client.ts` (Client-side)

```typescript
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs'

export function createClient() {
  return createClientComponentClient()
}
```

### `lib/supabase/server.ts` (Server-side)

```typescript
import { createServerComponentClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'

export function createServerClient() {
  return createServerComponentClient({ cookies })
}
```

### `lib/supabase/middleware.ts` (Middleware)

```typescript
import { createMiddlewareClient } from '@supabase/auth-helpers-nextjs'
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function createMiddlewareSupabaseClient(req: NextRequest) {
  const res = NextResponse.next()
  return createMiddlewareClient({ req, res })
}
```

### `lib/auth/auth-helpers.ts` (Helper Functions)

```typescript
import { createServerClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'

export async function requireAuth() {
  const supabase = createServerClient()
  const { data: { session } } = await supabase.auth.getSession()
  
  if (!session) {
    redirect('/login')
  }
  
  return session
}

export async function requireActiveSubscription() {
  const supabase = createServerClient()
  const session = await requireAuth()
  
  const { data: subscription, error } = await supabase
    .from('subscriptions')
    .select(`
      *,
      plan:subscription_plans(*)
    `)
    .eq('user_id', session.user.id)
    .eq('status', 'active')
    .single()
  
  if (error || !subscription) {
    redirect('/subscribe')
  }
  
  return { session, subscription }
}

export async function getUserSubscriptionData(userId: string) {
  const supabase = createServerClient()
  
  const { data, error } = await supabase
    .rpc('get_active_subscription', { p_user_id: userId })
  
  if (error) throw error
  
  return data[0] || null
}
```

---

## 🚪 Paso 5: Crear Páginas de Autenticación

### `app/[locale]/login/page.tsx`

```typescript
'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const router = useRouter()
  const supabase = createClient()

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError('')

    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })

    if (error) {
      setError(error.message)
      setLoading(false)
      return
    }

    router.push('/dashboard')
    router.refresh()
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center p-6">
      <div className="max-w-md w-full bg-slate-800/50 backdrop-blur rounded-xl p-8 border border-slate-700">
        <h1 className="text-3xl font-bold text-white mb-6">Iniciar Sesión</h1>
        
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 bg-slate-900/50 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Contraseña
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 bg-slate-900/50 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
              required
            />
          </div>

          {error && (
            <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold transition disabled:opacity-50"
          >
            {loading ? 'Iniciando sesión...' : 'Iniciar Sesión'}
          </button>
        </form>

        <p className="text-slate-400 text-sm mt-6 text-center">
          ¿No tienes cuenta?{' '}
          <a href="/signup" className="text-blue-400 hover:text-blue-300">
            Regístrate
          </a>
        </p>
      </div>
    </div>
  )
}
```

### `app/[locale]/signup/page.tsx`

```typescript
'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'

export default function SignupPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const router = useRouter()
  const supabase = createClient()

  async function handleSignup(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError('')

    if (password !== confirmPassword) {
      setError('Las contraseñas no coinciden')
      setLoading(false)
      return
    }

    if (password.length < 8) {
      setError('La contraseña debe tener al menos 8 caracteres')
      setLoading(false)
      return
    }

    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        emailRedirectTo: `${window.location.origin}/auth/callback`,
      },
    })

    if (error) {
      setError(error.message)
      setLoading(false)
      return
    }

    // Mostrar mensaje de verificación de email
    alert('¡Registro exitoso! Revisa tu email para confirmar tu cuenta.')
    router.push('/login')
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center p-6">
      <div className="max-w-md w-full bg-slate-800/50 backdrop-blur rounded-xl p-8 border border-slate-700">
        <h1 className="text-3xl font-bold text-white mb-6">Crear Cuenta</h1>
        
        <form onSubmit={handleSignup} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 bg-slate-900/50 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Contraseña
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 bg-slate-900/50 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
              required
              minLength={8}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Confirmar Contraseña
            </label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full px-4 py-3 bg-slate-900/50 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
              required
              minLength={8}
            />
          </div>

          {error && (
            <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold transition disabled:opacity-50"
          >
            {loading ? 'Creando cuenta...' : 'Crear Cuenta'}
          </button>
        </form>

        <p className="text-slate-400 text-sm mt-6 text-center">
          ¿Ya tienes cuenta?{' '}
          <a href="/login" className="text-blue-400 hover:text-blue-300">
            Inicia sesión
          </a>
        </p>
      </div>
    </div>
  )
}
```

### `app/[locale]/auth/callback/route.ts` (Auth Callback)

```typescript
import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export async function GET(request: NextRequest) {
  const requestUrl = new URL(request.url)
  const code = requestUrl.searchParams.get('code')

  if (code) {
    const supabase = createRouteHandlerClient({ cookies })
    await supabase.auth.exchangeCodeForSession(code)
  }

  return NextResponse.redirect(requestUrl.origin)
}
```

---

## 🛡️ Paso 6: Actualizar Middleware con Auth

### `middleware.ts`

```typescript
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
  const res = NextResponse.next()
  const supabase = createMiddlewareClient({ req, res })

  // Refresh session si existe
  const { data: { session } } = await supabase.auth.getSession()

  // Rutas protegidas
  const protectedPaths = [
    '/dashboard',
    '/settings',
    '/analytics',
    '/search',
    '/account'
  ]

  const isProtectedPath = protectedPaths.some(path =>
    req.nextUrl.pathname.includes(path)
  )

  // Si es ruta protegida y NO hay sesión → redirigir a login
  if (isProtectedPath && !session) {
    const redirectUrl = req.nextUrl.clone()
    redirectUrl.pathname = '/login'
    redirectUrl.searchParams.set('redirectTo', req.nextUrl.pathname)
    return NextResponse.redirect(redirectUrl)
  }

  // Si tiene sesión, verificar suscripción activa
  if (isProtectedPath && session) {
    const { data: subscription } = await supabase
      .from('subscriptions')
      .select('status')
      .eq('user_id', session.user.id)
      .eq('status', 'active')
      .single()

    if (!subscription) {
      return NextResponse.redirect(new URL('/subscribe', req.url))
    }
  }

  // Continuar con i18n middleware
  return intlMiddleware(req)
}

export const config = {
  matcher: ['/', '/(ko|zh|hi|vi|th|ja|en)/:path*']
}
```

---

## 📊 Paso 7: Actualizar Dashboard con Datos Reales

### `app/[locale]/dashboard/page.tsx`

```typescript
import { requireActiveSubscription } from '@/lib/auth/auth-helpers'
import StreetScoutDashboard from '@/components/StreetScoutDashboard'
import { createServerClient } from '@/lib/supabase/server'

export default async function DashboardPage() {
  const { session, subscription } = await requireActiveSubscription()
  
  const supabase = createServerClient()
  
  // Obtener datos de uso real
  const { data: usage } = await supabase
    .from('subscription_usage')
    .select('*')
    .eq('subscription_id', subscription.id)
    .eq('period_start', subscription.current_period_start)
    .single()

  const statsData = {
    searchesUsed: usage?.searches_used || 0,
    searchesLimit: subscription.plan.searches_per_month,
    marketsUsed: subscription.selected_markets?.length || 0,
    marketsLimit: subscription.plan.max_markets,
    currentPeriodStart: subscription.current_period_start,
    currentPeriodEnd: subscription.current_period_end,
    subscriptionStatus: subscription.status,
  }

  return (
    <StreetScoutDashboard 
      userId={session.user.id}
      initialStats={statsData}
    />
  )
}
```

### `components/StreetScoutDashboard.tsx` (Actualizado)

```typescript
'use client'

import React, { useState, useEffect } from 'react'
import { createClient } from '@/lib/supabase/client'

interface DashboardProps {
  userId: string
  initialStats: UsageStats
}

export default function StreetScoutDashboard({ userId, initialStats }: DashboardProps) {
  const [stats, setStats] = useState<UsageStats>(initialStats)
  const [loading, setLoading] = useState(false)
  const supabase = createClient()

  useEffect(() => {
    // Cargar datos actualizados
    async function fetchLatestData() {
      const { data } = await supabase
        .from('active_subscriptions_view')
        .select('*')
        .eq('user_id', userId)
        .single()

      if (data) {
        setStats({
          searchesUsed: data.searches_used,
          searchesLimit: data.searches_limit,
          // ... resto de campos
        })
      }
    }

    fetchLatestData()
  }, [userId])

  // Resto del componente igual...
  // pero ahora usa datos reales de la DB
}
```

---

## 🔒 Paso 8: Proteger APIs con Auth Middleware

### `lib/api/auth-middleware.ts`

```typescript
import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { NextResponse } from 'next/server'
import type { Session } from '@supabase/supabase-js'

export type AuthenticatedHandler = (
  request: Request,
  session: Session
) => Promise<Response>

export function withAuth(handler: AuthenticatedHandler) {
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

export function withSubscription(handler: AuthenticatedHandler) {
  return withAuth(async (request: Request, session: Session) => {
    const supabase = createRouteHandlerClient({ cookies })
    
    const { data: subscription } = await supabase
      .from('subscriptions')
      .select('*')
      .eq('user_id', session.user.id)
      .eq('status', 'active')
      .single()
    
    if (!subscription) {
      return NextResponse.json(
        { error: 'Active subscription required' },
        { status: 403 }
      )
    }

    return handler(request, session)
  })
}
```

### `app/api/search/route.ts` (Ejemplo protegido)

```typescript
import { withSubscription } from '@/lib/api/auth-middleware'
import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { NextResponse } from 'next/server'

export const POST = withSubscription(async (request: Request, session: any) => {
  const supabase = createRouteHandlerClient({ cookies })
  const body = await request.json()
  
  // Verificar que el usuario puede hacer búsquedas
  const { data: canSearch } = await supabase
    .rpc('can_user_search', { p_user_id: session.user.id })
  
  if (!canSearch) {
    return NextResponse.json(
      { error: 'Search limit reached' },
      { status: 429 }
    )
  }

  // Realizar búsqueda...
  const results = await performSearch(body.query)

  // Incrementar contador
  await supabase.rpc('increment_search_count', { 
    p_user_id: session.user.id 
  })

  return NextResponse.json(results)
})
```

---

## 🚀 Paso 9: Testing

### Probar el flujo completo:

```bash
# 1. Iniciar dev server
cd frontend
npm run dev

# 2. Abrir http://localhost:3000

# 3. Intentar acceder a /dashboard
#    → Debe redirigir a /login

# 4. Crear cuenta en /signup
#    → Verificar email recibido

# 5. Confirmar email y login

# 6. Intentar acceder a /dashboard
#    → Debe redirigir a /subscribe (no tiene suscripción)

# 7. Completar pago en /subscribe/street-scout

# 8. Acceder a /dashboard
#    → Ahora SÍ debe mostrar el dashboard con datos reales
```

---

## ✅ Checklist de Implementación

### Básico (Esencial)
- [ ] Instalar `@supabase/auth-helpers-nextjs`
- [ ] Configurar variables de entorno
- [ ] Ejecutar migración SQL
- [ ] Crear páginas de login/signup
- [ ] Actualizar middleware con auth
- [ ] Proteger ruta del dashboard
- [ ] Conectar dashboard con DB real

### Intermedio (Recomendado)
- [ ] Implementar `withAuth` middleware para APIs
- [ ] Proteger todas las APIs con auth
- [ ] Verificar suscripción activa en APIs
- [ ] Implementar rate limiting básico
- [ ] Validar inputs con Zod

### Avanzado (Producción)
- [ ] Rate limiting con Upstash Redis
- [ ] CSRF protection
- [ ] Audit logging
- [ ] Security headers en next.config.js
- [ ] Testing de seguridad
- [ ] Monitoring de accesos

---

## 🆘 Troubleshooting

### Error: "Invalid Refresh Token"
```typescript
// Limpiar sesión y redirigir a login
const supabase = createClient()
await supabase.auth.signOut()
router.push('/login')
```

### Error: "Failed to fetch session"
```typescript
// Verificar que NEXT_PUBLIC_SUPABASE_URL está configurado
console.log(process.env.NEXT_PUBLIC_SUPABASE_URL)
```

### Error: "Could not find subscription"
```sql
-- Asegurarse de que RLS está habilitado y políticas creadas
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public';
```

---

## 📚 Referencias

- [Supabase Auth Helpers](https://supabase.com/docs/guides/auth/auth-helpers/nextjs)
- [Next.js Middleware](https://nextjs.org/docs/app/building-your-application/routing/middleware)
- [Supabase RLS](https://supabase.com/docs/guides/auth/row-level-security)
