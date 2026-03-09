import React, { useState, useEffect } from 'react';

interface UsageStats {
  searchesUsed: number;
  searchesLimit: number;
  marketsUsed: number;
  marketsLimit: number;
  currentPeriodStart: string;
  currentPeriodEnd: string;
  subscriptionStatus: 'active' | 'trial' | 'expired';
  daysRemaining: number;
}

interface MarketAccess {
  id: string;
  name: string;
  region: string;
  flag: string;
  playersDiscovered: number;
}

export default function StreetScoutDashboard() {
  const [stats, setStats] = useState<UsageStats>({
    searchesUsed: 23,
    searchesLimit: 50,
    marketsUsed: 3,
    marketsLimit: 3,
    currentPeriodStart: '2026-03-01',
    currentPeriodEnd: '2026-03-31',
    subscriptionStatus: 'active',
    daysRemaining: 22,
  });

  const [selectedMarkets, setSelectedMarkets] = useState<MarketAccess[]>([
    {
      id: 'kr',
      name: 'Corea del Sur',
      region: 'East Asia',
      flag: '🇰🇷',
      playersDiscovered: 45,
    },
    {
      id: 'jp',
      name: 'Japón',
      region: 'East Asia',
      flag: '🇯🇵',
      playersDiscovered: 32,
    },
    {
      id: 'th',
      name: 'Tailandia',
      region: 'Southeast Asia',
      flag: '🇹🇭',
      playersDiscovered: 18,
    },
  ]);

  const [recentSearches, setRecentSearches] = useState([
    {
      id: 1,
      query: 'mid lane high KDA Korea',
      results: 12,
      timestamp: '2026-03-08 14:30',
      market: 'Corea del Sur',
    },
    {
      id: 2,
      query: 'support players Thailand emerging',
      results: 8,
      timestamp: '2026-03-08 11:15',
      market: 'Tailandia',
    },
    {
      id: 3,
      query: 'top lane Japan Diamond+',
      results: 15,
      timestamp: '2026-03-07 19:45',
      market: 'Japón',
    },
  ]);

  const searchesPercentage = (stats.searchesUsed / stats.searchesLimit) * 100;
  const isNearLimit = searchesPercentage >= 80;

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'text-green-400 bg-green-400/10 border-green-400/30';
      case 'trial':
        return 'text-blue-400 bg-blue-400/10 border-blue-400/30';
      case 'expired':
        return 'text-red-400 bg-red-400/10 border-red-400/30';
      default:
        return 'text-slate-400 bg-slate-400/10 border-slate-400/30';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-4xl font-bold text-white mb-2">
                Dashboard <span className="text-blue-400">Street Scout</span>
              </h1>
              <p className="text-slate-400">Gestiona tu plan y monitorea tu uso</p>
            </div>
            <div
              className={`px-4 py-2 rounded-lg border ${getStatusColor(stats.subscriptionStatus)}`}
            >
              <span className="font-semibold uppercase text-sm">
                {stats.subscriptionStatus === 'active'
                  ? 'Activo'
                  : stats.subscriptionStatus === 'trial'
                  ? 'Prueba'
                  : 'Expirado'}
              </span>
            </div>
          </div>
        </div>

        {/* Usage Overview */}
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          {/* Searches Card */}
          <div className="bg-slate-800/50 backdrop-blur rounded-xl p-6 border border-slate-700">
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="text-slate-400 text-sm">Búsquedas este mes</p>
                <div className="text-3xl font-bold text-white mt-1">
                  {stats.searchesUsed}
                  <span className="text-xl text-slate-400">/{stats.searchesLimit}</span>
                </div>
              </div>
              <div className="text-4xl">🔍</div>
            </div>
            <div className="relative w-full h-2 bg-slate-700 rounded-full overflow-hidden">
              <div
                className={`absolute top-0 left-0 h-full transition-all ${
                  isNearLimit ? 'bg-red-500' : 'bg-blue-500'
                }`}
                style={{ width: `${searchesPercentage}%` }}
              ></div>
            </div>
            {isNearLimit && (
              <p className="text-orange-400 text-xs mt-2">⚠️ Cerca del límite mensual</p>
            )}
          </div>

          {/* Markets Card */}
          <div className="bg-slate-800/50 backdrop-blur rounded-xl p-6 border border-slate-700">
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="text-slate-400 text-sm">Mercados activos</p>
                <div className="text-3xl font-bold text-white mt-1">
                  {stats.marketsUsed}
                  <span className="text-xl text-slate-400">/{stats.marketsLimit}</span>
                </div>
              </div>
              <div className="text-4xl">🌏</div>
            </div>
            <div className="flex space-x-2 mt-4">
              {selectedMarkets.map((market) => (
                <div
                  key={market.id}
                  className="text-3xl"
                  title={market.name}
                >
                  {market.flag}
                </div>
              ))}
            </div>
          </div>

          {/* Period Card */}
          <div className="bg-slate-800/50 backdrop-blur rounded-xl p-6 border border-slate-700">
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="text-slate-400 text-sm">Días restantes</p>
                <div className="text-3xl font-bold text-white mt-1">{stats.daysRemaining}</div>
              </div>
              <div className="text-4xl">📅</div>
            </div>
            <p className="text-slate-400 text-xs">
              Renovación: {new Date(stats.currentPeriodEnd).toLocaleDateString('es-ES')}
            </p>
          </div>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Selected Markets */}
          <div className="bg-slate-800/50 backdrop-blur rounded-xl p-6 border border-slate-700">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-white">Tus Mercados</h2>
              <button className="text-blue-400 hover:text-blue-300 text-sm font-medium">
                Cambiar →
              </button>
            </div>
            <div className="space-y-4">
              {selectedMarkets.map((market) => (
                <div
                  key={market.id}
                  className="flex items-center justify-between p-4 bg-slate-900/50 rounded-lg border border-slate-700 hover:border-blue-500/50 transition"
                >
                  <div className="flex items-center space-x-4">
                    <div className="text-3xl">{market.flag}</div>
                    <div>
                      <div className="text-white font-semibold">{market.name}</div>
                      <div className="text-slate-400 text-sm">{market.region}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-white font-semibold">{market.playersDiscovered}</div>
                    <div className="text-slate-400 text-xs">jugadores</div>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-6 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
              <p className="text-sm text-slate-300">
                💡 Puedes cambiar tus mercados una vez por mes al renovar tu suscripción.
              </p>
            </div>
          </div>

          {/* Recent Searches */}
          <div className="bg-slate-800/50 backdrop-blur rounded-xl p-6 border border-slate-700">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-white">Búsquedas Recientes</h2>
              <button className="text-blue-400 hover:text-blue-300 text-sm font-medium">
                Ver todo →
              </button>
            </div>
            <div className="space-y-4">
              {recentSearches.map((search) => (
                <div
                  key={search.id}
                  className="p-4 bg-slate-900/50 rounded-lg border border-slate-700 hover:border-blue-500/50 transition"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <div className="text-white font-medium mb-1">"{search.query}"</div>
                      <div className="flex items-center space-x-3 text-sm text-slate-400">
                        <span>🌏 {search.market}</span>
                        <span>•</span>
                        <span>{search.results} resultados</span>
                      </div>
                    </div>
                  </div>
                  <div className="text-xs text-slate-500">{search.timestamp}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mt-8 grid md:grid-cols-3 gap-6">
          <button className="bg-blue-600 hover:bg-blue-700 text-white p-6 rounded-xl font-semibold transition text-left">
            <div className="text-2xl mb-2">🔍</div>
            <div className="text-lg">Nueva Búsqueda</div>
            <div className="text-sm opacity-80 mt-1">
              {stats.searchesLimit - stats.searchesUsed} búsquedas disponibles
            </div>
          </button>

          <button className="bg-purple-600 hover:bg-purple-700 text-white p-6 rounded-xl font-semibold transition text-left">
            <div className="text-2xl mb-2">📊</div>
            <div className="text-lg">Ver Análisis</div>
            <div className="text-sm opacity-80 mt-1">Insights de tus jugadores</div>
          </button>

          <button className="bg-slate-700 hover:bg-slate-600 text-white p-6 rounded-xl font-semibold transition text-left">
            <div className="text-2xl mb-2">⬆️</div>
            <div className="text-lg">Actualizar Plan</div>
            <div className="text-sm opacity-80 mt-1">Acceso a Elite Analyst</div>
          </button>
        </div>

        {/* Upgrade Banner */}
        <div className="mt-8 bg-gradient-to-r from-blue-600/20 to-purple-600/20 border border-blue-500/30 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-xl font-bold text-white mb-2">
                ¿Necesitas más búsquedas? 🚀
              </h3>
              <p className="text-slate-300 mb-4">
                Actualiza a Elite Analyst para búsquedas ilimitadas, 7 mercados y análisis avanzados
              </p>
              <ul className="text-sm text-slate-300 space-y-1">
                <li>✓ Búsquedas ilimitadas</li>
                <li>✓ Acceso a los 7 mercados asiáticos</li>
                <li>✓ Alertas TalentPing en tiempo real</li>
                <li>✓ API access para integraciones</li>
              </ul>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-white mb-2">$299/mes</div>
              <button className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-6 py-3 rounded-lg font-semibold transition">
                Actualizar Ahora
              </button>
            </div>
          </div>
        </div>

        {/* Support Section */}
        <div className="mt-8 bg-slate-800/30 rounded-xl p-6 border border-slate-700">
          <h3 className="text-lg font-bold text-white mb-4">Soporte Comunitario</h3>
          <div className="grid md:grid-cols-3 gap-4">
            <a
              href="#"
              className="flex items-center space-x-3 p-4 bg-slate-800/50 rounded-lg border border-slate-700 hover:border-blue-500/50 transition"
            >
              <div className="text-2xl">💬</div>
              <div>
                <div className="text-white font-medium">Discord</div>
                <div className="text-slate-400 text-sm">Únete a la comunidad</div>
              </div>
            </a>
            <a
              href="#"
              className="flex items-center space-x-3 p-4 bg-slate-800/50 rounded-lg border border-slate-700 hover:border-blue-500/50 transition"
            >
              <div className="text-2xl">📚</div>
              <div>
                <div className="text-white font-medium">Documentación</div>
                <div className="text-slate-400 text-sm">Guías y tutoriales</div>
              </div>
            </a>
            <a
              href="#"
              className="flex items-center space-x-3 p-4 bg-slate-800/50 rounded-lg border border-slate-700 hover:border-blue-500/50 transition"
            >
              <div className="text-2xl">❓</div>
              <div>
                <div className="text-white font-medium">FAQ</div>
                <div className="text-slate-400 text-sm">Preguntas frecuentes</div>
              </div>
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
