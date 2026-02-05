"use client";

/**
 * PlayerCard Component - Adaptive UX Cultural
 * 
 * Diseño dual según is_mobile_heavy:
 * - TRUE (India/Vietnam): Tarjeta táctil, fuentes grandes, WhatsApp share
 * - FALSE (Korea/Japan): Layout minimalista, tabla técnica, radar charts
 * 
 * Vibe: E-Sports oscuro, profesional, extremadamente rápido
 */

import { useState } from "react";
import { twMerge } from "tailwind-merge";
import {
  Trophy,
  TrendingUp,
  Zap,
  Target,
  Gamepad2,
  Share2,
  ExternalLink,
  Star,
  Award,
  ChevronRight,
  MessageCircle,
  Mail,
  Phone,
  Copy,
  CheckCircle2,
} from "lucide-react";

// Tipos
interface PlayerStats {
  win_rate?: number;
  kda?: number;
  games_played?: number;
  talent_score?: number;
  gameradar_score?: number;
  main_role?: string;
  top_champions?: string[];
}

interface PlayerCardProps {
  // Datos del jugador
  player_id: string;
  nickname: string;
  real_name?: string;
  country_code: string;
  region: string;
  game: string;
  rank: string;
  avatar_url?: string;
  profile_url?: string;
  
  // Stats
  stats: PlayerStats;
  
  // UX Cultural flag
  is_mobile_heavy: boolean;
  
  // Opcionales
  is_verified?: boolean;
  className?: string;
  onContact?: () => void;
}

export default function PlayerCard({
  player_id,
  nickname,
  real_name,
  country_code,
  region,
  game,
  rank,
  avatar_url,
  profile_url,
  stats,
  is_mobile_heavy,
  is_verified = false,
  className,
  onContact,
}: PlayerCardProps) {
  const [copied, setCopied] = useState(false);

  // Handler para compartir en WhatsApp
  const handleWhatsAppShare = () => {
    const message = encodeURIComponent(
      `🎮 GameRadar AI - Talento Descubierto!\n\n` +
      `👤 ${nickname} ${real_name ? `(${real_name})` : ''}\n` +
      `🏆 Rank: ${rank}\n` +
      `📊 Score: ${stats.gameradar_score?.toFixed(0) || 'N/A'}/100\n` +
      `💯 Win Rate: ${stats.win_rate?.toFixed(1)}%\n` +
      `⚡ KDA: ${stats.kda?.toFixed(2)}\n` +
      `🌏 Region: ${region} (${country_code})\n\n` +
      `¡Mira su perfil completo en GameRadar AI!`
    );
    
    // Abrir WhatsApp en móvil o desktop
    const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
    const whatsappUrl = isMobile 
      ? `whatsapp://send?text=${message}`
      : `https://web.whatsapp.com/send?text=${message}`;
    
    window.open(whatsappUrl, '_blank');
  };

  // Handler para copiar ID
  const handleCopyId = () => {
    navigator.clipboard.writeText(player_id);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Share API nativa (fallback)
  const handleNativeShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: `${nickname} - GameRadar AI`,
          text: `Descubre el talento de ${nickname} en GameRadar AI`,
          url: profile_url || window.location.href,
        });
      } catch (err) {
        console.log('Share cancelled');
      }
    } else {
      handleWhatsAppShare();
    }
  };

  // Renderizar según is_mobile_heavy
  return is_mobile_heavy ? (
    <MobileHeavyCard
      nickname={nickname}
      real_name={real_name}
      country_code={country_code}
      region={region}
      game={game}
      rank={rank}
      avatar_url={avatar_url}
      profile_url={profile_url}
      stats={stats}
      is_verified={is_verified}
      onWhatsAppShare={handleWhatsAppShare}
      onNativeShare={handleNativeShare}
      onCopyId={handleCopyId}
      copied={copied}
      className={className}
    />
  ) : (
    <TechnicalCard
      nickname={nickname}
      real_name={real_name}
      country_code={country_code}
      region={region}
      game={game}
      rank={rank}
      avatar_url={avatar_url}
      profile_url={profile_url}
      stats={stats}
      is_verified={is_verified}
      onCopyId={handleCopyId}
      copied={copied}
      className={className}
    />
  );
}

/**
 * ====================================================================
 * MOBILE-HEAVY CARD (India/Vietnam/Thailand)
 * Diseño táctil, fuentes grandes, botones de acción directos
 * ====================================================================
 */
interface MobileHeavyCardProps {
  nickname: string;
  real_name?: string;
  country_code: string;
  region: string;
  game: string;
  rank: string;
  avatar_url?: string;
  profile_url?: string;
  stats: PlayerStats;
  is_verified: boolean;
  onWhatsAppShare: () => void;
  onNativeShare: () => void;
  onCopyId: () => void;
  copied: boolean;
  className?: string;
}

function MobileHeavyCard({
  nickname,
  real_name,
  country_code,
  region,
  game,
  rank,
  avatar_url,
  profile_url,
  stats,
  is_verified,
  onWhatsAppShare,
  onNativeShare,
  onCopyId,
  copied,
  className,
}: MobileHeavyCardProps) {
  return (
    <div
      className={twMerge(
        "relative overflow-hidden rounded-2xl",
        "bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900",
        "border-2 border-slate-700/50",
        "shadow-2xl shadow-purple-900/20",
        "transform transition-all duration-300",
        "hover:scale-[1.02] hover:shadow-purple-500/30 hover:border-purple-500/50",
        "active:scale-[0.98]",
        className
      )}
    >
      {/* Animated Background Gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-purple-600/10 via-transparent to-cyan-600/10 animate-pulse" />
      
      {/* Verified Badge */}
      {is_verified && (
        <div className="absolute top-4 right-4 z-10">
          <div className="flex items-center gap-1.5 bg-green-500 text-white text-xs font-bold px-3 py-1.5 rounded-full shadow-lg">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span className="font-devanagari">Verified</span>
          </div>
        </div>
      )}

      {/* Header - Avatar + Nombre */}
      <div className="relative bg-gradient-to-r from-purple-600 to-cyan-600 p-6">
        <div className="flex items-center gap-4">
          {/* Avatar Grande */}
          <div className="relative">
            <div className="w-24 h-24 rounded-full border-4 border-white/30 overflow-hidden bg-slate-900 shadow-xl">
              {avatar_url ? (
                <img
                  src={avatar_url}
                  alt={nickname}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center">
                  <span className="text-4xl font-bold text-white">
                    {nickname.charAt(0).toUpperCase()}
                  </span>
                </div>
              )}
            </div>
            {/* Score Badge flotante */}
            {stats.gameradar_score && (
              <div className="absolute -bottom-2 -right-2 bg-gradient-to-br from-yellow-400 to-orange-500 text-white rounded-full w-12 h-12 flex flex-col items-center justify-center shadow-lg border-2 border-white">
                <span className="text-sm font-bold">{stats.gameradar_score.toFixed(0)}</span>
                <span className="text-[8px] font-medium opacity-90">SCORE</span>
              </div>
            )}
          </div>

          {/* Información del Jugador */}
          <div className="flex-1">
            <h2 className="text-3xl font-black text-white mb-1 tracking-tight font-devanagari drop-shadow-lg">
              {nickname}
            </h2>
            {real_name && (
              <p className="text-white/90 text-base font-medium font-devanagari mb-2">
                {real_name}
              </p>
            )}
            <div className="flex items-center gap-2 flex-wrap">
              <span className="bg-white/20 backdrop-blur-sm text-white text-sm font-bold px-3 py-1 rounded-full">
                {region}
              </span>
              <span className="bg-white/20 backdrop-blur-sm text-white text-sm font-bold px-3 py-1 rounded-full">
                {country_code}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Rank Destacado */}
      <div className="bg-slate-800/50 backdrop-blur-sm px-6 py-4 border-b border-slate-700/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Trophy className="w-8 h-8 text-yellow-400" />
            <div>
              <p className="text-slate-400 text-xs uppercase tracking-wide font-medium">
                Current Rank
              </p>
              <p className="text-white text-2xl font-black font-devanagari">
                {rank}
              </p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-slate-400 text-xs uppercase tracking-wide font-medium">
              Game
            </p>
            <p className="text-white text-xl font-bold">
              {game}
            </p>
          </div>
        </div>
      </div>

      {/* Stats Grid - Táctil y grande */}
      <div className="p-6 space-y-4">
        {/* Win Rate & KDA - Destacados */}
        <div className="grid grid-cols-2 gap-4">
          <StatCardLarge
            icon={<Target className="w-8 h-8" />}
            label="Win Rate"
            value={`${stats.win_rate?.toFixed(1) || 0}%`}
            color="green"
            highlight={stats.win_rate && stats.win_rate >= 55}
          />
          <StatCardLarge
            icon={<Zap className="w-8 h-8" />}
            label="KDA"
            value={stats.kda?.toFixed(2) || "N/A"}
            color="purple"
            highlight={stats.kda && stats.kda >= 3}
          />
        </div>

        {/* Stats Secundarios */}
        <div className="grid grid-cols-3 gap-3">
          <StatCardSmall
            icon={<Gamepad2 className="w-5 h-5" />}
            label="Games"
            value={stats.games_played?.toLocaleString() || "0"}
          />
          <StatCardSmall
            icon={<Award className="w-5 h-5" />}
            label="Talent"
            value={stats.talent_score?.toFixed(0) || "N/A"}
          />
          <StatCardSmall
            icon={<Star className="w-5 h-5" />}
            label="Role"
            value={stats.main_role || "All"}
          />
        </div>

        {/* Top Champions - Visual */}
        {stats.top_champions && stats.top_champions.length > 0 && (
          <div className="bg-slate-800/30 rounded-xl p-4 border border-slate-700/30">
            <p className="text-slate-400 text-sm uppercase tracking-wide font-medium mb-3 font-devanagari">
              Top Champions
            </p>
            <div className="flex flex-wrap gap-2">
              {stats.top_champions.slice(0, 4).map((champ, idx) => (
                <div
                  key={idx}
                  className="bg-gradient-to-r from-cyan-600/20 to-blue-600/20 border border-cyan-500/30 text-cyan-300 px-4 py-2 rounded-lg text-sm font-bold font-devanagari shadow-sm"
                >
                  {champ}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Botones de Acción - GRANDES y BRILLANTES */}
      <div className="px-6 pb-6 space-y-3">
        {/* WhatsApp - Botón Principal */}
        <button
          onClick={onWhatsAppShare}
          className="w-full bg-gradient-to-r from-green-500 to-green-600 hover:from-green-400 hover:to-green-500 text-white font-black text-lg py-5 rounded-xl transition-all duration-200 active:scale-95 shadow-lg shadow-green-500/30 flex items-center justify-center gap-3 font-devanagari"
        >
          <MessageCircle className="w-6 h-6" />
          Share on WhatsApp
        </button>

        {/* Botones Secundarios */}
        <div className="grid grid-cols-2 gap-3">
          {profile_url && (
            <a
              href={profile_url}
              target="_blank"
              rel="noopener noreferrer"
              className="bg-cyan-600 hover:bg-cyan-500 text-white font-bold py-4 rounded-xl transition-all duration-200 active:scale-95 shadow-md flex items-center justify-center gap-2"
            >
              <ExternalLink className="w-5 h-5" />
              Profile
            </a>
          )}
          <button
            onClick={onNativeShare}
            className="bg-purple-600 hover:bg-purple-500 text-white font-bold py-4 rounded-xl transition-all duration-200 active:scale-95 shadow-md flex items-center justify-center gap-2"
          >
            <Share2 className="w-5 h-5" />
            Share
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * ====================================================================
 * TECHNICAL CARD (Korea/Japan/China)
 * Layout minimalista, tipo tabla técnica, gráficos compactos
 * ====================================================================
 */
interface TechnicalCardProps {
  nickname: string;
  real_name?: string;
  country_code: string;
  region: string;
  game: string;
  rank: string;
  avatar_url?: string;
  profile_url?: string;
  stats: PlayerStats;
  is_verified: boolean;
  onCopyId: () => void;
  copied: boolean;
  className?: string;
}

function TechnicalCard({
  nickname,
  real_name,
  country_code,
  region,
  game,
  rank,
  avatar_url,
  profile_url,
  stats,
  is_verified,
  onCopyId,
  copied,
  className,
}: TechnicalCardProps) {
  return (
    <div
      className={twMerge(
        "relative overflow-hidden rounded-lg",
        "bg-slate-900/95 backdrop-blur-sm",
        "border border-slate-800/50",
        "shadow-lg shadow-black/50",
        "hover:border-cyan-500/30 hover:shadow-cyan-500/10",
        "transition-all duration-200",
        className
      )}
    >
      {/* Header Compacto */}
      <div className="bg-slate-800/50 border-b border-slate-700/50 px-4 py-3">
        <div className="flex items-center justify-between">
          {/* Avatar + Nombre */}
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="w-12 h-12 rounded-lg border border-slate-700/50 overflow-hidden bg-slate-800">
                {avatar_url ? (
                  <img
                    src={avatar_url}
                    alt={nickname}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-lg font-bold text-slate-400 font-cjk">
                    {nickname.charAt(0).toUpperCase()}
                  </div>
                )}
              </div>
              {is_verified && (
                <div className="absolute -top-1 -right-1 bg-green-500 rounded-full p-0.5">
                  <CheckCircle2 className="w-3 h-3 text-white" />
                </div>
              )}
            </div>
            
            <div>
              <h3 className="text-white font-bold text-base font-cjk leading-tight">
                {nickname}
              </h3>
              {real_name && (
                <p className="text-slate-400 text-xs font-cjk">
                  {real_name}
                </p>
              )}
            </div>
          </div>

          {/* Score Badge */}
          {stats.gameradar_score && (
            <div className="bg-gradient-to-br from-cyan-600 to-blue-600 rounded-lg px-3 py-2 text-center min-w-[60px]">
              <div className="text-white text-xl font-bold leading-none">
                {stats.gameradar_score.toFixed(0)}
              </div>
              <div className="text-cyan-100 text-[10px] font-medium uppercase opacity-90">
                Score
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Tabla de Stats - Compacta */}
      <div className="p-4 space-y-2">
        {/* Row 1: Rank + Region */}
        <div className="grid grid-cols-2 gap-3">
          <DataRow label="Rank" value={rank} icon={<Trophy className="w-3.5 h-3.5" />} />
          <DataRow label="Region" value={`${region} • ${country_code}`} />
        </div>

        {/* Row 2: Win Rate + KDA */}
        <div className="grid grid-cols-2 gap-3">
          <DataRow
            label="Win Rate"
            value={`${stats.win_rate?.toFixed(1) || 0}%`}
            valueColor={stats.win_rate && stats.win_rate >= 55 ? "text-green-400" : "text-slate-300"}
          />
          <DataRow
            label="KDA"
            value={stats.kda?.toFixed(2) || "N/A"}
            valueColor={stats.kda && stats.kda >= 3 ? "text-purple-400" : "text-slate-300"}
          />
        </div>

        {/* Row 3: Games + Talent */}
        <div className="grid grid-cols-2 gap-3">
          <DataRow
            label="Games"
            value={stats.games_played?.toLocaleString() || "0"}
            icon={<Gamepad2 className="w-3.5 h-3.5" />}
          />
          <DataRow
            label="Talent"
            value={stats.talent_score?.toFixed(0) || "N/A"}
            icon={<Award className="w-3.5 h-3.5" />}
          />
        </div>

        {/* Top Champions - Compacto */}
        {stats.top_champions && stats.top_champions.length > 0 && (
          <div className="pt-2 border-t border-slate-800/50">
            <p className="text-slate-500 text-[10px] uppercase tracking-wider font-medium mb-1.5">
              Top Champions
            </p>
            <div className="flex flex-wrap gap-1.5">
              {stats.top_champions.slice(0, 3).map((champ, idx) => (
                <span
                  key={idx}
                  className="bg-slate-800/50 border border-slate-700/30 text-slate-300 px-2 py-0.5 rounded text-xs font-medium font-cjk"
                >
                  {champ}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Footer - Acciones Minimalistas */}
      <div className="bg-slate-800/30 border-t border-slate-800/50 px-4 py-2 flex items-center justify-between">
        <button
          onClick={onCopyId}
          className="text-slate-400 hover:text-cyan-400 transition-colors text-xs font-medium flex items-center gap-1.5"
        >
          {copied ? (
            <>
              <CheckCircle2 className="w-3.5 h-3.5 text-green-400" />
              <span className="text-green-400">Copied</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              Copy ID
            </>
          )}
        </button>

        {profile_url && (
          <a
            href={profile_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-cyan-400 hover:text-cyan-300 transition-colors text-xs font-medium flex items-center gap-1.5"
          >
            View Profile
            <ChevronRight className="w-3.5 h-3.5" />
          </a>
        )}
      </div>
    </div>
  );
}

/**
 * ====================================================================
 * UTILITY COMPONENTS
 * ====================================================================
 */

// Stat Card Grande (Mobile-Heavy)
function StatCardLarge({
  icon,
  label,
  value,
  color,
  highlight,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  color: "green" | "purple";
  highlight?: boolean;
}) {
  const colorClasses = {
    green: highlight
      ? "from-green-600 to-emerald-600 border-green-500/50"
      : "from-green-600/30 to-emerald-600/30 border-green-500/20",
    purple: highlight
      ? "from-purple-600 to-violet-600 border-purple-500/50"
      : "from-purple-600/30 to-violet-600/30 border-purple-500/20",
  };

  return (
    <div
      className={twMerge(
        "bg-gradient-to-br rounded-xl p-4 border shadow-lg",
        colorClasses[color]
      )}
    >
      <div className="flex items-center gap-2 mb-2 text-white/80">
        {icon}
        <span className="text-xs uppercase tracking-wide font-medium font-devanagari">
          {label}
        </span>
      </div>
      <div className="text-white text-3xl font-black font-devanagari">
        {value}
      </div>
    </div>
  );
}

// Stat Card Pequeña (Mobile-Heavy)
function StatCardSmall({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="bg-slate-800/30 rounded-lg p-3 border border-slate-700/30">
      <div className="flex items-center gap-1.5 mb-1.5 text-slate-400">
        {icon}
      </div>
      <div className="text-white text-lg font-bold font-devanagari">
        {value}
      </div>
      <div className="text-slate-500 text-[10px] uppercase tracking-wide font-medium">
        {label}
      </div>
    </div>
  );
}

// Data Row (Technical Card)
function DataRow({
  label,
  value,
  icon,
  valueColor = "text-slate-300",
}: {
  label: string;
  value: string;
  icon?: React.ReactNode;
  valueColor?: string;
}) {
  return (
    <div className="bg-slate-800/30 rounded px-3 py-2 border border-slate-800/50">
      <div className="flex items-center gap-1.5 mb-1">
        {icon && <span className="text-slate-500">{icon}</span>}
        <span className="text-slate-500 text-[10px] uppercase tracking-wider font-medium">
          {label}
        </span>
      </div>
      <div className={twMerge("text-sm font-bold font-cjk", valueColor)}>
        {value}
      </div>
    </div>
  );
}
