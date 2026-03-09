import { createMiddlewareClient } from '@supabase/auth-helpers-nextjs'
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function createMiddlewareSupabaseClient(req: NextRequest) {
  const res = NextResponse.next()
  return createMiddlewareClient({ req, res })
}
