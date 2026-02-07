"""
Ejemplos de uso del sistema de embeddings semánticos de GameRadar AI
"""
from openai import OpenAI
from supabase import create_client
import os


def search_players_semantic(
    query: str,
    match_threshold: float = 0.7,
    match_count: int = 20,
    region_filter: str = None
):
    """
    Búsqueda semántica de jugadores usando lenguaje natural.
    
    Args:
        query: Consulta en lenguaje natural (ej: "jugadores agresivos de Corea")
        match_threshold: Similitud mínima (0-1)
        match_count: Número máximo de resultados
        region_filter: Filtro opcional por región (KR, IN, VN, etc.)
    
    Returns:
        Lista de jugadores encontrados con su score de similitud
    """
    # 1. Inicializar clientes
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )
    
    # 2. Convertir consulta a embedding
    print(f"🔍 Generando embedding para: '{query}'")
    embedding_response = openai_client.embeddings.create(
        input=query,
        model="text-embedding-3-small"
    )
    query_embedding = embedding_response.data[0].embedding
    
    # 3. Buscar en Supabase usando la función match_players
    print(f"🎯 Buscando jugadores con similitud >= {match_threshold}")
    
    response = supabase.rpc(
        'match_players',
        {
            'query_embedding': query_embedding,
            'match_threshold': match_threshold,
            'match_count': match_count,
            'region_filter': region_filter
        }
    ).execute()
    
    # 4. Formatear resultados
    players = response.data
    print(f"✅ Encontrados {len(players)} jugadores\n")
    
    return players


# ============================================================
# EJEMPLO 1: Búsqueda por estilo de juego
# ============================================================
def example_aggressive_korean_players():
    """Buscar jugadores agresivos coreanos con alto KDA"""
    print("=" * 60)
    print("EJEMPLO 1: Jugadores agresivos de Corea")
    print("=" * 60)
    
    results = search_players_semantic(
        query="aggressive korean players with high KDA and winrate",
        match_threshold=0.75,
        match_count=10,
        region_filter="KR"
    )
    
    for player in results:
        print(f"🏆 {player['handle']}")
        print(f"   Score: {player['gameradar_score']:.2f}")
        print(f"   Similitud: {player['similarity']:.3f}")
        print()


# ============================================================
# EJEMPLO 2: Búsqueda multilingüe
# ============================================================
def example_multilingual_search():
    """Búsqueda en diferentes idiomas"""
    print("=" * 60)
    print("EJEMPLO 2: Búsqueda multilingüe")
    print("=" * 60)
    
    queries = [
        ("English", "mobile gaming grinders from India", "IN"),
        ("Hindi", "भारत से मोबाइल गेमिंग खिलाड़ी", "IN"),
        ("Korean", "한국의 공격적인 플레이어", "KR"),
        ("Japanese", "日本の技術的なプレイヤー", "JP"),
    ]
    
    for language, query, region in queries:
        print(f"\n🌐 {language}: '{query}'")
        results = search_players_semantic(
            query=query,
            match_threshold=0.7,
            match_count=5,
            region_filter=region
        )
        print(f"   → {len(results)} resultados")


# ============================================================
# EJEMPLO 3: Búsqueda por rango y región
# ============================================================
def example_rank_based_search():
    """Buscar jugadores de alto rango en diferentes regiones"""
    print("=" * 60)
    print("EJEMPLO 3: Búsqueda por rango")
    print("=" * 60)
    
    results = search_players_semantic(
        query="high rank challenger players with consistent performance",
        match_threshold=0.8,
        match_count=15,
        region_filter=None  # Todas las regiones
    )
    
    # Agrupar por región
    by_region = {}
    for player in results:
        region = player.get('region', 'Unknown')
        if region not in by_region:
            by_region[region] = []
        by_region[region].append(player)
    
    print("\n📊 Resultados por región:")
    for region, players in by_region.items():
        print(f"\n🌍 {region}: {len(players)} jugadores")
        for p in players[:3]:  # Top 3 por región
            print(f"   • {p['handle']} (Score: {p['gameradar_score']:.2f})")


# ============================================================
# EJEMPLO 4: Recomendación de jugadores similares
# ============================================================
def example_similar_players():
    """Encontrar jugadores similares a un perfil dado"""
    print("=" * 60)
    print("EJEMPLO 4: Jugadores similares a Faker")
    print("=" * 60)
    
    # Descripción del perfil objetivo
    target_profile = """
    Professional mid-lane player from Korea with exceptional KDA (above 5.0),
    very high winrate (above 60%), plays in Challenger rank,
    specializes in control mages and assassins
    """
    
    results = search_players_semantic(
        query=target_profile,
        match_threshold=0.75,
        match_count=10,
        region_filter="KR"
    )
    
    print("\n👥 Jugadores con perfil similar:")
    for i, player in enumerate(results, 1):
        print(f"{i}. {player['handle']}")
        print(f"   GameRadar Score: {player['gameradar_score']:.2f}")
        print(f"   Similitud: {player['similarity']:.1%}")
        print()


# ============================================================
# EJEMPLO 5: Descubrimiento de talentos emergentes
# ============================================================
def example_talent_discovery():
    """Encontrar talentos emergentes en regiones mobile-heavy"""
    print("=" * 60)
    print("EJEMPLO 5: Descubrimiento de talentos (India/Vietnam)")
    print("=" * 60)
    
    regions = ["IN", "VN"]
    
    for region in regions:
        print(f"\n🔎 Buscando en {region}...")
        results = search_players_semantic(
            query="rising mobile gaming talent with high winrate and consistent performance",
            match_threshold=0.7,
            match_count=5,
            region_filter=region
        )
        
        if results:
            print(f"✨ Top talentos en {region}:")
            for player in results:
                print(f"   • {player['handle']} - Score: {player['gameradar_score']:.2f}")
        else:
            print(f"   No se encontraron resultados")


# ============================================================
# EJEMPLO 6: Análisis de competitividad regional
# ============================================================
def example_regional_competitiveness():
    """Comparar nivel competitivo entre regiones"""
    print("=" * 60)
    print("EJEMPLO 6: Análisis de competitividad regional")
    print("=" * 60)
    
    query = "top competitive players with high skill rating and tournament experience"
    regions = ["KR", "CN", "JP", "IN", "VN"]
    
    print("\n📈 Comparación de competitividad:")
    for region in regions:
        results = search_players_semantic(
            query=query,
            match_threshold=0.75,
            match_count=10,
            region_filter=region
        )
        
        if results:
            avg_score = sum(p['gameradar_score'] for p in results) / len(results)
            avg_similarity = sum(p['similarity'] for p in results) / len(results)
            
            print(f"\n🌍 {region}:")
            print(f"   Jugadores encontrados: {len(results)}")
            print(f"   GameRadar Score promedio: {avg_score:.2f}")
            print(f"   Similitud promedio: {avg_similarity:.1%}")


# ============================================================
# MAIN: Ejecutar todos los ejemplos
# ============================================================
if __name__ == "__main__":
    import sys
    
    examples = {
        "1": ("Jugadores agresivos de Corea", example_aggressive_korean_players),
        "2": ("Búsqueda multilingüe", example_multilingual_search),
        "3": ("Búsqueda por rango", example_rank_based_search),
        "4": ("Jugadores similares", example_similar_players),
        "5": ("Descubrimiento de talentos", example_talent_discovery),
        "6": ("Competitividad regional", example_regional_competitiveness),
    }
    
    if len(sys.argv) > 1:
        # Ejecutar ejemplo específico
        example_num = sys.argv[1]
        if example_num in examples:
            name, func = examples[example_num]
            print(f"\n🚀 Ejecutando: {name}\n")
            func()
        else:
            print(f"❌ Ejemplo '{example_num}' no existe")
            print("\nEjemplos disponibles:")
            for num, (name, _) in examples.items():
                print(f"  {num}. {name}")
    else:
        # Ejecutar todos los ejemplos
        print("\n" + "=" * 60)
        print("EJEMPLOS DE BÚSQUEDA SEMÁNTICA - GameRadar AI")
        print("=" * 60)
        
        for num, (name, func) in examples.items():
            print(f"\n\n🎯 Ejemplo {num}: {name}")
            input("Presiona Enter para continuar...")
            func()
        
        print("\n" + "=" * 60)
        print("✅ Todos los ejemplos completados")
        print("=" * 60)
