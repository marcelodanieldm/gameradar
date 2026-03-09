import React, { useState } from 'react';
import { useRouter } from 'next/navigation';

interface SubscriptionPlan {
  id: string;
  name: string;
  price: number;
  currency: string;
  interval: string;
  features: string[];
  limits: {
    markets: number;
    searches: number;
    analytics: string;
  };
}

const streetScoutPlan: SubscriptionPlan = {
  id: 'street-scout',
  name: 'Street Scout',
  price: 99,
  currency: 'USD',
  interval: 'month',
  features: [
    'Acceso a 3 mercados asiáticos',
    '50 búsquedas por mes',
    'Análisis básicos de jugadores',
    'Notificaciones por email',
    'Soporte comunitario',
    'Exportación de datos (CSV)',
    'Actualizaciones semanales',
  ],
  limits: {
    markets: 3,
    searches: 50,
    analytics: 'basic',
  },
};

export default function StreetScoutSubscription() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [selectedPaymentMethod, setSelectedPaymentMethod] = useState<'card' | 'paypal'>('card');
  const [formData, setFormData] = useState({
    email: '',
    cardNumber: '',
    cardName: '',
    expiryDate: '',
    cvv: '',
    country: '',
    acceptTerms: false,
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.email || !/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email válido requerido';
    }

    if (selectedPaymentMethod === 'card') {
      if (!formData.cardNumber || formData.cardNumber.replace(/\s/g, '').length !== 16) {
        newErrors.cardNumber = 'Número de tarjeta inválido';
      }
      if (!formData.cardName) {
        newErrors.cardName = 'Nombre del titular requerido';
      }
      if (!formData.expiryDate || !/^\d{2}\/\d{2}$/.test(formData.expiryDate)) {
        newErrors.expiryDate = 'Formato: MM/YY';
      }
      if (!formData.cvv || formData.cvv.length !== 3) {
        newErrors.cvv = 'CVV inválido';
      }
    }

    if (!formData.country) {
      newErrors.country = 'País requerido';
    }

    if (!formData.acceptTerms) {
      newErrors.acceptTerms = 'Debes aceptar los términos';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubscribe = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      const response = await fetch('/api/payment/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          planId: streetScoutPlan.id,
          email: formData.email,
          paymentMethod: selectedPaymentMethod,
          paymentDetails: {
            cardNumber: formData.cardNumber,
            cardName: formData.cardName,
            expiryDate: formData.expiryDate,
            cvv: formData.cvv,
          },
          country: formData.country,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        // Redirect to success page
        router.push(`/subscription/success?sessionId=${data.sessionId}`);
      } else {
        setErrors({ submit: data.error || 'Error al procesar el pago' });
      }
    } catch (error) {
      setErrors({ submit: 'Error de conexión. Intenta nuevamente.' });
    } finally {
      setLoading(false);
    }
  };

  const formatCardNumber = (value: string) => {
    const v = value.replace(/\s+/g, '').replace(/[^0-9]/gi, '');
    const matches = v.match(/\d{4,16}/g);
    const match = (matches && matches[0]) || '';
    const parts = [];

    for (let i = 0, len = match.length; i < len; i += 4) {
      parts.push(match.substring(i, i + 4));
    }

    if (parts.length) {
      return parts.join(' ');
    } else {
      return value;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 py-12 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
            Suscripción <span className="text-blue-400">Street Scout</span>
          </h1>
          <p className="text-xl text-slate-300">
            Comienza tu viaje en el scouting profesional de e-sports
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Plan Details */}
          <div className="bg-slate-800/50 backdrop-blur rounded-2xl p-8 border border-slate-700">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-3xl font-bold text-white">{streetScoutPlan.name}</h2>
                <p className="text-slate-400 mt-1">Plan Básico</p>
              </div>
              <div className="text-right">
                <div className="text-4xl font-bold text-blue-400">
                  ${streetScoutPlan.price}
                </div>
                <div className="text-slate-400">por mes</div>
              </div>
            </div>

            <div className="border-t border-slate-700 pt-6 mb-6">
              <h3 className="text-lg font-semibold text-white mb-4">Características incluidas:</h3>
              <ul className="space-y-3">
                {streetScoutPlan.features.map((feature, index) => (
                  <li key={index} className="flex items-start">
                    <svg
                      className="w-6 h-6 text-green-400 mr-3 flex-shrink-0"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                    <span className="text-slate-300">{feature}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-blue-400 mb-2">💡 Límites del plan:</h4>
              <ul className="text-sm text-slate-300 space-y-1">
                <li>• Máximo {streetScoutPlan.limits.markets} mercados simultáneos</li>
                <li>• {streetScoutPlan.limits.searches} búsquedas mensuales</li>
                <li>• Análisis {streetScoutPlan.limits.analytics}</li>
              </ul>
            </div>

            <div className="mt-6 text-sm text-slate-400">
              <p>✓ Cancela en cualquier momento</p>
              <p>✓ Sin compromisos a largo plazo</p>
              <p>✓ Facturación mensual automática</p>
            </div>
          </div>

          {/* Payment Form */}
          <div className="bg-slate-800/50 backdrop-blur rounded-2xl p-8 border border-slate-700">
            <h2 className="text-2xl font-bold text-white mb-6">Información de Pago</h2>

            <form onSubmit={handleSubscribe} className="space-y-6">
              {/* Email */}
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-slate-300 mb-2">
                  Email *
                </label>
                <input
                  type="email"
                  id="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-3 text-white focus:border-blue-500 focus:outline-none"
                  placeholder="tu@email.com"
                />
                {errors.email && <p className="text-red-400 text-sm mt-1">{errors.email}</p>}
              </div>

              {/* Payment Method Selector */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-3">
                  Método de Pago
                </label>
                <div className="grid grid-cols-2 gap-4">
                  <button
                    type="button"
                    onClick={() => setSelectedPaymentMethod('card')}
                    className={`p-4 rounded-lg border-2 transition ${
                      selectedPaymentMethod === 'card'
                        ? 'border-blue-500 bg-blue-500/10'
                        : 'border-slate-600 bg-slate-900'
                    }`}
                  >
                    <div className="text-2xl mb-2">💳</div>
                    <div className="text-white font-medium">Tarjeta</div>
                  </button>
                  <button
                    type="button"
                    onClick={() => setSelectedPaymentMethod('paypal')}
                    className={`p-4 rounded-lg border-2 transition ${
                      selectedPaymentMethod === 'paypal'
                        ? 'border-blue-500 bg-blue-500/10'
                        : 'border-slate-600 bg-slate-900'
                    }`}
                  >
                    <div className="text-2xl mb-2">🅿️</div>
                    <div className="text-white font-medium">PayPal</div>
                  </button>
                </div>
              </div>

              {selectedPaymentMethod === 'card' && (
                <>
                  {/* Card Number */}
                  <div>
                    <label htmlFor="cardNumber" className="block text-sm font-medium text-slate-300 mb-2">
                      Número de Tarjeta *
                    </label>
                    <input
                      type="text"
                      id="cardNumber"
                      value={formData.cardNumber}
                      onChange={(e) =>
                        setFormData({ ...formData, cardNumber: formatCardNumber(e.target.value) })
                      }
                      maxLength={19}
                      className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-3 text-white focus:border-blue-500 focus:outline-none"
                      placeholder="1234 5678 9012 3456"
                    />
                    {errors.cardNumber && (
                      <p className="text-red-400 text-sm mt-1">{errors.cardNumber}</p>
                    )}
                  </div>

                  {/* Card Name */}
                  <div>
                    <label htmlFor="cardName" className="block text-sm font-medium text-slate-300 mb-2">
                      Nombre del Titular *
                    </label>
                    <input
                      type="text"
                      id="cardName"
                      value={formData.cardName}
                      onChange={(e) => setFormData({ ...formData, cardName: e.target.value })}
                      className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-3 text-white focus:border-blue-500 focus:outline-none"
                      placeholder="JUAN PÉREZ"
                    />
                    {errors.cardName && (
                      <p className="text-red-400 text-sm mt-1">{errors.cardName}</p>
                    )}
                  </div>

                  {/* Expiry and CVV */}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="expiryDate" className="block text-sm font-medium text-slate-300 mb-2">
                        Vencimiento *
                      </label>
                      <input
                        type="text"
                        id="expiryDate"
                        value={formData.expiryDate}
                        onChange={(e) => setFormData({ ...formData, expiryDate: e.target.value })}
                        maxLength={5}
                        className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-3 text-white focus:border-blue-500 focus:outline-none"
                        placeholder="MM/YY"
                      />
                      {errors.expiryDate && (
                        <p className="text-red-400 text-sm mt-1">{errors.expiryDate}</p>
                      )}
                    </div>
                    <div>
                      <label htmlFor="cvv" className="block text-sm font-medium text-slate-300 mb-2">
                        CVV *
                      </label>
                      <input
                        type="text"
                        id="cvv"
                        value={formData.cvv}
                        onChange={(e) =>
                          setFormData({ ...formData, cvv: e.target.value.replace(/\D/g, '') })
                        }
                        maxLength={3}
                        className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-3 text-white focus:border-blue-500 focus:outline-none"
                        placeholder="123"
                      />
                      {errors.cvv && <p className="text-red-400 text-sm mt-1">{errors.cvv}</p>}
                    </div>
                  </div>
                </>
              )}

              {/* Country */}
              <div>
                <label htmlFor="country" className="block text-sm font-medium text-slate-300 mb-2">
                  País *
                </label>
                <select
                  id="country"
                  value={formData.country}
                  onChange={(e) => setFormData({ ...formData, country: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-3 text-white focus:border-blue-500 focus:outline-none"
                >
                  <option value="">Selecciona tu país</option>
                  <option value="AR">Argentina</option>
                  <option value="BR">Brasil</option>
                  <option value="CL">Chile</option>
                  <option value="CO">Colombia</option>
                  <option value="MX">México</option>
                  <option value="PE">Perú</option>
                  <option value="ES">España</option>
                  <option value="US">Estados Unidos</option>
                  <option value="OTHER">Otro</option>
                </select>
                {errors.country && <p className="text-red-400 text-sm mt-1">{errors.country}</p>}
              </div>

              {/* Terms */}
              <div>
                <label className="flex items-start">
                  <input
                    type="checkbox"
                    checked={formData.acceptTerms}
                    onChange={(e) => setFormData({ ...formData, acceptTerms: e.target.checked })}
                    className="mt-1 mr-3"
                  />
                  <span className="text-sm text-slate-400">
                    Acepto los{' '}
                    <a href="#" className="text-blue-400 hover:text-blue-300">
                      Términos de Servicio
                    </a>{' '}
                    y la{' '}
                    <a href="#" className="text-blue-400 hover:text-blue-300">
                      Política de Privacidad
                    </a>
                  </span>
                </label>
                {errors.acceptTerms && (
                  <p className="text-red-400 text-sm mt-1">{errors.acceptTerms}</p>
                )}
              </div>

              {/* Submit Error */}
              {errors.submit && (
                <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
                  <p className="text-red-400 text-sm">{errors.submit}</p>
                </div>
              )}

              {/* Submit Button */}
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white py-4 rounded-lg text-lg font-semibold transition transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
              >
                {loading ? (
                  <span className="flex items-center justify-center">
                    <svg
                      className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      ></circle>
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      ></path>
                    </svg>
                    Procesando...
                  </span>
                ) : (
                  `Suscribirse por $${streetScoutPlan.price}/mes`
                )}
              </button>

              <div className="text-center text-sm text-slate-400">
                <p>🔒 Pago seguro procesado con encriptación SSL</p>
              </div>
            </form>
          </div>
        </div>

        {/* FAQ */}
        <div className="mt-16 bg-slate-800/30 rounded-2xl p-8 border border-slate-700">
          <h3 className="text-2xl font-bold text-white mb-6">Preguntas Frecuentes</h3>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h4 className="text-lg font-semibold text-blue-400 mb-2">
                ¿Puedo cancelar en cualquier momento?
              </h4>
              <p className="text-slate-300">
                Sí, puedes cancelar tu suscripción en cualquier momento desde tu panel de control. No
                hay penalizaciones ni cargos adicionales.
              </p>
            </div>
            <div>
              <h4 className="text-lg font-semibold text-blue-400 mb-2">
                ¿Qué pasa si supero el límite de búsquedas?
              </h4>
              <p className="text-slate-300">
                Recibirás una notificación cuando estés cerca del límite. Puedes actualizar a Elite
                Analyst para búsquedas ilimitadas.
              </p>
            </div>
            <div>
              <h4 className="text-lg font-semibold text-blue-400 mb-2">
                ¿Los mercados se renuevan mensualmente?
              </h4>
              <p className="text-slate-300">
                Puedes cambiar tus 3 mercados seleccionados una vez por mes. Los cambios se aplican al
                inicio de tu nuevo ciclo de facturación.
              </p>
            </div>
            <div>
              <h4 className="text-lg font-semibold text-blue-400 mb-2">
                ¿Hay período de prueba gratuito?
              </h4>
              <p className="text-slate-300">
                Sí, todos los planes nuevos incluyen 14 días de prueba gratuita con acceso completo a
                todas las características del plan.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
