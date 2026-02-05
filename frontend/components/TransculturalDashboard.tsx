"use client";

/**
 * Transcultural Dashboard Component
 * Consume tabla silver_players y renderiza UI adaptativa según región
 * 
 * Lógica:
 * - is_mobile_heavy = true → Mobile Cards (India/Vietnam)
 * - region = KR/CN → Data Table de alta densidad
 * 
 * Usa lucide-react para iconos y tailwind-merge para clases dinámicas
 * Fuentes optimizadas para CJK (Chino/Coreano/Japonés) y Devanagari (Hindi)
 */

import { useEffect, useState } from "react";
import { createClient } from "@supabase/supabase-js";
import { twMerge } from "tailwind-merge";
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
} from "lucide-react";

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
  const [players, setPlayers] = useState<SilverPlayer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortField, setSortField] = useState<keyof SilverPlayer>("talent_score");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("desc");
  const [viewMode, setViewMode] = useState<"auto" | "cards" | "table">("auto");

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

  // Determine UI mode based on is_mobile_heavy
  const getModeForPlayer = (player: SilverPlayer): "cards" | "table" => {
    if (viewMode !== "auto") return viewMode;

    // Lógica de negocio: is_mobile_heavy → Cards
    if (player.is_mobile_heavy) return "cards";

    // Región KR/CN → Table
    if (["KR", "CN", "JP"].includes(player.region.toUpperCase())) {
      return "table";
    }

    // Default: Cards para regiones mobile-heavy (IN, VN, TH, etc.)
    return "cards";
  };

  // Determinar modo predominante en el dataset
  const predominantMode = (() => {
    if (viewMode !== "auto") return viewMode;

    const mobileHeavyCount = players.filter((p) => p.is_mobile_heavy).length;
    const totalCount = players.length;

    // Si más del 50% es mobile-heavy → Cards
    if (mobileHeavyCount > totalCount / 2) return "cards";

    // Si hay muchos KR/CN → Table
    const denseRegions = players.filter((p) =>
      ["KR", "CN", "JP"].includes(p.region.toUpperCase())
    ).length;
    if (denseRegions > totalCount / 2) return "table";

    // Default: Cards
    return "cards";
  })();

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
            Cargando jugadores...
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
                <span className="text-sm font-medium">Auto</span>
              </button>
              <button
                onClick={() => setViewMode("cards")}
                className={twMerge(
                  "px-3 py-2 rounded-md transition-all flex items-center gap-2",
                  viewMode === "cards"
                    ? "bg-cyan-600 text-white shadow-lg"
                    : "text-slate-400 hover:text-white"
                )}
              >
                <Smartphone className="w-4 h-4" />
                <span className="text-sm font-medium">Cards</span>
              </button>
              <button
                onClick={() => setViewMode("table")}
                className={twMerge(
                  "px-3 py-2 rounded-md transition-all flex items-center gap-2",
                  viewMode === "table"
                    ? "bg-cyan-600 text-white shadow-lg"
                    : "text-slate-400 hover:text-white"
                )}
              >
                <Monitor className="w-4 h-4" />
                <span className="text-sm font-medium">Table</span>
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
        {predominantMode === "cards" ? (
          <MobileCards players={sortedPlayers} />
        ) : (
          <DataTable
            players={sortedPlayers}
            sortField={sortField}
            sortDirection={sortDirection}
            onSort={handleSort}
          />
        )}
      </main>
    </div>
  );
}

/**
 * Mobile Cards Component
 * Para regiones mobile-heavy (India, Vietnam, Tailandia)
 * Cards grandes con botones de acción directos
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
