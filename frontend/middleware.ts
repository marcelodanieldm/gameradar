import { NextRequest } from 'next/server'
import createMiddleware from 'next-intl/middleware'

export default createMiddleware({
  // A list of all locales that are supported
  locales: ['en', 'ko', 'zh', 'hi', 'vi', 'th', 'ja'],
  
  // Used when no locale matches
  defaultLocale: 'en',
  
  // Automatically detect user's locale
  localeDetection: true
})

export const config = {
  // Match only internationalized pathnames
  matcher: ['/', '/(ko|zh|hi|vi|th|ja|en)/:path*']
}
