'use client'

import { useTranslations } from 'next-intl'
import { Player } from './RadarDashboard'
import { ArrowUp, ArrowDown, TrendingUp } from 'lucide-react'
import { useState } from 'react'

interface DenseStatsTableProps {
  players: Player[]
}

type SortField = 'nickname' | 'rank' | 'win_rate' | 'kda' | 'talent_score' | 'games_played'
type SortDirection = 'asc' | 'desc'

export default function DenseStatsTable({ players }: DenseStatsTableProps) {
  const t = useTranslations('table')
  const [sortField, setSortField] = useState<SortField>('talent_score')
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc')

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('desc')
    }
  }

  const sortedPlayers = [...players].sort((a, b) => {
    let aValue: any
    let bValue: any

    switch (sortField) {
      case 'nickname':
        aValue = a.nickname
        bValue = b.nickname
        break
      case 'rank':
        aValue = a.rank
        bValue = b.rank
        break
      case 'win_rate':
        aValue = a.stats.win_rate || 0
        bValue = b.stats.win_rate || 0
        break
      case 'kda':
        aValue = a.stats.kda || 0
        bValue = b.stats.kda || 0
        break
      case 'talent_score':
        aValue = a.talent_score || 0
        bValue = b.talent_score || 0
        break
      case 'games_played':
        aValue = a.stats.games_played || 0
        bValue = b.stats.games_played || 0
        break
      default:
        return 0
    }

    if (typeof aValue === 'string') {
      return sortDirection === 'asc' 
        ? aValue.localeCompare(bValue)
        : bValue.localeCompare(aValue)
    }

    return sortDirection === 'asc' ? aValue - bValue : bValue - aValue
  })

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) return <TrendingUp className="w-3 h-3 opacity-30" />
    return sortDirection === 'asc' 
      ? <ArrowUp className="w-3 h-3 text-dark-accent-primary" />
      : <ArrowDown className="w-3 h-3 text-dark-accent-primary" />
  }

  const getChampionEmoji = (championName: string) => {
    // Simple mapping - extend as needed
    const emojiMap: Record<string, string> = {
      'default': '🎮'
    }
    return emojiMap[championName.toLowerCase()] || emojiMap.default
  }

  return (
    <div className="glass rounded-2xl p-4 overflow-hidden">
      <div className="overflow-x-auto scrollbar-thin">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-dark-border-primary">
              <th className="px-2 py-3 text-left font-medium text-dark-text-secondary">
                #
              </th>
              <th 
                className="px-2 py-3 text-left font-medium text-dark-text-secondary cursor-pointer hover:text-dark-text-primary"
                onClick={() => handleSort('nickname')}
              >
                <div className="flex items-center gap-1">
                  {t('nickname')}
                  <SortIcon field="nickname" />
                </div>
              </th>
              <th className="px-2 py-3 text-left font-medium text-dark-text-secondary">
                {t('country')}
              </th>
              <th className="px-2 py-3 text-left font-medium text-dark-text-secondary">
                {t('game')}
              </th>
              <th 
                className="px-2 py-3 text-left font-medium text-dark-text-secondary cursor-pointer hover:text-dark-text-primary"
                onClick={() => handleSort('rank')}
              >
                <div className="flex items-center gap-1">
                  {t('rank')}
                  <SortIcon field="rank" />
                </div>
              </th>
              <th 
                className="px-2 py-3 text-right font-medium text-dark-text-secondary cursor-pointer hover:text-dark-text-primary"
                onClick={() => handleSort('win_rate')}
              >
                <div className="flex items-center justify-end gap-1">
                  {t('winRate')}
                  <SortIcon field="win_rate" />
                </div>
              </th>
              <th 
                className="px-2 py-3 text-right font-medium text-dark-text-secondary cursor-pointer hover:text-dark-text-primary"
                onClick={() => handleSort('kda')}
              >
                <div className="flex items-center justify-end gap-1">
                  {t('kda')}
                  <SortIcon field="kda" />
                </div>
              </th>
              <th 
                className="px-2 py-3 text-right font-medium text-dark-text-secondary cursor-pointer hover:text-dark-text-primary"
                onClick={() => handleSort('games_played')}
              >
                <div className="flex items-center justify-end gap-1">
                  {t('gamesPlayed')}
                  <SortIcon field="games_played" />
                </div>
              </th>
              <th className="px-2 py-3 text-left font-medium text-dark-text-secondary">
                {t('championPool')}
              </th>
              <th className="px-2 py-3 text-left font-medium text-dark-text-secondary">
                {t('topChampion1')}
              </th>
              <th className="px-2 py-3 text-left font-medium text-dark-text-secondary">
                {t('topChampion2')}
              </th>
              <th className="px-2 py-3 text-left font-medium text-dark-text-secondary">
                {t('topChampion3')}
              </th>
              <th className="px-2 py-3 text-right font-medium text-dark-text-secondary">
                {t('c1WinRate')}
              </th>
              <th className="px-2 py-3 text-right font-medium text-dark-text-secondary">
                {t('c2WinRate')}
              </th>
              <th 
                className="px-2 py-3 text-right font-medium text-dark-text-secondary cursor-pointer hover:text-dark-text-primary"
                onClick={() => handleSort('talent_score')}
              >
                <div className="flex items-center justify-end gap-1">
                  {t('talentScore')}
                  <SortIcon field="talent_score" />
                </div>
              </th>
            </tr>
          </thead>
          <tbody>
            {sortedPlayers.map((player, index) => (
              <tr 
                key={player.id}
                className="border-b border-dark-border-primary hover:bg-dark-bg-hover transition-colors animate-slide-up"
                style={{ animationDelay: `${index * 20}ms` }}
              >
                <td className="px-2 py-3 text-dark-text-tertiary">
                  {index + 1}
                </td>
                <td className="px-2 py-3 font-medium">
                  {player.nickname}
                </td>
                <td className="px-2 py-3">
                  <span className="text-lg">{getCountryFlag(player.country)}</span>
                </td>
                <td className="px-2 py-3 text-dark-text-secondary">
                  {player.game}
                </td>
                <td className="px-2 py-3">
                  <span className={getRankColor(player.rank)}>
                    {player.rank}
                  </span>
                </td>
                <td className="px-2 py-3 text-right font-mono">
                  {player.stats.win_rate?.toFixed(1)}%
                </td>
                <td className="px-2 py-3 text-right font-mono">
                  {player.stats.kda?.toFixed(2)}
                </td>
                <td className="px-2 py-3 text-right text-dark-text-secondary">
                  {player.stats.games_played || '-'}
                </td>
                <td className="px-2 py-3 text-dark-text-secondary">
                  {player.stats.champion_pool || '-'}
                </td>
                <td className="px-2 py-3">
                  <div className="flex items-center gap-1">
                    <span>{getChampionEmoji(player.top_champions[0]?.name || '')}</span>
                    <span className="text-dark-text-secondary text-xs">
                      {player.top_champions[0]?.name || '-'}
                    </span>
                  </div>
                </td>
                <td className="px-2 py-3">
                  <div className="flex items-center gap-1">
                    <span>{getChampionEmoji(player.top_champions[1]?.name || '')}</span>
                    <span className="text-dark-text-secondary text-xs">
                      {player.top_champions[1]?.name || '-'}
                    </span>
                  </div>
                </td>
                <td className="px-2 py-3">
                  <div className="flex items-center gap-1">
                    <span>{getChampionEmoji(player.top_champions[2]?.name || '')}</span>
                    <span className="text-dark-text-secondary text-xs">
                      {player.top_champions[2]?.name || '-'}
                    </span>
                  </div>
                </td>
                <td className="px-2 py-3 text-right font-mono text-xs text-dark-text-secondary">
                  {player.top_champions[0]?.win_rate?.toFixed(0)}%
                </td>
                <td className="px-2 py-3 text-right font-mono text-xs text-dark-text-secondary">
                  {player.top_champions[1]?.win_rate?.toFixed(0)}%
                </td>
                <td className="px-2 py-3 text-right">
                  <span className={getTalentScoreColor(player.talent_score || 0)}>
                    {player.talent_score?.toFixed(0) || '-'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function getCountryFlag(countryCode: string): string {
  const flags: Record<string, string> = {
    'KR': '🇰🇷',
    'CN': '🇨🇳',
    'IN': '🇮🇳',
    'VN': '🇻🇳',
    'TH': '🇹🇭',
    'JP': '🇯🇵',
    'US': '🇺🇸',
  }
  return flags[countryCode] || '🌍'
}

function getRankColor(rank: string): string {
  const rankLower = rank.toLowerCase()
  if (rankLower.includes('challenger') || rankLower.includes('grandmaster')) {
    return 'text-yellow-400 font-bold'
  }
  if (rankLower.includes('master') || rankLower.includes('diamond')) {
    return 'text-blue-400 font-semibold'
  }
  if (rankLower.includes('platinum') || rankLower.includes('gold')) {
    return 'text-purple-400'
  }
  return 'text-dark-text-secondary'
}

function getTalentScoreColor(score: number): string {
  if (score >= 90) return 'text-yellow-400 font-bold'
  if (score >= 75) return 'text-green-400 font-semibold'
  if (score >= 60) return 'text-blue-400'
  return 'text-dark-text-secondary'
}
