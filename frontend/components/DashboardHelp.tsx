'use client'

import { useState } from 'react'
import { Info, X, Trophy, TrendingUp, Target, BarChart, Eye } from 'lucide-react'
import { useTranslations } from 'next-intl'

interface DashboardHelpProps {
  locale?: string
}

export default function DashboardHelp({ locale = 'en' }: DashboardHelpProps) {
  const [isOpen, setIsOpen] = useState(false)
  const t = useTranslations('dashboard.help')

  return (
    <>
      {/* Help Button */}
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 z-40 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white rounded-full p-4 shadow-2xl transition-all hover:scale-110 group"
        aria-label="Help"
      >
        <Info className="w-6 h-6 group-hover:rotate-12 transition-transform" />
        <span className="absolute -top-10 right-0 bg-gray-900 text-white text-xs px-3 py-1 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
          {locale === 'es' ? '¿Necesitas ayuda?' : locale === 'zh' ? '需要帮助?' : locale === 'ko' ? '도움이 필요하세요?' : locale === 'ja' ? 'ヘルプが必要ですか？' : 'Need help?'}
        </span>
      </button>

      {/* Help Modal */}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center animate-fadeIn">
          {/* Backdrop */}
          <div
            onClick={() => setIsOpen(false)}
            className="absolute inset-0 bg-black/70 backdrop-blur-sm"
          />

          {/* Modal Content */}
          <div className="relative bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden border border-gray-700">
            {/* Header */}
            <div className="bg-gradient-to-r from-purple-600 to-blue-600 p-6 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Info className="w-8 h-8 text-white" />
                <h2 className="text-2xl font-bold text-white">{t('title')}</h2>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="text-white/80 hover:text-white transition-colors hover:rotate-90 transition-transform duration-300"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            {/* Scrollable Content */}
            <div className="p-6 overflow-y-auto max-h-[calc(90vh-100px)] custom-scrollbar">
              {/* Introduction */}
              <div className="bg-gradient-to-r from-purple-500/10 to-blue-500/10 border border-purple-500/20 rounded-xl p-6 mb-6">
                <p className="text-gray-300 text-lg">{t('description')}</p>
              </div>

              {/* What is this Dashboard */}
              <div className="mb-8">
                <div className="flex items-center gap-3 mb-4">
                  <Trophy className="w-6 h-6 text-yellow-400" />
                  <h3 className="text-xl font-bold text-white">{t('whatIs')}</h3>
                </div>
                <p className="text-gray-300 leading-relaxed">{t('whatIsDesc')}</p>
              </div>

              {/* Understanding Metrics */}
              <div className="mb-8">
                <div className="flex items-center gap-3 mb-4">
                  <BarChart className="w-6 h-6 text-blue-400" />
                  <h3 className="text-xl font-bold text-white">{t('metrics')}</h3>
                </div>
                <p className="text-gray-400 mb-4">{t('metricsDesc')}</p>

                {/* Metrics Grid */}
                <div className="grid gap-4 md:grid-cols-2">
                  {/* Talent Score */}
                  <div className="bg-gradient-to-br from-purple-900/30 to-purple-800/20 border border-purple-500/30 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Target className="w-5 h-5 text-purple-400" />
                      <h4 className="font-bold text-white">{t('talentScore')}</h4>
                    </div>
                    <p className="text-sm text-gray-300">{t('talentScoreDesc')}</p>
                  </div>

                  {/* Win Rate */}
                  <div className="bg-gradient-to-br from-green-900/30 to-green-800/20 border border-green-500/30 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <TrendingUp className="w-5 h-5 text-green-400" />
                      <h4 className="font-bold text-white">{t('winRate')}</h4>
                    </div>
                    <p className="text-sm text-gray-300">{t('winRateDesc')}</p>
                  </div>

                  {/* KDA */}
                  <div className="bg-gradient-to-br from-blue-900/30 to-blue-800/20 border border-blue-500/30 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Target className="w-5 h-5 text-blue-400" />
                      <h4 className="font-bold text-white">{t('kda')}</h4>
                    </div>
                    <p className="text-sm text-gray-300">{t('kdaDesc')}</p>
                  </div>

                  {/* Games Played */}
                  <div className="bg-gradient-to-br from-orange-900/30 to-orange-800/20 border border-orange-500/30 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <BarChart className="w-5 h-5 text-orange-400" />
                      <h4 className="font-bold text-white">{t('gamesPlayed')}</h4>
                    </div>
                    <p className="text-sm text-gray-300">{t('gamesPlayedDesc')}</p>
                  </div>

                  {/* Rank/Tier */}
                  <div className="bg-gradient-to-br from-yellow-900/30 to-yellow-800/20 border border-yellow-500/30 rounded-lg p-4 md:col-span-2">
                    <div className="flex items-center gap-2 mb-2">
                      <Trophy className="w-5 h-5 text-yellow-400" />
                      <h4 className="font-bold text-white">{t('rank')}</h4>
                    </div>
                    <p className="text-sm text-gray-300">{t('rankDesc')}</p>
                  </div>
                </div>
              </div>

              {/* View Modes */}
              <div>
                <div className="flex items-center gap-3 mb-4">
                  <Eye className="w-6 h-6 text-cyan-400" />
                  <h3 className="text-xl font-bold text-white">{t('viewModes')}</h3>
                </div>
                <p className="text-gray-400 mb-4">{t('viewModesDesc')}</p>

                <div className="space-y-3">
                  {['autoMode', 'feedMode', 'denseMode', 'minimalMode'].map((mode) => (
                    <div
                      key={mode}
                      className="bg-gray-800/50 border border-gray-700 rounded-lg p-4 hover:border-cyan-500/50 transition-colors"
                    >
                      <h4 className="font-bold text-white mb-2">{t(mode)}</h4>
                      <p className="text-sm text-gray-300">{t(`${mode}Desc`)}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="bg-gray-900/80 border-t border-gray-700 p-4 text-center">
              <p className="text-sm text-gray-400">
                {locale === 'es'
                  ? '¿Tienes más preguntas? Contáctanos en support@gameradar.ai'
                  : locale === 'zh'
                  ? '还有问题？联系我们：support@gameradar.ai'
                  : locale === 'ko'
                  ? '더 궁금한 점이 있으신가요? 문의: support@gameradar.ai'
                  : locale === 'ja'
                  ? 'ご質問がありますか？ support@gameradar.ai までお問い合わせください'
                  : 'Have more questions? Contact us at support@gameradar.ai'}
              </p>
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
          }
          to {
            opacity: 1;
          }
        }

        .animate-fadeIn {
          animation: fadeIn 0.2s ease-out;
        }

        .custom-scrollbar::-webkit-scrollbar {
          width: 8px;
        }

        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgba(31, 41, 55, 0.3);
          border-radius: 4px;
        }

        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(139, 92, 246, 0.5);
          border-radius: 4px;
        }

        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(139, 92, 246, 0.7);
        }
      `}</style>
    </>
  )
}
