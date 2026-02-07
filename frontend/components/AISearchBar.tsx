"use client";

/**
 * AI-Powered Semantic Search Bar
 * Búsqueda inteligente con embeddings semánticos
 * 
 * Características:
 * - Placeholder localizado según idioma (Hindi, Coreano, Vietnamita, etc.)
 * - Resultados adaptativos según región:
 *   → India/Vietnam: Mobile Cards con neón
 *   → Corea/Japón: Lista técnica compacta
 * - Animaciones suaves con Framer Motion
 * - Dark mode elegante
 * - Integración con OpenAI embeddings + Supabase match_players()
 */

import { useState, useRef, useEffect } from "react";
import { useTranslations, useLocale } from "next-intl";
import { motion, AnimatePresence } from "framer-motion";
import {
  Sparkles,
  Search,
  Loader2,
  TrendingUp,
  MapPin,
  Trophy,
  Zap,
  X,
  ExternalLink,
  MessageCircle,
} from "lucide-react";
import { useCountryDetection } from "@/hooks/useCountryDetection";

// Tipos
interface SearchResult {
  player_id: string;
  handle: string;
  gameradar_score: number;
  similarity: number;
  // Metadata adicional (se puede enriquecer con JOIN)
  country?: string;
  region?: string;
  rank?: string;
  win_rate?: number;
  kda?: number;
  avatar_url?: string;
  profile_url?: string;
}

interface AISearchBarProps {
  supabaseUrl: string;
  supabaseKey: string;
  openaiApiKey?: string; // Opcional: si se hace desde backend
  onResultsChange?: (results: SearchResult[]) => void;
  regionFilter?: string; // Filtro opcional por región
  className?: string;
}

export default function AISearchBar({
  supabaseUrl,
  supabaseKey,
  openaiApiKey,
  onResultsChange,
  regionFilter,
  className = "",
}: AISearchBarProps) {
  const t = useTranslations("search");
  const locale = useLocale();
  const { countryCode } = useCountryDetection();

  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const searchRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Determinar vista según región
  const isMobileHeavy = ["IN", "VN", "TH", "PH", "ID"].includes(countryCode);
  const isTechnical = ["KR", "CN", "JP"].includes(countryCode);

  // Cerrar resultados al hacer clic fuera
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Búsqueda semántica
  const handleSearch = async () => {
    if (!query.trim() || query.length < 3) {
      setError(t("errorMinLength"));
      return;
    }

    setIsSearching(true);
    setError(null);

    try {
      // TODO: En producción, esto debe hacerse desde el backend
      // Para evitar exponer la API key de OpenAI en el cliente
      
      // Opción 1: Backend API route (recomendado)
      const response = await fetch("/api/semantic-search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query,
          region_filter: regionFilter,
          match_threshold: 0.7,
          match_count: 20,
        }),
      });

      if (!response.ok) {
        throw new Error("Search failed");
      }

      const data = await response.json();
      setResults(data.results || []);
      setIsOpen(true);

      if (onResultsChange) {
        onResultsChange(data.results || []);
      }
    } catch (err) {
      console.error("Search error:", err);
      setError(t("errorSearch"));
      setResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSearch();
    } else if (e.key === "Escape") {
      setIsOpen(false);
      setQuery("");
    }
  };

  const clearSearch = () => {
    setQuery("");
    setResults([]);
    setIsOpen(false);
    setError(null);
    inputRef.current?.focus();
  };

  return (
    <div ref={searchRef} className={`relative w-full max-w-2xl ${className}`}>
      {/* Search Input */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative"
      >
        {/* AI Sparkle Icon */}
        <div className="absolute left-4 top-1/2 -translate-y-1/2 z-10">
          <motion.div
            animate={{
              rotate: [0, 10, -10, 0],
              scale: [1, 1.1, 1],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          >
            <Sparkles className="w-5 h-5 text-cyan-400" />
          </motion.div>
        </div>

        {/* Input Field */}
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => results.length > 0 && setIsOpen(true)}
          placeholder={t("placeholder")}
          className={`
            w-full h-14 pl-14 pr-28
            bg-slate-900/80 backdrop-blur-sm
            border-2 border-slate-700/50
            rounded-2xl
            text-white placeholder:text-slate-500
            focus:outline-none focus:border-cyan-500/50
            focus:ring-2 focus:ring-cyan-500/20
            transition-all duration-300
            ${locale === "hi" ? "font-devanagari" : ""}
            ${["ko", "ja", "zh"].includes(locale) ? "font-cjk" : ""}
          `}
        />

        {/* Clear Button */}
        {query && (
          <motion.button
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            exit={{ scale: 0 }}
            onClick={clearSearch}
            className="absolute right-20 top-1/2 -translate-y-1/2
              w-8 h-8 rounded-full
              bg-slate-700/50 hover:bg-slate-600/50
              flex items-center justify-center
              transition-colors"
          >
            <X className="w-4 h-4 text-slate-400" />
          </motion.button>
        )}

        {/* Search Button */}
        <button
          onClick={handleSearch}
          disabled={isSearching || query.length < 3}
          className="absolute right-2 top-1/2 -translate-y-1/2
            h-10 px-5
            bg-gradient-to-r from-cyan-500 to-blue-600
            hover:from-cyan-400 hover:to-blue-500
            disabled:from-slate-700 disabled:to-slate-600
            disabled:cursor-not-allowed
            rounded-xl
            font-semibold text-white text-sm
            transition-all duration-300
            flex items-center gap-2"
        >
          {isSearching ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              {t("searching")}
            </>
          ) : (
            <>
              <Search className="w-4 h-4" />
              {t("search")}
            </>
          )}
        </button>
      </motion.div>

      {/* Error Message */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-2 px-4 py-2 bg-red-500/10 border border-red-500/30 rounded-lg"
        >
          <p className="text-red-400 text-sm">{error}</p>
        </motion.div>
      )}

      {/* Results Dropdown */}
      <AnimatePresence>
        {isOpen && results.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
            className="absolute top-full mt-2 w-full
              bg-slate-900/95 backdrop-blur-md
              border border-slate-700/50
              rounded-2xl
              shadow-2xl shadow-cyan-500/10
              overflow-hidden
              z-50"
          >
            {/* Results Header */}
            <div className="px-4 py-3 border-b border-slate-700/50
              flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-cyan-400" />
                <span className="text-sm font-semibold text-slate-300">
                  {t("resultsFound", { count: results.length })}
                </span>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Results List - Adaptive Rendering */}
            <div className="max-h-[600px] overflow-y-auto custom-scrollbar">
              {isMobileHeavy ? (
                <MobileHeavyResults results={results} locale={locale} t={t} />
              ) : isTechnical ? (
                <TechnicalResults results={results} locale={locale} t={t} />
              ) : (
                <TechnicalResults results={results} locale={locale} t={t} />
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Empty State */}
      {isOpen && results.length === 0 && !isSearching && query.length >= 3 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="absolute top-full mt-2 w-full
            bg-slate-900/95 backdrop-blur-md
            border border-slate-700/50
            rounded-2xl
            p-8
            text-center"
        >
          <Search className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <p className="text-slate-400">{t("noResults")}</p>
          <p className="text-slate-500 text-sm mt-1">{t("tryDifferent")}</p>
        </motion.div>
      )}
    </div>
  );
}

// ============================================================
// MOBILE-HEAVY RESULTS (India/Vietnam) - Neón y Cards grandes
// ============================================================
function MobileHeavyResults({
  results,
  locale,
  t,
}: {
  results: SearchResult[];
  locale: string;
  t: any;
}) {
  return (
    <div className="p-2 space-y-2">
      {results.map((player, index) => (
        <motion.div
          key={player.player_id}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: index * 0.05 }}
          className="p-4 bg-gradient-to-br from-slate-800/50 to-slate-900/50
            hover:from-slate-700/50 hover:to-slate-800/50
            border border-slate-700/30
            rounded-xl
            transition-all duration-300
            cursor-pointer
            group"
        >
          <div className="flex items-start gap-4">
            {/* Avatar */}
            <div className="relative">
              {player.avatar_url ? (
                <img
                  src={player.avatar_url}
                  alt={player.handle}
                  className="w-16 h-16 rounded-xl object-cover"
                />
              ) : (
                <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600
                  flex items-center justify-center">
                  <span className="text-2xl font-bold text-white">
                    {player.handle[0].toUpperCase()}
                  </span>
                </div>
              )}
              {/* Similarity Badge - NEÓN */}
              <div className="absolute -top-1 -right-1
                bg-gradient-to-r from-pink-500 via-purple-500 to-cyan-500
                text-white text-[10px] font-bold
                px-2 py-0.5 rounded-full
                shadow-lg shadow-purple-500/50">
                {Math.round(player.similarity * 100)}%
              </div>
            </div>

            {/* Info */}
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <h3 className={`font-bold text-lg text-white truncate
                    ${locale === "hi" ? "font-devanagari" : ""}`}>
                    {player.handle}
                  </h3>
                  {player.region && (
                    <div className="flex items-center gap-1 text-slate-400 text-sm mt-1">
                      <MapPin className="w-3 h-3" />
                      <span>{player.region}</span>
                      {player.rank && <span>• {player.rank}</span>}
                    </div>
                  )}
                </div>

                {/* GameRadar Score - NEÓN PROMINENTE */}
                <motion.div
                  whileHover={{ scale: 1.05 }}
                  className="flex flex-col items-center
                    bg-gradient-to-br from-green-500 via-emerald-500 to-teal-500
                    rounded-xl px-3 py-2
                    shadow-lg shadow-green-500/50">
                  <Trophy className="w-4 h-4 text-white mb-1" />
                  <span className="text-2xl font-black text-white">
                    {Math.round(player.gameradar_score)}
                  </span>
                  <span className="text-[10px] font-semibold text-white/80">
                    {t("gameRadarScore")}
                  </span>
                </motion.div>
              </div>

              {/* Stats Row */}
              <div className="flex gap-3 mt-3">
                {player.win_rate && (
                  <div className="flex items-center gap-1 text-sm">
                    <TrendingUp className="w-3 h-3 text-green-400" />
                    <span className="text-slate-300">
                      {player.win_rate.toFixed(1)}%
                    </span>
                  </div>
                )}
                {player.kda && (
                  <div className="flex items-center gap-1 text-sm">
                    <Zap className="w-3 h-3 text-yellow-400" />
                    <span className="text-slate-300">
                      {player.kda.toFixed(2)} KDA
                    </span>
                  </div>
                )}
              </div>

              {/* Action Buttons - WhatsApp/Zalo prominent */}
              <div className="flex gap-2 mt-3">
                <button
                  className="flex-1 py-2 px-3
                    bg-green-600 hover:bg-green-500
                    rounded-lg
                    flex items-center justify-center gap-2
                    text-white text-sm font-semibold
                    transition-colors">
                  <MessageCircle className="w-4 h-4" />
                  {player.country === "VN" ? "Zalo" : "WhatsApp"}
                </button>
                {player.profile_url && (
                  <button
                    className="py-2 px-3
                      bg-slate-700/50 hover:bg-slate-600/50
                      rounded-lg
                      flex items-center justify-center
                      transition-colors">
                    <ExternalLink className="w-4 h-4 text-slate-300" />
                  </button>
                )}
              </div>
            </div>
          </div>
        </motion.div>
      ))}
    </div>
  );
}

// ============================================================
// TECHNICAL RESULTS (Korea/Japan) - Lista compacta
// ============================================================
function TechnicalResults({
  results,
  locale,
  t,
}: {
  results: SearchResult[];
  locale: string;
  t: any;
}) {
  return (
    <div className="divide-y divide-slate-700/30">
      {results.map((player, index) => (
        <motion.div
          key={player.player_id}
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: index * 0.03 }}
          className="px-4 py-3
            hover:bg-slate-800/30
            transition-colors
            cursor-pointer
            group"
        >
          <div className="flex items-center gap-4">
            {/* Avatar Small */}
            {player.avatar_url ? (
              <img
                src={player.avatar_url}
                alt={player.handle}
                className="w-10 h-10 rounded-lg object-cover"
              />
            ) : (
              <div className="w-10 h-10 rounded-lg bg-slate-700
                flex items-center justify-center">
                <span className="text-sm font-bold text-slate-400">
                  {player.handle[0].toUpperCase()}
                </span>
              </div>
            )}

            {/* Info - Compact */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <h3 className={`font-semibold text-white truncate
                  ${["ko", "ja", "zh"].includes(locale) ? "font-cjk" : ""}`}>
                  {player.handle}
                </h3>
                {player.region && (
                  <span className="text-xs text-slate-500">
                    {player.region}
                  </span>
                )}
              </div>

              {/* Stats Inline */}
              <div className="flex items-center gap-3 mt-1 text-xs text-slate-400">
                <span className="flex items-center gap-1">
                  <Trophy className="w-3 h-3 text-cyan-400" />
                  {Math.round(player.gameradar_score)}
                </span>
                {player.win_rate && (
                  <span>{player.win_rate.toFixed(1)}% WR</span>
                )}
                {player.kda && <span>{player.kda.toFixed(2)} KDA</span>}
                <span className="text-cyan-400 font-semibold">
                  {Math.round(player.similarity * 100)}%
                </span>
              </div>
            </div>

            {/* Quick Action */}
            {player.profile_url && (
              <a
                href={player.profile_url}
                target="_blank"
                rel="noopener noreferrer"
                className="opacity-0 group-hover:opacity-100
                  transition-opacity
                  p-2 rounded-lg
                  hover:bg-slate-700/50">
                <ExternalLink className="w-4 h-4 text-slate-400" />
              </a>
            )}
          </div>
        </motion.div>
      ))}
    </div>
  );
}
