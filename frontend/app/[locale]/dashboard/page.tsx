import { requireActiveSubscription } from '@/lib/auth/auth-helpers'
import StreetScoutDashboard from '@/components/StreetScoutDashboard'
import { createServerClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'

export default async function DashboardPage() {
  try {
    const { session, subscription } = await requireActiveSubscription()
    
    const supabase = createServerClient()
    
    // Get real usage data
    const { data: usage } = await supabase
      .from('subscription_usage')
      .select('*')
      .eq('subscription_id', subscription.id)
      .gte('period_start', subscription.current_period_start)
      .lte('period_end', subscription.current_period_end)
      .single()

    // Calculate days remaining
    const daysRemaining = Math.ceil(
      (new Date(subscription.current_period_end).getTime() - new Date().getTime()) / 
      (1000 * 60 * 60 * 24)
    )

    const statsData = {
      searchesUsed: usage?.searches_used || 0,
      searchesLimit: subscription.plan.searches_per_month || 50,
      marketsUsed: subscription.selected_markets?.length || 0,
      marketsLimit: subscription.plan.max_markets || 3,
      currentPeriodStart: subscription.current_period_start,
      currentPeriodEnd: subscription.current_period_end,
      subscriptionStatus: subscription.status as 'active' | 'trial' | 'expired',
      daysRemaining: daysRemaining,
    }

    return (
      <StreetScoutDashboard 
        userId={session.user.id}
        initialStats={statsData}
        selectedMarkets={subscription.selected_markets || []}
      />
    )
  } catch (error) {
    console.error('Dashboard error:', error)
    // If any error occurs, redirect to login
    redirect('/login')
  }
}
