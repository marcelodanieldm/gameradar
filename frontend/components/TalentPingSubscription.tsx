"use client";

import React, { useState } from 'react';
import { useRegion } from '@/hooks/useRegion';

interface TalentPingSubscriptionProps {
  userId: string;
  onSubscribe?: (data: SubscriptionData) => void;
}

interface SubscriptionData {
  userId: string;
  region: string;
  channels: string[];
  whatsappNumber?: string;
  telegramId?: string;
  email?: string;
  alertFrequency: 'instant' | 'daily' | 'weekly';
}

/**
 * TalentPing Subscription Component
 * Cultural UX/UI: 
 * - India/Vietnam: Prominent WhatsApp/Telegram subscription
 * - Korea/Japan/China: Professional email + PDF reports
 */
export default function TalentPingSubscription({ 
  userId, 
  onSubscribe 
}: TalentPingSubscriptionProps) {
  const { region } = useRegion();
  const [channels, setChannels] = useState<string[]>([]);
  const [whatsappNumber, setWhatsappNumber] = useState('');
  const [telegramId, setTelegramId] = useState('');
  const [email, setEmail] = useState('');
  const [alertFrequency, setAlertFrequency] = useState<'instant' | 'daily' | 'weekly'>('instant');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Determine if region is "push-first" (India/Vietnam) or "professional" (Korea/Japan/China)
  const isPushFirst = ['india', 'vietnam'].includes(region.toLowerCase());
  const isProfessional = ['korea', 'japan', 'china'].includes(region.toLowerCase());

  const handleChannelToggle = (channel: string) => {
    setChannels(prev => 
      prev.includes(channel) 
        ? prev.filter(c => c !== channel)
        : [...prev, channel]
    );
  };

  const handleSubscribe = async () => {
    setIsSubmitting(true);
    
    const subscriptionData: SubscriptionData = {
      userId,
      region,
      channels,
      whatsappNumber: channels.includes('whatsapp') ? whatsappNumber : undefined,
      telegramId: channels.includes('telegram') ? telegramId : undefined,
      email: channels.includes('email') ? email : undefined,
      alertFrequency
    };

    try {
      const response = await fetch('/api/talent-ping/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(subscriptionData)
      });

      if (response.ok) {
        onSubscribe?.(subscriptionData);
      }
    } catch (error) {
      console.error('Subscription error:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      {/* Header - Different messaging for different regions */}
      <div className="mb-6">
        {isPushFirst ? (
          <>
            <h2 className="text-3xl font-bold text-gray-900 mb-2">
              🔥 Never Miss a Talent! 🔥
            </h2>
            <p className="text-gray-600">
              Get instant alerts when we find players matching your criteria. 
              Subscribe via WhatsApp or Telegram for real-time updates!
            </p>
          </>
        ) : (
          <>
            <h2 className="text-3xl font-bold text-gray-900 mb-2">
              Talent-Ping Alert System
            </h2>
            <p className="text-gray-600">
              Receive comprehensive talent reports with detailed analytics and PDF documentation.
            </p>
          </>
        )}
      </div>

      {/* Channel Selection */}
      <div className="space-y-4 mb-6">
        <h3 className="text-lg font-semibold text-gray-800">Notification Channels</h3>

        {/* WhatsApp - Prominent for India/Vietnam */}
        {(isPushFirst || region === 'global') && (
          <div className={`border rounded-lg p-4 ${
            channels.includes('whatsapp') ? 'border-green-500 bg-green-50' : 'border-gray-300'
          }`}>
            <label className="flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={channels.includes('whatsapp')}
                onChange={() => handleChannelToggle('whatsapp')}
                className="w-5 h-5 text-green-600"
              />
              <div className="ml-3 flex-1">
                <div className="flex items-center">
                  <span className="text-2xl mr-2">💬</span>
                  <span className="font-semibold text-gray-900">WhatsApp Alerts</span>
                  {isPushFirst && (
                    <span className="ml-2 px-2 py-1 bg-orange-500 text-white text-xs rounded-full">
                      RECOMMENDED
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-600 mt-1">
                  Get instant push notifications on WhatsApp
                </p>
              </div>
            </label>
            
            {channels.includes('whatsapp') && (
              <input
                type="tel"
                placeholder="+91 9876543210"
                value={whatsappNumber}
                onChange={(e) => setWhatsappNumber(e.target.value)}
                className="mt-3 w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
              />
            )}
          </div>
        )}

        {/* Telegram - For India/Vietnam */}
        {(isPushFirst || region === 'global') && (
          <div className={`border rounded-lg p-4 ${
            channels.includes('telegram') ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
          }`}>
            <label className="flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={channels.includes('telegram')}
                onChange={() => handleChannelToggle('telegram')}
                className="w-5 h-5 text-blue-600"
              />
              <div className="ml-3 flex-1">
                <div className="flex items-center">
                  <span className="text-2xl mr-2">✈️</span>
                  <span className="font-semibold text-gray-900">Telegram Alerts</span>
                </div>
                <p className="text-sm text-gray-600 mt-1">
                  Receive alerts via Telegram bot
                </p>
              </div>
            </label>
            
            {channels.includes('telegram') && (
              <input
                type="text"
                placeholder="@yourusername or Telegram ID"
                value={telegramId}
                onChange={(e) => setTelegramId(e.target.value)}
                className="mt-3 w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            )}
          </div>
        )}

        {/* Email - Premium for Korea/Japan/China */}
        <div className={`border rounded-lg p-4 ${
          channels.includes('email') ? 'border-purple-500 bg-purple-50' : 'border-gray-300'
        }`}>
          <label className="flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={channels.includes('email')}
              onChange={() => handleChannelToggle('email')}
              className="w-5 h-5 text-purple-600"
            />
            <div className="ml-3 flex-1">
              <div className="flex items-center">
                <span className="text-2xl mr-2">📧</span>
                <span className="font-semibold text-gray-900">Email Reports</span>
                {isProfessional && (
                  <>
                    <span className="ml-2 px-2 py-1 bg-blue-600 text-white text-xs rounded-full">
                      PROFESSIONAL
                    </span>
                    <span className="ml-2 px-2 py-1 bg-gray-200 text-gray-700 text-xs rounded">
                      + PDF Attached
                    </span>
                  </>
                )}
              </div>
              <p className="text-sm text-gray-600 mt-1">
                {isProfessional 
                  ? 'Comprehensive reports with PDF documentation for presentations'
                  : 'Detailed email notifications with player analysis'
                }
              </p>
            </div>
          </label>
          
          {channels.includes('email') && (
            <input
              type="email"
              placeholder="your.email@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-3 w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
            />
          )}
        </div>

        {/* In-App Notifications */}
        <div className={`border rounded-lg p-4 ${
          channels.includes('in_app') ? 'border-indigo-500 bg-indigo-50' : 'border-gray-300'
        }`}>
          <label className="flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={channels.includes('in_app')}
              onChange={() => handleChannelToggle('in_app')}
              className="w-5 h-5 text-indigo-600"
            />
            <div className="ml-3 flex-1">
              <div className="flex items-center">
                <span className="text-2xl mr-2">🔔</span>
                <span className="font-semibold text-gray-900">Dashboard Notifications</span>
              </div>
              <p className="text-sm text-gray-600 mt-1">
                See alerts on your GameRadar dashboard
              </p>
            </div>
          </label>
        </div>
      </div>

      {/* Alert Frequency */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-3">Alert Frequency</h3>
        <div className="flex gap-3">
          {(['instant', 'daily', 'weekly'] as const).map((freq) => (
            <button
              key={freq}
              onClick={() => setAlertFrequency(freq)}
              className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all ${
                alertFrequency === freq
                  ? 'bg-blue-600 text-white shadow-lg'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {freq === 'instant' && '⚡ Instant'}
              {freq === 'daily' && '📅 Daily Digest'}
              {freq === 'weekly' && '📊 Weekly Summary'}
            </button>
          ))}
        </div>
      </div>

      {/* Subscribe Button */}
      <button
        onClick={handleSubscribe}
        disabled={channels.length === 0 || isSubmitting}
        className={`w-full py-4 px-6 rounded-lg font-bold text-lg transition-all ${
          channels.length === 0
            ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
            : isPushFirst
            ? 'bg-gradient-to-r from-orange-500 to-red-500 text-white hover:shadow-xl'
            : 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:shadow-xl'
        }`}
      >
        {isSubmitting ? (
          <span className="flex items-center justify-center">
            <svg className="animate-spin h-5 w-5 mr-3" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            Subscribing...
          </span>
        ) : (
          <>
            {isPushFirst ? '🔥 Subscribe Now - Never Miss Talent!' : '✓ Activate Talent-Ping Alerts'}
          </>
        )}
      </button>

      {/* Privacy Note */}
      <p className="mt-4 text-xs text-gray-500 text-center">
        Your contact information is encrypted and used only for talent alerts. 
        You can unsubscribe anytime.
      </p>
    </div>
  );
}
