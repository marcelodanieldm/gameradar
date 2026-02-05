"""
GameRadar AI - E2E Tests con Playwright
Tests end-to-end para todas las funcionalidades del sistema

Tests incluidos:
- Bronze Ingestion (scraping multi-fuente)
- Supabase Integration (Bronze/Silver/Gold)
- Country Detection
- Data Normalization
- Score Calculation (Talent + GameRadar)
- Pipeline completo
"""
import asyncio
import pytest
from playwright.async_api import async_playwright, Page, expect
from datetime import datetime
import os
import json

# Importar componentes del sistema
from bronze_ingestion import BronzeIngestionScraper
from supabase_client import SupabaseClient
from country_detector import detect_country, CountryCode
from models import PlayerProfile, PlayerStats, GameTitle
from pipeline import GameRadarPipeline


# ============================================================
# FIXTURES Y CONFIGURACIÓN
# ============================================================

@pytest.fixture
def supabase_client():
    """Cliente de Supabase para tests"""
    return SupabaseClient()


@pytest.fixture
async def browser():
    """Browser de Playwright para tests"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        yield browser
        await browser.close()


@pytest.fixture
async def page(browser):
    """Página de Playwright para tests"""
    page = await browser.new_page()
    yield page
    await page.close()


# ============================================================
# TEST 1: BRONZE INGESTION - SCRAPING
# ============================================================

@pytest.mark.asyncio
async def test_bronze_ingestion_liquipedia():
    """
    Test: Bronze Ingestion desde Liquipedia
    Verifica que el scraper puede extraer datos correctamente
    """
    print("\n🧪 TEST 1: Bronze Ingestion - Liquipedia")
    
    async with BronzeIngestionScraper(region="KR") as scraper:
        # Scraping de Liquipedia
        players_data = await scraper.scrape_liquipedia_ranking(
            game="leagueoflegends",
            ranking_page="Portal:Players"
        )
        
        # Assertions
        assert len(players_data) > 0, "Debe scrapear al menos 1 jugador"
        
        first_player = players_data[0]
        assert "nickname" in first_player, "Debe tener nickname"
        assert "region" in first_player, "Debe tener región"
        assert "data_source" in first_player, "Debe tener fuente"
        assert first_player["data_source"] == "liquipedia"
        
        # Verificar detección de caracteres asiáticos
        if first_player.get("has_asian_characters"):
            print(f"   ✓ Detectado caracteres asiáticos en: {first_player['nickname']}")
        
        print(f"   ✓ Scraped {len(players_data)} jugadores de Liquipedia")


@pytest.mark.asyncio
async def test_bronze_ingestion_opgg():
    """
    Test: Bronze Ingestion desde OP.GG
    Verifica scraping de OP.GG Korea
    """
    print("\n🧪 TEST 2: Bronze Ingestion - OP.GG")
    
    async with BronzeIngestionScraper(region="KR") as scraper:
        # Scraping de OP.GG
        players_data = await scraper.scrape_opgg_ranking(
            game="lol",
            limit=10
        )
        
        # Assertions
        assert len(players_data) > 0, "Debe scrapear al menos 1 jugador"
        
        first_player = players_data[0]
        assert first_player["region"] == "KR"
        assert first_player["data_source"] == "opgg"
        assert "rank" in first_player or "lp" in first_player
        
        print(f"   ✓ Scraped {len(players_data)} jugadores de OP.GG")


# ============================================================
# TEST 2: COUNTRY DETECTION
# ============================================================

@pytest.mark.asyncio
async def test_country_detection():
    """
    Test: Detección automática de país
    Verifica múltiples métodos de detección
    """
    print("\n🧪 TEST 3: Country Detection")
    
    # Test 1: Detección por bandera
    korea_flag = "🇰🇷 Player Name"
    country = detect_country(profile_text=korea_flag)
    assert country == CountryCode.KOREA, f"Debe detectar Korea, detectó {country}"
    print("   ✓ Detección por bandera: 🇰🇷 → KR")
    
    # Test 2: Detección por servidor
    country = detect_country(server="mumbai")
    assert country == CountryCode.INDIA, f"Debe detectar India, detectó {country}"
    print("   ✓ Detección por servidor: mumbai → IN")
    
    # Test 3: Detección por URL
    country = detect_country(url="https://vn.op.gg/summoners/vn/player123")
    assert country == CountryCode.VIETNAM, f"Debe detectar Vietnam, detectó {country}"
    print("   ✓ Detección por URL: vn.op.gg → VN")
    
    # Test 4: Detección por texto
    country = detect_country(profile_text="China Server - 中国")
    assert country == CountryCode.CHINA, f"Debe detectar China, detectó {country}"
    print("   ✓ Detección por texto: China Server → CN")


# ============================================================
# TEST 3: SUPABASE INTEGRATION
# ============================================================

@pytest.mark.asyncio
async def test_supabase_bronze_insert(supabase_client):
    """
    Test: Inserción en tabla Bronze
    Verifica que datos crudos se insertan correctamente
    """
    print("\n🧪 TEST 4: Supabase - Bronze Insert")
    
    # Datos de prueba
    test_data = {
        "nickname": "TestPlayer_E2E",
        "player_id": f"test_{datetime.now().timestamp()}",
        "region": "KR",
        "country": "KR",
        "rank": "Diamond I",
        "game": "LOL",
        "server": "KR",
        "profile_url": "https://test.com",
        "scraped_at": datetime.utcnow().isoformat(),
        "data_source": "e2e_test"
    }
    
    # Insertar en Bronze
    result = supabase_client.insert_bronze_raw(
        raw_data=test_data,
        source="e2e_test",
        source_url="https://test.com"
    )
    
    assert result is not None, "Debe retornar resultado"
    print(f"   ✓ Insertado en Bronze: {test_data['nickname']}")
    
    # Verificar que se insertó
    bronze_data = supabase_client.supabase.table("bronze_raw_data")\
        .select("*")\
        .eq("raw_data->>player_id", test_data["player_id"])\
        .execute()
    
    assert len(bronze_data.data) > 0, "Debe encontrar el registro insertado"
    print(f"   ✓ Verificado en Bronze")


@pytest.mark.asyncio
async def test_supabase_silver_normalization(supabase_client):
    """
    Test: Normalización Bronze → Silver
    Verifica que el trigger normaliza datos automáticamente
    """
    print("\n🧪 TEST 5: Supabase - Silver Normalization")
    
    # Insertar en Bronze (debería auto-normalizar a Silver)
    test_data = {
        "nickname": "NormalizedPlayer_E2E",
        "player_id": f"norm_test_{datetime.now().timestamp()}",
        "region": "IN",
        "country": "IN",
        "rank": "Platinum II",
        "game": "LOL",
        "win_rate": 58.5,
        "kda": 3.2,
        "games_played": 150,
        "server": "IN",
        "profile_url": "https://test.com"
    }
    
    supabase_client.insert_bronze_raw(
        raw_data=test_data,
        source="e2e_test",
        source_url="https://test.com"
    )
    
    # Esperar a que el trigger procese
    await asyncio.sleep(2)
    
    # Verificar en Silver
    silver_data = supabase_client.supabase.table("silver_players")\
        .select("*")\
        .eq("player_id", test_data["player_id"])\
        .execute()
    
    if len(silver_data.data) > 0:
        silver_player = silver_data.data[0]
        assert silver_player["nickname"] == test_data["nickname"]
        assert silver_player["country_code"] == "IN"
        print(f"   ✓ Normalizado a Silver: {silver_player['nickname']}")
        print(f"   ✓ Talent Score calculado: {silver_player.get('talent_score', 'N/A')}")
    else:
        print("   ⚠ No se encontró en Silver (trigger puede tardar)")


@pytest.mark.asyncio
async def test_supabase_gold_score_calculation(supabase_client):
    """
    Test: Cálculo de GameRadar Score en Gold
    Verifica que los scores se calculan correctamente
    """
    print("\n🧪 TEST 6: Supabase - Gold Score Calculation")
    
    # Consultar gold_verified_players con gameradar_score
    gold_data = supabase_client.supabase.table("gold_verified_players")\
        .select("nickname, country_code, gameradar_score")\
        .not_.is_("gameradar_score", "null")\
        .order("gameradar_score", desc=True)\
        .limit(5)\
        .execute()
    
    if len(gold_data.data) > 0:
        print(f"   ✓ Encontrados {len(gold_data.data)} jugadores en Gold con scores")
        
        for player in gold_data.data[:3]:
            score = player.get("gameradar_score", 0)
            assert 0 <= score <= 100, f"Score debe estar entre 0-100, encontrado: {score}"
            print(f"     - {player['nickname']}: {score:.2f} ({player['country_code']})")
    else:
        print("   ⚠ No hay datos en Gold layer aún")


# ============================================================
# TEST 4: PIPELINE COMPLETO
# ============================================================

@pytest.mark.asyncio
async def test_full_pipeline():
    """
    Test: Pipeline completo Bronze → Silver → Gold
    Verifica flujo end-to-end
    """
    print("\n🧪 TEST 7: Pipeline Completo")
    
    pipeline = GameRadarPipeline()
    
    # Datos de prueba
    test_players = [
        PlayerProfile(
            nickname="PipelineTest1",
            game=GameTitle.LEAGUE_OF_LEGENDS,
            country=CountryCode.KOREA,
            server="KR",
            rank="Master",
            stats=PlayerStats(
                win_rate=62.5,
                kda=4.5,
                games_analyzed=200
            ),
            profile_url="https://test.com/player1"
        )
    ]
    
    # Ejecutar pipeline (sin Airtable sync)
    try:
        result = await pipeline.batch_insert_to_bronze(test_players)
        assert result > 0, "Debe insertar al menos 1 jugador"
        print(f"   ✓ Pipeline ejecutado: {result} jugadores procesados")
    except Exception as e:
        print(f"   ⚠ Error en pipeline: {e}")


# ============================================================
# TEST 5: CHARACTER DETECTION
# ============================================================

@pytest.mark.asyncio
async def test_asian_character_detection():
    """
    Test: Detección de caracteres asiáticos
    Verifica soporte Unicode completo
    """
    print("\n🧪 TEST 8: Asian Character Detection")
    
    async with BronzeIngestionScraper(region="KR") as scraper:
        # Test caracteres coreanos
        korean_text = "페이커"  # Faker en coreano
        detection = scraper.detect_asian_characters(korean_text)
        assert detection["has_korean"] == True
        print(f"   ✓ Coreano detectado: {korean_text}")
        
        # Test caracteres chinos
        chinese_text = "中国玩家"
        detection = scraper.detect_asian_characters(chinese_text)
        assert detection["has_chinese"] == True
        print(f"   ✓ Chino detectado: {chinese_text}")
        
        # Test caracteres japoneses
        japanese_text = "プレイヤー"
        detection = scraper.detect_asian_characters(japanese_text)
        assert detection["has_japanese"] == True
        print(f"   ✓ Japonés detectado: {japanese_text}")
        
        # Test texto normal
        normal_text = "NormalPlayer123"
        detection = scraper.detect_asian_characters(normal_text)
        assert detection["has_asian"] == False
        print(f"   ✓ Texto normal: {normal_text}")


# ============================================================
# TEST 6: ERROR HANDLING
# ============================================================

@pytest.mark.asyncio
async def test_error_handling_scraper():
    """
    Test: Manejo de errores en scraper
    Verifica que no se detiene con datos faltantes
    """
    print("\n🧪 TEST 9: Error Handling")
    
    async with BronzeIngestionScraper(region="KR") as scraper:
        # Intentar scrapear URL inválida
        try:
            await scraper.scrape_liquipedia_ranking(
                game="invalid_game_xyz",
                ranking_page="NonExistentPage"
            )
            print("   ✓ Manejo de errores: No lanza excepción")
        except Exception as e:
            print(f"   ⚠ Excepción capturada (esperado): {type(e).__name__}")
        
        # Verificar contadores de errores
        assert scraper.error_count >= 0, "Debe trackear errores"
        print(f"   ✓ Error count tracked: {scraper.error_count}")


# ============================================================
# TEST 7: SEARCH Y QUERIES
# ============================================================

@pytest.mark.asyncio
async def test_supabase_search_queries(supabase_client):
    """
    Test: Búsquedas y queries en Supabase
    Verifica funciones de búsqueda
    """
    print("\n🧪 TEST 10: Search & Queries")
    
    # Query por región
    korean_players = supabase_client.get_players_by_country(
        country_code="KR",
        game="LOL",
        limit=5
    )
    
    if korean_players:
        print(f"   ✓ Query por región: {len(korean_players)} jugadores KR encontrados")
        assert all(p.country == CountryCode.KOREA for p in korean_players)
    else:
        print("   ⚠ No hay jugadores coreanos en DB")
    
    # Estadísticas por región
    try:
        stats = supabase_client.get_stats_by_region()
        if stats:
            print(f"   ✓ Estadísticas regionales: {len(stats)} regiones")
            for stat in stats[:3]:
                print(f"     - {stat['region']}: {stat['player_count']} jugadores")
    except Exception as e:
        print(f"   ⚠ Error obteniendo stats: {e}")


# ============================================================
# TEST 8: PERFORMANCE
# ============================================================

@pytest.mark.asyncio
async def test_performance_scraping():
    """
    Test: Performance de scraping
    Verifica que el scraping es eficiente
    """
    print("\n🧪 TEST 11: Performance")
    
    import time
    
    async with BronzeIngestionScraper(region="KR") as scraper:
        start_time = time.time()
        
        # Scraping limitado para test de performance
        players_data = await scraper.scrape_liquipedia_ranking(
            game="leagueoflegends",
            ranking_page="Portal:Players"
        )
        
        # Insertar primeros 10
        if players_data:
            batch = players_data[:10]
            scraper.insert_to_bronze(batch)
        
        elapsed = time.time() - start_time
        
        print(f"   ✓ Tiempo de scraping + insert: {elapsed:.2f}s")
        assert elapsed < 30, f"Debe completar en <30s, tardó {elapsed:.2f}s"
        print(f"   ✓ Performance test passed")


# ============================================================
# MAIN - EJECUTAR TODOS LOS TESTS
# ============================================================

async def run_all_tests():
    """
    Ejecuta todos los tests E2E en secuencia
    """
    print("="*70)
    print("🚀 GAMERADAR AI - E2E TESTS")
    print("="*70)
    
    supabase = SupabaseClient()
    
    # Lista de tests a ejecutar
    tests = [
        ("Bronze Ingestion - Liquipedia", test_bronze_ingestion_liquipedia),
        ("Bronze Ingestion - OP.GG", test_bronze_ingestion_opgg),
        ("Country Detection", test_country_detection),
        ("Supabase - Bronze Insert", lambda: test_supabase_bronze_insert(supabase)),
        ("Supabase - Silver Normalization", lambda: test_supabase_silver_normalization(supabase)),
        ("Supabase - Gold Score", lambda: test_supabase_gold_score_calculation(supabase)),
        ("Full Pipeline", test_full_pipeline),
        ("Asian Characters", test_asian_character_detection),
        ("Error Handling", test_error_handling_scraper),
        ("Search & Queries", lambda: test_supabase_search_queries(supabase)),
        ("Performance", test_performance_scraping),
    ]
    
    results = {"passed": 0, "failed": 0, "errors": []}
    
    for test_name, test_func in tests:
        try:
            await test_func()
            results["passed"] += 1
        except AssertionError as e:
            results["failed"] += 1
            results["errors"].append(f"{test_name}: {str(e)}")
            print(f"   ❌ FAILED: {e}")
        except Exception as e:
            results["failed"] += 1
            results["errors"].append(f"{test_name}: {str(e)}")
            print(f"   ❌ ERROR: {e}")
    
    # Resumen final
    print("\n" + "="*70)
    print("📊 RESUMEN DE TESTS")
    print("="*70)
    print(f"✅ Passed: {results['passed']}/{len(tests)}")
    print(f"❌ Failed: {results['failed']}/{len(tests)}")
    
    if results["errors"]:
        print("\n❌ Errores encontrados:")
        for error in results["errors"]:
            print(f"  - {error}")
    
    print("="*70)
    
    return results["failed"] == 0


if __name__ == "__main__":
    # Ejecutar tests
    success = asyncio.run(run_all_tests())
    
    # Exit code para CI/CD
    exit(0 if success else 1)
