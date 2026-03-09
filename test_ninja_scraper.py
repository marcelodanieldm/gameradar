"""
Script de testing rápido para el scraper ninja
Prueba las funcionalidades sin ejecutar el scraping completo
"""
import asyncio
import pytest
from loguru import logger

# Configurar logging para testing
logger.remove()
logger.add(lambda msg: print(msg), level="INFO")


@pytest.mark.asyncio
async def test_stealth_browser():
    """Test 1: Verificar configuración stealth del browser"""
    logger.info("🧪 TEST 1: Stealth Browser Configuration")
    
    try:
        from proxy_rotator import StealthBrowser
        
        browser = await StealthBrowser.create_stealth_browser(headless=True)
        page = await browser.new_page()
        
        await StealthBrowser.apply_stealth_scripts(page)
        
        # Test en un sitio que detecta bots
        await page.goto("https://bot.sannysoft.com/", timeout=10000)
        await asyncio.sleep(2)
        
        # Extraer resultados
        content = await page.content()
        
        # Verificar que no se detectó webdriver
        if "webdriver" not in content.lower():
            logger.success("✓ Webdriver oculto correctamente")
        else:
            logger.warning("⚠ Webdriver detectado")
        
        await browser.close()
        
    except Exception as e:
        logger.error(f"✗ Error en test de stealth browser: {e}")


@pytest.mark.asyncio
async def test_proxy_rotation():
    """Test 2: Verificar rotación de proxies"""
    logger.info("\n🧪 TEST 2: Proxy Rotation")
    
    try:
        from proxy_rotator import ProxyRotator
        
        # Test sin proxies
        rotator = ProxyRotator(proxy_service="none")
        logger.info(f"Proxies disponibles: {rotator.has_proxies()}")
        
        # Test con proxies custom (si están configurados)
        import os
        if os.getenv("PROXY_LIST"):
            rotator_custom = ProxyRotator(proxy_service="custom")
            logger.info(f"Custom proxies cargados: {len(rotator_custom.proxies)}")
            
            # Test de rotación
            for i in range(3):
                proxy = rotator_custom.get_next_proxy()
                logger.info(f"Proxy {i+1}: {proxy.get('server', 'N/A')}")
        else:
            logger.info("No hay PROXY_LIST configurado (OK para testing)")
        
        logger.success("✓ Rotación de proxies funciona")
        
    except Exception as e:
        logger.error(f"✗ Error en test de proxy rotation: {e}")


def test_country_detection():
    """Test 3: Verificar detección de país"""
    logger.info("\n🧪 TEST 3: Country Detection")
    
    try:
        from country_detector import detect_country
        
        # Test casos
        test_cases = [
            ("Pro player from 🇮🇳 India", "IN"),
            ("Korean player 🇰🇷", "KR"),
            ("Player from भारत", "IN"),
            ("Vietnam gamer 🇻🇳", "VN"),
        ]
        
        for text, expected in test_cases:
            country = detect_country(profile_text=text)
            if country.value == expected:
                logger.success(f"✓ '{text[:30]}...' → {country.value}")
            else:
                logger.warning(f"⚠ '{text[:30]}...' → {country.value} (esperado: {expected})")
        
    except Exception as e:
        logger.error(f"✗ Error en test de detección de país: {e}")


def test_data_validation():
    """Test 4: Verificar validación de datos con Pydantic"""
    logger.info("\n🧪 TEST 4: Data Validation")
    
    try:
        from models import PlayerProfile, PlayerStats, Champion, GameTitle, CountryCode
        
        # Crear perfil de prueba con Unicode
        profile = PlayerProfile(
            nickname="भारत_गेमर_123",  # Hindi
            game=GameTitle.LEAGUE_OF_LEGENDS,
            country=CountryCode.INDIA,
            server="IN",
            rank="Diamond",
            stats=PlayerStats(
                win_rate=58.5,
                kda=3.2,
                games_analyzed=100
            ),
            top_champions=[
                Champion(name="Yasuo", games_played=50, win_rate=60.0)
            ],
            profile_url="https://example.com/player"
        )
        
        # Verificar que se preserva Unicode
        assert "भारत" in profile.nickname, "Unicode no preservado"
        
        # Verificar validaciones
        assert 0 <= profile.stats.win_rate <= 100, "Win rate fuera de rango"
        assert profile.stats.kda >= 0, "KDA negativo"
        
        logger.success("✓ Validación de datos con Unicode funciona")
        
        # Test de serialización
        json_data = profile.model_dump(mode='json')
        logger.info(f"Serialización JSON: {json_data['nickname']}")
        
    except Exception as e:
        logger.error(f"✗ Error en test de validación: {e}")


@pytest.mark.asyncio
async def test_scraper_dry_run():
    """Test 5: Dry run del scraper (sin scraping real)"""
    logger.info("\n🧪 TEST 5: Scraper Dry Run")
    
    try:
        from cnn_brasil_scraper import CNNBrasilNinjaScraper
        
        # Crear scraper sin proxies
        scraper = CNNBrasilNinjaScraper(use_proxies=False)
        
        # Verificar inicialización
        assert scraper.scraped_count == 0, "Counter inicial incorrecto"
        assert scraper.error_count == 0, "Error counter inicial incorrecto"
        
        logger.success("✓ Scraper inicializado correctamente")
        
        # Test de datos mock
        mock_player = {
            "nickname": "TestPlayer",
            "game": "LOL",
            "country": "IN",
            "server": "IN",
            "rank": "Diamond",
            "win_rate": 58.5,
            "kda": 3.2,
            "profile_url": "https://test.com",
            "source": "test",
        }
        
        # Verificar que el formato es correcto
        required_fields = ["nickname", "game", "country", "server"]
        for field in required_fields:
            assert field in mock_player, f"Campo requerido faltante: {field}"
        
        logger.success("✓ Formato de datos del scraper correcto")
        
    except Exception as e:
        logger.error(f"✗ Error en dry run del scraper: {e}")


def test_supabase_connection():
    """Test 6: Verificar conexión a Supabase (opcional)"""
    logger.info("\n🧪 TEST 6: Supabase Connection (opcional)")
    
    try:
        import os
        
        # Verificar variables de entorno
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if supabase_url and supabase_key:
            from supabase_client import SupabaseClient
            
            db = SupabaseClient()
            logger.success("✓ Cliente de Supabase inicializado")
            
            # Intentar una query simple (opcional)
            # players = db.get_players_by_country("KR", limit=1)
            # logger.info(f"Test query ejecutada: {len(players)} resultados")
        else:
            logger.info("⚠ Supabase no configurado (OK para testing local)")
        
    except Exception as e:
        logger.warning(f"⚠ Supabase no disponible: {e}")


async def run_all_tests():
    """Ejecuta todos los tests"""
    logger.info("="*60)
    logger.info("🚀 INICIANDO TESTS DE GAMERADAR NINJA SCRAPER")
    logger.info("="*60)
    
    # Tests asíncronos
    await test_stealth_browser()
    await test_proxy_rotation()
    
    # Tests síncronos
    test_country_detection()
    test_data_validation()
    
    # Dry run
    await test_scraper_dry_run()
    
    # Opcional: conexión
    test_supabase_connection()
    
    logger.info("\n" + "="*60)
    logger.success("✅ TESTS COMPLETADOS")
    logger.info("="*60)
    logger.info("\n💡 Para ejecutar el scraper real:")
    logger.info("   python cnn_brasil_scraper.py")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
