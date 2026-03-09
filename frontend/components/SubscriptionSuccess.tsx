'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

interface SubscriptionDetails {
  plan: string;
  amount: number;
  currency: string;
  periodStart: string;
  periodEnd: string;
  sessionId: string;
  email: string;
}

export default function SubscriptionSuccess() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [subscription, setSubscription] = useState<SubscriptionDetails | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    const sessionId = searchParams.get('sessionId');
    
    if (!sessionId) {
      setError('No se encontró información de la suscripción');
      setLoading(false);
      return;
    }

    // Fetch subscription details
    fetch(`/api/payment/verify?sessionId=${sessionId}`)
      .then((res) => res.json())
      .then((data) => {
        if (data.error) {
          setError(data.error);
        } else {
          setSubscription(data);
        }
        setLoading(false);
      })
      .catch((err) => {
        setError('Error al verificar la suscripción');
        setLoading(false);
      });
  }, [searchParams]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-blue-500 mx-auto"></div>
          <p className="text-slate-400 mt-4">Verificando tu suscripción...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center p-6">
        <div className="max-w-md w-full bg-slate-800/50 backdrop-blur rounded-xl p-8 border border-red-500/30 text-center">
          <div className="text-6xl mb-4">❌</div>
          <h1 className="text-2xl font-bold text-white mb-4">Error</h1>
          <p className="text-slate-300 mb-6">{error}</p>
          <button
            onClick={() => router.push('/')}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold transition"
          >
            Volver al inicio
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-4xl mx-auto pt-12">
        {/* Success Animation */}
        <div className="text-center mb-8">
          <div className="inline-block animate-bounce mb-4">
            <div className="text-8xl">🎉</div>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
            ¡Bienvenido a <span className="text-blue-400">GameRadar AI</span>!
          </h1>
          <p className="text-xl text-slate-300">
            Tu suscripción se ha activado exitosamente
          </p>
        </div>

        {/* Subscription Details Card */}
        {subscription && (
          <div className="bg-slate-800/50 backdrop-blur rounded-xl p-8 border border-slate-700 mb-8">
            <div className="flex items-start justify-between mb-6">
              <div>
                <h2 className="text-2xl font-bold text-white mb-2">
                  Plan: {subscription.plan}
                </h2>
                <p className="text-slate-400">
                  Gracias por confiar en nosotros, <span className="text-white">{subscription.email}</span>
                </p>
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-green-400">
                  ${subscription.amount}
                </div>
                <div className="text-slate-400 text-sm">{subscription.currency}/mes</div>
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-6 mb-6">
              <div className="p-4 bg-slate-900/50 rounded-lg border border-slate-700">
                <div className="text-slate-400 text-sm mb-1">Período actual</div>
                <div className="text-white font-semibold">
                  {new Date(subscription.periodStart).toLocaleDateString('es-ES')} -{' '}
                  {new Date(subscription.periodEnd).toLocaleDateString('es-ES')}
                </div>
              </div>
              <div className="p-4 bg-slate-900/50 rounded-lg border border-slate-700">
                <div className="text-slate-400 text-sm mb-1">ID de transacción</div>
                <div className="text-white font-mono text-sm">
                  {subscription.sessionId.slice(0, 20)}...
                </div>
              </div>
            </div>

            <div className="p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
              <p className="text-sm text-slate-300">
                📧 Hemos enviado un correo de confirmación a <strong>{subscription.email}</strong> con los detalles de tu suscripción.
              </p>
            </div>
          </div>
        )}

        {/* What's Next Section */}
        <div className="bg-slate-800/50 backdrop-blur rounded-xl p-8 border border-slate-700 mb-8">
          <h2 className="text-2xl font-bold text-white mb-6">¿Qué sigue?</h2>
          <div className="space-y-6">
            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0 w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center text-xl font-bold text-white">
                1
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-white mb-2">
                  Accede a tu Dashboard
                </h3>
                <p className="text-slate-400 mb-3">
                  Explora tu panel de control donde podrás ver tus límites de uso, mercados seleccionados y comenzar a buscar talento.
                </p>
                <button
                  onClick={() => router.push('/dashboard')}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-semibold transition inline-flex items-center"
                >
                  Ir al Dashboard →
                </button>
              </div>
            </div>

            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0 w-12 h-12 bg-purple-600 rounded-lg flex items-center justify-center text-xl font-bold text-white">
                2
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-white mb-2">
                  Selecciona tus 3 mercados
                </h3>
                <p className="text-slate-400 mb-3">
                  Elige los países en los que quieres enfocarte: Corea del Sur, Japón, China, Tailandia, Vietnam, India o Filipinas.
                </p>
                <button
                  onClick={() => router.push('/settings/markets')}
                  className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-2 rounded-lg font-semibold transition"
                >
                  Configurar Mercados
                </button>
              </div>
            </div>

            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0 w-12 h-12 bg-green-600 rounded-lg flex items-center justify-center text-xl font-bold text-white">
                3
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-white mb-2">
                  Realiza tu primera búsqueda
                </h3>
                <p className="text-slate-400 mb-3">
                  Usa nuestra búsqueda semántica con IA para descubrir jugadores emergentes con criterios específicos.
                </p>
                <button
                  onClick={() => router.push('/search')}
                  className="bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-lg font-semibold transition"
                >
                  Comenzar Búsqueda
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Features Reminder */}
        <div className="bg-slate-800/50 backdrop-blur rounded-xl p-8 border border-slate-700 mb-8">
          <h2 className="text-2xl font-bold text-white mb-6">
            Lo que incluye tu plan Street Scout
          </h2>
          <div className="grid md:grid-cols-2 gap-4">
            <div className="flex items-start space-x-3">
              <div className="text-2xl">✓</div>
              <div>
                <div className="text-white font-semibold">3 mercados asiáticos</div>
                <div className="text-slate-400 text-sm">
                  Puedes cambiarlos mensualmente
                </div>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="text-2xl">✓</div>
              <div>
                <div className="text-white font-semibold">50 búsquedas/mes</div>
                <div className="text-slate-400 text-sm">
                  Búsqueda semántica con IA
                </div>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="text-2xl">✓</div>
              <div>
                <div className="text-white font-semibold">Análisis básicos</div>
                <div className="text-slate-400 text-sm">
                  Estadísticas clave de jugadores
                </div>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="text-2xl">✓</div>
              <div>
                <div className="text-white font-semibold">Notificaciones email</div>
                <div className="text-slate-400 text-sm">
                  Alertas semanales de nuevos talentos
                </div>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="text-2xl">✓</div>
              <div>
                <div className="text-white font-semibold">Soporte comunitario</div>
                <div className="text-slate-400 text-sm">
                  Discord y foros
                </div>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="text-2xl">✓</div>
              <div>
                <div className="text-white font-semibold">Exportación CSV</div>
                <div className="text-slate-400 text-sm">
                  Descarga tus hallazgos
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Support and Resources */}
        <div className="bg-slate-800/50 backdrop-blur rounded-xl p-8 border border-slate-700 mb-8">
          <h2 className="text-2xl font-bold text-white mb-6">Recursos y Soporte</h2>
          <div className="grid md:grid-cols-3 gap-4">
            <a
              href="#"
              className="flex flex-col items-center p-6 bg-slate-900/50 rounded-lg border border-slate-700 hover:border-blue-500/50 transition text-center"
            >
              <div className="text-4xl mb-3">📚</div>
              <div className="text-white font-semibold mb-1">Documentación</div>
              <div className="text-slate-400 text-sm">
                Guías paso a paso
              </div>
            </a>
            <a
              href="#"
              className="flex flex-col items-center p-6 bg-slate-900/50 rounded-lg border border-slate-700 hover:border-blue-500/50 transition text-center"
            >
              <div className="text-4xl mb-3">💬</div>
              <div className="text-white font-semibold mb-1">Discord</div>
              <div className="text-slate-400 text-sm">
                Únete a la comunidad
              </div>
            </a>
            <a
              href="#"
              className="flex flex-col items-center p-6 bg-slate-900/50 rounded-lg border border-slate-700 hover:border-blue-500/50 transition text-center"
            >
              <div className="text-4xl mb-3">🎥</div>
              <div className="text-white font-semibold mb-1">Video Tutorial</div>
              <div className="text-slate-400 text-sm">
                Aprende a usar GameRadar
              </div>
            </a>
          </div>
        </div>

        {/* Upgrade Prompt */}
        <div className="bg-gradient-to-r from-blue-600/20 to-purple-600/20 border border-blue-500/30 rounded-xl p-6 mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-xl font-bold text-white mb-2">
                ¿Necesitas más capacidad? 🚀
              </h3>
              <p className="text-slate-300 mb-2">
                Actualiza a <strong>Elite Analyst</strong> para búsquedas ilimitadas, 7 mercados y análisis avanzados por solo $299/mes.
              </p>
              <ul className="text-sm text-slate-300 space-y-1">
                <li>✓ Búsquedas ilimitadas</li>
                <li>✓ Todos los mercados asiáticos</li>
                <li>✓ TalentPing en tiempo real</li>
              </ul>
            </div>
            <button className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-6 py-3 rounded-lg font-semibold transition whitespace-nowrap">
              Ver Elite Analyst
            </button>
          </div>
        </div>

        {/* Back to Home */}
        <div className="text-center pb-12">
          <button
            onClick={() => router.push('/')}
            className="text-slate-400 hover:text-white transition"
          >
            ← Volver al inicio
          </button>
        </div>
      </div>
    </div>
  );
}
