# GameRadar AI - Frontend Dashboard

## Overview
Transcultural Next.js dashboard that adapts UI based on user's region:
- **Korea/China/Japan**: Dense 15-column stats table for data-heavy analysis
- **India/Vietnam/Thailand**: Large card layout with profile photos and WhatsApp contact button

## Features
- ✅ **Country Detection**: Auto-detects user country via browser locale + IP geolocation
- ✅ **Adaptive UI**: Two distinct layouts optimized for regional preferences
- ✅ **Multi-language**: Support for 7 languages (EN, KO, ZH, HI, VI, TH, JA)
- ✅ **Dark Theme**: Professional dark mode with glass morphism effects
- ✅ **Real-time Data**: Fetches player data from Supabase Gold layer
- ✅ **Responsive**: Mobile-first design with Tailwind CSS
- ✅ **Performance**: Next.js 14 App Router with server components
- ✨ **Discovery Hub**: Culturally-differentiated player discovery interface
  - **Street Scout** (India/Vietnam): TikTok-style infinite scroll with WhatsApp/Zalo sharing
  - **Elite Analyst** (Korea/China/Japan): Professional comparison tool with PDF/CSV export
- 🔍 **AI Search**: Semantic search powered by OpenAI embeddings (1536D vectors)
- 📊 **Skill Radar**: Interactive radar charts for player skill visualization

## Tech Stack
- **Framework**: Next.js 14.1.0 (App Router)
- **Language**: TypeScript 5.3.3
- **Styling**: Tailwind CSS 3.4.1
- **i18n**: next-intl 3.9.0
- **Database**: Supabase (PostgreSQL + pgvector)
- **Icons**: Lucide React
- **Animation**: Framer Motion 11.0.3
- **Charts**: Recharts 2.10.4
- **PDF Export**: jsPDF 2.5.1 + jspdf-autotable 3.8.2
- **AI**: OpenAI text-embedding-3-small

## Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env.local

# Add your Supabase credentials to .env.local
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## Project Structure

```
frontend/
├── app/
│   ├── [locale]/           # Internationalized routes
│   │   ├── layout.tsx      # Root layout with i18n provider
│   │   └── page.tsx        # Home page
│   ├── api/
│   │   └── semantic-search/  # AI search endpoint
│   │       └── route.ts    
│   └── globals.css         # Global styles + Tailwind
├── components/
│   ├── RadarDashboard.tsx           # Main dashboard component
│   ├── TransculturalDashboard.tsx   # Regional adaptive dashboard
│   ├── GameRadarDiscoveryHub.tsx    # Discovery Hub (auto-detection)
│   ├── StreetScoutView.tsx          # TikTok-style for India/Vietnam
│   ├── EliteAnalystView.tsx         # Professional comparison for Korea/China/Japan
│   ├── AISearchBar.tsx              # Semantic search with adaptive results
│   ├── DenseStatsTable.tsx          # Dense table for KR/CN/JP
│   └── PlayerCards.tsx              # Card layout for IN/VN/TH
├── hooks/
│   └── useCountryDetection.ts  # Country detection logic
├── messages/
│   ├── en.json             # English translations
│   ├── ko.json             # Korean
│   ├── zh.json             # Chinese
│   ├── hi.json             # Hindi
│   ├── vi.json             # Vietnamese
│   ├── th.json             # Thai
│   └── ja.json             # Japanese
├── middleware.ts           # next-intl locale routing
├── i18n.ts                 # i18n configuration
├── next.config.js          # Next.js config
├── tailwind.config.js      # Tailwind config
└── tsconfig.json           # TypeScript config
```

## UI Modes

### Dense Table Mode (Korea, China, Japan)
- 15 columns: Rank, Nickname, Country, Game, Win Rate, KDA, Games, Champion Pool, Top 3 Champions, Talent Score
- Sortable columns with arrow indicators
- Compact design for power users
- Hover effects and smooth animations

### Card Layout Mode (India, Vietnam, Thailand)
- Large profile cards with photos
- Prominent stats display (Win Rate, KDA, Games, Champion Pool)
- WhatsApp contact button for direct messaging
- Visual champion icons and flags

## Country Detection Strategy

1. **Browser Locale** (Primary): Checks `navigator.language`
2. **IP Geolocation** (Fallback): Uses ipapi.co API
3. **Default**: Falls back to Card Layout if detection fails

## Discovery Hub 🎯

The **GameRadar Discovery Hub** is a culturally-differentiated interface that adapts to regional user behavior:

### Street Scout (India/Vietnam/Indonesia/Philippines)
- **UX**: TikTok-style vertical infinite scroll
- **Features**: 
  - 🔥 Trending badges for rising players
  - 💬 WhatsApp/Zalo share buttons with pre-written messages
  - 📱 Mobile-first large cards with neón effects
  - ⚡ Auto-loading on scroll intersection

### Elite Analyst (Korea/China/Japan/Taiwan)
- **UX**: Professional comparison and analysis tools
- **Features**:
  - 📊 A/B comparison tables with automatic winner detection
  - 📈 Skill radar charts (GameRadar, Talent, WinRate, KDA)
  - 📄 PDF export for professional reports
  - 📊 CSV export for data analysis
  - 🎯 Side-by-side player comparison

**Documentation**: See [DISCOVERY_HUB.md](../DISCOVERY_HUB.md) for full technical details.

## AI Semantic Search 🔍

Powered by OpenAI's `text-embedding-3-small` model:
- Natural language queries ("aggressive mid laner with high KDA")
- 1536D vector embeddings stored in PostgreSQL with pgvector
- Regional adaptive results (Mobile-Heavy vs Technical display)
- Cost: ~$0.001 per 1000 players

**Documentation**: See [AISEARCHBAR.md](../AISEARCHBAR.md) and [EMBEDDING_GENERATOR.md](../EMBEDDING_GENERATOR.md)

## Environment Variables

```bash
NEXT_PUBLIC_SUPABASE_URL      # Your Supabase project URL
NEXT_PUBLIC_SUPABASE_ANON_KEY # Your Supabase anonymous key
```

## Commands

```bash
npm run dev          # Start development server (localhost:3000)
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
```

## Database Requirements

Expects Supabase table `gold_verified_players` with schema:
```typescript
{
  id: string
  nickname: string
  game: string
  country: string
  rank: string
  stats: {
    win_rate: number
    kda: number
    games_played: number
    champion_pool: number
  }
  top_champions: Array<{
    name: string
    win_rate: number
  }>
  talent_score: number
  profile_photo_url?: string
  contact_whatsapp?: string
  created_at: string
  updated_at: string
}
```

## Customization

### Adding a New Language
1. Create `messages/{locale}.json` with translations
2. Add locale to `next.config.js` locales array
3. Update `middleware.ts` matcher pattern

### Changing UI Mode Regions
Edit `useCountryDetection.ts`:
```typescript
const DENSE_TABLE_COUNTRIES = ['KR', 'CN', 'JP']  // Add/remove countries
const CARD_LAYOUT_COUNTRIES = ['IN', 'VN', 'TH']
```

### Styling
- Colors: `tailwind.config.js` → `theme.extend.colors`
- Fonts: `tailwind.config.js` → `theme.extend.fontFamily`
- Animations: `tailwind.config.js` → `theme.extend.animation`

## Performance Optimizations
- Server components by default (Next.js 14)
- Client components only for interactivity (`'use client'`)
- Image optimization with next/image
- Tailwind CSS purging (automatic in production)
- Lazy loading for player cards

## Browser Support
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Deployment

### Vercel (Recommended)
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

### Manual Build
```bash
npm run build
npm run start
```

## API Integration
Connect to existing Python backend by updating Supabase queries in [RadarDashboard.tsx](components/RadarDashboard.tsx).

## Troubleshooting

**Country detection not working?**
- Check browser console for API errors
- Verify ipapi.co is accessible
- Test with different browser locales

**Translations not loading?**
- Ensure all JSON files have matching keys
- Check middleware.ts locale configuration
- Verify i18n.ts import paths

**Supabase connection fails?**
- Verify .env.local has correct credentials
- Check Supabase project is active
- Test database query in Supabase dashboard

## Contributing
Built for GameRadar AI Asia e-sports scouting platform. See backend documentation in `../docs/`.

## License
Proprietary - GameRadar AI 2024
