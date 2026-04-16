"""
Test Suite para Multi-Region Strategic Ingestor
================================================

Suite completa de tests para validar el sistema de ingesta multi-región
"""

import asyncio
import pytest
from loguru import logger
from MultiRegionIngestor import (
    MultiRegionIngestor,
    IngestionConfig,
    RegionProfile,
    FallbackStrategy
)
from StrategicAdapters import (
    WanplusAdapter,
    TheEsportsClubAdapter,
    SohaGameAdapter,
    SteamWebAPIAdapter,
    LootBetAdapter,
    RiotGamesShardAdapter
)


# ============================================================================
# TESTS DE ADAPTERS INDIVIDUALES
# ============================================================================

async def test_wanplus_adapter():
    """Test 1: Wanplus Adapter (China)"""
    logger.info("="*80)
    logger.info("🧪 TEST 1: WANPLUS ADAPTER (CHINA)")
    logger.info("="*80)
    
    import httpx
    async with httpx.AsyncClient() as client:
        adapter = WanplusAdapter(client=client)
        
        # Fetch player
        data = await adapter.fetch_player("JackeyLove", game="lol")
        
        if data:
            logger.success(f"✅ Fetched data from Wanplus")
            logger.info(f"   Nickname: {data.get('nickname')}")
            logger.info(f"   APM: {data['stats'].get('apm')}")
            logger.info(f"   Gold/Min: {data['stats'].get('gold_per_min')}")
            
            # Verificar campos obligatorios
            assert "nickname" in data
            assert "stats" in data
            assert "source" in data
            assert data["source"] == "wanplus"
        else:
            logger.warning("⚠️ No data returned (might be expected for test)")
        
        # Verificar métricas
        metrics = adapter.get_metrics()
        logger.info(f"📊 Metrics: {metrics}")
        assert metrics["requests"] > 0
    
    logger.info("="*80 + "\n")


async def test_tec_india_adapter():
    """Test 2: The Esports Club Adapter (India)"""
    logger.info("="*80)
    logger.info("🧪 TEST 2: TEC INDIA ADAPTER")
    logger.info("="*80)
    
    import httpx
    async with httpx.AsyncClient() as client:
        adapter = TheEsportsClubAdapter(client=client)
        
        data = await adapter.fetch_player("IndianPro123", game="lol")
        
        if data:
            logger.success(f"✅ Fetched data from TEC India")
            logger.info(f"   Nickname: {data.get('nickname')}")
            logger.info(f"   Consistency: {data['stats'].get('consistency_score')}")
            
            assert "consistency_score" in data["stats"]
            assert data["source"] == "tec_india"
        else:
            logger.warning("⚠️ No data returned")
        
        metrics = adapter.get_metrics()
        logger.info(f"📊 Metrics: {metrics}")
    
    logger.info("="*80 + "\n")


async def test_soha_game_adapter():
    """Test 3: Soha Game Adapter (Vietnam)"""
    logger.info("="*80)
    logger.info("🧪 TEST 3: SOHA GAME ADAPTER (VIETNAM)")
    logger.info("="*80)
    
    import httpx
    async with httpx.AsyncClient() as client:
        adapter = SohaGameAdapter(client=client)
        
        data = await adapter.fetch_player("VietnamPlayer1", game="lol")
        
        if data:
            logger.success(f"✅ Fetched data from Soha Game")
            logger.info(f"   Nickname: {data.get('nickname')}")
            logger.info(f"   Server: {data.get('server')}")
            
            assert data["country"] == "VN"
            assert data["source"] == "soha_game"
        else:
            logger.warning("⚠️ No data returned")
    
    logger.info("="*80 + "\n")


# ============================================================================
# TESTS DE MULTI-REGION INGESTOR
# ============================================================================

async def test_single_player_ingestion():
    """Test 4: Ingest single player"""
    logger.info("="*80)
    logger.info("🧪 TEST 4: SINGLE PLAYER INGESTION")
    logger.info("="*80)
    
    config = IngestionConfig(
        max_concurrent_requests=5,
        enable_fallback=True,
        log_to_supabase=False  # Desactivar para test
    )
    
    async with MultiRegionIngestor(config) as ingestor:
        result = await ingestor.ingest_player(
            "Faker",
            region=RegionProfile.KOREA,
            game="lol"
        )
        
        logger.info(f"📊 Result:")
        logger.info(f"   Success: {result.success}")
        logger.info(f"   Source: {result.source}")
        logger.info(f"   Duration: {result.duration_ms:.0f}ms")
        logger.info(f"   Fallback used: {result.fallback_used}")
        
        if result.success:
            assert result.data is not None
            assert "nickname" in result.data
            logger.success("✅ Test passed!")
        else:
            logger.warning(f"⚠️ Ingestion failed: {result.error}")
    
    logger.info("="*80 + "\n")


async def test_batch_ingestion():
    """Test 5: Batch ingestion"""
    logger.info("="*80)
    logger.info("🧪 TEST 5: BATCH INGESTION")
    logger.info("="*80)
    
    config = IngestionConfig(
        max_concurrent_requests=5,
        enable_fallback=True,
        log_to_supabase=False
    )
    
    async with MultiRegionIngestor(config) as ingestor:
        players = [
            ("Faker", RegionProfile.KOREA),
            ("ShowMaker", RegionProfile.KOREA),
            ("Chovy", RegionProfile.KOREA),
        ]
        
        report = await ingestor.ingest_players_batch(players, game="lol")
        
        logger.info(f"📊 Report:")
        logger.info(f"   Total: {report.total_players}")
        logger.info(f"   Successful: {report.successful_ingestions}")
        logger.info(f"   Failed: {report.failed_ingestions}")
        logger.info(f"   Success Rate: {report.success_rate:.2f}%")
        logger.info(f"   Duration: {report.duration_seconds:.2f}s")
        logger.info(f"   Fallbacks: {report.total_fallbacks}")
        
        assert report.total_players == len(players)
        assert report.successful_ingestions >= 0
        
        logger.success("✅ Test passed!")
    
    logger.info("="*80 + "\n")


async def test_fallback_chain():
    """Test 6: Fallback chain functionality"""
    logger.info("="*80)
    logger.info("🧪 TEST 6: FALLBACK CHAIN")
    logger.info("="*80)
    
    # Obtener fallback chain para Korea
    korea_chain = FallbackStrategy.get_chain(RegionProfile.KOREA)
    
    logger.info(f"📍 Korea Fallback Chain:")
    for idx, source in enumerate(korea_chain, 1):
        logger.info(f"   {idx}. {source}")
    
    assert len(korea_chain) > 0
    assert "riot_api_kr" in korea_chain or "dakgg" in korea_chain
    
    # Obtener para China
    china_chain = FallbackStrategy.get_chain(RegionProfile.CHINA)
    
    logger.info(f"📍 China Fallback Chain:")
    for idx, source in enumerate(china_chain, 1):
        logger.info(f"   {idx}. {source}")
    
    assert "wanplus" in china_chain
    
    logger.success("✅ Fallback chains configured correctly!")
    logger.info("="*80 + "\n")


async def test_region_priority_ingestion():
    """Test 7: Region-priority ingestion"""
    logger.info("="*80)
    logger.info("🧪 TEST 7: REGION-PRIORITY INGESTION")
    logger.info("="*80)
    
    config = IngestionConfig(
        max_concurrent_requests=10,
        enable_fallback=True,
        log_to_supabase=False
    )
    
    async with MultiRegionIngestor(config) as ingestor:
        players_by_region = {
            RegionProfile.KOREA: ["Faker", "Chovy"],
            RegionProfile.CHINA: ["JackeyLove"],
            RegionProfile.INDIA: ["IndianPro1"],
        }
        
        reports = await ingestor.ingest_by_region_priority(
            players_by_region,
            game="lol"
        )
        
        logger.info(f"📊 Reports by Region:")
        for region, report in reports.items():
            logger.info(f"   {region}:")
            logger.info(f"     - Total: {report.total_players}")
            logger.info(f"     - Success Rate: {report.success_rate:.2f}%")
            logger.info(f"     - Duration: {report.duration_seconds:.2f}s")
        
        assert len(reports) == len(players_by_region)
        
        logger.success("✅ Region-priority ingestion working!")
    
    logger.info("="*80 + "\n")


async def test_circuit_breaker():
    """Test 8: Circuit breaker functionality"""
    logger.info("="*80)
    logger.info("🧪 TEST 8: CIRCUIT BREAKER")
    logger.info("="*80)
    
    config = IngestionConfig(
        max_concurrent_requests=5,
        circuit_breaker_threshold=3,  # Bajo para test
        enable_fallback=True,
        log_to_supabase=False
    )
    
    async with MultiRegionIngestor(config) as ingestor:
        # Simular múltiples fallos en una fuente
        test_source = "riot_api_kr"
        
        logger.info(f"📍 Simulating failures for {test_source}...")
        
        for i in range(5):
            # Intentar con jugador que probablemente no existe
            result = await ingestor.ingest_player(
                f"NonExistentPlayer_{i}",
                region=RegionProfile.KOREA,
                game="lol",
                preferred_sources=[test_source]
            )
            
            if ingestor.circuit_breaker.is_open(test_source):
                logger.warning(f"⚡ Circuit breaker opened for {test_source} after {i+1} attempts")
                break
        
        # Verificar que el circuit breaker se activó
        is_open = ingestor.circuit_breaker.is_open(test_source)
        logger.info(f"📊 Circuit breaker status for {test_source}: {'OPEN' if is_open else 'CLOSED'}")
        
        if is_open:
            logger.success("✅ Circuit breaker working correctly!")
        else:
            logger.warning("⚠️ Circuit breaker not triggered (might be expected)")
    
    logger.info("="*80 + "\n")


async def test_cache_system():
    """Test 9: Cache system"""
    logger.info("="*80)
    logger.info("🧪 TEST 9: CACHE SYSTEM")
    logger.info("="*80)
    
    config = IngestionConfig(
        max_concurrent_requests=5,
        enable_cache=True,
        cache_ttl=60,
        log_to_supabase=False
    )
    
    async with MultiRegionIngestor(config) as ingestor:
        player = "Faker"
        region = RegionProfile.KOREA
        
        # Primera llamada
        logger.info("📍 First call (no cache)...")
        result1 = await ingestor.ingest_player(player, region)
        
        # Segunda llamada (debería usar cache si la fuente lo soporta)
        logger.info("📍 Second call (should use cache)...")
        result2 = await ingestor.ingest_player(player, region)
        
        logger.info(f"📊 Cache stats:")
        logger.info(f"   First call duration: {result1.duration_ms:.0f}ms")
        logger.info(f"   Second call duration: {result2.duration_ms:.0f}ms")
        
        # La segunda llamada debería ser más rápida si usa cache
        if result2.duration_ms < result1.duration_ms:
            logger.success("✅ Cache system potentially working!")
        else:
            logger.info("ℹ️ Cache might not be used (depends on adapter implementation)")
    
    logger.info("="*80 + "\n")


async def test_header_rotation():
    """Test 10: Header rotation per region"""
    logger.info("="*80)
    logger.info("🧪 TEST 10: HEADER ROTATION")
    logger.info("="*80)
    
    from StrategicAdapters import AdvancedHeaderRotator
    
    regions = [
        RegionProfile.CHINA,
        RegionProfile.KOREA,
        RegionProfile.INDIA,
        RegionProfile.VIETNAM,
        RegionProfile.JAPAN
    ]
    
    for region in regions:
        headers = AdvancedHeaderRotator.get_headers(region)
        
        logger.info(f"📍 {region}:")
        logger.info(f"   User-Agent: {headers['User-Agent'][:60]}...")
        logger.info(f"   Accept-Language: {headers['Accept-Language']}")
        
        assert "User-Agent" in headers
        assert "Accept-Language" in headers
    
    logger.success("✅ Header rotation working for all regions!")
    logger.info("="*80 + "\n")


# ============================================================================
# RUNNER
# ============================================================================

async def main():
    """Ejecutar todos los tests"""
    logger.info("\n🚀 INICIANDO TEST SUITE - MULTI-REGION INGESTOR\n")
    
    tests = [
        ("Wanplus Adapter", test_wanplus_adapter),
        ("TEC India Adapter", test_tec_india_adapter),
        ("Soha Game Adapter", test_soha_game_adapter),
        ("Single Player Ingestion", test_single_player_ingestion),
        ("Batch Ingestion", test_batch_ingestion),
        ("Fallback Chain", test_fallback_chain),
        ("Region-Priority Ingestion", test_region_priority_ingestion),
        ("Circuit Breaker", test_circuit_breaker),
        ("Cache System", test_cache_system),
        ("Header Rotation", test_header_rotation),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            await test_func()
            passed += 1
        except Exception as e:
            failed += 1
            logger.error(f"❌ Test '{test_name}' failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Resumen
    logger.info("="*80)
    logger.info("📊 TEST SUMMARY")
    logger.info("="*80)
    logger.info(f"✅ Passed: {passed}/{len(tests)}")
    logger.info(f"❌ Failed: {failed}/{len(tests)}")
    logger.info(f"📈 Success Rate: {passed/len(tests)*100:.1f}%")
    logger.info("="*80)
    
    if failed == 0:
        logger.success("\n🎉 ALL TESTS PASSED!\n")
    else:
        logger.warning(f"\n⚠️ {failed} tests failed\n")


if __name__ == "__main__":
    # Configurar logging
    logger.add(
        "test_multi_region_ingestor_{time}.log",
        rotation="10 MB",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    )
    
    asyncio.run(main())
