'use client'

import { useTranslations } from 'next-intl'
import { useCountryDetection } from '@/hooks/useCountryDetection'
import DenseStatsTable from './DenseStatsTable'
import PlayerCards from './PlayerCards'
import { Trophy, Users, TrendingUp, Globe } from 'lucide-react'
import { useEffect, useState } from 'react'
import { createClient } from '@supabase/supabase-js'

// Initialize Supabase client (replace with your actual credentials)
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL || '',
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''
)

export interface Player {
  id: string
  nickname: string
  game: string
  country: string
  rank: string
  stats: {
    win_rate?: number
    kda?: number
    games_played?: number
    champion_pool?: number
  }
  top_champions: Array<{
    name: string
    mastery_points?: number
    games_played?: number
    win_rate?: number
  }>
  talent_score?: number
  profile_photo_url?: string
  contact_whatsapp?: string
  created_at: string
  updated_at: string
}

export default function RadarDashboard() {
  const t = useTranslations('dashboard')
  const { countryCode, uiMode, isLoading: countryLoading } = useCountryDetection()
  const [players, setPlayers] = useState<Player[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [stats, setStats] = useState({
    totalPlayers: 0,
    topRegions: 0,
    avgTalentScore: 0
  })

  useEffect(() => {
    fetchPlayers()
  }, [])

  async function fetchPlayers() {
    try {
      setIsLoading(true)
      
      // Fetch from Silver or Gold layer
      const { data, error } = await supabase
        .from('gold_verified_players')
        .select('*')
        .order('talent_score', { ascending: false })
        .limit(100)

      if (error) throw error

      setPlayers(data as Player[])
      
      // Calculate stats
      setStats({
        totalPlayers: data.length,
        topRegions: new Set(data.map(p => p.country)).size,
        avgTalentScore: data.reduce((sum, p) => sum + (p.talent_score || 0), 0) / data.length
      })

      setIsLoading(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load players')
      setIsLoading(false)
    }
  }

  if (countryLoading || isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-pulse-slow">
          <Trophy className="w-16 h-16 text-dark-accent-primary" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="glass p-8 rounded-lg text-center max-w-md">
          <div className="text-red-500 mb-4">⚠️</div>
          <h2 className="text-xl font-bold mb-2">{t('error.title')}</h2>
          <p className="text-dark-text-secondary">{error}</p>
          <button 
            onClick={fetchPlayers}
            className="mt-4 px-6 py-2 bg-dark-accent-primary rounded-lg hover:bg-dark-accent-primary/80 transition-colors"
          >
            {t('error.retry')}
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-[1920px] mx-auto space-y-6 animate-fade-in">
      {/* Header */}
      <header className="glass rounded-2xl p-6">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-3xl font-bold gradient-text mb-2">
              {t('title')}
            </h1>
            <p className="text-dark-text-secondary flex items-center gap-2">
              <Globe className="w-4 h-4" />
              {t('subtitle')} • {countryCode}
            </p>
          </div>
          
          {/* Stats Cards */}
          <div className="flex gap-4">
            <div className="glass px-4 py-2 rounded-lg">
              <div className="flex items-center gap-2 text-dark-text-secondary text-sm mb-1">
                <Users className="w-4 h-4" />
                {t('stats.totalPlayers')}
              </div>
              <div className="text-2xl font-bold">{stats.totalPlayers}</div>
            </div>
            
            <div className="glass px-4 py-2 rounded-lg">
              <div className="flex items-center gap-2 text-dark-text-secondary text-sm mb-1">
                <Globe className="w-4 h-4" />
                {t('stats.regions')}
              </div>
              <div className="text-2xl font-bold">{stats.topRegions}</div>
            </div>
            
            <div className="glass px-4 py-2 rounded-lg">
              <div className="flex items-center gap-2 text-dark-text-secondary text-sm mb-1">
                <TrendingUp className="w-4 h-4" />
                {t('stats.avgTalent')}
              </div>
              <div className="text-2xl font-bold">{stats.avgTalentScore.toFixed(1)}</div>
            </div>
          </div>
        </div>
      </header>

      {/* Dynamic UI based on region */}
      {uiMode === 'DENSE_TABLE' ? (
        <DenseStatsTable players={players} />
      ) : (
        <PlayerCards players={players} />
      )}
    </div>
  )
}
