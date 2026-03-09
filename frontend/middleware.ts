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

  // Refresh session if exists
  const { data: { session } } = await supabase.auth.getSession()

  // Define protected routes that require authentication
  const protectedPaths = [
    '/dashboard',
    '/settings',
    '/analytics',
    '/search',
    '/account'
  ]

  // Elite Analyst specific routes
  const eliteAnalystPaths = [
    '/dashboard-elite'
  ]

  // Check if current path is protected
  const isProtectedPath = protectedPaths.some(path =>
    req.nextUrl.pathname.includes(path)
  )

  const isEliteAnalystPath = eliteAnalystPaths.some(path =>
    req.nextUrl.pathname.includes(path)
  )

  // Redirect to login if accessing protected route without session
  if ((isProtectedPath || isEliteAnalystPath) && !session) {
    const redirectUrl = req.nextUrl.clone()
    redirectUrl.pathname = '/login'
    redirectUrl.searchParams.set('redirectTo', req.nextUrl.pathname)
    return NextResponse.redirect(redirectUrl)
  }

  // If user has session, verify active subscription for protected routes
  if ((isProtectedPath || isEliteAnalystPath) && session) {
    const { data: subscription } = await supabase
      .from('subscriptions')
      .select('status, current_period_end, subscription_plans(name)')
      .eq('user_id', session.user.id)
      .eq('status', 'active')
      .single()

    // Check if subscription exists and is not expired
    if (!subscription || new Date(subscription.current_period_end) < new Date()) {
      // Redirect to subscription page if no active subscription
      return NextResponse.redirect(new URL('/subscribe/street-scout', req.url))
    }

    // For Elite Analyst specific routes, verify user has Elite Analyst plan
    if (isEliteAnalystPath && subscription.subscription_plans?.name !== 'Elite Analyst') {
      // User doesn't have Elite Analyst plan, redirect to upgrade page
      return NextResponse.redirect(new URL('/subscribe/elite-analyst', req.url))
    }
  }

  // Continue with i18n middleware for other routes
  return intlMiddleware(req)
}

export const config = {
  matcher: ['/', '/(ko|zh|hi|vi|th|ja|en)/:path*']
}
