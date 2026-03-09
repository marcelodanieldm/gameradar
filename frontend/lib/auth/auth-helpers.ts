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
  
  return data && data.length > 0 ? data[0] : null
}
