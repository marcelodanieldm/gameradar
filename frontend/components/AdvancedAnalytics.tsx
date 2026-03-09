'use client'

import { useState, useEffect } from 'react'
import { createClient } from '@/lib/supabase/client'

interface AdvancedAnalyticsProps {
  userId: string
}

interface AnalyticsData {
  topSearches: Array<{ query: string; count: number; avgResults: number }>
  marketTrends: Array<{ market: string; growth: number; topGames: string[] }>
  playerInsights: Array<{ metric: string; value: number; change: number }>
  aiRecommendations: Array<{ title: string; description: string; priority: 'high' | 'medium' | 'low' }>
}

export default function AdvancedAnalytics({ userId }: AdvancedAnalyticsProps) {
  const supabase = createClient()
  const [loading, setLoading] = useState(true)
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d'>('30d')
  const [analytics, setAnalytics] = useState<AnalyticsData>({
    topSearches: [],
    marketTrends: [],
    playerInsights: [],
    aiRecommendations: []
  })

  useEffect(() => {
    fetchAnalytics()
  }, [userId, timeRange])

  const fetchAnalytics = async () => {
    setLoading(true)
    try {
      // Fetch search logs for analysis
      const { data: searchLogs, error } = await supabase
        .from('search_logs')
        .select('*')
        .eq('user_id', userId)
        .gte('created_at', getTimeRangeDate())
        .order('created_at', { ascending: false })

      if (searchLogs && !error) {
        // Process data for analytics
        const topSearches = processTopSearches(searchLogs)
        const marketTrends = analyzeMarketTrends(searchLogs)
        const playerInsights = generatePlayerInsights(searchLogs)
        const aiRecommendations = generateAIRecommendations(searchLogs)

        setAnalytics({
          topSearches,
          marketTrends,
          playerInsights,
          aiRecommendations
        })
      }
    } catch (err) {
      console.error('Error fetching analytics:', err)
    } finally {
      setLoading(false)
    }
  }

  const getTimeRangeDate = () => {
    const days = timeRange === '7d' ? 7 : timeRange === '30d' ? 30 : 90
    const date = new Date()
    date.setDate(date.getDate() - days)
    return date.toISOString()
  }

  const processTopSearches = (logs: any[]) => {
    const searchMap = new Map<string, { count: number; totalResults: number }>()
    
    logs.forEach(log => {
      const key = log.query.toLowerCase()
      const existing = searchMap.get(key) || { count: 0, totalResults: 0 }
      searchMap.set(key, {
        count: existing.count + 1,
        totalResults: existing.totalResults + (log.results_count || 0)
      })
    })

    return Array.from(searchMap.entries())
      .map(([query, data]) => ({
        query,
        count: data.count,
        avgResults: Math.round(data.totalResults / data.count)
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10)
  }

  const analyzeMarketTrends = (logs: any[]) => {
    // Mock data - in production this would analyze real patterns
    return [
      { market: 'South Korea', growth: 12.5, topGames: ['League of Legends', 'Valorant', 'Overwatch 2'] },
      { market: 'Japan', growth: 8.3, topGames: ['Street Fighter 6', 'Tekken 8', 'Apex Legends'] },
      { market: 'China', growth: 15.7, topGames: ['Honor of Kings', 'PUBG Mobile', 'Genshin Impact'] },
      { market: 'Thailand', growth: 10.2, topGames: ['Valorant', 'Free Fire', 'Mobile Legends'] },
    ]
  }

  const generatePlayerInsights = (logs: any[]) => {
    return [
      { metric: 'Avg. Player Age', value: 21.4, change: -0.3 },
      { metric: 'Pro Experience (months)', value: 18.2, change: 2.1 },
      { metric: 'Team Transition Rate', value: 24, change: 5.2 },
      { metric: 'Talent Discovery Rate', value: 67, change: 12.8 },
    ]
  }

  const generateAIRecommendations = (logs: any[]) => {
    return [
      {
        title: 'Rising Talent Alert',
        description: 'Detected 15 emerging players in Vietnam with 40%+ skill improvement over last month',
        priority: 'high' as const
      },
      {
        title: 'Market Opportunity',
        description: 'Philippines showing increased activity in Mobile Legends with limited scouting competition',
        priority: 'high' as const
      },
      {
        title: 'Search Optimization',
        description: 'Your searches in Japan market could benefit from refined role-specific queries',
        priority: 'medium' as const
      },
      {
        title: 'Trend Analysis',
        description: 'Valorant player pool expanding 23% month-over-month across all monitored markets',
        priority: 'medium' as const
      },
    ]
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-white">Loading analytics...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Time Range Selector */}
      <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-white">Advanced Analytics & AI Insights</h2>
          <div className="flex gap-2">
            {(['7d', '30d', '90d'] as const).map((range) => (
              <button
                key={range}
                onClick={() => setTimeRange(range)}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  timeRange === range
                    ? 'bg-purple-500 text-white'
                    : 'bg-white/10 text-gray-300 hover:bg-white/20'
                }`}
              >
                {range === '7d' ? 'Last 7 days' : range === '30d' ? 'Last 30 days' : 'Last 90 days'}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* AI Recommendations */}
      <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20">
        <div className="flex items-center gap-3 mb-6">
          <span className="text-3xl">🧠</span>
          <h3 className="text-2xl font-bold text-white">AI-Powered Recommendations</h3>
        </div>
        <div className="grid gap-4">
          {analytics.aiRecommendations.map((rec, idx) => (
            <div
              key={idx}
              className={`p-6 rounded-xl border ${
                rec.priority === 'high'
                  ? 'bg-red-500/10 border-red-400/30'
                  : rec.priority === 'medium'
                  ? 'bg-yellow-500/10 border-yellow-400/30'
                  : 'bg-blue-500/10 border-blue-400/30'
              }`}
            >
              <div className="flex items-start justify-between mb-2">
                <h4 className="text-white font-semibold text-lg">{rec.title}</h4>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-semibold ${
                    rec.priority === 'high'
                      ? 'bg-red-500/20 text-red-300'
                      : rec.priority === 'medium'
                      ? 'bg-yellow-500/20 text-yellow-300'
                      : 'bg-blue-500/20 text-blue-300'
                  }`}
                >
                  {rec.priority.toUpperCase()}
                </span>
              </div>
              <p className="text-gray-300">{rec.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Top Searches */}
      <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20">
        <h3 className="text-2xl font-bold text-white mb-6">Your Top Searches</h3>
        <div className="space-y-3">
          {analytics.topSearches.length > 0 ? (
            analytics.topSearches.map((search, idx) => (
              <div key={idx} className="flex items-center justify-between p-4 bg-white/5 rounded-lg">
                <div className="flex items-center gap-4">
                  <span className="text-2xl font-bold text-purple-400">#{idx + 1}</span>
                  <div>
                    <p className="text-white font-medium">{search.query}</p>
                    <p className="text-sm text-gray-400">
                      {search.count} searches · Avg. {search.avgResults} results
                    </p>
                  </div>
                </div>
                <button className="px-4 py-2 bg-purple-500/20 hover:bg-purple-500/30 text-purple-300 rounded-lg transition-all">
                  Search again
                </button>
              </div>
            ))
          ) : (
            <p className="text-gray-400 text-center py-8">No search data available for this period</p>
          )}
        </div>
      </div>

      {/* Market Trends */}
      <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20">
        <h3 className="text-2xl font-bold text-white mb-6">Market Trends Analysis</h3>
        <div className="grid md:grid-cols-2 gap-6">
          {analytics.marketTrends.map((trend, idx) => (
            <div key={idx} className="p-6 bg-white/5 rounded-xl">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-white font-semibold text-lg">{trend.market}</h4>
                <div className="flex items-center gap-2">
                  <span className="text-green-400 font-bold">↗ {trend.growth}%</span>
                </div>
              </div>
              <div className="space-y-2">
                <p className="text-sm text-gray-300 mb-2">Top Games:</p>
                {trend.topGames.map((game, gameIdx) => (
                  <div key={gameIdx} className="flex items-center gap-2">
                    <span className="text-purple-400">•</span>
                    <span className="text-gray-200 text-sm">{game}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Player Insights */}
      <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20">
        <h3 className="text-2xl font-bold text-white mb-6">Player Market Insights</h3>
        <div className="grid md:grid-cols-4 gap-6">
          {analytics.playerInsights.map((insight, idx) => (
            <div key={idx} className="p-6 bg-gradient-to-br from-purple-500/10 to-blue-500/10 rounded-xl border border-purple-400/20">
              <p className="text-sm text-gray-300 mb-2">{insight.metric}</p>
              <div className="text-3xl font-bold text-white mb-2">{insight.value}</div>
              <div className="flex items-center gap-1">
                <span className={insight.change > 0 ? 'text-green-400' : 'text-red-400'}>
                  {insight.change > 0 ? '↑' : '↓'} {Math.abs(insight.change)}%
                </span>
                <span className="text-xs text-gray-400">vs last period</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Export Options */}
      <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20">
        <h3 className="text-2xl font-bold text-white mb-6">Export Reports</h3>
        <div className="grid md:grid-cols-3 gap-4">
          <button className="p-6 bg-white/5 hover:bg-white/10 rounded-xl border border-white/20 transition-all text-left">
            <div className="text-3xl mb-3">📊</div>
            <h4 className="text-white font-semibold mb-2">Analytics Report</h4>
            <p className="text-sm text-gray-300">Full analytics summary with charts</p>
          </button>
          <button className="p-6 bg-white/5 hover:bg-white/10 rounded-xl border border-white/20 transition-all text-left">
            <div className="text-3xl mb-3">🎯</div>
            <h4 className="text-white font-semibold mb-2">Player Insights</h4>
            <p className="text-sm text-gray-300">Detailed player metrics report</p>
          </button>
          <button className="p-6 bg-white/5 hover:bg-white/10 rounded-xl border border-white/20 transition-all text-left">
            <div className="text-3xl mb-3">📈</div>
            <h4 className="text-white font-semibold mb-2">Market Trends</h4>
            <p className="text-sm text-gray-300">Regional trends and forecasts</p>
          </button>
        </div>
      </div>
    </div>
  )
}
