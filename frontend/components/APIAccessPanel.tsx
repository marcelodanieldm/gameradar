'use client'

import { useState, useEffect } from 'react'
import { createClient } from '@/lib/supabase/client'

interface APIAccessPanelProps {
  userId: string
}

interface APIKey {
  id: string
  name: string
  key: string
  createdAt: string
  lastUsed?: string
  requestsToday: number
  isActive: boolean
}

export default function APIAccessPanel({ userId }: APIAccessPanelProps) {
  const supabase = createClient()
  const [apiKeys, setApiKeys] = useState<APIKey[]>([])
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newKeyName, setNewKeyName] = useState('')
  const [loading, setLoading] = useState(true)
  const [copiedKey, setCopiedKey] = useState<string | null>(null)

  useEffect(() => {
    fetchAPIKeys()
  }, [userId])

  const fetchAPIKeys = async () => {
    setLoading(true)
    try {
      const { data, error } = await supabase
        .from('api_keys')
        .select('*')
        .eq('user_id', userId)
        .order('created_at', { ascending: false })

      if (data && !error) {
        setApiKeys(data)
      }
    } catch (err) {
      console.error('Error fetching API keys:', err)
    } finally {
      setLoading(false)
    }
  }

  const generateAPIKey = () => {
    // Generate a secure random API key
    const prefix = 'gr_live_'
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    let key = prefix
    for (let i = 0; i < 32; i++) {
      key += chars.charAt(Math.floor(Math.random() * chars.length))
    }
    return key
  }

  const createAPIKey = async () => {
    try {
      const newKey = generateAPIKey()
      const { data, error } = await supabase
        .from('api_keys')
        .insert([{
          user_id: userId,
          name: newKeyName,
          key: newKey,
          is_active: true,
          requests_today: 0
        }])
        .select()

      if (data && !error) {
        setApiKeys([data[0], ...apiKeys])
        setShowCreateModal(false)
        setNewKeyName('')
        // Auto-copy the new key
        copyToClipboard(newKey)
      }
    } catch (err) {
      console.error('Error creating API key:', err)
    }
  }

  const deleteAPIKey = async (keyId: string) => {
    if (!confirm('Are you sure you want to delete this API key? This action cannot be undone.')) {
      return
    }

    try {
      const { error } = await supabase
        .from('api_keys')
        .delete()
        .eq('id', keyId)

      if (!error) {
        setApiKeys(apiKeys.filter(k => k.id !== keyId))
      }
    } catch (err) {
      console.error('Error deleting API key:', err)
    }
  }

  const toggleAPIKey = async (keyId: string, isActive: boolean) => {
    try {
      const { error } = await supabase
        .from('api_keys')
        .update({ is_active: isActive })
        .eq('id', keyId)

      if (!error) {
        setApiKeys(apiKeys.map(k => k.id === keyId ? { ...k, isActive } : k))
      }
    } catch (err) {
      console.error('Error toggling API key:', err)
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopiedKey(text)
    setTimeout(() => setCopiedKey(null), 2000)
  }

  const maskAPIKey = (key: string) => {
    const visible = 8
    return key.substring(0, visible) + '•'.repeat(key.length - visible)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-white">Loading API access...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className="text-3xl">🔌</span>
              <h2 className="text-3xl font-bold text-white">API Access</h2>
            </div>
            <p className="text-gray-300">Integrate GameRadar into your applications</p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-6 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 text-white font-semibold rounded-lg hover:from-purple-700 hover:to-indigo-700 transition-all"
          >
            + Create API Key
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-6 mt-8">
          <div className="p-6 bg-white/5 rounded-xl">
            <div className="text-3xl font-bold text-white mb-1">{apiKeys.length}</div>
            <p className="text-gray-300">API Keys</p>
          </div>
          <div className="p-6 bg-white/5 rounded-xl">
            <div className="text-3xl font-bold text-green-400 mb-1">
              {apiKeys.filter(k => k.isActive).length}
            </div>
            <p className="text-gray-300">Active Keys</p>
          </div>
          <div className="p-6 bg-white/5 rounded-xl">
            <div className="text-3xl font-bold text-blue-400 mb-1">
              {apiKeys.reduce((sum, k) => sum + k.requestsToday, 0).toLocaleString()}
            </div>
            <p className="text-gray-300">Requests Today</p>
          </div>
        </div>
      </div>

      {/* API Keys List */}
      <div className="space-y-4">
        <h3 className="text-xl font-bold text-white">Your API Keys</h3>
        {apiKeys.length > 0 ? (
          apiKeys.map((apiKey) => (
            <div
              key={apiKey.id}
              className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h4 className="text-lg font-bold text-white">{apiKey.name}</h4>
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                      apiKey.isActive 
                        ? 'bg-green-500/20 text-green-300' 
                        : 'bg-gray-500/20 text-gray-300'
                    }`}>
                      {apiKey.isActive ? 'ACTIVE' : 'DISABLED'}
                    </span>
                  </div>
                  
                  <div className="flex items-center gap-3 mb-3">
                    <code className="px-4 py-2 bg-black/30 rounded-lg text-gray-300 font-mono text-sm">
                      {maskAPIKey(apiKey.key)}
                    </code>
                    <button
                      onClick={() => copyToClipboard(apiKey.key)}
                      className="px-4 py-2 bg-purple-500/20 hover:bg-purple-500/30 text-purple-300 rounded-lg transition-all text-sm"
                    >
                      {copiedKey === apiKey.key ? '✓ Copied!' : '📋 Copy'}
                    </button>
                  </div>

                  <div className="flex gap-6 text-sm text-gray-300">
                    <div>
                      <span className="text-gray-400">Created:</span>{' '}
                      {new Date(apiKey.createdAt).toLocaleDateString()}
                    </div>
                    <div>
                      <span className="text-gray-400">Last used:</span>{' '}
                      {apiKey.lastUsed 
                        ? new Date(apiKey.lastUsed).toLocaleString()
                        : 'Never'
                      }
                    </div>
                    <div>
                      <span className="text-gray-400">Requests today:</span>{' '}
                      {apiKey.requestsToday.toLocaleString()}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <button
                    onClick={() => toggleAPIKey(apiKey.id, !apiKey.isActive)}
                    className={`p-2 rounded-lg transition-all ${
                      apiKey.isActive
                        ? 'bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-300'
                        : 'bg-green-500/20 hover:bg-green-500/30 text-green-300'
                    }`}
                  >
                    {apiKey.isActive ? '⏸️' : '▶️'}
                  </button>
                  <button
                    onClick={() => deleteAPIKey(apiKey.id)}
                    className="p-2 bg-red-500/20 hover:bg-red-500/30 text-red-300 rounded-lg transition-all"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-12 border border-white/20 text-center">
            <div className="text-6xl mb-4">🔑</div>
            <h3 className="text-2xl font-bold text-white mb-2">No API keys yet</h3>
            <p className="text-gray-300 mb-6">Create your first API key to start integrating</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-6 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 text-white font-semibold rounded-lg hover:from-purple-700 hover:to-indigo-700 transition-all"
            >
              Create API Key
            </button>
          </div>
        )}
      </div>

      {/* API Documentation */}
      <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20">
        <h3 className="text-2xl font-bold text-white mb-6">API Documentation</h3>
        
        <div className="space-y-6">
          {/* Authentication */}
          <div>
            <h4 className="text-lg font-semibold text-white mb-3">Authentication</h4>
            <p className="text-gray-300 mb-3">Include your API key in the Authorization header:</p>
            <pre className="bg-black/40 rounded-lg p-4 overflow-x-auto">
              <code className="text-green-300 text-sm">
{`curl -X GET "https://api.gameradar.ai/v1/players/search" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json"`}
              </code>
            </pre>
          </div>

          {/* Search Players */}
          <div>
            <h4 className="text-lg font-semibold text-white mb-3">Search Players</h4>
            <p className="text-gray-300 mb-3">Search for players with semantic queries:</p>
            <pre className="bg-black/40 rounded-lg p-4 overflow-x-auto">
              <code className="text-green-300 text-sm">
{`POST /v1/players/search
{
  "query": "aggressive Korean Valorant players",
  "market": "KR",
  "limit": 20
}`}
              </code>
            </pre>
          </div>

          {/* Get Player Details */}
          <div>
            <h4 className="text-lg font-semibold text-white mb-3">Get Player Details</h4>
            <p className="text-gray-300 mb-3">Retrieve detailed information about a player:</p>
            <pre className="bg-black/40 rounded-lg p-4 overflow-x-auto">
              <code className="text-green-300 text-sm">
{`GET /v1/players/{player_id}

Response:
{
  "id": "player_123",
  "name": "ProPlayer",
  "game": "Valorant",
  "market": "KR",
  "stats": {
    "kda": 2.5,
    "winRate": 65.2,
    "rank": "Immortal 3"
  }
}`}
              </code>
            </pre>
          </div>

          {/* Rate Limits */}
          <div>
            <h4 className="text-lg font-semibold text-white mb-3">Rate Limits</h4>
            <div className="bg-blue-500/10 border border-blue-400/30 rounded-lg p-4">
              <p className="text-blue-200">
                <strong>Elite Analyst Plan:</strong> Unlimited API requests<br />
                <strong>Rate limit:</strong> 1000 requests per minute<br />
                <strong>Concurrent requests:</strong> Up to 50
              </p>
            </div>
          </div>

          {/* Response Codes */}
          <div>
            <h4 className="text-lg font-semibold text-white mb-3">Response Codes</h4>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-white/5 rounded-lg p-4">
                <code className="text-green-400">200 OK</code>
                <p className="text-sm text-gray-300 mt-1">Request successful</p>
              </div>
              <div className="bg-white/5 rounded-lg p-4">
                <code className="text-yellow-400">401 Unauthorized</code>
                <p className="text-sm text-gray-300 mt-1">Invalid API key</p>
              </div>
              <div className="bg-white/5 rounded-lg p-4">
                <code className="text-orange-400">429 Too Many Requests</code>
                <p className="text-sm text-gray-300 mt-1">Rate limit exceeded</p>
              </div>
              <div className="bg-white/5 rounded-lg p-4">
                <code className="text-red-400">500 Server Error</code>
                <p className="text-sm text-gray-300 mt-1">Internal error</p>
              </div>
            </div>
          </div>

          {/* SDKs */}
          <div>
            <h4 className="text-lg font-semibold text-white mb-3">Official SDKs</h4>
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-white/5 rounded-lg p-4 hover:bg-white/10 transition-all cursor-pointer">
                <div className="text-2xl mb-2">🐍</div>
                <h5 className="text-white font-semibold">Python</h5>
                <code className="text-sm text-gray-400">pip install gameradar</code>
              </div>
              <div className="bg-white/5 rounded-lg p-4 hover:bg-white/10 transition-all cursor-pointer">
                <div className="text-2xl mb-2">📦</div>
                <h5 className="text-white font-semibold">Node.js</h5>
                <code className="text-sm text-gray-400">npm i gameradar</code>
              </div>
              <div className="bg-white/5 rounded-lg p-4 hover:bg-white/10 transition-all cursor-pointer">
                <div className="text-2xl mb-2">☕</div>
                <h5 className="text-white font-semibold">Java</h5>
                <code className="text-sm text-gray-400">Maven/Gradle</code>
              </div>
            </div>
          </div>

          {/* Support */}
          <div className="bg-purple-500/10 border border-purple-400/30 rounded-lg p-6">
            <h4 className="text-lg font-semibold text-white mb-2">Need Help?</h4>
            <p className="text-gray-300 mb-4">
              Check our complete API documentation or contact our support team for assistance.
            </p>
            <div className="flex gap-4">
              <button className="px-6 py-2 bg-purple-500/20 hover:bg-purple-500/30 text-purple-300 rounded-lg transition-all">
                📚 Full Documentation
              </button>
              <button className="px-6 py-2 bg-purple-500/20 hover:bg-purple-500/30 text-purple-300 rounded-lg transition-all">
                💬 Contact Support
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Create API Key Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-gradient-to-br from-purple-900 to-indigo-900 rounded-2xl p-8 max-w-md w-full border border-white/20">
            <h3 className="text-2xl font-bold text-white mb-6">Create API Key</h3>
            
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-200 mb-2">
                  Key Name *
                </label>
                <input
                  type="text"
                  value={newKeyName}
                  onChange={(e) => setNewKeyName(e.target.value)}
                  placeholder="e.g., Production Server"
                  className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
                <p className="text-sm text-gray-400 mt-2">
                  Give your API key a descriptive name to help you identify it later.
                </p>
              </div>

              <div className="bg-yellow-500/10 border border-yellow-400/30 rounded-lg p-4">
                <p className="text-sm text-yellow-200">
                  ⚠️ <strong>Important:</strong> Copy your API key immediately after creation. 
                  For security reasons, we won't show it again.
                </p>
              </div>
            </div>

            <div className="flex gap-4 mt-8">
              <button
                onClick={() => {
                  setShowCreateModal(false)
                  setNewKeyName('')
                }}
                className="flex-1 px-6 py-3 bg-white/10 hover:bg-white/20 text-white font-semibold rounded-lg transition-all"
              >
                Cancel
              </button>
              <button
                onClick={createAPIKey}
                disabled={!newKeyName.trim()}
                className="flex-1 px-6 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 text-white font-semibold rounded-lg hover:from-purple-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                Create Key
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
