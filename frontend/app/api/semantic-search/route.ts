/**
 * API Route: Semantic Search (PROTECTED)
 * Endpoint para búsqueda semántica de jugadores usando OpenAI + Supabase
 * Requiere autenticación y suscripción activa
 * 
 * POST /api/semantic-search
 * Body: { query: string, region_filter?: string, match_threshold?: number, match_count?: number }
 */

import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";
import { withSubscription, canUserSearch, incrementSearchCount } from "@/lib/api/auth-middleware";
import OpenAI from "openai";

// Inicializar clientes (usar variables de entorno)
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY! // Service role para RPC functions
);

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY!,
});

export const POST = withSubscription(async (request: NextRequest, session: any) => {
  try {
    const userId = session.user.id;

    // Verificar límite de búsquedas
    const canSearch = await canUserSearch(userId);
    if (!canSearch) {
      return NextResponse.json(
        { 
          error: 'Search limit reached',
          message: 'Has alcanzado tu límite de búsquedas mensuales. Actualiza tu plan para continuar.'
        },
        { status: 429 }
      );
    }

    const body = await request.json();
    const {
      query,
      region_filter = null,
      match_threshold = 0.7,
      match_count = 20,
    } = body;

    // Validación
    if (!query || typeof query !== "string" || query.trim().length < 3) {
      return NextResponse.json(
        { error: "Query must be at least 3 characters" },
        { status: 400 }
      );
    }

    // 1. Generar embedding del query usando OpenAI
    console.log(`[Semantic Search] User ${userId} searching: "${query}"`);
    
    const embeddingResponse = await openai.embeddings.create({
      input: query,
      model: "text-embedding-3-small",
    });

    const queryEmbedding = embeddingResponse.data[0].embedding;

    // 2. Buscar jugadores similares usando la función match_players de Supabase
    console.log(
      `[Semantic Search] Searching players (threshold: ${match_threshold}, count: ${match_count})`
    );

    const { data, error } = await supabase.rpc("match_players", {
      query_embedding: queryEmbedding,
      match_threshold,
      match_count,
      region_filter,
    });

    if (error) {
      console.error("[Semantic Search] Supabase RPC error:", error);
      return NextResponse.json(
        { error: "Database search failed", details: error.message },
        { status: 500 }
      );
    }

    // 3. Enriquecer resultados con metadata adicional (opcional)
    // Hacer JOIN con silver_players para obtener avatar, rank, etc.
    const enrichedResults = await Promise.all(
      (data || []).map(async (result: any) => {
        const { data: playerData } = await supabase
          .from("silver_players")
          .select("avatar_url, rank, win_rate, kda, country_code, region, profile_url")
          .eq("id", result.player_id)
          .single();

        return {
          ...result,
          avatar_url: playerData?.avatar_url,
          rank: playerData?.rank,
          win_rate: playerData?.win_rate,
          kda: playerData?.kda,
          country: playerData?.country_code,
          region: playerData?.region,
          profile_url: playerData?.profile_url,
        };
      })
    );

    console.log(`[Semantic Search] Found ${enrichedResults.length} players`);

    // Incrementar contador de búsquedas
    await incrementSearchCount(userId);

    // Log de la búsqueda para analytics
    await supabase.from('search_logs').insert({
      user_id: userId,
      query: query,
      market: region_filter,
      results_count: enrichedResults.length,
    });

    return NextResponse.json({
      success: true,
      query,
      results: enrichedResults,
      count: enrichedResults.length,
    });
  } catch (error: any) {
    console.error("[Semantic Search] Error:", error);
    return NextResponse.json(
      {
        error: "Internal server error",
        message: error.message,
      },
      { status: 500 }
    );
  }
});

// GET method (opcional): para health check
export async function GET() {
  return NextResponse.json({
    service: "Semantic Search API",
    status: "operational",
    version: "1.0.0",
  });
}
