"use client";

/**
 * Transcultural Dashboard Component
 * Consume tabla silver_players y renderiza UI adaptativa según región
 * 
 * Lógica:
 * - India/Vietnam (is_mobile_heavy) → Feed vertical estilo red social
 * - Corea/China → Grilla técnica de alta densidad
 * - Japón → Vista minimalista con tooltips explicativos
 * 
 * Usa lucide-react para iconos, tailwind-merge para clases dinámicas
 * next-intl para i18n sin recargar página
 * Fuentes optimizadas para CJK (Chino/Coreano/Japonés) y Devanagari (Hindi)
 */

import { useEffect, useState } from "react";
import { createClient } from "@supabase/supabase-js";
import { twMerge } from "tailwind-merge";
import { useTranslations } from "next-intl";
import {
  Trophy,
  TrendingUp,
  Globe,
  Smartphone,
  Monitor,
  ChevronUp,
  ChevronDown,
  Phone,
  Mail,
  ExternalLink,
  MessageCircle,
  Info,
  Zap,
  Target,
  Award,
} from "lucide-react";
import { useCountryDetection } from "@/hooks/useCountryDetection";

// Tipos de vista regional
type RegionalView = "feed" | "dense" | "minimal" | "auto";

// Tipos
interface SilverPlayer {
  id: string;
  player_id: string;
  nickname: string;
  real_name: string | null;
  country_code: string;
  region: string;
  server: string;
  game: string;
  rank: string;
  tier: string;
  division: string;
  lp: number | null;
  win_rate: number | null;
  games_played: number | null;
  kda: number | null;
  main_role: string | null;
  top_champions: string[] | null;
  profile_url: string | null;
  avatar_url: string | null;
  social_links: Record<string, string> | null;
  is_mobile_heavy: boolean;
  is_verified: boolean;
  talent_score: number | null;
  last_updated: string;
  metadata: Record<string, any> | null;
}

interface TransculturalDashboardProps {
  supabaseUrl: string;
  supabaseKey: string;
  limit?: number;
}

export default function TransculturalDashboard({
  supabaseUrl,
  supabaseKey,
  limit = 100,
}: TransculturalDashboardProps) {
  const t = useTranslations("dashboard");
  const { countryCode, uiMode } = useCountryDetection();
  
  const [players, setPlayers] = useState<SilverPlayer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortField, setSortField] = useState<keyof SilverPlayer>("talent_score");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("desc");
  const [viewMode, setViewMode] = useState<RegionalView>("auto");

  // Cliente Supabase
  const supabase = createClient(supabaseUrl, supabaseKey);

  // Fetch players from silver_players
  useEffect(() => {
    fetchPlayers();
  }, [limit]);

  const fetchPlayers = async () => {
    try {
      setLoading(true);
      setError(null);

      const { data, error: fetchError } = await supabase
        .from("silver_players")
        .select("*")
        .order("talent_score", { ascending: false })
        .limit(limit);

      if (fetchError) throw fetchError;

      setPlayers(data || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error desconocido");
      console.error("Error fetching silver players:", err);
    } finally {
      setLoading(false);
    }
  };

  // Sorting logic
  const sortedPlayers = [...players].sort((a, b) => {
    const aVal = a[sortField];
    const bVal = b[sortField];

    if (aVal === null) return 1;
    if (bVal === null) return -1;

    if (typeof aVal === "number" && typeof bVal === "number") {
      return sortDirection === "asc" ? aVal - bVal : bVal - aVal;
    }

    const aStr = String(aVal).toLowerCase();
    const bStr = String(bVal).toLowerCase();
    return sortDirection === "asc"
      ? aStr.localeCompare(bStr)
      : bStr.localeCompare(aStr);
  });

  // Determinar vista regional basada en país del usuario
  const determineRegionalView = (): RegionalView => {
    if (viewMode !== "auto") return viewMode;

    // Basado en detección de país del usuario
    switch (countryCode) {
      case "IN":
      case "VN":
      case "TH":
      case "PH":
      case "ID":
        return "feed"; // Feed vertical para mobile-heavy
      
      case "KR":
      case "CN":
        return "dense"; // Grilla técnica de alta densidad
      
      case "JP":
        return "minimal"; // Vista minimalista con tooltips
      
      default:
        // Fallback: analizar jugadores en el dataset
        const mobileHeavyCount = players.filter((p) => p.is_mobile_heavy).length;
        if (mobileHeavyCount > players.length / 2) return "feed";
        return "dense";
    }
  };

  const currentView = determineRegionalView();

  // Handle sort
  const handleSort = (field: keyof SilverPlayer) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection("desc");
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-cyan-400 border-opacity-75 mx-auto" />
          <p className="text-cyan-300 text-lg font-medium">
            {t("loading")}
          </p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-red-900 via-slate-800 to-slate-900">
        <div className="bg-red-900/20 border border-red-500 rounded-lg p-8 max-w-md">
          <h2 className="text-red-400 text-xl font-bold mb-2">Error</h2>
          <p className="text-red-300">{error}</p>
          <button
            onClick={fetchPlayers}
            className="mt-4 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
          >
            Reintentar
          </button>
        </div>
      </div>
    );
  }

  // Empty state
  if (players.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        <div className="text-center space-y-4">
          <Trophy className="w-16 h-16 text-slate-600 mx-auto" />
          <p className="text-slate-400 text-lg">No hay jugadores disponibles</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
      {/* Header */}
      <header className="border-b border-slate-700/50 bg-slate-900/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">
                GameRadar Silver
              </h1>
              <p className="text-slate-400 mt-1">
                UI Transcultural • Datos en tiempo real
              </p>
            </div>

            {/* View Mode Toggle */}
            <div className="flex items-center gap-2 bg-slate-800/50 rounded-lg p-1">
              <button
                onClick={() => setViewMode("auto")}
                className={twMerge(
                  "px-3 py-2 rounded-md transition-all flex items-center gap-2",
                  viewMode === "auto"
                    ? "bg-cyan-600 text-white shadow-lg"
                    : "text-slate-400 hover:text-white"
                )}
              >
                <Globe className="w-4 h-4" />
                <span className="text-sm font-medium">{t("viewMode.auto")}</span>
              </button>
              <button
                onClick={() => setViewMode("feed")}
                className={twMerge(
                  "px-3 py-2 rounded-md transition-all flex items-center gap-2",
                  viewMode === "feed"
                    ? "bg-cyan-600 text-white shadow-lg"
                    : "text-slate-400 hover:text-white"
                )}
              >
                <Smartphone className="w-4 h-4" />
                <span className="text-sm font-medium">{t("viewMode.feed")}</span>
              </button>
              <button
                onClick={() => setViewMode("dense")}
                className={twMerge(
                  "px-3 py-2 rounded-md transition-all flex items-center gap-2",
                  viewMode === "dense"
                    ? "bg-cyan-600 text-white shadow-lg"
                    : "text-slate-400 hover:text-white"
                )}
              >
                <Monitor className="w-4 h-4" />
                <span className="text-sm font-medium">{t("viewMode.dense")}</span>
              </button>
              <button
                onClick={() => setViewMode("minimal")}
                className={twMerge(
                  "px-3 py-2 rounded-md transition-all flex items-center gap-2",
                  viewMode === "minimal"
                    ? "bg-cyan-600 text-white shadow-lg"
                    : "text-slate-400 hover:text-white"
                )}
              >
                <Award className="w-4 h-4" />
                <span className="text-sm font-medium">{t("viewMode.minimal")}</span>
              </button>
            </div>
          </div>

          {/* Stats */}
          <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-slate-800/30 rounded-lg p-4 border border-slate-700/30">
              <div className="flex items-center gap-3">
                <Trophy className="w-8 h-8 text-yellow-400" />
                <div>
                  <p className="text-slate-400 text-sm">Total Jugadores</p>
                  <p className="text-2xl font-bold">{players.length}</p>
                </div>
              </div>
            </div>
            <div className="bg-slate-800/30 rounded-lg p-4 border border-slate-700/30">
              <div className="flex items-center gap-3">
                <Smartphone className="w-8 h-8 text-cyan-400" />
                <div>
                  <p className="text-slate-400 text-sm">Mobile-Heavy</p>
                  <p className="text-2xl font-bold">
                    {players.filter((p) => p.is_mobile_heavy).length}
                  </p>
                </div>
              </div>
            </div>
            <div className="bg-slate-800/30 rounded-lg p-4 border border-slate-700/30">
              <div className="flex items-center gap-3">
                <TrendingUp className="w-8 h-8 text-green-400" />
                <div>
                  <p className="text-slate-400 text-sm">Avg Talent Score</p>
                  <p className="text-2xl font-bold">
                    {(
                      players.reduce((sum, p) => sum + (p.talent_score || 0), 0) /
                      players.length
                    ).toFixed(1)}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {currentView === "feed" && (
          <IndiaVietnamFeed players={sortedPlayers} />
        )}
        {currentView === "dense" && (
          <KoreaChinaDenseTable
            players={sortedPlayers}
            sortField={sortField}
            sortDirection={sortDirection}
            onSort={handleSort}
          />
        )}
        {currentView === "minimal" && (
          <JapanMinimalistView players={sortedPlayers} />
        )}
      </main>
    </div>
  );
}

/**
 * India/Vietnam Feed Component
 * Feed vertical estilo red social para regiones mobile-heavy
 * Prioriza GameRadar Score y botones de contacto rápido (WhatsApp/Zalo)
 */
interface IndiaVietnamFeedProps {
  players: SilverPlayer[];
}

function IndiaVietnamFeed({ players }: IndiaVietnamFeedProps) {
  const t = useTranslations("feed");

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      {players.map((player) => (
        <div
          key={player.id}
          className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-md border border-slate-700/50 rounded-2xl overflow-hidden hover:border-cyan-500/50 transition-all hover:shadow-2xl hover:shadow-cyan-500/10"
        >
          {/* Header con GameRadar Score destacado */}
          <div className="relative bg-gradient-to-r from-cyan-600 via-blue-600 to-purple-600 p-8">
            {player.is_verified && (
              <div className="absolute top-4 right-4">
                <div className="bg-green-500 text-white text-xs px-3 py-1.5 rounded-full font-bold shadow-lg">
                  ✓ {t("verified")}
                </div>
              </div>
            )}

            {/* GameRadar Score - PROMINENTE */}
            <div className="text-center mb-6">
              <div className="inline-block bg-white/10 backdrop-blur-sm rounded-3xl px-8 py-4 border-2 border-white/20">
                <p className="text-white/80 text-sm font-semibold uppercase tracking-wider mb-1">
                  {t("gameRadarScore")}
                </p>
                <p className="text-6xl font-black text-white drop-shadow-2xl">
                  {player.talent_score ? player.talent_score.toFixed(0) : "—"}
                </p>
              </div>
            </div>

            {/* Jugador Info */}
            <div className="text-center">
              <h2 className="text-3xl font-black text-white mb-2 font-devanagari drop-shadow-lg">
                {player.nickname}
              </h2>
              {player.real_name && (
                <p className="text-cyan-100 text-lg font-medium font-devanagari">
                  {player.real_name}
                </p>
              )}
              <div className="mt-3 flex items-center justify-center gap-3 text-white/90">
                <span className="font-bold text-lg">{player.rank}</span>
                <span className="text-white/60">•</span>
                <span className="font-semibold">
                  {player.region} • {player.country_code}
                </span>
              </div>
            </div>
          </div>

          {/* Stats Grid - GRANDES Y LEGIBLES */}
          <div className="p-6 space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-gradient-to-br from-green-600/20 to-green-800/20 border border-green-600/30 rounded-2xl p-5 text-center">
                <Trophy className="w-8 h-8 text-green-400 mx-auto mb-2" />
                <p className="text-green-300 text-xs font-bold uppercase mb-1">
                  {t("winRate")}
                </p>
                <p className="text-3xl font-black text-green-400">
                  {player.win_rate ? `${player.win_rate.toFixed(0)}%` : "—"}
                </p>
              </div>

              <div className="bg-gradient-to-br from-purple-600/20 to-purple-800/20 border border-purple-600/30 rounded-2xl p-5 text-center">
                <Target className="w-8 h-8 text-purple-400 mx-auto mb-2" />
                <p className="text-purple-300 text-xs font-bold uppercase mb-1">
                  {t("kda")}
                </p>
                <p className="text-3xl font-black text-purple-400">
                  {player.kda ? player.kda.toFixed(1) : "—"}
                </p>
              </div>

              <div className="bg-gradient-to-br from-blue-600/20 to-blue-800/20 border border-blue-600/30 rounded-2xl p-5 text-center">
                <Zap className="w-8 h-8 text-blue-400 mx-auto mb-2" />
                <p className="text-blue-300 text-xs font-bold uppercase mb-1">
                  {t("games")}
                </p>
                <p className="text-3xl font-black text-blue-400">
                  {player.games_played || "—"}
                </p>
              </div>
            </div>

            {/* Top Champions */}
            {player.top_champions && player.top_champions.length > 0 && (
              <div className="bg-slate-800/40 rounded-xl p-4">
                <p className="text-slate-300 text-sm font-bold uppercase mb-3">
                  {t("topChampions")}
                </p>
                <div className="flex flex-wrap gap-2">
                  {player.top_champions.slice(0, 3).map((champ, idx) => (
                    <span
                      key={idx}
                      className="bg-gradient-to-r from-cyan-600/30 to-blue-600/30 border border-cyan-500/40 text-cyan-100 text-sm font-bold px-4 py-2 rounded-full"
                    >
                      {champ}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Botones de Acción - PROMINENTES */}
            <div className="grid grid-cols-2 gap-3 pt-2">
              {/* WhatsApp para India */}
              {(player.country_code === "IN" || player.is_mobile_heavy) && (
                <button className="flex items-center justify-center gap-3 bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white font-black py-4 rounded-xl transition-all shadow-lg hover:shadow-green-500/50 hover:scale-105">
                  <Phone className="w-5 h-5" />
                  <span className="text-lg">{t("contactWhatsApp")}</span>
                </button>
              )}

              {/* Zalo para Vietnam */}
              {player.country_code === "VN" && (
                <button className="flex items-center justify-center gap-3 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-black py-4 rounded-xl transition-all shadow-lg hover:shadow-blue-500/50 hover:scale-105">
                  <MessageCircle className="w-5 h-5" />
                  <span className="text-lg">{t("contactZalo")}</span>
                </button>
              )}

              {/* Ver Perfil */}
              {player.profile_url && (
                <a
                  href={player.profile_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-center gap-3 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 text-white font-black py-4 rounded-xl transition-all shadow-lg hover:shadow-cyan-500/50 hover:scale-105"
                >
                  <ExternalLink className="w-5 h-5" />
                  <span className="text-lg">{t("viewProfile")}</span>
                </a>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

/**
 * Korea/China Dense Table Component
 * Grilla técnica de alta densidad con micro-stats
 * Fuentes compactas, máxima información visible
 */
interface KoreaChinaDenseTableProps {
  players: SilverPlayer[];
  sortField: keyof SilverPlayer;
  sortDirection: "asc" | "desc";
  onSort: (field: keyof SilverPlayer) => void;
}

function KoreaChinaDenseTable({
  players,
  sortField,
  sortDirection,
  onSort,
}: KoreaChinaDenseTableProps) {
  const t = useTranslations("denseTable");

  const SortIcon = ({ field }: { field: keyof SilverPlayer }) => {
    if (sortField !== field) return null;
    return sortDirection === "asc" ? (
      <ChevronUp className="w-3 h-3" />
    ) : (
      <ChevronDown className="w-3 h-3" />
    );
  };

  return (
    <div className="bg-slate-900/90 backdrop-blur-sm border border-slate-700/50 rounded-lg overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-xs font-cjk">
          <thead className="bg-slate-950/90 border-b-2 border-cyan-600/50">
            <tr>
              <th className="px-2 py-2 text-left text-[10px] font-black text-cyan-400 uppercase tracking-wider">
                #
              </th>
              <th
                onClick={() => onSort("nickname")}
                className="px-2 py-2 text-left text-[10px] font-black text-cyan-400 uppercase tracking-wider cursor-pointer hover:text-cyan-300 transition-colors"
              >
                <div className="flex items-center gap-1">
                  {t("nickname")} <SortIcon field="nickname" />
                </div>
              </th>
              <th className="px-2 py-2 text-left text-[10px] font-black text-cyan-400 uppercase">
                {t("country")}
              </th>
              <th
                onClick={() => onSort("rank")}
                className="px-2 py-2 text-left text-[10px] font-black text-cyan-400 uppercase cursor-pointer hover:text-cyan-300"
              >
                <div className="flex items-center gap-1">
                  {t("rank")} <SortIcon field="rank" />
                </div>
              </th>
              <th
                onClick={() => onSort("win_rate")}
                className="px-2 py-2 text-center text-[10px] font-black text-cyan-400 uppercase cursor-pointer hover:text-cyan-300"
              >
                <div className="flex items-center justify-center gap-1">
                  {t("winRate")} <SortIcon field="win_rate" />
                </div>
              </th>
              <th
                onClick={() => onSort("kda")}
                className="px-2 py-2 text-center text-[10px] font-black text-cyan-400 uppercase cursor-pointer hover:text-cyan-300"
              >
                <div className="flex items-center justify-center gap-1">
                  {t("kda")} <SortIcon field="kda" />
                </div>
              </th>
              <th
                onClick={() => onSort("games_played")}
                className="px-2 py-2 text-center text-[10px] font-black text-cyan-400 uppercase cursor-pointer hover:text-cyan-300"
              >
                <div className="flex items-center justify-center gap-1">
                  {t("games")} <SortIcon field="games_played" />
                </div>
              </th>
              <th className="px-2 py-2 text-left text-[10px] font-black text-cyan-400 uppercase">
                {t("champions")}
              </th>
              <th
                onClick={() => onSort("talent_score")}
                className="px-2 py-2 text-center text-[10px] font-black text-yellow-400 uppercase cursor-pointer hover:text-yellow-300"
              >
                <div className="flex items-center justify-center gap-1">
                  {t("talent")} <SortIcon field="talent_score" />
                </div>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/50">
            {players.map((player, idx) => (
              <tr
                key={player.id}
                className="hover:bg-cyan-600/5 transition-colors border-l-2 border-transparent hover:border-cyan-600"
              >
                <td className="px-2 py-2 text-slate-500 font-bold">{idx + 1}</td>
                <td className="px-2 py-2">
                  <div className="flex items-center gap-2">
                    {player.avatar_url && (
                      <img
                        src={player.avatar_url}
                        alt={player.nickname}
                        className="w-6 h-6 rounded-full border border-slate-600"
                      />
                    )}
                    <span className="text-white font-bold font-cjk">
                      {player.nickname}
                    </span>
                    {player.is_verified && (
                      <span className="text-green-400 text-[10px]">✓</span>
                    )}
                  </div>
                </td>
                <td className="px-2 py-2 text-slate-300 font-semibold">
                  {player.country_code}
                </td>
                <td className="px-2 py-2 text-cyan-300 font-bold">
                  {player.rank}
                </td>
                <td className="px-2 py-2 text-center">
                  <span
                    className={twMerge(
                      "font-black text-sm",
                      player.win_rate && player.win_rate >= 55
                        ? "text-green-400"
                        : player.win_rate && player.win_rate >= 50
                        ? "text-yellow-400"
                        : "text-red-400"
                    )}
                  >
                    {player.win_rate ? `${player.win_rate.toFixed(1)}%` : "—"}
                  </span>
                </td>
                <td className="px-2 py-2 text-center">
                  <span className="text-purple-400 font-black text-sm">
                    {player.kda ? player.kda.toFixed(2) : "—"}
                  </span>
                </td>
                <td className="px-2 py-2 text-center text-slate-300 font-semibold">
                  {player.games_played || "—"}
                </td>
                <td className="px-2 py-2">
                  <div className="flex gap-1">
                    {player.top_champions?.slice(0, 3).map((champ, idx) => (
                      <span
                        key={idx}
                        className="text-[9px] text-cyan-300 bg-slate-800/70 px-1.5 py-0.5 rounded font-bold"
                      >
                        {champ}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="px-2 py-2 text-center">
                  {player.talent_score ? (
                    <span className="text-yellow-400 font-black text-sm">
                      {player.talent_score.toFixed(0)}
                    </span>
                  ) : (
                    <span className="text-slate-600">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/**
 * Japan Minimalist View Component
 * Diseño limpio con mucho espacio en blanco
 * Tooltips explicativos para generar confianza
 */
interface JapanMinimalistViewProps {
  players: SilverPlayer[];
}

function JapanMinimalistView({ players }: JapanMinimalistViewProps) {
  const t = useTranslations("minimal");
  const [hoveredMetric, setHoveredMetric] = useState<string | null>(null);

  return (
    <div className="space-y-12">
      {players.map((player) => (
        <div
          key={player.id}
          className="bg-white/[0.02] backdrop-blur-sm border border-slate-800/30 rounded-3xl p-12 hover:border-slate-700/50 transition-all duration-500"
        >
          {/* Header minimalista */}
          <div className="flex items-center justify-between mb-12">
            <div>
              <h3 className="text-4xl font-light text-white mb-3 font-cjk">
                {player.nickname}
              </h3>
              {player.real_name && (
                <p className="text-slate-400 text-lg font-light">
                  {player.real_name}
                </p>
              )}
            </div>
            {player.is_verified && (
              <div className="bg-green-500/10 border border-green-500/30 text-green-400 text-sm px-6 py-3 rounded-full font-medium">
                ✓ {t("verified")}
              </div>
            )}
          </div>

          {/* Métricas con tooltips */}
          <div className="grid grid-cols-4 gap-8 mb-12">
            {/* Talent Score */}
            <MetricCard
              icon={<Trophy className="w-6 h-6" />}
              label={t("talentScore")}
              value={player.talent_score ? player.talent_score.toFixed(0) : "—"}
              tooltip={t("talentScoreTooltip")}
              color="yellow"
            />

            {/* Win Rate */}
            <MetricCard
              icon={<Target className="w-6 h-6" />}
              label={t("winRate")}
              value={player.win_rate ? `${player.win_rate.toFixed(1)}%` : "—"}
              tooltip={t("winRateTooltip")}
              color="green"
            />

            {/* KDA */}
            <MetricCard
              icon={<Zap className="w-6 h-6" />}
              label={t("kda")}
              value={player.kda ? player.kda.toFixed(2) : "—"}
              tooltip={t("kdaTooltip")}
              color="purple"
            />

            {/* Games */}
            <MetricCard
              icon={<TrendingUp className="w-6 h-6" />}
              label={t("gamesPlayed")}
              value={player.games_played?.toString() || "—"}
              tooltip={t("gamesTooltip")}
              color="blue"
            />
          </div>

          {/* Información adicional */}
          <div className="flex items-center justify-between pt-8 border-t border-slate-800/30">
            <div className="flex items-center gap-8">
              <div>
                <p className="text-slate-500 text-xs uppercase tracking-wider mb-1">
                  {t("rank")}
                </p>
                <p className="text-white text-xl font-medium">{player.rank}</p>
              </div>
              <div>
                <p className="text-slate-500 text-xs uppercase tracking-wider mb-1">
                  {t("region")}
                </p>
                <p className="text-white text-xl font-medium">
                  {player.region} • {player.country_code}
                </p>
              </div>
            </div>

            {player.profile_url && (
              <a
                href={player.profile_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-3 bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 text-white px-8 py-4 rounded-2xl transition-all font-medium"
              >
                <span>{t("viewProfile")}</span>
                <ExternalLink className="w-5 h-5" />
              </a>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

/**
 * MetricCard con tooltip para vista minimalista japonesa
 */
interface MetricCardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  tooltip: string;
  color: "yellow" | "green" | "purple" | "blue";
}

function MetricCard({ icon, label, value, tooltip, color }: MetricCardProps) {
  const [showTooltip, setShowTooltip] = useState(false);

  const colorClasses = {
    yellow: "text-yellow-400 border-yellow-400/20 hover:border-yellow-400/40",
    green: "text-green-400 border-green-400/20 hover:border-green-400/40",
    purple: "text-purple-400 border-purple-400/20 hover:border-purple-400/40",
    blue: "text-blue-400 border-blue-400/20 hover:border-blue-400/40",
  };

  return (
    <div
      className={twMerge(
        "relative bg-white/[0.02] border rounded-2xl p-6 transition-all duration-300",
        colorClasses[color]
      )}
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      {/* Tooltip */}
      {showTooltip && (
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-3 w-64 bg-slate-900 border border-slate-700 rounded-xl p-4 shadow-2xl z-50">
          <div className="flex items-start gap-2">
            <Info className="w-4 h-4 text-cyan-400 mt-0.5 flex-shrink-0" />
            <p className="text-slate-300 text-xs leading-relaxed">{tooltip}</p>
          </div>
          <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-px">
            <div className="border-8 border-transparent border-t-slate-900" />
          </div>
        </div>
      )}

      <div className={twMerge("mb-3", `text-${color}-400`)}>{icon}</div>
      <p className="text-slate-400 text-xs uppercase tracking-wider mb-2">
        {label}
      </p>
      <p className={twMerge("text-3xl font-light", `text-${color}-400`)}>
        {value}
      </p>
    </div>
  );
}

/**
 * Legacy Components (mantener compatibilidad)
 */
interface MobileCardsProps {
  players: SilverPlayer[];
}

function MobileCards({ players }: MobileCardsProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {players.map((player) => (
        <div
          key={player.id}
          className="bg-slate-800/40 backdrop-blur-sm border border-slate-700/50 rounded-xl overflow-hidden hover:border-cyan-500/50 transition-all hover:shadow-xl hover:shadow-cyan-500/10"
        >
          {/* Player Header */}
          <div className="bg-gradient-to-br from-cyan-600 to-blue-600 p-6 text-center relative">
            {player.is_verified && (
              <div className="absolute top-2 right-2">
                <div className="bg-green-500 text-white text-xs px-2 py-1 rounded-full font-bold">
                  ✓ Verified
                </div>
              </div>
            )}
            
            {/* Avatar */}
            <div className="w-20 h-20 mx-auto mb-3 rounded-full border-4 border-white/20 overflow-hidden bg-slate-900">
              {player.avatar_url ? (
                <img
                  src={player.avatar_url}
                  alt={player.nickname}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-3xl font-bold text-white">
                  {player.nickname.charAt(0).toUpperCase()}
                </div>
              )}
            </div>

            {/* Nickname with CJK/Devanagari support */}
            <h3 className="text-xl font-bold text-white mb-1 font-cjk">
              {player.nickname}
            </h3>
            {player.real_name && (
              <p className="text-cyan-100 text-sm font-devanagari">
                {player.real_name}
              </p>
            )}
          </div>

          {/* Player Stats */}
          <div className="p-5 space-y-4">
            {/* Rank & Region */}
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-xs uppercase">Rank</p>
                <p className="text-white font-bold text-lg">{player.rank}</p>
              </div>
              <div className="text-right">
                <p className="text-slate-400 text-xs uppercase">Region</p>
                <p className="text-white font-bold text-lg">
                  {player.region} • {player.country_code}
                </p>
              </div>
            </div>

            {/* Win Rate & KDA */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-slate-900/50 rounded-lg p-3 text-center">
                <p className="text-slate-400 text-xs mb-1">Win Rate</p>
                <p className="text-2xl font-bold text-green-400">
                  {player.win_rate ? `${player.win_rate.toFixed(1)}%` : "N/A"}
                </p>
              </div>
              <div className="bg-slate-900/50 rounded-lg p-3 text-center">
                <p className="text-slate-400 text-xs mb-1">KDA</p>
                <p className="text-2xl font-bold text-purple-400">
                  {player.kda ? player.kda.toFixed(2) : "N/A"}
                </p>
              </div>
            </div>

            {/* Talent Score */}
            {player.talent_score && (
              <div className="bg-gradient-to-r from-yellow-600/20 to-orange-600/20 border border-yellow-600/30 rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <span className="text-yellow-400 text-sm font-medium">
                    Talent Score
                  </span>
                  <span className="text-yellow-300 text-2xl font-bold">
                    {player.talent_score.toFixed(0)}
                  </span>
                </div>
              </div>
            )}

            {/* Top Champions */}
            {player.top_champions && player.top_champions.length > 0 && (
              <div>
                <p className="text-slate-400 text-xs uppercase mb-2">
                  Top Champions
                </p>
                <div className="flex flex-wrap gap-2">
                  {player.top_champions.slice(0, 3).map((champ, idx) => (
                    <span
                      key={idx}
                      className="bg-slate-700/50 text-slate-300 text-xs px-2 py-1 rounded-full"
                    >
                      {champ}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="space-y-2 pt-2">
              {player.profile_url && (
                <a
                  href={player.profile_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-full flex items-center justify-center gap-2 bg-cyan-600 hover:bg-cyan-700 text-white font-medium py-3 rounded-lg transition-colors"
                >
                  <ExternalLink className="w-4 h-4" />
                  Ver Perfil
                </a>
              )}
              
              {/* WhatsApp Contact (para mobile-heavy regions) */}
              {player.is_mobile_heavy && (
                <button className="w-full flex items-center justify-center gap-2 bg-green-600 hover:bg-green-700 text-white font-medium py-3 rounded-lg transition-colors">
                  <Phone className="w-4 h-4" />
                  Contactar WhatsApp
                </button>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

/**
 * Data Table Component
 * Para regiones de alta densidad (Corea, China, Japón)
 * Tabla compacta con muchas columnas
 */
interface DataTableProps {
  players: SilverPlayer[];
  sortField: keyof SilverPlayer;
  sortDirection: "asc" | "desc";
  onSort: (field: keyof SilverPlayer) => void;
}

function DataTable({
  players,
  sortField,
  sortDirection,
  onSort,
}: DataTableProps) {
  const SortIcon = ({ field }: { field: keyof SilverPlayer }) => {
    if (sortField !== field) return null;
    return sortDirection === "asc" ? (
      <ChevronUp className="w-4 h-4" />
    ) : (
      <ChevronDown className="w-4 h-4" />
    );
  };

  return (
    <div className="bg-slate-800/30 backdrop-blur-sm border border-slate-700/50 rounded-xl overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-900/50 border-b border-slate-700">
            <tr>
              <th className="px-3 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">
                #
              </th>
              <th
                onClick={() => onSort("nickname")}
                className="px-3 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider cursor-pointer hover:text-cyan-400 transition-colors"
              >
                <div className="flex items-center gap-1">
                  Nickname <SortIcon field="nickname" />
                </div>
              </th>
              <th
                onClick={() => onSort("country_code")}
                className="px-3 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider cursor-pointer hover:text-cyan-400 transition-colors"
              >
                <div className="flex items-center gap-1">
                  Country <SortIcon field="country_code" />
                </div>
              </th>
              <th
                onClick={() => onSort("rank")}
                className="px-3 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider cursor-pointer hover:text-cyan-400 transition-colors"
              >
                <div className="flex items-center gap-1">
                  Rank <SortIcon field="rank" />
                </div>
              </th>
              <th
                onClick={() => onSort("win_rate")}
                className="px-3 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider cursor-pointer hover:text-cyan-400 transition-colors"
              >
                <div className="flex items-center gap-1">
                  WR% <SortIcon field="win_rate" />
                </div>
              </th>
              <th
                onClick={() => onSort("kda")}
                className="px-3 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider cursor-pointer hover:text-cyan-400 transition-colors"
              >
                <div className="flex items-center gap-1">
                  KDA <SortIcon field="kda" />
                </div>
              </th>
              <th
                onClick={() => onSort("games_played")}
                className="px-3 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider cursor-pointer hover:text-cyan-400 transition-colors"
              >
                <div className="flex items-center gap-1">
                  Games <SortIcon field="games_played" />
                </div>
              </th>
              <th className="px-3 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Main Role
              </th>
              <th className="px-3 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Top Champions
              </th>
              <th
                onClick={() => onSort("talent_score")}
                className="px-3 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider cursor-pointer hover:text-cyan-400 transition-colors"
              >
                <div className="flex items-center gap-1">
                  Talent <SortIcon field="talent_score" />
                </div>
              </th>
              <th className="px-3 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700/30">
            {players.map((player, idx) => (
              <tr
                key={player.id}
                className="hover:bg-slate-700/20 transition-colors"
              >
                <td className="px-3 py-3 text-slate-400">{idx + 1}</td>
                <td className="px-3 py-3">
                  <div className="flex items-center gap-2">
                    {player.avatar_url && (
                      <img
                        src={player.avatar_url}
                        alt={player.nickname}
                        className="w-8 h-8 rounded-full"
                      />
                    )}
                    <div>
                      <p className="text-white font-medium font-cjk">
                        {player.nickname}
                      </p>
                      {player.is_verified && (
                        <span className="text-green-400 text-xs">✓</span>
                      )}
                    </div>
                  </div>
                </td>
                <td className="px-3 py-3 text-slate-300">
                  {player.country_code}
                </td>
                <td className="px-3 py-3">
                  <span className="text-cyan-400 font-semibold">
                    {player.rank}
                  </span>
                </td>
                <td className="px-3 py-3">
                  <span
                    className={twMerge(
                      "font-semibold",
                      player.win_rate && player.win_rate >= 55
                        ? "text-green-400"
                        : player.win_rate && player.win_rate >= 50
                        ? "text-yellow-400"
                        : "text-red-400"
                    )}
                  >
                    {player.win_rate ? `${player.win_rate.toFixed(1)}%` : "—"}
                  </span>
                </td>
                <td className="px-3 py-3">
                  <span className="text-purple-400 font-semibold">
                    {player.kda ? player.kda.toFixed(2) : "—"}
                  </span>
                </td>
                <td className="px-3 py-3 text-slate-300">
                  {player.games_played || "—"}
                </td>
                <td className="px-3 py-3">
                  <span className="bg-slate-700/50 text-slate-300 text-xs px-2 py-1 rounded">
                    {player.main_role || "—"}
                  </span>
                </td>
                <td className="px-3 py-3">
                  <div className="flex flex-wrap gap-1">
                    {player.top_champions?.slice(0, 2).map((champ, idx) => (
                      <span
                        key={idx}
                        className="text-xs text-slate-400 bg-slate-800/50 px-1.5 py-0.5 rounded"
                      >
                        {champ}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="px-3 py-3">
                  {player.talent_score ? (
                    <div className="flex items-center gap-1">
                      <Trophy className="w-4 h-4 text-yellow-400" />
                      <span className="text-yellow-400 font-bold">
                        {player.talent_score.toFixed(0)}
                      </span>
                    </div>
                  ) : (
                    <span className="text-slate-500">—</span>
                  )}
                </td>
                <td className="px-3 py-3">
                  {player.profile_url && (
                    <a
                      href={player.profile_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-cyan-400 hover:text-cyan-300 transition-colors"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
