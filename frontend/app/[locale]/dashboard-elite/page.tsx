import { redirect } from 'next/navigation'
import { cookies } from 'next/headers'
import { createServerClient } from '@/lib/supabase/server'
import { requireActiveSubscription } from '@/lib/auth/auth-helpers'
import EliteAnalystDashboard from '@/components/EliteAnalystDashboard'

export default async function EliteAnalystDashboardPage() {
  // Require active Elite Analyst subscription
  const subscription = await requireActiveSubscription()
  
  // Verify this is Elite Analyst subscription
  const supabase = createServerClient(cookies())
  const { data: subscriptionData, error } = await supabase
    .from('subscriptions')
    .select('*, subscription_plans(*)')
    .eq('user_id', subscription.user.id)
    .eq('status', 'active')
    .single()

  if (error || !subscriptionData || subscriptionData.subscription_plans.name !== 'Elite Analyst') {
    redirect('/subscribe/elite-analyst')
  }

  // Fetch usage stats
  const { data: usageData } = await supabase
    .from('subscription_usage')
    .select('*')
    .eq('user_id', subscription.user.id)
    .single()

  // Fetch alert count
  const { count: alertsCount } = await supabase
    .from('talent_ping_alerts')
    .select('*', { count: 'exact', head: true })
    .eq('user_id', subscription.user.id)
    .eq('is_active', true)

  // Fetch API usage
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const { count: apiCallsToday } = await supabase
    .from('api_usage_logs')
    .select('*', { count: 'exact', head: true })
    .eq('user_id', subscription.user.id)
    .gte('created_at', today.toISOString())

  // Calculate days remaining
  const periodEnd = new Date(subscriptionData.current_period_end)
  const now = new Date()
  const daysRemaining = Math.ceil((periodEnd.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))

  const initialStats = {
    searchesCount: usageData?.searches_count || 0,
    daysRemaining: daysRemaining,
    alertsActive: alertsCount || 0,
    apiCallsToday: apiCallsToday || 0,
  }

  return (
    <EliteAnalystDashboard
      userId={subscription.user.id}
      initialStats={initialStats}
      selectedMarkets={subscriptionData.selected_markets || []}
    />
  )
}
