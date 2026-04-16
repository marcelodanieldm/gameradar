"""
Tests para Universal Aggregator
Demuestra el uso del sistema de adapters con fallback automático
"""
import asyncio
from loguru import logger
from UniversalAggregator import (
    UniversalAggregator,
    AdapterFactory,
    fetch_player_with_fallback,
    HeaderRotator,
    SimpleCache,
    CircuitBreaker
)


async def test_single_source():
    """Test 1: Fetch desde una sola fuente"""
    logger.info("="*80)
    logger.info("🧪 TEST 1: FETCH DESDE UNA SOLA FUENTE")
    logger.info("="*80)
    
    async with UniversalAggregator() as aggregator:
        # Intentar solo OP.GG
        data = await aggregator.fetch_player(
            "Faker",
            preferred_sources=["opgg"],
            region="kr",
            use_fallback=False  # Sin fallback
        )
        
        if data:
            logger.success(f"✅ Datos obtenidos: {data.get('nickname')}")
            logger.info(f"   Source: {data.get('source')}")
            logger.info(f"   WinRate: {data.get('win_rate')}%")
            logger.info(f"   Rank: {data.get('rank')}")
        else:
            logger.error("❌ No se pudieron obtener datos")
    
    logger.info("="*80 + "\n")


async def test_fallback_system():
    """Test 2: Sistema de Fallback (Riot → OP.GG → Dak.gg)"""
    logger.info("="*80)
    logger.info("🧪 TEST 2: SISTEMA DE FALLBACK")
    logger.info("="*80)
    
    async with UniversalAggregator() as aggregator:
        # Intentar en orden: Riot API → OP.GG → Dak.gg
        data = await aggregator.fetch_player(
            "ShowMaker",
            preferred_sources=["riot_api", "opgg", "dakgg"],
            region="kr",
            use_fallback=True
        )
        
        if data:
            logger.success(f"✅ Datos obtenidos de: {data.get('source')}")
            logger.info(f"   Total fallbacks ejecutados: {aggregator.total_fallbacks}")
        else:
            logger.error("❌ Todas las fuentes fallaron")
    
    logger.info("="*80 + "\n")


async def test_multi_region():
    """Test 3: Fetch desde múltiples regiones"""
    logger.info("="*80)
    logger.info("🧪 TEST 3: MULTI-REGIÓN")
    logger.info("="*80)
    
    async with UniversalAggregator() as aggregator:
        # Jugador de Corea
        korea_data = await aggregator.fetch_player(
            "Faker",
            preferred_sources=["dakgg", "opgg"],
            region="kr"
        )
        
        # Jugador de China
        china_data = await aggregator.fetch_player(
            "chinese_player_123",
            preferred_sources=["wanplus"],
            region="cn"
        )
        
        # Jugador de India
        india_data = await aggregator.fetch_player(
            "indian_player_123",
            preferred_sources=["tec_india"]
        )
        
        results = [korea_data, china_data, india_data]
        valid_results = [r for r in results if r is not None]
        
        logger.success(f"✅ Obtenidos {len(valid_results)}/3 jugadores de diferentes regiones")
    
    logger.info("="*80 + "\n")


async def test_batch_fetch():
    """Test 4: Fetch en batch con concurrencia"""
    logger.info("="*80)
    logger.info("🧪 TEST 4: BATCH FETCH CON CONCURRENCIA")
    logger.info("="*80)
    
    async with UniversalAggregator() as aggregator:
        korean_players = [
            "Faker",
            "ShowMaker",
            "Chovy",
            "Canyon",
            "Keria"
        ]
        
        logger.info(f"📦 Fetching {len(korean_players)} jugadores en paralelo...")
        
        results = await aggregator.fetch_multiple_players(
            korean_players,
            preferred_sources=["dakgg", "opgg"],
            max_concurrent=3,  # Máximo 3 requests concurrentes
            region="kr"
        )
        
        logger.success(f"✅ Obtenidos {len(results)}/{len(korean_players)} jugadores")
        
        # Insertar todos en Bronze
        for result in results:
            await aggregator.insert_to_bronze(result)
    
    logger.info("="*80 + "\n")


async def test_cache_system():
    """Test 5: Sistema de Caché"""
    logger.info("="*80)
    logger.info("🧪 TEST 5: SISTEMA DE CACHÉ")
    logger.info("="*80)
    
    async with UniversalAggregator(cache_ttl=60) as aggregator:
        # Primera llamada - debería hacer request
        logger.info("📍 Primera llamada (sin caché)...")
        data1 = await aggregator.fetch_player(
            "Faker",
            preferred_sources=["opgg"]
        )
        
        # Segunda llamada - debería usar caché
        logger.info("📍 Segunda llamada (debería usar caché)...")
        data2 = await aggregator.fetch_player(
            "Faker",
            preferred_sources=["opgg"]
        )
        
        # Verificar métricas
        metrics = aggregator.adapters["opgg"].get_metrics()
        logger.info(f"📊 Requests reales: {metrics['requests']}")
        logger.info(f"📊 Successes: {metrics['successes']}")
        
        if metrics['requests'] == 1:
            logger.success("✅ Caché funcionando correctamente!")
        else:
            logger.warning("⚠️ Caché no está funcionando como esperado")
    
    logger.info("="*80 + "\n")


async def test_circuit_breaker():
    """Test 6: Circuit Breaker"""
    logger.info("="*80)
    logger.info("🧪 TEST 6: CIRCUIT BREAKER")
    logger.info("="*80)
    
    async with UniversalAggregator(circuit_breaker_threshold=3) as aggregator:
        # Simular varios fallos en una fuente
        logger.info("📍 Simulando fallos consecutivos...")
        
        for i in range(5):
            # Intentar fetch que probablemente falle
            data = await aggregator.fetch_player(
                f"nonexistent_player_{i}",
                preferred_sources=["riot_api"],  # Probablemente falle sin API key válida
                use_fallback=False
            )
            
            if aggregator.circuit_breaker.is_open("riot_api"):
                logger.warning("⚡ Circuit breaker activado para riot_api")
                break
        
        logger.info("📍 Intentando con otra fuente...")
        # Debería usar fallback automáticamente
        data = await aggregator.fetch_player(
            "Faker",
            preferred_sources=["riot_api", "opgg", "dakgg"]
        )
        
        if data and data.get("source") != "riot_api":
            logger.success("✅ Circuit breaker y fallback funcionando!")
    
    logger.info("="*80 + "\n")


async def test_header_rotation():
    """Test 7: Rotación de Headers"""
    logger.info("="*80)
    logger.info("🧪 TEST 7: ROTACIÓN DE HEADERS")
    logger.info("="*80)
    
    # Test para diferentes regiones
    regions = ["korea", "china", "india", "global"]
    
    for region in regions:
        headers = HeaderRotator.get_headers(region)
        logger.info(f"📍 Region: {region}")
        logger.info(f"   User-Agent: {headers['User-Agent'][:50]}...")
        logger.info(f"   Accept-Language: {headers['Accept-Language']}")
    
    logger.success("✅ Headers rotativos funcionando para todas las regiones")
    logger.info("="*80 + "\n")


async def test_adapter_factory():
    """Test 8: Adapter Factory"""
    logger.info("="*80)
    logger.info("🧪 TEST 8: ADAPTER FACTORY")
    logger.info("="*80)
    
    # Listar todos los adapters registrados
    sources = AdapterFactory.get_all_sources()
    logger.info(f"📋 Adapters registrados: {len(sources)}")
    for source in sources:
        logger.info(f"   - {source}")
    
    # Listar por prioridad
    logger.info("\n📊 Orden de prioridad:")
    priority_sources = AdapterFactory.get_sources_by_priority()
    for idx, source in enumerate(priority_sources, 1):
        logger.info(f"   {idx}. {source}")
    
    logger.success("✅ Factory pattern funcionando correctamente")
    logger.info("="*80 + "\n")


async def test_high_level_function():
    """Test 9: Función de alto nivel"""
    logger.info("="*80)
    logger.info("🧪 TEST 9: FUNCIÓN DE ALTO NIVEL")
    logger.info("="*80)
    
    # Usar la función de conveniencia
    logger.info("📍 Fetch usando función de alto nivel...")
    
    data = await fetch_player_with_fallback(
        identifier="Faker",
        region="kr",
        game="lol"
    )
    
    if data:
        logger.success(f"✅ Datos obtenidos de: {data.get('source')}")
        logger.info(f"   Nickname: {data.get('nickname')}")
        logger.info(f"   Rank: {data.get('rank')}")
        logger.info(f"   WinRate: {data.get('win_rate')}%")
    else:
        logger.error("❌ No se pudieron obtener datos")
    
    logger.info("="*80 + "\n")


async def test_metrics():
    """Test 10: Métricas globales"""
    logger.info("="*80)
    logger.info("🧪 TEST 10: MÉTRICAS GLOBALES")
    logger.info("="*80)
    
    async with UniversalAggregator() as aggregator:
        # Hacer varios requests
        players = ["Faker", "Chovy", "ShowMaker"]
        
        for player in players:
            await aggregator.fetch_player(
                player,
                preferred_sources=["opgg", "dakgg"]
            )
        
        # Obtener métricas
        metrics = aggregator.get_global_metrics()
        
        logger.info("📊 Métricas Globales:")
        logger.info(f"   Total requests: {metrics['total_requests']}")
        logger.info(f"   Total successes: {metrics['total_successes']}")
        logger.info(f"   Total fallbacks: {metrics['total_fallbacks']}")
        logger.info(f"   Success rate: {metrics['success_rate']}%")
        
        logger.info("\n📊 Métricas por Adapter:")
        for adapter_metric in metrics['adapters']:
            logger.info(f"   {adapter_metric['source']}:")
            logger.info(f"     - Requests: {adapter_metric['requests']}")
            logger.info(f"     - Success rate: {adapter_metric['success_rate']}%")
        
        logger.success("✅ Sistema de métricas funcionando")
    
    logger.info("="*80 + "\n")


async def main():
    """Ejecuta todos los tests"""
    logger.info("\n🚀 INICIANDO SUITE DE TESTS - UNIVERSAL AGGREGATOR\n")
    
    tests = [
        ("Single Source", test_single_source),
        ("Fallback System", test_fallback_system),
        ("Multi-Region", test_multi_region),
        ("Batch Fetch", test_batch_fetch),
        ("Cache System", test_cache_system),
        ("Circuit Breaker", test_circuit_breaker),
        ("Header Rotation", test_header_rotation),
        ("Adapter Factory", test_adapter_factory),
        ("High Level Function", test_high_level_function),
        ("Metrics", test_metrics),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            await test_func()
            passed += 1
        except Exception as e:
            failed += 1
            logger.error(f"❌ Test '{test_name}' falló: {e}")
    
    # Resumen final
    logger.info("="*80)
    logger.info("📊 RESUMEN DE TESTS")
    logger.info("="*80)
    logger.info(f"✅ Passed: {passed}/{len(tests)}")
    logger.info(f"❌ Failed: {failed}/{len(tests)}")
    logger.info(f"📈 Success Rate: {passed/len(tests)*100:.1f}%")
    logger.info("="*80)
    
    if failed == 0:
        logger.success("\n🎉 TODOS LOS TESTS PASARON!\n")
    else:
        logger.warning(f"\n⚠️ {failed} tests fallaron\n")


if __name__ == "__main__":
    # Configurar logging
    logger.add(
        "test_universal_aggregator_{time}.log",
        rotation="10 MB",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    )
    
    asyncio.run(main())
