'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'

export default function EliteAnalystSubscriptionPage() {
  const router = useRouter()
  const supabase = createClient()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [selectedMarkets, setSelectedMarkets] = useState<string[]>([
    'KR', 'JP', 'CN', 'TH', 'VN', 'PH', 'IN'
  ])

  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    organization: '',
    phone: '',
    useCase: '',
    expectedSearches: '200+',
  })

  const allMarkets = [
    { code: 'KR', name: 'South Korea', flag: '🇰🇷' },
    { code: 'JP', name: 'Japan', flag: '🇯🇵' },
    { code: 'CN', name: 'China', flag: '🇨🇳' },
    { code: 'TH', name: 'Thailand', flag: '🇹🇭' },
    { code: 'VN', name: 'Vietnam', flag: '🇻🇳' },
    { code: 'PH', name: 'Philippines', flag: '🇵🇭' },
    { code: 'IN', name: 'India', flag: '🇮🇳' },
  ]

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const { data: { session } } = await supabase.auth.getSession()
      
      if (!session) {
        router.push('/login')
        return
      }

      // Aquí iría la integración real con el payment gateway
      // Por ahora simulamos el proceso
      
      const response = await fetch('/api/payment/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          planType: 'elite-analyst',
          amount: 299,
          currency: 'USD',
          markets: selectedMarkets,
          organizationInfo: {
            name: formData.organization,
            contactName: formData.fullName,
            email: formData.email,
            phone: formData.phone,
          },
          metadata: {
            useCase: formData.useCase,
            expectedSearches: formData.expectedSearches,
          }
        }),
      })

      const data = await response.json()

      if (response.ok && data.paymentUrl) {
        window.location.href = data.paymentUrl
      } else {
        throw new Error(data.error || 'Payment initialization failed')
      }
    } catch (err: any) {
      setError(err.message || 'Error processing subscription')
      console.error('Subscription error:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-indigo-900 to-blue-900 py-12 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-block px-4 py-2 bg-purple-500/20 rounded-full border border-purple-400/30 mb-6">
            <span className="text-purple-300 font-semibold">ELITE ANALYST PLAN</span>
          </div>
          <h1 className="text-5xl font-bold text-white mb-4">
            Professional Team Access
          </h1>
          <p className="text-xl text-gray-300 max-w-2xl mx-auto">
            Complete platform access with unlimited searches, advanced analytics, and real-time alerts
          </p>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Left: Features List */}
          <div className="lg:col-span-1">
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20 sticky top-8">
              <div className="text-center mb-6">
                <div className="text-5xl font-bold text-white mb-2">
                  $299
                  <span className="text-2xl text-gray-300">/month</span>
                </div>
                <p className="text-gray-300">Billed monthly</p>
              </div>

              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-green-500 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-white font-semibold">All 7 Markets</h3>
                    <p className="text-sm text-gray-300">Complete Asia coverage</p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-green-500 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-white font-semibold">Unlimited Searches</h3>
                    <p className="text-sm text-gray-300">No usage restrictions</p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-green-500 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-white font-semibold">Advanced Analytics</h3>
                    <p className="text-sm text-gray-300">AI-powered insights</p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-green-500 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-white font-semibold">TalentPing Alerts</h3>
                    <p className="text-sm text-gray-300">Real-time notifications</p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-green-500 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-white font-semibold">API Access</h3>
                    <p className="text-sm text-gray-300">Integration ready</p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-green-500 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-white font-semibold">Priority Support</h3>
                    <p className="text-sm text-gray-300">24/7 assistance</p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-green-500 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-white font-semibold">Custom Reports</h3>
                    <p className="text-sm text-gray-300">PDF export unlimited</p>
                  </div>
                </div>
              </div>

              <div className="mt-6 p-4 bg-purple-500/20 rounded-lg border border-purple-400/30">
                <p className="text-sm text-purple-200 text-center">
                  <span className="font-semibold">Save 20%</span> with annual billing
                </p>
              </div>
            </div>
          </div>

          {/* Right: Subscription Form */}
          <div className="lg:col-span-2">
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20">
              <h2 className="text-2xl font-bold text-white mb-6">Organization Information</h2>
              
              {error && (
                <div className="mb-6 p-4 bg-red-500/20 border border-red-500/50 rounded-lg">
                  <p className="text-red-200">{error}</p>
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Contact Information */}
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-200 mb-2">
                      Full Name *
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.fullName}
                      onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
                      className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                      placeholder="John Doe"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-200 mb-2">
                      Email *
                    </label>
                    <input
                      type="email"
                      required
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                      placeholder="john@company.com"
                    />
                  </div>
                </div>

                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-200 mb-2">
                      Organization *
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.organization}
                      onChange={(e) => setFormData({ ...formData, organization: e.target.value })}
                      className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                      placeholder="Company Name"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-200 mb-2">
                      Phone (optional)
                    </label>
                    <input
                      type="tel"
                      value={formData.phone}
                      onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                      className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                      placeholder="+1 (555) 000-0000"
                    />
                  </div>
                </div>

                {/* Use Case */}
                <div>
                  <label className="block text-sm font-medium text-gray-200 mb-2">
                    Primary Use Case *
                  </label>
                  <select
                    required
                    value={formData.useCase}
                    onChange={(e) => setFormData({ ...formData, useCase: e.target.value })}
                    className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    <option value="">Select use case...</option>
                    <option value="professional-scouting">Professional Scouting</option>
                    <option value="team-management">Team Management</option>
                    <option value="tournament-organization">Tournament Organization</option>
                    <option value="analytics-research">Analytics & Research</option>
                    <option value="talent-agency">Talent Agency</option>
                    <option value="other">Other</option>
                  </select>
                </div>

                {/* Expected Usage */}
                <div>
                  <label className="block text-sm font-medium text-gray-200 mb-2">
                    Expected Monthly Searches
                  </label>
                  <select
                    value={formData.expectedSearches}
                    onChange={(e) => setFormData({ ...formData, expectedSearches: e.target.value })}
                    className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    <option value="200+">200+ searches</option>
                    <option value="500+">500+ searches</option>
                    <option value="1000+">1,000+ searches</option>
                    <option value="unlimited">Unlimited usage</option>
                  </select>
                </div>

                {/* Markets Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-200 mb-3">
                    Markets Access (All 7 included)
                  </label>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {allMarkets.map((market) => (
                      <div
                        key={market.code}
                        className="flex items-center gap-2 p-3 bg-white/5 border border-white/20 rounded-lg"
                      >
                        <div className="w-5 h-5 rounded bg-green-500 flex items-center justify-center flex-shrink-0">
                          <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                        </div>
                        <span className="text-white text-sm">
                          {market.flag} {market.name}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Terms */}
                <div className="flex items-start gap-3">
                  <input
                    type="checkbox"
                    id="terms"
                    required
                    className="mt-1 w-4 h-4 rounded border-gray-600 text-purple-600 focus:ring-purple-500"
                  />
                  <label htmlFor="terms" className="text-sm text-gray-300">
                    I agree to the{' '}
                    <a href="/terms" className="text-purple-400 hover:text-purple-300 underline">
                      Terms of Service
                    </a>{' '}
                    and{' '}
                    <a href="/privacy" className="text-purple-400 hover:text-purple-300 underline">
                      Privacy Policy
                    </a>
                  </label>
                </div>

                {/* Submit Button */}
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-4 px-6 bg-gradient-to-r from-purple-600 to-indigo-600 text-white font-semibold rounded-lg hover:from-purple-700 hover:to-indigo-700 focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                  {loading ? (
                    <span className="flex items-center justify-center gap-2">
                      <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      Processing...
                    </span>
                  ) : (
                    'Subscribe to Elite Analyst - $299/month'
                  )}
                </button>

                <p className="text-sm text-gray-400 text-center">
                  Secure payment processing. Cancel anytime.
                </p>
              </form>
            </div>

            {/* Trust Signals */}
            <div className="mt-8 grid md:grid-cols-3 gap-4">
              <div className="text-center p-4 bg-white/5 rounded-lg">
                <div className="text-3xl mb-2">🔒</div>
                <p className="text-sm text-gray-300">Secure Payment</p>
              </div>
              <div className="text-center p-4 bg-white/5 rounded-lg">
                <div className="text-3xl mb-2">💳</div>
                <p className="text-sm text-gray-300">Cancel Anytime</p>
              </div>
              <div className="text-center p-4 bg-white/5 rounded-lg">
                <div className="text-3xl mb-2">⚡</div>
                <p className="text-sm text-gray-300">Instant Access</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
