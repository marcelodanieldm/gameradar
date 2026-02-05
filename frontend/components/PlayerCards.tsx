'use client'

import { useTranslations } from 'next-intl'
import { Player } from './RadarDashboard'
import { Trophy, Target, TrendingUp, Users, MessageCircle, ExternalLink } from 'lucide-react'
import Image from 'next/image'

interface PlayerCardsProps {
  players: Player[]
}

export default function PlayerCards({ players }: PlayerCardsProps) {
  const t = useTranslations('cards')

  const handleWhatsAppClick = (player: Player) => {
    const message = encodeURIComponent(
      `Hi ${player.nickname}! I'm interested in your e-sports talent. Let's connect!`
    )
    const whatsappNumber = player.contact_whatsapp || ''
    const whatsappUrl = `https://wa.me/${whatsappNumber}?text=${message}`
    window.open(whatsappUrl, '_blank')
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {players.map((player, index) => (
        <div 
          key={player.id}
          className="glass rounded-2xl p-6 hover:scale-105 transition-transform duration-300 animate-slide-up"
          style={{ animationDelay: `${index * 50}ms` }}
        >
          {/* Profile Header */}
          <div className="flex items-start gap-4 mb-4">
            <div className="relative">
              {player.profile_photo_url ? (
                <Image
                  src={player.profile_photo_url}
                  alt={player.nickname}
                  width={80}
                  height={80}
                  className="rounded-full border-2 border-dark-accent-primary"
                />
              ) : (
                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-dark-accent-primary to-dark-accent-secondary flex items-center justify-center text-2xl font-bold">
                  {player.nickname.charAt(0).toUpperCase()}
                </div>
              )}
              
              {/* Country Flag Badge */}
              <div className="absolute -bottom-1 -right-1 text-2xl">
                {getCountryFlag(player.country)}
              </div>
            </div>

            <div className="flex-1">
              <h3 className="text-xl font-bold mb-1">{player.nickname}</h3>
              <div className="flex items-center gap-2 text-sm text-dark-text-secondary mb-1">
                <span>{player.game}</span>
                <span>•</span>
                <span className={getRankColor(player.rank)}>
                  {player.rank}
                </span>
              </div>
              
              {/* Talent Score Badge */}
              {player.talent_score && (
                <div className="inline-flex items-center gap-1 px-2 py-1 bg-dark-accent-primary/20 rounded-full text-xs font-semibold">
                  <Trophy className="w-3 h-3" />
                  {t('talentScore')}: {player.talent_score.toFixed(0)}
                </div>
              )}
            </div>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 gap-3 mb-4">
            <div className="bg-dark-bg-secondary rounded-lg p-3">
              <div className="flex items-center gap-2 text-dark-text-tertiary text-xs mb-1">
                <Target className="w-3 h-3" />
                {t('winRate')}
              </div>
              <div className="text-2xl font-bold">
                {player.stats.win_rate?.toFixed(1)}%
              </div>
            </div>

            <div className="bg-dark-bg-secondary rounded-lg p-3">
              <div className="flex items-center gap-2 text-dark-text-tertiary text-xs mb-1">
                <TrendingUp className="w-3 h-3" />
                {t('kda')}
              </div>
              <div className="text-2xl font-bold">
                {player.stats.kda?.toFixed(2)}
              </div>
            </div>

            <div className="bg-dark-bg-secondary rounded-lg p-3">
              <div className="flex items-center gap-2 text-dark-text-tertiary text-xs mb-1">
                <Users className="w-3 h-3" />
                {t('gamesPlayed')}
              </div>
              <div className="text-xl font-semibold">
                {player.stats.games_played || 0}
              </div>
            </div>

            <div className="bg-dark-bg-secondary rounded-lg p-3">
              <div className="flex items-center gap-2 text-dark-text-tertiary text-xs mb-1">
                <Trophy className="w-3 h-3" />
                {t('champions')}
              </div>
              <div className="text-xl font-semibold">
                {player.stats.champion_pool || 0}
              </div>
            </div>
          </div>

          {/* Top Champions */}
          <div className="mb-4">
            <div className="text-xs text-dark-text-tertiary mb-2 font-medium">
              {t('topChampions')}
            </div>
            <div className="flex gap-2">
              {player.top_champions.slice(0, 3).map((champion, i) => (
                <div 
                  key={i}
                  className="flex-1 bg-dark-bg-secondary rounded-lg p-2 text-center"
                >
                  <div className="text-lg mb-1">
                    {getChampionEmoji(champion.name)}
                  </div>
                  <div className="text-xs text-dark-text-secondary truncate">
                    {champion.name}
                  </div>
                  {champion.win_rate && (
                    <div className="text-xs text-dark-accent-success font-semibold">
                      {champion.win_rate.toFixed(0)}%
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-2">
            {player.contact_whatsapp && (
              <button
                onClick={() => handleWhatsAppClick(player)}
                className="flex-1 flex items-center justify-center gap-2 bg-green-600 hover:bg-green-700 text-white px-4 py-3 rounded-lg font-semibold transition-colors"
              >
                <MessageCircle className="w-4 h-4" />
                {t('contactWhatsApp')}
              </button>
            )}
            
            <button
              className="flex items-center justify-center gap-2 bg-dark-bg-secondary hover:bg-dark-bg-hover px-4 py-3 rounded-lg font-semibold transition-colors"
              title={t('viewProfile')}
            >
              <ExternalLink className="w-4 h-4" />
            </button>
          </div>
        </div>
      ))}
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

function getChampionEmoji(championName: string): string {
  const emojiMap: Record<string, string> = {
    'default': '🎮',
    'yasuo': '⚔️',
    'zed': '🗡️',
    'lee sin': '👊',
    'ahri': '🦊',
    'thresh': '⛓️',
    'vayne': '🏹',
    'jinx': '💥',
    'lux': '✨',
    'katarina': '🔪',
  }
  return emojiMap[championName.toLowerCase()] || emojiMap.default
}
