# AISearchBar - Componente de Búsqueda Semántica

## Descripción
Componente de búsqueda inteligente con AI que utiliza embeddings semánticos de OpenAI para encontrar jugadores basándose en lenguaje natural.

## Características

### 🌍 Localización Completa
Placeholders en 7 idiomas:
- **Hindi**: "अपने अगले स्टार खिलाड़ी को खोजें..."
- **Coreano**: "다음 스타 플레이어를 찾으세요..."
- **Vietnamita**: "Tìm kiếm ngôi sao tiếp theo của bạn..."
- **Japonés**: "次のスターブレイヤーを見つける..."
- **Chino**: "寻找你的下一个明星选手..."
- **Tailandés**: "ค้นหาผู้เล่นดาวรุ่งคนต่อไปของคุณ..."
- **English**: "Find your next star player..."

### 🎨 Vistas Adaptativas por Región

#### Mobile-Heavy (India/Vietnam/Tailandia)
- Cards grandes con diseño vertical
- GameRadar Score prominente con efectos neón
- Colores vibrantes (gradientes verde/púrpura/cyan)
- Botones WhatsApp/Zalo destacados
- Avatares grandes (64px)
- Shadow effects con glow

#### Technical (Corea/China/Japón)
- Lista compacta y densa
- Stats inline (WR%, KDA)
- Avatares pequeños (40px)
- Diseño minimalista
- Hover effects sutiles
- Eficiencia espacial

### ✨ Animaciones
- Framer Motion para transiciones suaves
- AI Sparkle icon animado (rotación y escala)
- Fade in para resultados (staggered)
- Smooth dropdown con backdrop blur
- Scale effects en hover

### 🎯 Funcionalidades

1. **Búsqueda en Tiempo Real**
   - Mínimo 3 caracteres
   - Enter para buscar
   - Escape para cerrar

2. **Resultados Enriquecidos**
   - Avatar, rank, región
   - Win rate y KDA
   - GameRadar Score
   - Similarity score (%)
   - Links a perfil

3. **Error Handling**
   - Validación de input
   - Mensajes localizados
   - Retry automático
   - Loading states

## Uso

### Instalación de Dependencias

```bash
cd frontend
npm install framer-motion openai
```

### Configuración de Variables de Entorno

Crear archivo `.env.local` en `frontend/`:

```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
OPENAI_API_KEY=sk-your-openai-api-key
```

### Uso Básico

```tsx
import AISearchBar from "@/components/AISearchBar";

export default function SearchPage() {
  return (
    <div className="container mx-auto p-8">
      <h1 className="text-4xl font-bold mb-8">
        Búsqueda Inteligente de Jugadores
      </h1>

      <AISearchBar
        supabaseUrl={process.env.NEXT_PUBLIC_SUPABASE_URL!}
        supabaseKey={process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!}
      />
    </div>
  );
}
```

### Con Callback de Resultados

```tsx
import { useState } from "react";
import AISearchBar from "@/components/AISearchBar";

export default function AdvancedSearch() {
  const [results, setResults] = useState([]);

  return (
    <div className="space-y-8">
      <AISearchBar
        supabaseUrl={process.env.NEXT_PUBLIC_SUPABASE_URL!}
        supabaseKey={process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!}
        onResultsChange={(newResults) => {
          setResults(newResults);
          console.log("Encontrados:", newResults.length, "jugadores");
        }}
        regionFilter="KR" // Opcional: filtrar solo Corea
      />

      {/* Mostrar resultados en otro componente */}
      <div className="grid grid-cols-3 gap-4">
        {results.map((player) => (
          <PlayerCard key={player.player_id} player={player} />
        ))}
      </div>
    </div>
  );
}
```

### Integración con Dashboard

```tsx
"use client";

import { useState } from "react";
import AISearchBar from "@/components/AISearchBar";
import TransculturalDashboard from "@/components/TransculturalDashboard";

export default function MainDashboard() {
  const [searchActive, setSearchActive] = useState(false);

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Header con búsqueda */}
      <header className="sticky top-0 z-50 bg-slate-900/80 backdrop-blur-md border-b border-slate-800">
        <div className="container mx-auto px-4 py-4">
          <AISearchBar
            supabaseUrl={process.env.NEXT_PUBLIC_SUPABASE_URL!}
            supabaseKey={process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!}
            onResultsChange={(results) => setSearchActive(results.length > 0)}
          />
        </div>
      </header>

      {/* Dashboard */}
      {!searchActive && (
        <TransculturalDashboard
          supabaseUrl={process.env.NEXT_PUBLIC_SUPABASE_URL!}
          supabaseKey={process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!}
        />
      )}
    </div>
  );
}
```

## Ejemplos de Búsqueda

### En Lenguaje Natural (Inglés)
```
"aggressive korean players with high KDA"
"mobile gaming talent from India"
"challenger players with consistent performance"
"rising stars in Vietnam"
```

### Multilingüe

**Hindi:**
```
"भारत से मोबाइल गेमिंग खिलाड़ी"
"उच्च KDA वाले आक्रामक खिलाड़ी"
```

**Coreano:**
```
"한국의 공격적인 플레이어"
"높은 승률을 가진 챌린저"
```

**Vietnamita:**
```
"tài năng game mobile từ Việt Nam"
"người chơi có tỷ lệ thắng cao"
```

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────┐
│  AISearchBar Component (Client)                     │
│  - Input con localización                           │
│  - Validación y UI states                           │
│  - Rendering adaptativo por región                  │
└─────────────────┬───────────────────────────────────┘
                  │
                  │ POST /api/semantic-search
                  ↓
┌─────────────────────────────────────────────────────┐
│  Next.js API Route (Server)                         │
│  - Recibe query en lenguaje natural                 │
│  - Genera embedding con OpenAI                      │
│  - Llama a match_players() en Supabase              │
│  - Enriquece resultados con JOIN                    │
└─────────────────┬───────────────────────────────────┘
                  │
                  │ RPC call
                  ↓
┌─────────────────────────────────────────────────────┐
│  Supabase PostgreSQL + pgvector                     │
│  - match_players() function                         │
│  - Cosine similarity search                         │
│  - IVFFlat index optimization                       │
│  - Retorna top N jugadores similares                │
└─────────────────────────────────────────────────────┘
```

## Performance

### Tiempos Esperados
- **Embedding generation**: ~200ms (OpenAI API)
- **Database search**: ~50-100ms (con índice IVFFlat)
- **Data enrichment**: ~50ms (JOIN con silver_players)
- **Total**: ~300-400ms

### Optimizaciones
1. **Caching**: Implementar cache de embeddings para queries frecuentes
2. **Debouncing**: Agregar debounce de 300ms en el input
3. **Lazy loading**: Cargar avatares de forma lazy
4. **Pagination**: Implementar "Load More" para >20 resultados

## Costos

### OpenAI API
- **Modelo**: text-embedding-3-small
- **Precio**: $0.02 per 1M tokens
- **Tokens por query**: ~20-50 tokens
- **Costo por búsqueda**: ~$0.000001 USD (prácticamente gratis)
- **10,000 búsquedas**: ~$0.01 USD

### Supabase
- Incluido en plan gratuito (500MB database)
- pgvector no tiene costo adicional

## Troubleshooting

### Error: "OPENAI_API_KEY no configurada"
```bash
# Verificar .env.local
echo $OPENAI_API_KEY

# Reiniciar servidor Next.js
npm run dev
```

### Error: "match_players function does not exist"
```sql
-- Ejecutar en Supabase SQL Editor
-- Verificar que existe la función
SELECT proname FROM pg_proc WHERE proname = 'match_players';

-- Si no existe, ejecutar gold_analytics.sql
```

### Resultados vacíos
- Verificar que existen embeddings en gold_analytics:
  ```sql
  SELECT COUNT(*) FROM gold_analytics WHERE embedding_vector IS NOT NULL;
  ```
- Reducir match_threshold (ej: 0.5 en lugar de 0.7)
- Verificar que el query tiene al menos 3 caracteres

### Animaciones lentas
- Reducir stagger delay en Framer Motion
- Deshabilitar backdrop-blur en dispositivos móviles
- Usar CSS transitions en lugar de Framer Motion para efectos simples

## Próximas Mejoras

- [ ] Autocompletion con sugerencias
- [ ] Historial de búsquedas (localStorage)
- [ ] Filtros avanzados (rank, region, game)
- [ ] Export de resultados (CSV/JSON)
- [ ] Voice search (Web Speech API)
- [ ] Búsqueda por imagen (avatar similarity)
- [ ] Keyboard navigation (Arrow keys)
- [ ] Dark/Light mode toggle

## Licencia

Parte del proyecto GameRadar AI - Sprint 2: Semantic Search & Transcultural UX
