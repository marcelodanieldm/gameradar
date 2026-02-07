"use client";

/**
 * Elite Analyst View - Módulo Corea/China/Japón
 * Enfoque: Precisión y comparación
 * 
 * Características:
 * - Tablas de comparación lateral (A/B testing)
 * - Gráficos de radar para Hero Pool
 * - Exportar a PDF/CSV
 * - Diseño técnico y denso
 */

import { useState } from "react";
import { useTranslations, useLocale } from "next-intl";
import { motion } from "framer-motion";
import {
  GitCompare,
  Download,
  FileText,
  Table,
  BarChart3,
  TrendingUp,
  Trophy,
  Target,
  Award,
  Zap,
  Users,
  Check,
  X,
} from "lucide-react";
import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Legend,
} from "recharts";
import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";

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
}

interface EliteAnalystViewProps {
  players: Player[];
}

export default function EliteAnalystView({ players }: EliteAnalystViewProps) {
  const t = useTranslations("eliteAnalyst");
  const locale = useLocale();

  const [selectedPlayers, setSelectedPlayers] = useState<string[]>([]);
  const [viewMode, setViewMode] = useState<"comparison" | "table">("comparison");

  const togglePlayerSelection = (playerId: string) => {
    setSelectedPlayers((prev) =>
      prev.includes(playerId)
        ? prev.filter((id) => id !== playerId)
        : prev.length < 2
        ? [...prev, playerId]
        : [prev[1], playerId] // Máximo 2 jugadores
    );
  };

  const selectedPlayerData = players.filter((p) =>
    selectedPlayers.includes(p.player_id)
  );

  const exportToPDF = () => {
    const doc = new jsPDF();
    
    // Header
    doc.setFontSize(20);
    doc.text("GameRadar AI - Elite Analysis Report", 14, 20);
    doc.setFontSize(10);
    doc.text(`Generated: ${new Date().toLocaleDateString()}`, 14, 28);

    // Comparison Table
    if (selectedPlayerData.length === 2) {
      const comparisonData = [
        ["Metric", selectedPlayerData[0].nickname, selectedPlayerData[1].nickname],
        ["GameRadar Score", selectedPlayerData[0].gameradar_score || "-", selectedPlayerData[1].gameradar_score || "-"],
        ["Talent Score", selectedPlayerData[0].talent_score || "-", selectedPlayerData[1].talent_score || "-"],
        ["Win Rate", `${(selectedPlayerData[0].win_rate || 0).toFixed(1)}%`, `${(selectedPlayerData[1].win_rate || 0).toFixed(1)}%`],
        ["KDA", (selectedPlayerData[0].kda || 0).toFixed(2), (selectedPlayerData[1].kda || 0).toFixed(2)],
        ["Games Played", selectedPlayerData[0].games_played || "-", selectedPlayerData[1].games_played || "-"],
        ["Rank", selectedPlayerData[0].rank, selectedPlayerData[1].rank],
        ["Region", selectedPlayerData[0].region, selectedPlayerData[1].region],
      ];

      autoTable(doc, {
        head: [comparisonData[0]],
        body: comparisonData.slice(1),
        startY: 35,
        theme: "grid",
        headStyles: { fillColor: [6, 182, 212] },
      });
    }

    // All Players Table
    const playersData = players.map((p) => [
      p.nickname,
      p.region,
      p.rank,
      Math.round(p.gameradar_score || 0),
      `${(p.win_rate || 0).toFixed(1)}%`,
      (p.kda || 0).toFixed(2),
    ]);

    autoTable(doc, {
      head: [["Nickname", "Region", "Rank", "Score", "WR%", "KDA"]],
      body: playersData,
      startY: selectedPlayerData.length === 2 ? (doc as any).lastAutoTable.finalY + 10 : 35,
      theme: "striped",
      headStyles: { fillColor: [100, 116, 139] },
    });

    doc.save("gameradar-elite-analysis.pdf");
  };

  const exportToCSV = () => {
    const headers = ["Nickname", "Region", "Game", "Rank", "GameRadar Score", "Talent Score", "Win Rate", "KDA", "Games Played"];
    const rows = players.map((p) => [
      p.nickname,
      p.region,
      p.game,
      p.rank,
      p.gameradar_score || 0,
      p.talent_score || 0,
      (p.win_rate || 0).toFixed(1),
      (p.kda || 0).toFixed(2),
      p.games_played || 0,
    ]);

    const csvContent = [
      headers.join(","),
      ...rows.map((row) => row.join(",")),
    ].join("\n");

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "gameradar-players.csv";
    link.click();
  };

  return (
    <div className="w-full bg-slate-950 min-h-screen p-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className={`text-3xl font-bold text-white flex items-center gap-3
              ${["ko", "ja", "zh"].includes(locale) ? "font-cjk" : ""}`}>
              <GitCompare className="w-8 h-8 text-cyan-500" />
              {t("title")}
            </h1>
            <p className="text-slate-400 text-sm mt-1">
              {t("subtitle")}
            </p>
          </div>

          {/* Export Buttons */}
          <div className="flex gap-2">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={exportToPDF}
              className="px-4 py-2 bg-red-600 hover:bg-red-500 rounded-lg
                flex items-center gap-2 text-white font-semibold text-sm
                transition-colors"
            >
              <FileText className="w-4 h-4" />
              {t("exportPDF")}
            </motion.button>

            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={exportToCSV}
              className="px-4 py-2 bg-green-600 hover:bg-green-500 rounded-lg
                flex items-center gap-2 text-white font-semibold text-sm
                transition-colors"
            >
              <Table className="w-4 h-4" />
              {t("exportCSV")}
            </motion.button>
          </div>
        </div>

        {/* View Toggle */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setViewMode("comparison")}
            className={`px-4 py-2 rounded-lg font-semibold text-sm transition-colors
              ${viewMode === "comparison"
                ? "bg-cyan-600 text-white"
                : "bg-slate-800 text-slate-400 hover:bg-slate-700"
              }`}
          >
            <GitCompare className="w-4 h-4 inline mr-2" />
            {t("comparisonMode")}
          </button>
          <button
            onClick={() => setViewMode("table")}
            className={`px-4 py-2 rounded-lg font-semibold text-sm transition-colors
              ${viewMode === "table"
                ? "bg-cyan-600 text-white"
                : "bg-slate-800 text-slate-400 hover:bg-slate-700"
              }`}
          >
            <BarChart3 className="w-4 h-4 inline mr-2" />
            {t("tableMode")}
          </button>
        </div>

        {/* Selection Info */}
        {selectedPlayers.length > 0 && (
          <div className="bg-cyan-500/10 border border-cyan-500/30 rounded-lg p-3 mb-6">
            <p className="text-cyan-400 text-sm">
              {t("selectedCount", { count: selectedPlayers.length })}
              {selectedPlayers.length === 2 && ` - ${t("readyToCompare")}`}
            </p>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto">
        {viewMode === "comparison" && selectedPlayerData.length === 2 ? (
          <ComparisonView players={selectedPlayerData} t={t} locale={locale} />
        ) : (
          <PlayerSelectionGrid
            players={players}
            selectedPlayers={selectedPlayers}
            onToggleSelection={togglePlayerSelection}
            t={t}
            locale={locale}
          />
        )}
      </div>
    </div>
  );
}

// ============================================================
// COMPARISON VIEW - A/B Testing
// ============================================================
function ComparisonView({
  players,
  t,
  locale,
}: {
  players: Player[];
  t: any;
  locale: string;
}) {
  const [playerA, playerB] = players;

  // Radar chart data
  const radarData = [
    {
      metric: t("gameRadarScore"),
      playerA: Math.round(playerA.gameradar_score || 0),
      playerB: Math.round(playerB.gameradar_score || 0),
      fullMark: 100,
    },
    {
      metric: t("talentScore"),
      playerA: Math.round(playerA.talent_score || 0),
      playerB: Math.round(playerB.talent_score || 0),
      fullMark: 100,
    },
    {
      metric: t("winRate"),
      playerA: Math.round(playerA.win_rate || 0),
      playerB: Math.round(playerB.win_rate || 0),
      fullMark: 100,
    },
    {
      metric: "KDA",
      playerA: Math.min(Math.round((playerA.kda || 0) * 10), 100),
      playerB: Math.min(Math.round((playerB.kda || 0) * 10), 100),
      fullMark: 100,
    },
  ];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Player A */}
      <PlayerComparisonCard player={playerA} side="A" t={t} locale={locale} />

      {/* Player B */}
      <PlayerComparisonCard player={playerB} side="B" t={t} locale={locale} />

      {/* Radar Chart - Full Width */}
      <div className="lg:col-span-2 bg-slate-900 rounded-xl border border-slate-800 p-6">
        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-cyan-500" />
          {t("skillRadar")}
        </h3>

        <ResponsiveContainer width="100%" height={400}>
          <RadarChart data={radarData}>
            <PolarGrid stroke="#334155" />
            <PolarAngleAxis
              dataKey="metric"
              tick={{ fill: "#94a3b8", fontSize: 12 }}
            />
            <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: "#64748b" }} />
            <Radar
              name={playerA.nickname}
              dataKey="playerA"
              stroke="#06b6d4"
              fill="#06b6d4"
              fillOpacity={0.3}
            />
            <Radar
              name={playerB.nickname}
              dataKey="playerB"
              stroke="#8b5cf6"
              fill="#8b5cf6"
              fillOpacity={0.3}
            />
            <Legend wrapperStyle={{ color: "#fff" }} />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* Comparison Table */}
      <div className="lg:col-span-2 bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-800">
            <tr>
              <th className="px-4 py-3 text-left text-slate-300 font-semibold">
                {t("metric")}
              </th>
              <th className="px-4 py-3 text-center text-cyan-400 font-semibold">
                {playerA.nickname}
              </th>
              <th className="px-4 py-3 text-center text-slate-400">
                {t("winner")}
              </th>
              <th className="px-4 py-3 text-center text-purple-400 font-semibold">
                {playerB.nickname}
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            <ComparisonRow
              label={t("gameRadarScore")}
              valueA={Math.round(playerA.gameradar_score || 0)}
              valueB={Math.round(playerB.gameradar_score || 0)}
            />
            <ComparisonRow
              label={t("talentScore")}
              valueA={Math.round(playerA.talent_score || 0)}
              valueB={Math.round(playerB.talent_score || 0)}
            />
            <ComparisonRow
              label={t("winRate")}
              valueA={`${(playerA.win_rate || 0).toFixed(1)}%`}
              valueB={`${(playerB.win_rate || 0).toFixed(1)}%`}
              compareNumeric
            />
            <ComparisonRow
              label="KDA"
              valueA={(playerA.kda || 0).toFixed(2)}
              valueB={(playerB.kda || 0).toFixed(2)}
              compareNumeric
            />
            <ComparisonRow
              label={t("gamesPlayed")}
              valueA={playerA.games_played || 0}
              valueB={playerB.games_played || 0}
            />
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ============================================================
// PLAYER COMPARISON CARD
// ============================================================
function PlayerComparisonCard({
  player,
  side,
  t,
  locale,
}: {
  player: Player;
  side: "A" | "B";
  t: any;
  locale: string;
}) {
  const sideColor = side === "A" ? "cyan" : "purple";

  return (
    <div className={`bg-slate-900 rounded-xl border-2 border-${sideColor}-500/30 p-6`}>
      {/* Side Badge */}
      <div className="flex items-center justify-between mb-4">
        <div className={`px-3 py-1 rounded-full bg-${sideColor}-500/20 border border-${sideColor}-500/50`}>
          <span className={`text-${sideColor}-400 font-bold text-sm`}>
            {t("player")} {side}
          </span>
        </div>
      </div>

      {/* Player Info */}
      <div className="flex items-center gap-4 mb-6">
        {player.avatar_url ? (
          <img
            src={player.avatar_url}
            alt={player.nickname}
            className="w-16 h-16 rounded-lg object-cover"
          />
        ) : (
          <div className="w-16 h-16 rounded-lg bg-slate-800 flex items-center justify-center">
            <span className="text-2xl font-bold text-slate-600">
              {player.nickname[0]}
            </span>
          </div>
        )}

        <div className="flex-1">
          <h3 className={`text-xl font-bold text-white
            ${["ko", "ja", "zh"].includes(locale) ? "font-cjk" : ""}`}>
            {player.nickname}
          </h3>
          <p className="text-sm text-slate-400">
            {player.region} • {player.rank}
          </p>
        </div>
      </div>

      {/* Stats */}
      <div className="space-y-3">
        <StatRow
          icon={<Trophy className="w-4 h-4" />}
          label={t("gameRadarScore")}
          value={Math.round(player.gameradar_score || 0)}
          color={sideColor}
        />
        <StatRow
          icon={<Award className="w-4 h-4" />}
          label={t("talentScore")}
          value={Math.round(player.talent_score || 0)}
          color={sideColor}
        />
        <StatRow
          icon={<TrendingUp className="w-4 h-4" />}
          label={t("winRate")}
          value={`${(player.win_rate || 0).toFixed(1)}%`}
          color={sideColor}
        />
        <StatRow
          icon={<Zap className="w-4 h-4" />}
          label="KDA"
          value={(player.kda || 0).toFixed(2)}
          color={sideColor}
        />
        <StatRow
          icon={<Target className="w-4 h-4" />}
          label={t("gamesPlayed")}
          value={player.games_played || 0}
          color={sideColor}
        />
      </div>

      {/* Top Champions */}
      {player.top_champions && player.top_champions.length > 0 && (
        <div className="mt-6 pt-6 border-t border-slate-800">
          <h4 className="text-xs font-semibold text-slate-400 uppercase mb-2">
            {t("topChampions")}
          </h4>
          <div className="flex gap-2 flex-wrap">
            {player.top_champions.slice(0, 5).map((champion, idx) => (
              <span
                key={idx}
                className="px-2 py-1 rounded bg-slate-800 text-xs text-slate-300"
              >
                {champion}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================
// HELPER COMPONENTS
// ============================================================
function StatRow({
  icon,
  label,
  value,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  color: string;
}) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2 text-slate-400 text-sm">
        {icon}
        {label}
      </div>
      <div className={`text-${color}-400 font-bold`}>{value}</div>
    </div>
  );
}

function ComparisonRow({
  label,
  valueA,
  valueB,
  compareNumeric = true,
}: {
  label: string;
  valueA: any;
  valueB: any;
  compareNumeric?: boolean;
}) {
  const numA = typeof valueA === "string" ? parseFloat(valueA) : valueA;
  const numB = typeof valueB === "string" ? parseFloat(valueB) : valueB;
  
  const winner = compareNumeric && numA !== numB ? (numA > numB ? "A" : "B") : null;

  return (
    <tr>
      <td className="px-4 py-3 text-slate-300">{label}</td>
      <td className="px-4 py-3 text-center text-cyan-400 font-semibold">
        {valueA}
      </td>
      <td className="px-4 py-3 text-center">
        {winner === "A" && <Check className="w-5 h-5 text-cyan-500 mx-auto" />}
        {winner === "B" && <Check className="w-5 h-5 text-purple-500 mx-auto" />}
        {!winner && <span className="text-slate-600">-</span>}
      </td>
      <td className="px-4 py-3 text-center text-purple-400 font-semibold">
        {valueB}
      </td>
    </tr>
  );
}

// ============================================================
// PLAYER SELECTION GRID
// ============================================================
function PlayerSelectionGrid({
  players,
  selectedPlayers,
  onToggleSelection,
  t,
  locale,
}: {
  players: Player[];
  selectedPlayers: string[];
  onToggleSelection: (id: string) => void;
  t: any;
  locale: string;
}) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {players.map((player) => {
        const isSelected = selectedPlayers.includes(player.player_id);
        
        return (
          <motion.div
            key={player.player_id}
            whileHover={{ scale: 1.02 }}
            onClick={() => onToggleSelection(player.player_id)}
            className={`p-4 rounded-lg border-2 cursor-pointer transition-all
              ${isSelected
                ? "bg-cyan-500/10 border-cyan-500"
                : "bg-slate-900 border-slate-800 hover:border-slate-700"
              }`}
          >
            {/* Selection Checkbox */}
            <div className="flex items-center justify-between mb-3">
              <div className={`w-5 h-5 rounded border-2 flex items-center justify-center
                ${isSelected ? "bg-cyan-500 border-cyan-500" : "border-slate-700"}`}>
                {isSelected && <Check className="w-3 h-3 text-white" />}
              </div>
              <div className={`px-2 py-0.5 rounded text-xs font-bold
                ${isSelected ? "bg-cyan-500 text-white" : "bg-slate-800 text-slate-400"}`}>
                {Math.round(player.gameradar_score || 0)}
              </div>
            </div>

            {/* Player Info */}
            <h3 className={`text-sm font-bold text-white mb-1 truncate
              ${["ko", "ja", "zh"].includes(locale) ? "font-cjk" : ""}`}>
              {player.nickname}
            </h3>
            <p className="text-xs text-slate-400 mb-2">
              {player.region} • {player.rank}
            </p>

            {/* Quick Stats */}
            <div className="flex gap-2 text-xs">
              <div className="flex-1 bg-slate-800 rounded px-2 py-1">
                <div className="text-slate-500">WR</div>
                <div className="text-green-400 font-bold">
                  {(player.win_rate || 0).toFixed(0)}%
                </div>
              </div>
              <div className="flex-1 bg-slate-800 rounded px-2 py-1">
                <div className="text-slate-500">KDA</div>
                <div className="text-yellow-400 font-bold">
                  {(player.kda || 0).toFixed(1)}
                </div>
              </div>
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}
