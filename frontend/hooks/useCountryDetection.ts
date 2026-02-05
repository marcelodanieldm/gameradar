'use client'

import { useState, useEffect } from 'react'

export type CountryCode = 
  | 'KR' // Korea
  | 'CN' // China
  | 'IN' // India
  | 'VN' // Vietnam
  | 'TH' // Thailand
  | 'JP' // Japan
  | 'US' // United States
  | 'UNKNOWN'

export type RegionUiMode = 'DENSE_TABLE' | 'CARD_LAYOUT'

interface CountryDetectionResult {
  countryCode: CountryCode
  uiMode: RegionUiMode
  isLoading: boolean
  error: string | null
}

const DENSE_TABLE_COUNTRIES: CountryCode[] = ['KR', 'CN', 'JP']
const CARD_LAYOUT_COUNTRIES: CountryCode[] = ['IN', 'VN', 'TH']

/**
 * Custom hook to detect user's country and determine UI layout mode
 * Uses multiple detection strategies with fallback priority:
 * 1. Browser locale (navigator.language)
 * 2. IP geolocation API (ipapi.co)
 * 3. Default to UNKNOWN
 */
export function useCountryDetection(): CountryDetectionResult {
  const [countryCode, setCountryCode] = useState<CountryCode>('UNKNOWN')
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    detectCountry()
  }, [])

  async function detectCountry() {
    try {
      setIsLoading(true)
      
      // Strategy 1: Browser locale
      const browserLocale = navigator.language || navigator.languages?.[0]
      if (browserLocale) {
        const localeCountry = extractCountryFromLocale(browserLocale)
        if (localeCountry !== 'UNKNOWN') {
          setCountryCode(localeCountry)
          setIsLoading(false)
          return
        }
      }

      // Strategy 2: IP Geolocation API
      try {
        const response = await fetch('https://ipapi.co/json/', {
          method: 'GET',
          headers: { 'Accept': 'application/json' }
        })
        
        if (response.ok) {
          const data = await response.json()
          const detectedCountry = normalizeCountryCode(data.country_code)
          if (detectedCountry !== 'UNKNOWN') {
            setCountryCode(detectedCountry)
            setIsLoading(false)
            return
          }
        }
      } catch (apiError) {
        console.warn('IP geolocation API failed:', apiError)
      }

      // Strategy 3: Default fallback
      setCountryCode('UNKNOWN')
      setIsLoading(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to detect country')
      setCountryCode('UNKNOWN')
      setIsLoading(false)
    }
  }

  const uiMode: RegionUiMode = DENSE_TABLE_COUNTRIES.includes(countryCode)
    ? 'DENSE_TABLE'
    : 'CARD_LAYOUT'

  return { countryCode, uiMode, isLoading, error }
}

function extractCountryFromLocale(locale: string): CountryCode {
  const countryMap: Record<string, CountryCode> = {
    'ko': 'KR',
    'ko-KR': 'KR',
    'zh': 'CN',
    'zh-CN': 'CN',
    'zh-Hans': 'CN',
    'zh-TW': 'CN',
    'zh-Hant': 'CN',
    'hi': 'IN',
    'hi-IN': 'IN',
    'vi': 'VN',
    'vi-VN': 'VN',
    'th': 'TH',
    'th-TH': 'TH',
    'ja': 'JP',
    'ja-JP': 'JP',
    'en-US': 'US',
  }

  return countryMap[locale] || 'UNKNOWN'
}

function normalizeCountryCode(code: string): CountryCode {
  const validCodes: CountryCode[] = ['KR', 'CN', 'IN', 'VN', 'TH', 'JP', 'US']
  const upperCode = code.toUpperCase() as CountryCode
  return validCodes.includes(upperCode) ? upperCode : 'UNKNOWN'
}
