'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useRegion } from '@/hooks/useRegion';
import { useTranslations } from 'next-intl';
import { Trophy, Star, TrendingUp, Users, Flame } from 'lucide-react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
  createColumnHelper,
  SortingState,
} from '@tanstack/react-table';

// ============================================================================
// TYPES
// ============================================================================

interface Player {
  player_id: string;
  nickname: string;
  country: string;
  game: string;
  rank: string;
  game_radar_score: number;
  talent_score: number;
  win_rate: number;
  kda: number;
  games_played: number;
  avatar_url?: string;
  is_verified: boolean;
  match_score?: number; // For recommendation similarity
}

interface MarketplaceViewProps {
  players: Player[];
  title?: string;
  subtitle?: string;
  isRecommendation?: boolean;
}

// ============================================================================
// MOBILE-HEAVY CARD COMPONENT (India/Vietnam)
// ============================================================================

function MobileHeavyCard({ player }: { player: Player }) {
  const t = useTranslations('marketplace');

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3 }}
      className="relative bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl p-6 
                 border-2 border-emerald-500/30 shadow-lg shadow-emerald-500/20
                 hover:shadow-emerald-500/40 hover:border-emerald-500/60 transition-all duration-300"
    >
      {/* Neon Glow Effect */}
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-emerald-500/10 to-teal-500/10 
                      blur-xl opacity-0 hover:opacity-100 transition-opacity duration-300" />

      {/* Content */}
      <div className="relative z-10">
        {/* Header with Avatar */}
        <div className="flex items-start gap-4 mb-4">
          <div className="relative">
            {player.avatar_url ? (
              <img
                src={player.avatar_url}
                alt={player.nickname}
                className="w-20 h-20 rounded-xl object-cover border-2 border-emerald-500/50"
              />
            ) : (
              <div className="w-20 h-20 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-500 
                              flex items-center justify-center text-white text-2xl font-bold">
                {player.nickname[0]}
              </div>
            )}
            {player.is_verified && (
              <div className="absolute -top-2 -right-2 bg-yellow-500 rounded-full p-1">
                <Star className="w-4 h-4 text-white" fill="white" />
              </div>
            )}
          </div>

          <div className="flex-1">
            <h3 className="text-2xl font-black text-white mb-1 font-sans tracking-tight">
              {player.nickname}
            </h3>
            <div className="flex items-center gap-2 text-sm text-gray-400">
              <span className="font-semibold">{player.country}</span>
              <span>•</span>
              <span>{player.game}</span>
            </div>
          </div>

          {player.match_score && (
            <div className="flex items-center gap-1 bg-gradient-to-r from-emerald-500 to-teal-500 
                            px-3 py-1 rounded-full">
              <Flame className="w-4 h-4 text-white" />
              <span className="text-white font-bold text-sm">
                {player.match_score}% Match
              </span>
            </div>
          )}
        </div>

        {/* GameRadar Score - ULTRA PROMINENT */}
        <div className="mb-6 p-4 bg-gradient-to-r from-emerald-600 to-teal-600 rounded-xl 
                        shadow-lg shadow-emerald-500/50">
          <div className="text-center">
            <div className="text-sm font-semibold text-emerald-100 mb-1">
              GameRadar Score
            </div>
            <div className="text-5xl font-black text-white drop-shadow-lg">
              {player.game_radar_score.toFixed(1)}
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          <StatCard
            label={t('talentScore')}
            value={player.talent_score.toFixed(1)}
            color="yellow"
          />
          <StatCard
            label={t('winRate')}
            value={`${player.win_rate.toFixed(1)}%`}
            color="green"
          />
          <StatCard
            label="KDA"
            value={player.kda.toFixed(2)}
            color="purple"
          />
          <StatCard
            label={t('rank')}
            value={player.rank}
            color="blue"
          />
        </div>

        {/* Games Played */}
        <div className="text-center text-sm text-gray-400 mb-4">
          <Users className="w-4 h-4 inline mr-1" />
          {player.games_played} {t('gamesPlayed')}
        </div>

        {/* CTA Button */}
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="w-full bg-gradient-to-r from-emerald-500 to-teal-500 text-white 
                     font-bold py-4 rounded-xl shadow-lg shadow-emerald-500/30
                     hover:shadow-emerald-500/50 transition-all duration-300"
        >
          {t('viewProfile')}
        </motion.button>
      </div>
    </motion.div>
  );
}

function StatCard({ label, value, color }: { label: string; value: string; color: string }) {
  const colorMap = {
    yellow: 'from-yellow-500 to-orange-500',
    green: 'from-green-500 to-emerald-500',
    purple: 'from-purple-500 to-pink-500',
    blue: 'from-blue-500 to-cyan-500',
  };

  return (
    <div className={`bg-gradient-to-br ${colorMap[color as keyof typeof colorMap]} p-3 rounded-lg`}>
      <div className="text-xs font-semibold text-white/80 mb-1">{label}</div>
      <div className="text-xl font-black text-white">{value}</div>
    </div>
  );
}

// ============================================================================
// ANALYTICAL TABLE COMPONENT (Korea/China/Japan)
// ============================================================================

function AnalyticalTable({ players }: { players: Player[] }) {
  const t = useTranslations('marketplace');
  const [sorting, setSorting] = useState<SortingState>([
    { id: 'game_radar_score', desc: true }
  ]);

  const columnHelper = createColumnHelper<Player>();

  const columns = [
    columnHelper.accessor('nickname', {
      header: t('player'),
      cell: (info) => (
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded bg-gradient-to-br from-emerald-500 to-teal-500 
                          flex items-center justify-center text-white text-xs font-bold">
            {info.getValue()[0]}
          </div>
          <div>
            <div className="font-semibold text-white">{info.getValue()}</div>
            {info.row.original.is_verified && (
              <Star className="w-3 h-3 text-yellow-500 inline" fill="currentColor" />
            )}
          </div>
        </div>
      ),
    }),
    columnHelper.accessor('country', {
      header: t('country'),
      cell: (info) => (
        <span className="text-gray-300 text-sm">{info.getValue()}</span>
      ),
    }),
    columnHelper.accessor('game_radar_score', {
      header: 'GameRadar',
      cell: (info) => (
        <div className="font-bold text-emerald-400 text-center">
          {info.getValue().toFixed(1)}
        </div>
      ),
    }),
    columnHelper.accessor('talent_score', {
      header: t('talent'),
      cell: (info) => (
        <div className="text-yellow-400 text-center">
          {info.getValue().toFixed(1)}
        </div>
      ),
    }),
    columnHelper.accessor('win_rate', {
      header: t('winRate'),
      cell: (info) => (
        <div className="text-green-400 text-center">
          {info.getValue().toFixed(1)}%
        </div>
      ),
    }),
    columnHelper.accessor('kda', {
      header: 'KDA',
      cell: (info) => (
        <div className="text-purple-400 text-center">
          {info.getValue().toFixed(2)}
        </div>
      ),
    }),
    columnHelper.accessor('rank', {
      header: t('rank'),
      cell: (info) => (
        <div className="text-blue-400 text-sm text-center">
          {info.getValue()}
        </div>
      ),
    }),
    columnHelper.accessor('games_played', {
      header: t('games'),
      cell: (info) => (
        <div className="text-gray-400 text-sm text-center">
          {info.getValue().toLocaleString()}
        </div>
      ),
    }),
  ];

  // Add match_score column if it exists
  if (players.some(p => p.match_score)) {
    columns.push(
      columnHelper.accessor('match_score', {
        header: 'Match',
        cell: (info) => (
          <div className="flex items-center justify-center gap-1 text-emerald-400 font-bold">
            <TrendingUp className="w-4 h-4" />
            {info.getValue()?.toFixed(0)}%
          </div>
        ),
      })
    );
  }

  const table = useReactTable({
    data: players,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="overflow-x-auto"
    >
      <table className="w-full border-collapse">
        <thead>
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id} className="border-b border-slate-700">
              {headerGroup.headers.map((header) => (
                <th
                  key={header.id}
                  className="px-4 py-3 text-left text-xs font-serif font-semibold 
                             text-gray-400 uppercase tracking-wider cursor-pointer
                             hover:text-emerald-400 transition-colors"
                  onClick={header.column.getToggleSortingHandler()}
                >
                  <div className="flex items-center gap-2">
                    {flexRender(
                      header.column.columnDef.header,
                      header.getContext()
                    )}
                    {{
                      asc: ' ↑',
                      desc: ' ↓',
                    }[header.column.getIsSorted() as string] ?? null}
                  </div>
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row, index) => (
            <motion.tr
              key={row.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              className="border-b border-slate-800 hover:bg-slate-800/50 transition-colors"
            >
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id} className="px-4 py-4 text-sm">
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </motion.tr>
          ))}
        </tbody>
      </table>
    </motion.div>
  );
}

// ============================================================================
// MAIN MARKETPLACE VIEW COMPONENT
// ============================================================================

export function MarketplaceView({
  players,
  title,
  subtitle,
  isRecommendation = false,
}: MarketplaceViewProps) {
  const region = useRegion();
  const t = useTranslations('marketplace');
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-white">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-950 to-slate-900 p-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-7xl mx-auto mb-8"
      >
        <div className="flex items-center gap-3 mb-2">
          <Trophy className="w-8 h-8 text-emerald-400" />
          <h1 className={`text-4xl font-black text-white ${
            region.typography === 'serif' ? 'font-serif' : 'font-sans'
          }`}>
            {title || t('title')}
          </h1>
        </div>
        <p className="text-gray-400 text-lg">
          {subtitle || t('subtitle')}
        </p>
        
        {/* Region Indicator */}
        <div className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-slate-800/50 
                        rounded-full border border-slate-700">
          <div className={`w-2 h-2 rounded-full ${
            region.type === 'mobile-heavy' ? 'bg-emerald-500' : 'bg-blue-500'
          }`} />
          <span className="text-sm text-gray-400">
            {region.type === 'mobile-heavy' ? 'Mobile-Heavy View' : 'Analytical View'}
            {' • '}
            {region.countryCode}
          </span>
        </div>
      </motion.div>

      {/* Content */}
      <div className="max-w-7xl mx-auto">
        <AnimatePresence mode="wait">
          {region.type === 'mobile-heavy' ? (
            <motion.div
              key="mobile-heavy"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className={`grid ${region.gridCols} gap-6`}
            >
              {players.map((player) => (
                <MobileHeavyCard key={player.player_id} player={player} />
              ))}
            </motion.div>
          ) : (
            <motion.div
              key="analytical"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="bg-slate-900/50 rounded-xl border border-slate-800 overflow-hidden"
            >
              <AnalyticalTable players={players} />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
