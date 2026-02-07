# Generador de Embeddings Semánticos

## Descripción
Script Python que genera embeddings semánticos de 1536 dimensiones usando el modelo `text-embedding-3-small` de OpenAI. Estos embeddings permiten búsqueda semántica basada en lenguaje natural.

## Diferencia con `skill_vector_embeddings.py`
- **skill_vector_embeddings.py**: Genera vectores de 4 dimensiones (`skill_vector`) basados en heurísticas matemáticas [kda, winrate, agresividad, versatilidad]
- **embedding_generator.py**: Genera vectores de 1536 dimensiones (`embedding_vector`) usando modelos de lenguaje para búsqueda semántica

## Requisitos

### 1. Instalar dependencias
```bash
pip install openai==1.12.0
```

### 2. Configurar API Key de OpenAI
Agregar a tu archivo `.env`:
```env
OPENAI_API_KEY=sk-your-openai-api-key-here
```

### 3. Ejecutar el SQL en Supabase
Asegúrate de haber ejecutado el SQL de `gold_analytics.sql` que incluye:
- Columna `embedding_vector vector(1536)`
- Índice `idx_gold_embedding_vector`
- Función `match_players()`

## Uso

### Comando básico (procesar 100 jugadores)
```bash
python embedding_generator.py
```

### Con filtros
```bash
# Solo jugadores coreanos
python embedding_generator.py --country KR --limit 500

# Solo jugadores de League of Legends
python embedding_generator.py --game LOL --limit 200

# Combinación de filtros
python embedding_generator.py --country IN --game VAL --limit 150
```

### Modo dry-run (prueba sin guardar)
```bash
python embedding_generator.py --dry-run --limit 10
```

### Ajustar tamaño de batch
```bash
# Procesar de 20 en 20 (útil si tienes rate limits bajos)
python embedding_generator.py --batch-size 20 --limit 100
```

## Cómo funciona

### 1. Genera descripciones naturales
Para cada jugador, crea un texto descriptivo:
```
"Jugador de LOL en región KR con 5.2 de KDA y 62% de winrate en el rango Challenger 
especializado en Yasuo, Zed, Lee Sin. Nickname: Faker"
```

### 2. Obtiene embeddings de OpenAI
Usa el modelo `text-embedding-3-small` (1536 dimensiones) para convertir el texto en vector numérico.

### 3. Guarda en gold_analytics
Actualiza la columna `embedding_vector` en la tabla `gold_analytics`.

## Procesamiento en batches
- **Batch size por defecto**: 50 jugadores
- **Delay entre batches**: 0.5 segundos (evita rate limits de OpenAI)
- **Eficiencia**: Procesa ~100 jugadores/minuto (~6000/hora)

## Costos estimados (OpenAI)

Con `text-embedding-3-small`:
- **Precio**: $0.02 por 1M tokens
- **Tokens promedio por jugador**: ~50 tokens
- **Costo por 1000 jugadores**: ~$0.001 USD (prácticamente gratis)
- **Costo por 100k jugadores**: ~$0.10 USD

## Ejemplos de uso en producción

### Procesar todos los jugadores nuevos diariamente
```bash
# Cron job diario (00:00 AM)
0 0 * * * cd /path/to/gameradar && python embedding_generator.py --limit 10000
```

### Procesar por región (para testing)
```bash
# Primero India (mobile-heavy)
python embedding_generator.py --country IN --limit 1000

# Luego Corea (PC-heavy)
python embedding_generator.py --country KR --limit 1000
```

### Monitoreo de progreso
El script usa `loguru` y muestra:
- ✓ Jugadores procesados exitosamente
- ✗ Errores (con detalles)
- 📦 Progreso de batches
- 📊 Resumen final

## Búsqueda semántica (uso del embedding)

Una vez generados los embeddings, puedes buscar jugadores usando la función SQL:

```sql
-- Obtener embedding de una consulta en tu backend
-- Ejemplo: "aggressive korean player with high winrate"
-- (convertir a embedding usando OpenAI)

SELECT * FROM match_players(
    query_embedding := '[0.123, 0.456, ...]'::vector(1536),
    match_threshold := 0.7,
    match_count := 10,
    region_filter := 'KR'
);
```

## Troubleshooting

### Error: "OPENAI_API_KEY no configurada"
```bash
# Verificar que existe en .env
cat .env | grep OPENAI_API_KEY

# O exportar temporalmente
export OPENAI_API_KEY=sk-your-key
```

### Error: "rate limit exceeded"
```bash
# Reducir batch size y aumentar delay
python embedding_generator.py --batch-size 10
```

### Error: "column embedding_vector does not exist"
```sql
-- Ejecutar en Supabase SQL Editor
ALTER TABLE gold_analytics ADD COLUMN embedding_vector vector(1536);
CREATE INDEX idx_gold_embedding_vector 
    ON gold_analytics USING ivfflat (embedding_vector vector_cosine_ops)
    WITH (lists = 100);
```

## Monitoreo

### Ver jugadores con embeddings
```sql
SELECT 
    COUNT(*) as total_con_embeddings,
    COUNT(DISTINCT country_code) as paises,
    COUNT(DISTINCT game) as juegos
FROM gold_analytics
WHERE embedding_vector IS NOT NULL;
```

### Ver jugadores sin embeddings (pendientes)
```sql
SELECT COUNT(*) as pendientes
FROM silver_players sp
LEFT JOIN gold_analytics ga ON sp.id = ga.player_id
WHERE ga.embedding_vector IS NULL OR ga.id IS NULL;
```

## Performance

### Optimización del índice IVFFlat
Para bases de datos grandes (>100k jugadores), ajustar el parámetro `lists`:

```sql
-- Para 100k+ jugadores
CREATE INDEX idx_gold_embedding_vector 
    ON gold_analytics USING ivfflat (embedding_vector vector_cosine_ops)
    WITH (lists = 1000);

-- Para 1M+ jugadores
CREATE INDEX idx_gold_embedding_vector 
    ON gold_analytics USING ivfflat (embedding_vector vector_cosine_ops)
    WITH (lists = 5000);
```

### Fórmula: `lists = sqrt(num_rows)`
- 10k rows → lists=100
- 100k rows → lists=316
- 1M rows → lists=1000

## Integración con Frontend

En Next.js/React:
```typescript
// 1. Usuario escribe query natural
const searchQuery = "jugadores agresivos de Corea con alto KDA";

// 2. Backend convierte a embedding
const embedding = await openai.embeddings.create({
  input: searchQuery,
  model: "text-embedding-3-small"
});

// 3. Búsqueda en Supabase
const { data } = await supabase.rpc('match_players', {
  query_embedding: embedding.data[0].embedding,
  match_threshold: 0.7,
  match_count: 20,
  region_filter: 'KR'
});
```

## Conclusión

Este script es la **capa de IA semántica** de GameRadar, permitiendo:
- ✅ Búsqueda en lenguaje natural
- ✅ Recomendaciones basadas en similitud
- ✅ Descubrimiento inteligente de talento
- ✅ Clustering automático de estilos de juego

Para más detalles técnicos, ver `SPRINT2_SUMMARY.md`.
