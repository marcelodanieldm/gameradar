'use client'

import { useState, useEffect } from 'react'
import { createClient } from '@/lib/supabase/client'

interface TalentPingAlertsProps {
  userId: string
}

interface Alert {
  id: string
  name: string
  markets: string[]
  games: string[]
  criteria: {
    minKDA?: number
    minWinRate?: number
    minRank?: string
    roles?: string[]
  }
  notificationChannels: Array<'email' | 'sms' | 'webhook'>
  isActive: boolean
  matchesFound: number
  lastTriggered?: string
  createdAt: string
}

export default function TalentPingAlerts({ userId }: TalentPingAlertsProps) {
  const supabase = createClient()
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [loading, setLoading] = useState(true)

  const [newAlert, setNewAlert] = useState<Partial<Alert>>({
    name: '',
    markets: [],
    games: [],
    criteria: {},
    notificationChannels: ['email'],
    isActive: true
  })

  useEffect(() => {
    fetchAlerts()
  }, [userId])

  const fetchAlerts = async () => {
    setLoading(true)
    try {
      const { data, error } = await supabase
        .from('talent_ping_alerts')
        .select('*')
        .eq('user_id', userId)
        .order('created_at', { ascending: false })

      if (data && !error) {
        setAlerts(data)
      }
    } catch (err) {
      console.error('Error fetching alerts:', err)
    } finally {
      setLoading(false)
    }
  }

  const createAlert = async () => {
    try {
      const { data, error } = await supabase
        .from('talent_ping_alerts')
        .insert([{
          user_id: userId,
          ...newAlert,
          matches_found: 0
        }])
        .select()

      if (data && !error) {
        setAlerts([data[0], ...alerts])
        setShowCreateModal(false)
        resetNewAlert()
      }
    } catch (err) {
      console.error('Error creating alert:', err)
    }
  }

  const toggleAlert = async (alertId: string, isActive: boolean) => {
    try {
      const { error } = await supabase
        .from('talent_ping_alerts')
        .update({ is_active: isActive })
        .eq('id', alertId)

      if (!error) {
        setAlerts(alerts.map(a => a.id === alertId ? { ...a, isActive } : a))
      }
    } catch (err) {
      console.error('Error toggling alert:', err)
    }
  }

  const deleteAlert = async (alertId: string) => {
    try {
      const { error } = await supabase
        .from('talent_ping_alerts')
        .delete()
        .eq('id', alertId)

      if (!error) {
        setAlerts(alerts.filter(a => a.id !== alertId))
      }
    } catch (err) {
      console.error('Error deleting alert:', err)
    }
  }

  const resetNewAlert = () => {
    setNewAlert({
      name: '',
      markets: [],
      games: [],
      criteria: {},
      notificationChannels: ['email'],
      isActive: true
    })
  }

  const marketOptions = [
    { code: 'KR', name: 'South Korea', flag: '🇰🇷' },
    { code: 'JP', name: 'Japan', flag: '🇯🇵' },
    { code: 'CN', name: 'China', flag: '🇨🇳' },
    { code: 'TH', name: 'Thailand', flag: '🇹🇭' },
    { code: 'VN', name: 'Vietnam', flag: '🇻🇳' },
    { code: 'PH', name: 'Philippines', flag: '🇵🇭' },
    { code: 'IN', name: 'India', flag: '🇮🇳' },
  ]

  const gameOptions = [
    'League of Legends',
    'Valorant',
    'Dota 2',
    'CS:GO',
    'Overwatch 2',
    'Mobile Legends',
    'PUBG Mobile'
  ]

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-white">Loading alerts...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className="text-3xl">🔔</span>
              <h2 className="text-3xl font-bold text-white">TalentPing Alerts</h2>
            </div>
            <p className="text-gray-300">Real-time notifications when new talent matches your criteria</p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-6 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 text-white font-semibold rounded-lg hover:from-purple-700 hover:to-indigo-700 transition-all"
          >
            + Create New Alert
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-6 mt-8">
          <div className="p-6 bg-white/5 rounded-xl">
            <div className="text-3xl font-bold text-white mb-1">{alerts.length}</div>
            <p className="text-gray-300">Total Alerts</p>
          </div>
          <div className="p-6 bg-white/5 rounded-xl">
            <div className="text-3xl font-bold text-green-400 mb-1">
              {alerts.filter(a => a.isActive).length}
            </div>
            <p className="text-gray-300">Active</p>
          </div>
          <div className="p-6 bg-white/5 rounded-xl">
            <div className="text-3xl font-bold text-blue-400 mb-1">
              {alerts.reduce((sum, a) => sum + a.matchesFound, 0)}
            </div>
            <p className="text-gray-300">Total Matches</p>
          </div>
        </div>
      </div>

      {/* Alerts List */}
      <div className="space-y-4">
        {alerts.length > 0 ? (
          alerts.map((alert) => (
            <div
              key={alert.id}
              className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20 hover:bg-white/15 transition-all"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-xl font-bold text-white">{alert.name}</h3>
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                      alert.isActive 
                        ? 'bg-green-500/20 text-green-300' 
                        : 'bg-gray-500/20 text-gray-300'
                    }`}>
                      {alert.isActive ? 'ACTIVE' : 'PAUSED'}
                    </span>
                  </div>
                  
                  <div className="flex flex-wrap gap-4 text-sm text-gray-300">
                    <div className="flex items-center gap-2">
                      <span>🌏</span>
                      <span>{alert.markets.length} markets</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span>🎮</span>
                      <span>{alert.games.join(', ')}</span>
                    </div>
                    {alert.criteria.minWinRate && (
                      <div className="flex items-center gap-2">
                        <span>📈</span>
                        <span>Win rate ≥ {alert.criteria.minWinRate}%</span>
                      </div>
                    )}
                    {alert.criteria.minKDA && (
                      <div className="flex items-center gap-2">
                        <span>⚔️</span>
                        <span>KDA ≥ {alert.criteria.minKDA}</span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <button
                    onClick={() => toggleAlert(alert.id, !alert.isActive)}
                    className={`p-2 rounded-lg transition-all ${
                      alert.isActive
                        ? 'bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-300'
                        : 'bg-green-500/20 hover:bg-green-500/30 text-green-300'
                    }`}
                  >
                    {alert.isActive ? '⏸️ Pause' : '▶️ Resume'}
                  </button>
                  <button
                    onClick={() => deleteAlert(alert.id)}
                    className="p-2 bg-red-500/20 hover:bg-red-500/30 text-red-300 rounded-lg transition-all"
                  >
                    🗑️ Delete
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t border-white/10">
                <div>
                  <p className="text-sm text-gray-400 mb-1">Matches Found</p>
                  <p className="text-2xl font-bold text-white">{alert.matchesFound}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-400 mb-1">Last Triggered</p>
                  <p className="text-sm text-gray-300">
                    {alert.lastTriggered 
                      ? new Date(alert.lastTriggered).toLocaleDateString()
                      : 'Never'
                    }
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-400 mb-1">Notifications</p>
                  <div className="flex gap-2">
                    {alert.notificationChannels.map((channel) => (
                      <span key={channel} className="px-2 py-1 bg-white/10 rounded text-xs text-gray-300">
                        {channel}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-12 border border-white/20 text-center">
            <div className="text-6xl mb-4">🔔</div>
            <h3 className="text-2xl font-bold text-white mb-2">No alerts yet</h3>
            <p className="text-gray-300 mb-6">Create your first alert to get notified about new talent</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-6 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 text-white font-semibold rounded-lg hover:from-purple-700 hover:to-indigo-700 transition-all"
            >
              Create Alert
            </button>
          </div>
        )}
      </div>

      {/* Create Alert Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-gradient-to-br from-purple-900 to-indigo-900 rounded-2xl p-8 max-w-2xl w-full border border-white/20 max-h-[90vh] overflow-y-auto">
            <h3 className="text-2xl font-bold text-white mb-6">Create New Alert</h3>
            
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-200 mb-2">Alert Name *</label>
                <input
                  type="text"
                  value={newAlert.name}
                  onChange={(e) => setNewAlert({ ...newAlert, name: e.target.value })}
                  placeholder="e.g., Korean Valorant Prospects"
                  className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-200 mb-2">Markets *</label>
                <div className="grid grid-cols-2 gap-3">
                  {marketOptions.map((market) => (
                    <label key={market.code} className="flex items-center gap-2 p-3 bg-white/10 rounded-lg cursor-pointer hover:bg-white/15">
                      <input
                        type="checkbox"
                        checked={newAlert.markets?.includes(market.code)}
                        onChange={(e) => {
                          const markets = e.target.checked
                            ? [...(newAlert.markets || []), market.code]
                            : (newAlert.markets || []).filter(m => m !== market.code)
                          setNewAlert({ ...newAlert, markets })
                        }}
                        className="w-4 h-4 rounded border-gray-600 text-purple-600 focus:ring-purple-500"
                      />
                      <span className="text-white">{market.flag} {market.name}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-200 mb-2">Games *</label>
                <div className="grid grid-cols-2 gap-3">
                  {gameOptions.map((game) => (
                    <label key={game} className="flex items-center gap-2 p-3 bg-white/10 rounded-lg cursor-pointer hover:bg-white/15">
                      <input
                        type="checkbox"
                        checked={newAlert.games?.includes(game)}
                        onChange={(e) => {
                          const games = e.target.checked
                            ? [...(newAlert.games || []), game]
                            : (newAlert.games || []).filter(g => g !== game)
                          setNewAlert({ ...newAlert, games })
                        }}
                        className="w-4 h-4 rounded border-gray-600 text-purple-600 focus:ring-purple-500"
                      />
                      <span className="text-white">{game}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-200 mb-2">Min Win Rate (%)</label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={newAlert.criteria?.minWinRate || ''}
                    onChange={(e) => setNewAlert({
                      ...newAlert,
                      criteria: { ...newAlert.criteria, minWinRate: parseFloat(e.target.value) }
                    })}
                    className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                    placeholder="55"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-200 mb-2">Min KDA</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    value={newAlert.criteria?.minKDA || ''}
                    onChange={(e) => setNewAlert({
                      ...newAlert,
                      criteria: { ...newAlert.criteria, minKDA: parseFloat(e.target.value) }
                    })}
                    className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                    placeholder="2.5"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-200 mb-2">Notification Channels *</label>
                <div className="flex gap-4">
                  {(['email', 'sms', 'webhook'] as const).map((channel) => (
                    <label key={channel} className="flex items-center gap-2 p-3 bg-white/10 rounded-lg cursor-pointer hover:bg-white/15">
                      <input
                        type="checkbox"
                        checked={newAlert.notificationChannels?.includes(channel)}
                        onChange={(e) => {
                          const channels = e.target.checked
                            ? [...(newAlert.notificationChannels || []), channel]
                            : (newAlert.notificationChannels || []).filter(c => c !== channel)
                          setNewAlert({ ...newAlert, notificationChannels: channels })
                        }}
                        className="w-4 h-4 rounded border-gray-600 text-purple-600 focus:ring-purple-500"
                      />
                      <span className="text-white capitalize">{channel}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex gap-4 mt-8">
              <button
                onClick={() => {
                  setShowCreateModal(false)
                  resetNewAlert()
                }}
                className="flex-1 px-6 py-3 bg-white/10 hover:bg-white/20 text-white font-semibold rounded-lg transition-all"
              >
                Cancel
              </button>
              <button
                onClick={createAlert}
                disabled={!newAlert.name || !newAlert.markets?.length || !newAlert.games?.length}
                className="flex-1 px-6 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 text-white font-semibold rounded-lg hover:from-purple-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                Create Alert
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
