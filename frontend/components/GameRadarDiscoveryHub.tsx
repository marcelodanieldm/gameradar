"use client";

/**
 * GameRadar Discovery Hub - Módulo Central
 * Interfaz híbrida que cambia dinámicamente según el mercado
 * 
 * Módulos:
 * - Street Scout (India/Vietnam): Viralidad y facilidad
 * - Elite Analyst (Corea/China/Japón): Precisión y comparación
 */

import { useState, useEffect } from "react";
import { useTranslations } from "next-intl";
import { motion, AnimatePresence } from "framer-motion";
import {
  Flame,
  GitCompare,
  Globe,
  Settings,
  RefreshCw,
} from "lucide-react";
import { createClient } from "@supabase/supabase-js";
import { useCountryDetection } from "@/hooks/useCountryDetection";

import StreetScoutView from "./StreetScoutView";
import EliteAnalystView from "./EliteAnalystView";

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
  talent_score: number | null;
  games_played: number | null;
  top_champions: string[] | null;
  avatar_url: string | null;
  profile_url: string | null;
  is_trending?: boolean;
  score_change?: number;
}

interface GameRadarDiscoveryHubProps {
  supabaseUrl: string;
  supabaseKey: string;
  initialPlayers?: Player[];
  pageSize?: number;
}

type ViewMode = "auto" | "street" | "elite";

export default function GameRadarDiscoveryHub({
  supabaseUrl,
  supabaseKey,
  initialPlayers = [],
  pageSize = 20,
}: GameRadarDiscoveryHubProps) {
  const t = useTranslations("discoveryHub");
  const { countryCode, isLoading: countryLoading } = useCountryDetection();

  const [players, setPlayers] = useState<Player[]>(initialPlayers);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  
  const [viewMode, setViewMode] = useState<ViewMode>("auto");
  const [manualOverride, setManualOverride] = useState(false);

  const supabase = createClient(supabaseUrl, supabaseKey);

  // Determinar vista según región
  const isMobileHeavy = ["IN", "VN", "TH", "PH", "ID"].includes(countryCode);
  const isElite = ["KR", "CN", "JP"].includes(countryCode);

  const effectiveViewMode =
    viewMode === "auto"
      ? isMobileHeavy
        ? "street"
        : "elite"
      : viewMode;

  // Cargar jugadores iniciales
  useEffect(() => {
    if (initialPlayers.length === 0) {
      loadPlayers();
    }
  }, []);

  const loadPlayers = async (reset = false) => {
    if (isLoading) return;

    setIsLoading(true);
    setError(null);

    try {
      const currentPage = reset ? 0 : page;
      const offset = currentPage * pageSize;

      // Query con trending logic
      const { data, error: queryError } = await supabase
        .from("silver_players")
        .select(`
          id,
          player_id:id,
          nickname,
          country_code:country,
          region,
          game,
          rank,
          win_rate:stats->win_rate,
          kda:stats->kda,
          games_played:stats->games_analyzed,
          top_champions,
          avatar_url,
          profile_url,
          talent_score
        `)
        .order("talent_score", { ascending: false, nullsFirst: false })
        .range(offset, offset + pageSize - 1);

      if (queryError) throw queryError;

      // Enriquecer con GameRadar Score de gold_analytics
      const enrichedPlayers = await Promise.all(
        (data || []).map(async (player: any) => {
          const { data: goldData } = await supabase
            .from("gold_analytics")
            .select("gameradar_score, last_updated")
            .eq("player_id", player.player_id)
            .order("calculation_date", { ascending: false })
            .limit(1)
            .single();

          // Simular trending (score_change)
          // En producción, esto vendría de un histórico real
          const score_change = Math.random() > 0.7 ? Math.floor(Math.random() * 15) : 0;
          const is_trending = score_change > 5;

          return {
            ...player,
            gameradar_score: goldData?.gameradar_score || null,
            is_trending,
            score_change,
          };
        })
      );

      if (reset) {
        setPlayers(enrichedPlayers);
        setPage(1);
      } else {
        setPlayers((prev) => [...prev, ...enrichedPlayers]);
        setPage((prev) => prev + 1);
      }

      setHasMore(enrichedPlayers.length === pageSize);
    } catch (err) {
      console.error("Error loading players:", err);
      setError(err instanceof Error ? err.message : "Failed to load players");
    } finally {
      setIsLoading(false);
    }
  };

  const handleLoadMore = () => {
    loadPlayers(false);
  };

  const handleRefresh = () => {
    loadPlayers(true);
  };

  const handleViewModeChange = (mode: ViewMode) => {
    setViewMode(mode);
    setManualOverride(mode !== "auto");
  };

  if (countryLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-950">
        <div className="text-center">
          <Globe className="w-12 h-12 text-cyan-500 animate-spin mx-auto mb-4" />
          <p className="text-slate-400">{t("detectingRegion")}</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-950">
        <div className="text-center max-w-md">
          <div className="text-red-500 text-lg font-bold mb-2">
            {t("errorTitle")}
          </div>
          <p className="text-slate-400 mb-4">{error}</p>
          <button
            onClick={handleRefresh}
            className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 rounded-lg text-white font-semibold transition-colors"
          >
            {t("retry")}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950">
      {/* View Mode Selector (floating) */}
      <div className="fixed top-4 right-4 z-50">
        <div className="bg-slate-900/90 backdrop-blur-md rounded-xl border border-slate-800 p-2 shadow-2xl">
          <div className="flex gap-2">
            <ViewModeButton
              icon={<Globe className="w-4 h-4" />}
              label={t("autoMode")}
              active={viewMode === "auto"}
              onClick={() => handleViewModeChange("auto")}
            />
            <ViewModeButton
              icon={<Flame className="w-4 h-4" />}
              label={t("streetMode")}
              active={viewMode === "street"}
              onClick={() => handleViewModeChange("street")}
            />
            <ViewModeButton
              icon={<GitCompare className="w-4 h-4" />}
              label={t("eliteMode")}
              active={viewMode === "elite"}
              onClick={() => handleViewModeChange("elite")}
            />
          </div>

          {/* Region Info */}
          <div className="mt-2 pt-2 border-t border-slate-800">
            <div className="text-xs text-slate-400 text-center">
              {t("detectedRegion")}: <span className="text-cyan-400 font-semibold">{countryCode}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Refresh Button */}
      <button
        onClick={handleRefresh}
        disabled={isLoading}
        className="fixed bottom-6 right-6 z-40
          w-14 h-14 rounded-full
          bg-cyan-600 hover:bg-cyan-500
          disabled:bg-slate-700 disabled:cursor-not-allowed
          shadow-lg shadow-cyan-500/30
          flex items-center justify-center
          transition-all duration-300
          group"
      >
        <RefreshCw className={`w-6 h-6 text-white ${isLoading ? "animate-spin" : "group-hover:rotate-180 transition-transform duration-500"}`} />
      </button>

      {/* View Content */}
      <AnimatePresence mode="wait">
        {effectiveViewMode === "street" ? (
          <motion.div
            key="street"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            transition={{ duration: 0.3 }}
          >
            <StreetScoutView
              players={players}
              onLoadMore={handleLoadMore}
              hasMore={hasMore}
              isLoading={isLoading}
            />
          </motion.div>
        ) : (
          <motion.div
            key="elite"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
          >
            <EliteAnalystView players={players} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ============================================================
// VIEW MODE BUTTON
// ============================================================
function ViewModeButton({
  icon,
  label,
  active,
  onClick,
}: {
  icon: React.ReactNode;
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <motion.button
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onClick={onClick}
      className={`px-3 py-2 rounded-lg flex items-center gap-2 text-sm font-semibold transition-colors
        ${active
          ? "bg-cyan-600 text-white"
          : "bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-slate-300"
        }`}
      title={label}
    >
      {icon}
      <span className="hidden md:inline">{label}</span>
    </motion.button>
  );
}
