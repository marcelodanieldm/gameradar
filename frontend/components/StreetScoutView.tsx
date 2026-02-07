"use client";

/**
 * Street Scout View - Módulo India/Vietnam
 * Enfoque: Viralidad y facilidad
 * 
 * Características:
 * - Scroll vertical infinito estilo TikTok/Reels
 * - Tarjetas con "flamas" para jugadores trending
 * - Botón WhatsApp integrado con mensaje pre-escrito
 * - Diseño mobile-first con colores vibrantes
 */

import { useState, useEffect, useRef, useCallback } from "react";
import { useTranslations, useLocale } from "next-intl";
import { motion, AnimatePresence } from "framer-motion";
import {
  TrendingUp,
  Flame,
  Share2,
  MessageCircle,
  ExternalLink,
  Zap,
  Trophy,
  Star,
  Target,
  Award,
  ArrowUp,
} from "lucide-react";

// Tipos
interface Player {
  id: string;
  player_id: string;
  nickname: string;
  country_code: string;
  region: string;
  game: string;
  rank: string;
  win_rate: number | null;
  kda: number | null;
  gameradar_score: number | null;
  avatar_url: string | null;
  profile_url: string | null;
  top_champions: string[] | null;
  talent_score: number | null;
  is_trending?: boolean; // Si el score sube rápido
  score_change?: number; // Cambio en últimas 24h
}

interface StreetScoutViewProps {
  players: Player[];
  onLoadMore?: () => void;
  hasMore?: boolean;
  isLoading?: boolean;
}

export default function StreetScoutView({
  players,
  onLoadMore,
  hasMore = false,
  isLoading = false,
}: StreetScoutViewProps) {
  const t = useTranslations("streetScout");
  const locale = useLocale();
  const observerRef = useRef<IntersectionObserver | null>(null);
  const lastCardRef = useRef<HTMLDivElement | null>(null);

  // Infinite scroll con Intersection Observer
  useEffect(() => {
    if (!hasMore || isLoading) return;

    observerRef.current = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && onLoadMore) {
          onLoadMore();
        }
      },
      { threshold: 0.5 }
    );

    if (lastCardRef.current) {
      observerRef.current.observe(lastCardRef.current);
    }

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, [hasMore, isLoading, onLoadMore]);

  const shareToWhatsApp = useCallback((player: Player) => {
    const message = generateShareMessage(player, locale);
    const url = `https://wa.me/?text=${encodeURIComponent(message)}`;
    window.open(url, "_blank");
  }, [locale]);

  const shareToZalo = useCallback((player: Player) => {
    const message = generateShareMessage(player, locale);
    // Zalo share URL (Vietnam)
    const url = `https://zalo.me/share?url=${encodeURIComponent(window.location.href)}&text=${encodeURIComponent(message)}`;
    window.open(url, "_blank");
  }, [locale]);

  return (
    <div className="w-full max-w-md mx-auto bg-slate-950 min-h-screen">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-gradient-to-b from-slate-900 to-slate-900/80 backdrop-blur-sm border-b border-slate-800 px-4 py-4">
        <div className="flex items-center gap-2">
          <Flame className="w-6 h-6 text-orange-500" />
          <h1 className={`text-xl font-bold text-white
            ${locale === "hi" ? "font-devanagari" : ""}`}>
            {t("title")}
          </h1>
        </div>
        <p className="text-sm text-slate-400 mt-1">
          {t("subtitle")}
        </p>
      </div>

      {/* Cards Scroll Vertical */}
      <div className="pb-20">
        <AnimatePresence>
          {players.map((player, index) => (
            <motion.div
              key={player.player_id}
              ref={index === players.length - 1 ? lastCardRef : null}
              initial={{ opacity: 0, y: 50 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -50 }}
              transition={{ duration: 0.4, delay: index * 0.05 }}
              className="relative"
            >
              <PlayerCard
                player={player}
                onShareWhatsApp={shareToWhatsApp}
                onShareZalo={shareToZalo}
                locale={locale}
                t={t}
              />
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Loading Indicator */}
        {isLoading && (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-12 w-12 border-4 border-cyan-500 border-t-transparent" />
          </div>
        )}

        {/* End Message */}
        {!hasMore && players.length > 0 && (
          <div className="text-center py-8 text-slate-500">
            <Trophy className="w-8 h-8 mx-auto mb-2" />
            <p>{t("endOfList")}</p>
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================
// PLAYER CARD - Estilo TikTok/Reels
// ============================================================
function PlayerCard({
  player,
  onShareWhatsApp,
  onShareZalo,
  locale,
  t,
}: {
  player: Player;
  onShareWhatsApp: (player: Player) => void;
  onShareZalo: (player: Player) => void;
  locale: string;
  t: any;
}) {
  const isTrending = player.is_trending || (player.score_change && player.score_change > 5);
  const isVietnam = player.country_code === "VN";

  return (
    <div className="relative bg-slate-900 border-b-8 border-slate-950 overflow-hidden">
      {/* Trending Badge */}
      {isTrending && (
        <motion.div
          animate={{
            scale: [1, 1.1, 1],
            rotate: [0, 5, -5, 0],
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: "easeInOut",
          }}
          className="absolute top-4 right-4 z-20
            bg-gradient-to-r from-orange-500 via-red-500 to-pink-500
            rounded-full px-3 py-1.5
            flex items-center gap-1
            shadow-lg shadow-orange-500/50"
        >
          <Flame className="w-4 h-4 text-white" />
          <span className="text-xs font-bold text-white">
            {t("trending")}
          </span>
        </motion.div>
      )}

      {/* Score Change Indicator */}
      {player.score_change && player.score_change > 0 && (
        <div className="absolute top-4 left-4 z-20
          bg-green-500/20 backdrop-blur-sm
          border border-green-500/50
          rounded-lg px-2 py-1
          flex items-center gap-1">
          <ArrowUp className="w-3 h-3 text-green-400" />
          <span className="text-xs font-bold text-green-400">
            +{player.score_change}
          </span>
        </div>
      )}

      <div className="p-6">
        {/* Avatar + Basic Info */}
        <div className="flex items-start gap-4 mb-6">
          <div className="relative">
            {player.avatar_url ? (
              <img
                src={player.avatar_url}
                alt={player.nickname}
                className="w-20 h-20 rounded-2xl object-cover ring-4 ring-cyan-500/30"
              />
            ) : (
              <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-cyan-500 to-blue-600
                flex items-center justify-center ring-4 ring-cyan-500/30">
                <span className="text-3xl font-bold text-white">
                  {player.nickname[0].toUpperCase()}
                </span>
              </div>
            )}

            {/* Country Flag Badge */}
            <div className="absolute -bottom-2 -right-2
              w-8 h-8 rounded-full
              bg-slate-800 border-2 border-slate-900
              flex items-center justify-center text-xs">
              {getCountryFlag(player.country_code)}
            </div>
          </div>

          <div className="flex-1 min-w-0">
            <h2 className={`text-2xl font-black text-white truncate
              ${locale === "hi" ? "font-devanagari" : ""}`}>
              {player.nickname}
            </h2>
            <div className="flex items-center gap-2 mt-1 text-sm text-slate-400">
              <span>{player.game}</span>
              <span>•</span>
              <span>{player.rank}</span>
            </div>
            <div className="flex items-center gap-1 mt-2">
              <Star className="w-4 h-4 text-yellow-400" />
              <span className="text-sm font-semibold text-yellow-400">
                {player.talent_score || 0}
              </span>
              <span className="text-xs text-slate-500 ml-1">
                {t("talentScore")}
              </span>
            </div>
          </div>
        </div>

        {/* GameRadar Score - PROMINENTE CON NEÓN */}
        <motion.div
          whileHover={{ scale: 1.02 }}
          className="relative mb-6 p-6 rounded-2xl
            bg-gradient-to-br from-green-500 via-emerald-500 to-teal-500
            shadow-2xl shadow-green-500/50
            overflow-hidden"
        >
          {/* Animated background pattern */}
          <div className="absolute inset-0 opacity-20">
            <div className="absolute top-0 left-0 w-full h-full
              bg-gradient-to-br from-white to-transparent
              animate-pulse" />
          </div>

          <div className="relative z-10 flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Trophy className="w-6 h-6 text-white" />
                <span className="text-sm font-bold text-white/90">
                  {t("gameRadarScore")}
                </span>
              </div>
              <div className="text-6xl font-black text-white">
                {Math.round(player.gameradar_score || 0)}
              </div>
            </div>
            <Zap className="w-16 h-16 text-white/30" />
          </div>
        </motion.div>

        {/* Stats Grid */}
        <div className="grid grid-cols-3 gap-3 mb-6">
          <StatCard
            icon={<TrendingUp className="w-5 h-5 text-green-400" />}
            label={t("winRate")}
            value={`${(player.win_rate || 0).toFixed(1)}%`}
            color="green"
          />
          <StatCard
            icon={<Target className="w-5 h-5 text-yellow-400" />}
            label="KDA"
            value={(player.kda || 0).toFixed(2)}
            color="yellow"
          />
          <StatCard
            icon={<Award className="w-5 h-5 text-purple-400" />}
            label={t("rank")}
            value={player.rank.split(" ")[0]}
            color="purple"
          />
        </div>

        {/* Top Champions */}
        {player.top_champions && player.top_champions.length > 0 && (
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-slate-400 mb-2">
              {t("topChampions")}
            </h3>
            <div className="flex gap-2 flex-wrap">
              {player.top_champions.slice(0, 3).map((champion, idx) => (
                <div
                  key={idx}
                  className="px-3 py-1.5 rounded-full
                    bg-slate-800 border border-slate-700
                    text-sm text-slate-300"
                >
                  {champion}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Action Buttons - WhatsApp/Zalo PROMINENTE */}
        <div className="flex gap-3">
          <motion.button
            whileTap={{ scale: 0.95 }}
            onClick={() => isVietnam ? onShareZalo(player) : onShareWhatsApp(player)}
            className="flex-1 py-4 rounded-xl
              bg-gradient-to-r from-green-600 to-green-500
              hover:from-green-500 hover:to-green-400
              flex items-center justify-center gap-2
              text-white font-bold text-lg
              shadow-lg shadow-green-500/30
              transition-all duration-300"
          >
            <MessageCircle className="w-6 h-6" />
            {isVietnam ? "Zalo" : "WhatsApp"}
          </motion.button>

          {player.profile_url && (
            <motion.a
              whileTap={{ scale: 0.95 }}
              href={player.profile_url}
              target="_blank"
              rel="noopener noreferrer"
              className="py-4 px-6 rounded-xl
                bg-slate-800 hover:bg-slate-700
                border border-slate-700
                flex items-center justify-center
                transition-colors"
            >
              <ExternalLink className="w-6 h-6 text-slate-300" />
            </motion.a>
          )}
        </div>
      </div>
    </div>
  );
}

// ============================================================
// STAT CARD Component
// ============================================================
function StatCard({
  icon,
  label,
  value,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  color: "green" | "yellow" | "purple";
}) {
  const colorClasses = {
    green: "bg-green-500/10 border-green-500/30",
    yellow: "bg-yellow-500/10 border-yellow-500/30",
    purple: "bg-purple-500/10 border-purple-500/30",
  };

  return (
    <div className={`p-3 rounded-xl border ${colorClasses[color]}`}>
      <div className="flex items-center justify-center mb-1">
        {icon}
      </div>
      <div className="text-center">
        <div className="text-lg font-bold text-white">{value}</div>
        <div className="text-[10px] text-slate-400 uppercase">{label}</div>
      </div>
    </div>
  );
}

// ============================================================
// HELPER FUNCTIONS
// ============================================================
function getCountryFlag(countryCode: string): string {
  const flags: Record<string, string> = {
    IN: "🇮🇳",
    VN: "🇻🇳",
    TH: "🇹🇭",
    PH: "🇵🇭",
    ID: "🇮🇩",
    KR: "🇰🇷",
    CN: "🇨🇳",
    JP: "🇯🇵",
  };
  return flags[countryCode] || "🌍";
}

function generateShareMessage(player: Player, locale: string): string {
  const messages: Record<string, string> = {
    hi: `🔥 देखो! ${player.nickname} को GameRadar AI पर खोजा!\n\n⭐ GameRadar Score: ${Math.round(player.gameradar_score || 0)}\n🎮 Game: ${player.game}\n🏆 Rank: ${player.rank}\n📊 Win Rate: ${(player.win_rate || 0).toFixed(1)}%\n\nयह अगला बड़ा स्टार हो सकता है! 🚀`,
    
    vi: `🔥 Nhìn này! Tôi đã tìm thấy ${player.nickname} trên GameRadar AI!\n\n⭐ GameRadar Score: ${Math.round(player.gameradar_score || 0)}\n🎮 Game: ${player.game}\n🏆 Rank: ${player.rank}\n📊 Tỷ lệ thắng: ${(player.win_rate || 0).toFixed(1)}%\n\nĐây có thể là ngôi sao tiếp theo! 🚀`,
    
    en: `🔥 Check this out! Found ${player.nickname} on GameRadar AI!\n\n⭐ GameRadar Score: ${Math.round(player.gameradar_score || 0)}\n🎮 Game: ${player.game}\n🏆 Rank: ${player.rank}\n📊 Win Rate: ${(player.win_rate || 0).toFixed(1)}%\n\nThis could be the next big star! 🚀`,
  };

  return messages[locale] || messages.en;
}
