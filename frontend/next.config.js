/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    serverActions: {
      allowedOrigins: ['localhost:3000']
    }
  },
  images: {
    domains: [
      'avatars.githubusercontent.com',
      'lh3.googleusercontent.com',
      'static-cdn.jtvnw.net',
      'i.imgur.com'
    ]
  },
  i18n: {
    locales: ['en', 'ko', 'zh', 'hi', 'vi', 'th', 'ja'],
    defaultLocale: 'en',
    localeDetection: true
  }
}

module.exports = nextConfig
