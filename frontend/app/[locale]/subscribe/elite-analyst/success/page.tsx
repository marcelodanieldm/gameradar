'use client'

import { useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'

export default function EliteAnalystSuccessPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const supabase = createClient()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    verifySubscription()
  }, [])

  const verifySubscription = async () => {
    try {
      const sessionId = searchParams.get('session_id')
      
      if (!sessionId) {
        throw new Error('No session ID provided')
      }

      // Verify payment with backend
      const response = await fetch('/api/payment/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sessionId })
      })

      const data = await response.json()

      if (!response.ok || !data.verified) {
        throw new Error(data.error || 'Payment verification failed')
      }

      // Subscription verified successfully
      setLoading(false)

      // Redirect to Elite Analyst dashboard after 3 seconds
      setTimeout(() => {
        router.push('/dashboard-elite')
      }, 3000)

    } catch (err: any) {
      setError(err.message || 'Verification error')
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-indigo-900 to-blue-900 flex items-center justify-center p-4">
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-12 border border-white/20 text-center max-w-md">
          <div className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-6"></div>
          <h1 className="text-2xl font-bold text-white mb-2">Verifying Payment...</h1>
          <p className="text-gray-300">Please wait while we confirm your subscription</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-indigo-900 to-blue-900 flex items-center justify-center p-4">
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-12 border border-white/20 text-center max-w-md">
          <div className="text-6xl mb-6">❌</div>
          <h1 className="text-2xl font-bold text-white mb-4">Verification Failed</h1>
          <p className="text-gray-300 mb-6">{error}</p>
          <button
            onClick={() => router.push('/subscribe/elite-analyst')}
            className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white font-semibold rounded-lg transition-all"
          >
            Try Again
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-indigo-900 to-blue-900 flex items-center justify-center p-4">
      <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-12 border border-white/20 text-center max-w-2xl">
        <div className="text-6xl mb-6 animate-bounce">🎉</div>
        <h1 className="text-4xl font-bold text-white mb-4">Welcome to Elite Analyst!</h1>
        <p className="text-xl text-gray-300 mb-8">
          Your subscription is now active. You have access to all premium features.
        </p>

        <div className="grid grid-cols-2 gap-6 mb-8">
          <div className="bg-white/5 rounded-xl p-6">
            <div className="text-3xl mb-2">🌏</div>
            <h3 className="text-white font-semibold mb-1">All 7 Markets</h3>
            <p className="text-sm text-gray-300">Complete Asia coverage</p>
          </div>
          <div className="bg-white/5 rounded-xl p-6">
            <div className="text-3xl mb-2">♾️</div>
            <h3 className="text-white font-semibold mb-1">Unlimited Searches</h3>
            <p className="text-sm text-gray-300">No restrictions</p>
          </div>
          <div className="bg-white/5 rounded-xl p-6">
            <div className="text-3xl mb-2">🧠</div>
            <h3 className="text-white font-semibold mb-1">AI Analytics</h3>
            <p className="text-sm text-gray-300">Advanced insights</p>
          </div>
          <div className="bg-white/5 rounded-xl p-6">
            <div className="text-3xl mb-2">🔔</div>
            <h3 className="text-white font-semibold mb-1">TalentPing</h3>
            <p className="text-sm text-gray-300">Real-time alerts</p>
          </div>
          <div className="bg-white/5 rounded-xl p-6">
            <div className="text-3xl mb-2">🔌</div>
            <h3 className="text-white font-semibold mb-1">API Access</h3>
            <p className="text-sm text-gray-300">Full integration</p>
          </div>
          <div className="bg-white/5 rounded-xl p-6">
            <div className="text-3xl mb-2">⚡</div>
            <h3 className="text-white font-semibold mb-1">Priority Support</h3>
            <p className="text-sm text-gray-300">24/7 assistance</p>
          </div>
        </div>

        <div className="bg-purple-500/20 border border-purple-400/30 rounded-xl p-6 mb-8">
          <p className="text-purple-200">
            Redirecting to your dashboard in 3 seconds...
          </p>
        </div>

        <button
          onClick={() => router.push('/dashboard-elite')}
          className="px-8 py-4 bg-gradient-to-r from-purple-600 to-indigo-600 text-white font-semibold rounded-lg hover:from-purple-700 hover:to-indigo-700 transition-all"
        >
          Go to Dashboard Now
        </button>
      </div>
    </div>
  )
}
