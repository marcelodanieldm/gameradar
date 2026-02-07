# 🎯 GameRadar Discovery Hub

## Arquitectura Culturalmente Diferenciada

El **Discovery Hub** es una interfaz híbrida que adapta su UX según el mercado regional, implementando dos módulos completamente distintos:

---

## 📱 Street Scout (India/Vietnam)

### Concepto
Interfaz mobile-first optimizada para mercados con alta penetración de WhatsApp/Zalo y consumo de contenido vertical (TikTok/Reels).

### Características

#### 🔥 Sistema de Trending
- **Flame Badge**: Indicador visual para jugadores con GameRadar Score en ascenso rápido
- Simulación de `score_change` (a reemplazar con datos históricos reales)
- Clasificación: `score_change > 10` → Trending

#### 📱 UX Mobile-First
- Scroll vertical infinito con `IntersectionObserver`
- Cards grandes tipo TikTok con neón effects
- GameRadar Score prominente (font-size 32px, shadow-green-500)
- Stats compactas con color-coding:
  - Verde: Win Rate
  - Amarillo: Talent Score  
  - Púrpura: Rank

#### 💬 Social Sharing
**WhatsApp Integration:**
```typescript
const shareToWhatsApp = (player: Player) => {
  const message = t('search.shareMessage', {
    nickname: player.nickname,
    score: player.gameRadarScore
  });
  const url = `https://wa.me/?text=${encodeURIComponent(message)}`;
  window.open(url, '_blank');
};
```

**Zalo Integration:**
```typescript
const shareToZalo = (player: Player) => {
  const message = t('search.shareMessage', {
    nickname: player.nickname,
    score: player.gameRadarScore
  });
  const url = `https://zalo.me/share?text=${encodeURIComponent(message)}`;
  window.open(url, '_blank');
};
```

#### 🌍 Mensajes Localizados
- **Hindi**: "देखो! ${player.nickname} को GameRadar AI पर खोजा! 🔥 स्कोर: ${score}"
- **Vietnamese**: "Nhìn này! Tìm thấy ${player.nickname} trên GameRadar AI! 🔥 Điểm: ${score}"
- **English**: "Check out ${player.nickname} on GameRadar AI! 🔥 Score: ${score}"

---

## 🎯 Elite Analyst (Korea/China/Japan)

### Concepto
Plataforma de análisis técnico para scouts profesionales en mercados desktop-analytical.

### Características

#### 📊 Comparison A/B
- Selección de hasta 2 jugadores
- Vista lado-a-lado con highlighting automático del "winner"
- Comparación de 7 métricas:
  1. GameRadar Score
  2. Talent Score
  3. Win Rate
  4. Games Played
  5. Top Champions
  6. Skill Radar
  7. Rank

#### 📈 Skill Radar Charts
Visualización con **recharts**:
```tsx
<RadarChart data={radarData}>
  <PolarGrid stroke="#10b981" strokeOpacity={0.2} />
  <PolarAngleAxis dataKey="metric" stroke="#10b981" />
  <PolarRadiusAxis angle={90} domain={[0, 100]} stroke="#34d399" />
  <Radar
    name={player.nickname}
    dataKey="value"
    stroke="#10b981"
    fill="#10b981"
    fillOpacity={0.3}
  />
</RadarChart>
```

**Métricas del Radar:**
- GameRadar Score (normalizado a 100)
- Talent Score (normalizado a 100)
- Win Rate (porcentaje)
- KDA (normalizado: `Math.min(kda * 10, 100)`)

#### 📄 PDF Export
Genera reportes profesionales con **jsPDF + autoTable**:
```typescript
const exportToPDF = () => {
  const doc = new jsPDF();
  
  // Header
  doc.setFontSize(20);
  doc.text('GameRadar AI - Player Comparison Report', 105, 20, { align: 'center' });
  
  // Comparison Table
  autoTable(doc, {
    head: [['Metric', playerA.nickname, playerB.nickname, 'Winner']],
    body: [
      ['GameRadar Score', playerA.gameRadarScore, playerB.gameRadarScore, winner('gameRadar')],
      ['Talent Score', playerA.talentScore, playerB.talentScore, winner('talent')],
      // ...más métricas
    ],
    startY: 30,
    theme: 'grid',
    styles: { fontSize: 10, cellPadding: 5 },
  });
  
  doc.save(`comparison_${playerA.nickname}_vs_${playerB.nickname}.pdf`);
};
```

#### 📊 CSV Export
Exporta datos crudos para análisis en Excel/Python:
```typescript
const exportToCSV = () => {
  const headers = ['Player', 'GameRadar Score', 'Talent Score', 'Win Rate', 'Games Played', 'Rank'];
  const rows = [playerA, playerB].map(p => [
    p.nickname,
    p.gameRadarScore,
    p.talentScore,
    p.winRate,
    p.gamesPlayed,
    p.rank
  ]);
  
  const csvContent = [headers, ...rows]
    .map(row => row.join(','))
    .join('\n');
  
  const blob = new Blob([csvContent], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `comparison_${Date.now()}.csv`;
  link.click();
};
```

---

## 🎛️ Sistema de Auto-Detection

### Lógica de Detección
```typescript
const countryCode = useCountryDetection();
const isMobileHeavy = ['IN', 'VN', 'ID', 'PH'].includes(countryCode);
const isElite = ['KR', 'JP', 'CN', 'TW'].includes(countryCode);
```

### ViewMode Selector
Floating UI con 3 modos:
- **Auto**: Detección automática basada en `countryCode`
- **Street**: Fuerza Street Scout view
- **Elite**: Fuerza Elite Analyst view

---

## 🌍 Internacionalización

### Namespaces

#### `streetScout`
```json
{
  "title": "Street Scout",
  "subtitle": "Discover Rising Stars",
  "trending": "TRENDING",
  "talentScore": "Talent",
  "gameRadarScore": "GameRadar Score",
  "winRate": "Win Rate",
  "rank": "Rank",
  "topChampions": "Top Champions",
  "endOfList": "You've reached the end"
}
```

#### `eliteAnalyst`
```json
{
  "title": "Elite Analyst",
  "subtitle": "Professional Comparison & Analysis",
  "exportPDF": "Export PDF",
  "exportCSV": "Export CSV",
  "comparisonMode": "Comparison",
  "tableMode": "Table",
  "selectedCount": "{count} selected",
  "readyToCompare": "Ready to compare",
  "skillRadar": "Skill Radar",
  "winner": "Winner"
}
```

#### `discoveryHub`
```json
{
  "detectingRegion": "Detecting your region...",
  "errorTitle": "Failed to load players",
  "retry": "Retry",
  "autoMode": "Auto",
  "streetMode": "Street",
  "eliteMode": "Elite",
  "detectedRegion": "Region"
}
```

---

## 🎨 Estilos y Animaciones

### Neón Effects (Street Scout)
```css
.neon-green {
  box-shadow: 0 0 20px rgba(16, 185, 129, 0.3);
  border: 1px solid rgb(16, 185, 129);
}

.text-shadow-green {
  text-shadow: 0 0 10px rgba(16, 185, 129, 0.5);
}
```

### Framer Motion Transitions
```tsx
<AnimatePresence mode="wait">
  {viewMode === 'street' && (
    <motion.div
      key="street"
      initial={{ opacity: 0, x: -50 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 50 }}
      transition={{ duration: 0.3 }}
    >
      <StreetScoutView players={players} />
    </motion.div>
  )}
</AnimatePresence>
```

---

## 📦 Dependencias

### Nuevas Librerías
```json
{
  "recharts": "^2.10.4",        // Radar charts
  "jspdf": "^2.5.1",            // PDF generation
  "jspdf-autotable": "^3.8.2"   // PDF tables
}
```

### Instalación
```bash
cd frontend
npm install recharts jspdf jspdf-autotable
```

---

## 🚀 Uso

### Integración Básica
```tsx
import { GameRadarDiscoveryHub } from '@/components/GameRadarDiscoveryHub';

export default function DiscoveryPage() {
  return (
    <div className="min-h-screen bg-gray-950">
      <GameRadarDiscoveryHub />
    </div>
  );
}
```

### Con Región Manual
```tsx
<GameRadarDiscoveryHub 
  defaultViewMode="elite" 
  countryCode="KR"
/>
```

---

## 📊 Métricas de Performance

### Street Scout
- **Target**: < 2s First Contentful Paint
- **Infinite Scroll**: Batch de 20 jugadores por carga
- **Image Optimization**: Lazy loading con `loading="lazy"`

### Elite Analyst
- **PDF Generation**: < 1s para 2 jugadores
- **Radar Chart Render**: < 100ms con recharts
- **CSV Export**: Instant download (< 50ms)

---

## 🎯 Roadmap

### Sprint 3 (Próximo)
- [ ] Integrar datos históricos reales para trending
- [ ] Implementar filtros avanzados (por juego, rank, país)
- [ ] Agregar sistema de "Save Comparison" con persistencia
- [ ] Optimizar carga de imágenes con CDN

### Sprint 4
- [ ] A/B testing de mensajes de WhatsApp/Zalo
- [ ] Implementar analytics de exports PDF/CSV
- [ ] Agregar modo "Scout Team" para múltiples comparaciones
- [ ] Sistema de notificaciones para jugadores trending

---

## 🐛 Debugging

### Verificar Auto-Detection
```typescript
console.log('Country Code:', countryCode);
console.log('Is Mobile Heavy:', isMobileHeavy);
console.log('Is Elite:', isElite);
console.log('View Mode:', viewMode);
```

### Testear Trending Simulation
```typescript
// En GameRadarDiscoveryHub.tsx
const simulatedTrending = players.map(p => ({
  ...p,
  score_change: Math.random() * 20 - 5  // Range: -5 to +15
}));
```

---

## 📝 Contribución

Al modificar estos componentes, mantener:
1. **Relevancia Regional**: UX debe ser culturalmente apropiada
2. **Performance**: Mobile-first debe ser < 3s load time
3. **Accesibilidad**: ARIA labels para screen readers
4. **i18n**: Todas las strings deben pasar por `t()` de next-intl

---

## 📚 Referencias

- [Recharts Documentation](https://recharts.org/)
- [jsPDF Documentation](https://github.com/parallax/jsPDF)
- [Framer Motion](https://www.framer.com/motion/)
- [Next-intl](https://next-intl-docs.vercel.app/)
