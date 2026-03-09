'use client'

import { useRouter } from 'next/navigation'

export default function PlansComparison() {
  const router = useRouter()

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-indigo-900 to-blue-900 py-12 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-white mb-4">
            Choose Your Plan
          </h1>
          <p className="text-xl text-gray-300 max-w-2xl mx-auto">
            Select the perfect plan for your scouting needs
          </p>
        </div>

        {/* Plans */}
        <div className="grid md:grid-cols-2 gap-8 max-w-5xl mx-auto">
          {/* Street Scout Plan */}
          <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20 hover:scale-105 transition-transform">
            <div className="text-center mb-6">
              <div className="inline-block px-4 py-2 bg-blue-500/20 rounded-full border border-blue-400/30 mb-4">
                <span className="text-blue-300 font-semibold">STREET SCOUT</span>
              </div>
              <div className="text-5xl font-bold text-white mb-2">
                $99
                <span className="text-2xl text-gray-300">/mes</span>
              </div>
              <p className="text-gray-300">Para scouts independientes</p>
            </div>

            <div className="space-y-4 mb-8">
              <div className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-full bg-green-500 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-white font-semibold">2 mercados a elegir</h3>
                  <p className="text-sm text-gray-300">Selecciona tus regiones</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-full bg-green-500 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-white font-semibold">50 búsquedas/mes</h3>
                  <p className="text-sm text-gray-300">Suficiente para la mayoría</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-full bg-green-500 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-white font-semibold">Perfiles detallados</h3>
                  <p className="text-sm text-gray-300">Estadísticas completas</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-full bg-green-500 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-white font-semibold">Exportar PDF</h3>
                  <p className="text-sm text-gray-300">5 reportes/mes</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-full bg-gray-500 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-gray-400 font-semibold">Análisis avanzados</h3>
                  <p className="text-sm text-gray-500">No incluido</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-full bg-gray-500 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-gray-400 font-semibold">Alertas TalentPing</h3>
                  <p className="text-sm text-gray-500">No incluido</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-full bg-gray-500 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-gray-400 font-semibold">Acceso a API</h3>
                  <p className="text-sm text-gray-500">No incluido</p>
                </div>
              </div>
            </div>

            <button
              onClick={() => router.push('/subscribe/street-scout')}
              className="w-full py-4 px-6 bg-gradient-to-r from-blue-600 to-cyan-600 text-white font-semibold rounded-lg hover:from-blue-700 hover:to-cyan-700 transition-all"
            >
              Comenzar con Street Scout
            </button>
          </div>

          {/* Elite Analyst Plan */}
          <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border-2 border-purple-400/50 hover:scale-105 transition-transform relative">
            {/* Popular Badge */}
            <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
              <div className="px-6 py-2 bg-gradient-to-r from-purple-600 to-pink-600 rounded-full">
                <span className="text-white font-bold text-sm">⭐ MÁS POPULAR</span>
              </div>
            </div>

            <div className="text-center mb-6 mt-4">
              <div className="inline-block px-4 py-2 bg-purple-500/20 rounded-full border border-purple-400/30 mb-4">
                <span className="text-purple-300 font-semibold">ELITE ANALYST</span>
              </div>
              <div className="text-5xl font-bold text-white mb-2">
                $299
                <span className="text-2xl text-gray-300">/mes</span>
              </div>
              <p className="text-gray-300">Para equipos profesionales</p>
            </div>

            <div className="space-y-4 mb-8">
              <div className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-full bg-purple-500 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-white font-semibold">Los 7 mercados</h3>
                  <p className="text-sm text-gray-300">Cobertura completa de Asia</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-full bg-purple-500 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-white font-semibold">Búsquedas ilimitadas</h3>
                  <p className="text-sm text-gray-300">Sin restricciones</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-full bg-purple-500 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-white font-semibold">Análisis avanzados con IA</h3>
                  <p className="text-sm text-gray-300">Insights profesionales</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-full bg-purple-500 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-white font-semibold">Alertas TalentPing</h3>
                  <p className="text-sm text-gray-300">Notificaciones en tiempo real</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-full bg-purple-500 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-white font-semibold">Acceso a API</h3>
                  <p className="text-sm text-gray-300">Integración completa</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-full bg-purple-500 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-white font-semibold">Reportes personalizados</h3>
                  <p className="text-sm text-gray-300">PDFs ilimitados</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-full bg-purple-500 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-white font-semibold">Soporte prioritario</h3>
                  <p className="text-sm text-gray-300">Atención 24/7</p>
                </div>
              </div>
            </div>

            <button
              onClick={() => router.push('/subscribe/elite-analyst')}
              className="w-full py-4 px-6 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-semibold rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all shadow-lg shadow-purple-500/50"
            >
              Comenzar con Elite Analyst
            </button>
          </div>
        </div>

        {/* Trust Signals */}
        <div className="mt-16 grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
          <div className="text-center">
            <div className="text-5xl mb-3">🔒</div>
            <h3 className="text-white font-semibold mb-2">Pago Seguro</h3>
            <p className="text-gray-300 text-sm">Procesamiento encriptado</p>
          </div>
          <div className="text-center">
            <div className="text-5xl mb-3">💳</div>
            <h3 className="text-white font-semibold mb-2">Cancela Cuando Quieras</h3>
            <p className="text-gray-300 text-sm">Sin compromisos a largo plazo</p>
          </div>
          <div className="text-center">
            <div className="text-5xl mb-3">⚡</div>
            <h3 className="text-white font-semibold mb-2">Acceso Instantáneo</h3>
            <p className="text-gray-300 text-sm">Comienza a usar de inmediato</p>
          </div>
        </div>

        {/* FAQ */}
        <div className="mt-16 max-w-3xl mx-auto">
          <h2 className="text-3xl font-bold text-white text-center mb-8">Preguntas Frecuentes</h2>
          <div className="space-y-4">
            <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
              <h3 className="text-white font-semibold mb-2">¿Puedo cambiar de plan después?</h3>
              <p className="text-gray-300">Sí, puedes actualizar o degradar tu plan en cualquier momento desde tu dashboard.</p>
            </div>
            <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
              <h3 className="text-white font-semibold mb-2">¿Qué métodos de pago aceptan?</h3>
              <p className="text-gray-300">Aceptamos tarjetas de crédito, débito, PayPal, y métodos de pago regionales como UPI, Alipay, etc.</p>
            </div>
            <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
              <h3 className="text-white font-semibold mb-2">¿Hay descuentos por pago anual?</h3>
              <p className="text-gray-300">Sí, ofrecemos 20% de descuento en planes anuales. Contacta con ventas para más información.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
