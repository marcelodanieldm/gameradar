import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { NextResponse } from 'next/server'
import type { Session } from '@supabase/supabase-js'

export type AuthenticatedHandler = (
  request: Request,
  session: Session
) => Promise<Response>

/**
 * Middleware to protect API routes with authentication
 * Usage: export const POST = withAuth(async (request, session) => { ... })
 */
export function withAuth(handler: AuthenticatedHandler) {
  return async (request: Request) => {
    const supabase = createRouteHandlerClient({ cookies })
    
    const { data: { session } } = await supabase.auth.getSession()
    
    if (!session) {
      return NextResponse.json(
        { error: 'Unauthorized - Please login' },
        { status: 401 }
      )
    }

    return handler(request, session)
  }
}

/**
 * Middleware to protect API routes with authentication AND active subscription
 * Usage: export const POST = withSubscription(async (request, session) => { ... })
 */
export function withSubscription(handler: AuthenticatedHandler) {
  return withAuth(async (request: Request, session: Session) => {
    const supabase = createRouteHandlerClient({ cookies })
    
    const { data: subscription } = await supabase
      .from('subscriptions')
      .select('*, plan:subscription_plans(*)')
      .eq('user_id', session.user.id)
      .eq('status', 'active')
      .gte('current_period_end', new Date().toISOString())
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

/**
 * Verify if user can perform a search
 */
export async function canUserSearch(userId: string): Promise<boolean> {
  const supabase = createRouteHandlerClient({ cookies })
  
  const { data, error } = await supabase
    .rpc('can_user_search', { p_user_id: userId })
  
  if (error) {
    console.error('Error checking search permission:', error)
    return false
  }
  
  return data || false
}

/**
 * Increment user's search count
 */
export async function incrementSearchCount(userId: string): Promise<boolean> {
  const supabase = createRouteHandlerClient({ cookies })
  
  const { data, error } = await supabase
    .rpc('increment_search_count', { p_user_id: userId })
  
  if (error) {
    console.error('Error incrementing search count:', error)
    return false
  }
  
  return data || false
}
