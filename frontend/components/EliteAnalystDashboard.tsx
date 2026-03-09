'use client'

import { useState, useEffect } from 'react'
import { createClient } from '@/lib/supabase/client'
import AdvancedAnalytics from './AdvancedAnalytics'
import TalentPingAlerts from './TalentPingAlerts'
import APIAccessPanel from './APIAccessPanel'

interface EliteAnalystDashboardProps {
  userId: string
  initialStats: {
    searchesCount: number
    daysRemaining: number
    alertsActive: number
    apiCallsToday: number
  }
  selectedMarkets: string[]
}

interface UsageStats {
  searchesCount: number
  daysRemaining: number
  alertsActive: number
  apiCallsToday: number
  lastSearchAt: string | null
}

const MARKET_DATA = {
  KR: { name: 'South Korea', flag: '🇰🇷', color: 'from-red-500 to-blue-500' },
  JP: { name: 'Japan', flag: '🇯🇵', color: 'from-red-600 to-white' },
  CN: { name: 'China', flag: '🇨🇳', color: 'from-red-600 to-yellow-400' },
  TH: { name: 'Thailand', flag: '🇹🇭', color: 'from-red-500 to-blue-600' },
  VN: { name: 'Vietnam', flag: '🇻🇳', color: 'from-red-600 to-yellow-500' },
  PH: { name: 'Philippines', flag: '🇵🇭', color: 'from-blue-500 to-red-500' },
  IN: { name: 'India', flag: '🇮🇳', color: 'from-orange-500 to-green-600' },
}

export default function EliteAnalystDashboard({
  userId,
  initialStats,
  selectedMarkets
}: EliteAnalystDashboardProps) {
  const supabase = createClient()
  const [stats, setStats] = useState<UsageStats>(initialStats)
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'overview' | 'analytics' | 'alerts' | 'api'>('overview')

  // Fetch updated stats every 30 seconds
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const { data, error } = await supabase
          .from('active_subscriptions_view')
          .select('*')
          .eq('user_id', userId)
          .single()

        if (data && !error) {
          const periodEnd = new Date(data.current_period_end)
          const now = new Date()
          const daysRemaining = Math.ceil((periodEnd.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))

          setStats({
            searchesCount: data.searches_count || 0,
            daysRemaining: daysRemaining,
            alertsActive: data.alerts_active || 0,
            apiCallsToday: data.api_calls_today || 0,
            lastSearchAt: data.last_search_at
          })
        }
      } catch (err) {
        console.error('Error fetching stats:', err)
      }
    }

    const interval = setInterval(fetchStats, 30000) // 30 seconds
    return () => clearInterval(interval)
  }, [userId, supabase])

  const markets = selectedMarkets.map(code => ({
    code,
    ...(MARKET_DATA[code as keyof typeof MARKET_DATA] || { name: code, flag: '🌏', color: 'from-gray-500 to-gray-700' })
  }))

  const tabs = [
    { id: 'overview', label: 'Overview', icon: '📊' },
    { id: 'analytics', label: 'Advanced Analytics', icon: '🧠' },
    { id: 'alerts', label: 'TalentPing Alerts', icon: '🔔' },
    { id: 'api', label: 'API Access', icon: '🔌' },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-indigo-900 to-blue-900 py-8 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20 mb-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <div className="px-3 py-1 bg-purple-500/30 rounded-full border border-purple-400/50">
                  <span className="text-purple-200 text-sm font-semibold">ELITE ANALYST</span>
                </div>
                <span className="text-gray-300 text-sm">Professional Plan</span>
              </div>
              <h1 className="text-4xl font-bold text-white">Advanced Dashboard</h1>
              <p className="text-gray-300 mt-2">Complete platform access with unlimited possibilities</p>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-300 mb-1">Subscription Status</div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-white font-semibold">Active</span>
              </div>
              <div className="text-sm text-gray-400 mt-1">{stats.daysRemaining} days remaining</div>
            </div>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="bg-gradient-to-br from-blue-500/20 to-cyan-500/20 rounded-xl p-6 border border-blue-400/30">
              <div className="flex items-center justify-between mb-2">
                <span className="text-blue-200 text-sm font-medium">Total Searches</span>
                <span className="text-2xl">🔍</span>
              </div>
              <div className="text-3xl font-bold text-white mb-1">{stats.searchesCount.toLocaleString()}</div>
              <div className="text-sm text-blue-200">Unlimited usage</div>
            </div>

            <div className="bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-xl p-6 border border-purple-400/30">
              <div className="flex items-center justify-between mb-2">
                <span className="text-purple-200 text-sm font-medium">Active Alerts</span>
                <span className="text-2xl">🔔</span>
              </div>
              <div className="text-3xl font-bold text-white mb-1">{stats.alertsActive}</div>
              <div className="text-sm text-purple-200">Real-time monitoring</div>
            </div>

            <div className="bg-gradient-to-br from-green-500/20 to-emerald-500/20 rounded-xl p-6 border border-green-400/30">
              <div className="flex items-center justify-between mb-2">
                <span className="text-green-200 text-sm font-medium">API Calls Today</span>
                <span className="text-2xl">🔌</span>
              </div>
              <div className="text-3xl font-bold text-white mb-1">{stats.apiCallsToday.toLocaleString()}</div>
              <div className="text-sm text-green-200">Integration active</div>
            </div>

            <div className="bg-gradient-to-br from-orange-500/20 to-red-500/20 rounded-xl p-6 border border-orange-400/30">
              <div className="flex items-center justify-between mb-2">
                <span className="text-orange-200 text-sm font-medium">Markets Access</span>
                <span className="text-2xl">🌏</span>
              </div>
              <div className="text-3xl font-bold text-white mb-1">{markets.length}/7</div>
              <div className="text-sm text-orange-200">All regions</div>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-2 border border-white/20 mb-8">
          <div className="flex gap-2">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex-1 py-3 px-4 rounded-xl font-medium transition-all ${
                  activeTab === tab.id
                    ? 'bg-white/20 text-white shadow-lg'
                    : 'text-gray-300 hover:bg-white/5'
                }`}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === 'overview' && (
          <div className="space-y-8">
            {/* Markets Access */}
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20">
              <h2 className="text-2xl font-bold text-white mb-6">Your Market Coverage</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {markets.map((market) => (
                  <div
                    key={market.code}
                    className={`bg-gradient-to-br ${market.color} bg-opacity-20 rounded-xl p-6 border border-white/30 hover:scale-105 transition-transform cursor-pointer`}
                  >
                    <div className="text-4xl mb-3">{market.flag}</div>
                    <h3 className="text-white font-semibold text-lg">{market.name}</h3>
                    <p className="text-gray-200 text-sm mt-1">Full access</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Quick Actions */}
            <div className="grid md:grid-cols-3 gap-6">
              <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20 hover:bg-white/15 transition-all cursor-pointer">
                <div className="text-3xl mb-3">📈</div>
                <h3 className="text-white font-semibold text-lg mb-2">View Analytics</h3>
                <p className="text-gray-300 text-sm">Deep insights and AI-powered analysis</p>
              </div>

              <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20 hover:bg-white/15 transition-all cursor-pointer">
                <div className="text-3xl mb-3">🎯</div>
                <h3 className="text-white font-semibold text-lg mb-2">Set Alerts</h3>
                <p className="text-gray-300 text-sm">Get notified of new talent instantly</p>
              </div>

              <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20 hover:bg-white/15 transition-all cursor-pointer">
                <div className="text-3xl mb-3">📥</div>
                <h3 className="text-white font-semibold text-lg mb-2">Export Reports</h3>
                <p className="text-gray-300 text-sm">Download custom PDF reports</p>
              </div>
            </div>

            {/* Recent Activity */}
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20">
              <h2 className="text-2xl font-bold text-white mb-6">Recent Activity</h2>
              <div className="space-y-4">
                <div className="flex items-center gap-4 p-4 bg-white/5 rounded-lg">
                  <div className="w-10 h-10 bg-blue-500/20 rounded-full flex items-center justify-center">
                    <span className="text-xl">🔍</span>
                  </div>
                  <div className="flex-1">
                    <p className="text-white font-medium">Search performed</p>
                    <p className="text-gray-400 text-sm">
                      {stats.lastSearchAt 
                        ? new Date(stats.lastSearchAt).toLocaleString()
                        : 'No recent searches'
                      }
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-4 p-4 bg-white/5 rounded-lg">
                  <div className="w-10 h-10 bg-green-500/20 rounded-full flex items-center justify-center">
                    <span className="text-xl">✅</span>
                  </div>
                  <div className="flex-1">
                    <p className="text-white font-medium">Subscription active</p>
                    <p className="text-gray-400 text-sm">Unlimited access enabled</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'analytics' && <AdvancedAnalytics userId={userId} />}
        {activeTab === 'alerts' && <TalentPingAlerts userId={userId} />}
        {activeTab === 'api' && <APIAccessPanel userId={userId} />}
      </div>
    </div>
  )
}
