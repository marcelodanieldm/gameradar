"""
Diagnóstico completo de todos los scrapers de GameRadar AI
Prueba cada scraper y muestra resultados detallados en consola
"""
import asyncio
import sys
import time
import os
from datetime import datetime
from loguru import logger

# Configurar logging para consola con formato legible
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
    level="DEBUG",
    colorize=True
)

# ─────────────────────────────────────────────────────────────
# RESULTADOS GLOBALES
# ─────────────────────────────────────────────────────────────
resultados = []


def registrar(nombre: str, estado: str, detalle: str = "", duracion: float = 0.0):
    resultados.append({
        "nombre": nombre,
        "estado": estado,
        "detalle": detalle,
        "duracion": duracion,
    })


def imprimir_separador(titulo: str = ""):
    ancho = 70
    if titulo:
        lado = (ancho - len(titulo) - 2) // 2
        print(f"\n{'═' * lado} {titulo} {'═' * lado}")
    else:
        print("═" * ancho)


# ─────────────────────────────────────────────────────────────
# TEST 1: IMPORTACIONES
# ─────────────────────────────────────────────────────────────
async def test_importaciones():
    imprimir_separador("TEST 1 · IMPORTACIONES")

    modulos = [
        ("models", "models"),
        ("config", "config"),
        ("country_detector", "country_detector"),
        ("scrapers (LiquipediaScraper)", "scrapers"),
        ("cnn_brasil_scraper", "cnn_brasil_scraper"),
        ("bronze_ingestion", "bronze_ingestion"),
        ("RegionalConnectors", "RegionalConnectors"),
        ("StrategicAdapters", "StrategicAdapters"),
        ("UniversalAggregator", "UniversalAggregator"),
        ("MultiRegionIngestor", "MultiRegionIngestor"),
        ("riot_api_client", "riot_api_client"),
        ("supabase_client", "supabase_client"),
    ]

    ok = 0
    fallo = 0
    for nombre, modulo in modulos:
        try:
            __import__(modulo)
            logger.success(f"  ✅ {nombre}")
            ok += 1
        except Exception as e:
            logger.error(f"  ❌ {nombre}: {e}")
            fallo += 1

    estado = "OK" if fallo == 0 else "PARCIAL" if ok > 0 else "FALLO"
    registrar("Importaciones", estado, f"{ok}/{ok+fallo} módulos importados")
    return fallo == 0


# ─────────────────────────────────────────────────────────────
# TEST 2: DETECCIÓN DE PAÍS
# ─────────────────────────────────────────────────────────────
async def test_country_detector():
    imprimir_separador("TEST 2 · COUNTRY DETECTOR")
    t0 = time.perf_counter()
    try:
        from country_detector import detect_country

        casos = [
            ("🇰🇷 Korean player",         "KR"),
            ("🇮🇳 Indian esports",         "IN"),
            ("🇻🇳 VCS Vietnam",            "VN"),
            ("🇨🇳 LPL China region",       "CN"),
            ("🇧🇷 Brasil / Brazil",         "BR"),
            ("🇯🇵 Japan server",            "JP"),
        ]

        ok = 0
        for texto, esperado in casos:
            resultado = detect_country(profile_text=texto)
            pais = resultado.value if hasattr(resultado, "value") else str(resultado)
            icono = "✅" if pais == esperado else "⚠️"
            logger.info(f"  {icono}  '{texto}' → {pais}  (esperado: {esperado})")
            if pais == esperado:
                ok += 1

        duracion = time.perf_counter() - t0
        registrar("CountryDetector", "OK", f"{ok}/{len(casos)} casos correctos", duracion)
    except Exception as e:
        duracion = time.perf_counter() - t0
        logger.error(f"  ❌ Error: {e}")
        registrar("CountryDetector", "FALLO", str(e), duracion)


# ─────────────────────────────────────────────────────────────
# TEST 3: MODELOS PYDANTIC
# ─────────────────────────────────────────────────────────────
async def test_modelos():
    imprimir_separador("TEST 3 · MODELOS PYDANTIC")
    t0 = time.perf_counter()
    try:
        from models import PlayerProfile, PlayerStats, Champion, GameTitle, CountryCode

        stats = PlayerStats(win_rate=65.0, kda=4.2, games_analyzed=50)
        champions = [
            Champion(name="Faker-Ahri", games_played=80, win_rate=70.0),
            Champion(name="Azir", games_played=50, win_rate=60.0),
        ]
        perfil = PlayerProfile(
            nickname="TestPlayer",
            game=GameTitle.LEAGUE_OF_LEGENDS,
            country=CountryCode.KOREA,
            server="KR",
            rank="Challenger",
            stats=stats,
            top_champions=champions,
            profile_url="https://liquipedia.net/leagueoflegends/TestPlayer",
        )
        logger.success(f"  ✅ PlayerProfile creado: {perfil.nickname}")
        logger.info(f"     Game: {perfil.game} | Country: {perfil.country}")
        logger.info(f"     WinRate: {perfil.stats.win_rate}% | KDA: {perfil.stats.kda}")
        logger.info(f"     Top Champion: {perfil.top_champions[0].name}")

        duracion = time.perf_counter() - t0
        registrar("Modelos Pydantic", "OK", "PlayerProfile creado correctamente", duracion)
    except Exception as e:
        duracion = time.perf_counter() - t0
        logger.error(f"  ❌ Error: {e}")
        registrar("Modelos Pydantic", "FALLO", str(e), duracion)


# ─────────────────────────────────────────────────────────────
# TEST 4: LIQUIPEDIA SCRAPER (1 jugador)
# ─────────────────────────────────────────────────────────────
async def test_liquipedia():
    imprimir_separador("TEST 4 · LIQUIPEDIA SCRAPER")
    t0 = time.perf_counter()
    try:
        from scrapers import LiquipediaScraper

        url_jugador = "https://liquipedia.net/leagueoflegends/Faker"
        logger.info(f"  🌐 URL: {url_jugador}")

        async with LiquipediaScraper() as scraper:
            perfil = await scraper.scrape_player(url_jugador)

        duracion = time.perf_counter() - t0
        if perfil:
            logger.success(f"  ✅ Scraped exitoso")
            logger.info(f"     Nickname : {perfil.nickname}")
            logger.info(f"     País     : {perfil.country}")
            logger.info(f"     WinRate  : {perfil.stats.win_rate}%")
            logger.info(f"     KDA      : {perfil.stats.kda}")
            registrar("LiquipediaScraper", "OK", f"Jugador: {perfil.nickname}", duracion)
        else:
            logger.warning("  ⚠️  No se obtuvo perfil (puede ser bloqueo o estructura cambiada)")
            registrar("LiquipediaScraper", "VACÍO", "Perfil None devuelto", duracion)

    except Exception as e:
        duracion = time.perf_counter() - t0
        logger.error(f"  ❌ Error: {e}")
        registrar("LiquipediaScraper", "FALLO", str(e)[:120], duracion)


# ─────────────────────────────────────────────────────────────
# TEST 5: CNN BRASIL NINJA SCRAPER
# ─────────────────────────────────────────────────────────────
async def test_cnn_brasil():
    imprimir_separador("TEST 5 · CNN BRASIL NINJA SCRAPER")
    t0 = time.perf_counter()
    try:
        from cnn_brasil_scraper import CNNBrasilNinjaScraper

        logger.info("  🥷 Iniciando ninja scraper (sin proxies)...")
        scraper = CNNBrasilNinjaScraper(use_proxies=False)
        stats = await scraper.run_ninja_scrape()

        duracion = time.perf_counter() - t0
        logger.success(f"  ✅ Scraper ejecutado")
        logger.info(f"     Scraped  : {stats.get('scraped', 0)}")
        logger.info(f"     Errores  : {stats.get('errors', 0)}")
        logger.info(f"     Duración : {stats.get('duration_seconds', duracion):.1f}s")
        registrar(
            "CNNBrasilNinja",
            "OK" if stats.get("scraped", 0) > 0 else "VACÍO",
            f"scraped={stats.get('scraped',0)} errores={stats.get('errors',0)}",
            duracion,
        )
    except Exception as e:
        duracion = time.perf_counter() - t0
        logger.error(f"  ❌ Error: {e}")
        registrar("CNNBrasilNinja", "FALLO", str(e)[:120], duracion)


# ─────────────────────────────────────────────────────────────
# TEST 6: BRONZE INGESTION (Liquipedia, 3 jugadores)
# ─────────────────────────────────────────────────────────────
async def test_bronze_ingestion():
    imprimir_separador("TEST 6 · BRONZE INGESTION (Liquipedia)")
    t0 = time.perf_counter()
    try:
        from bronze_ingestion import BronzeIngestionScraper

        logger.info("  📦 Scraping Liquipedia (límite: 3 jugadores)...")
        async with BronzeIngestionScraper(region="KR", headless=True) as scraper:
            await scraper.run_ingestion(
                source="liquipedia",
                game="leagueoflegends",
                limit=3,
            )

        duracion = time.perf_counter() - t0
        logger.success(f"  ✅ Bronze ingestion completado")
        logger.info(f"     Scraped : {scraper.scraped_count}")
        logger.info(f"     Errores : {scraper.error_count}")
        registrar(
            "BronzeIngestion",
            "OK" if scraper.scraped_count > 0 else "VACÍO",
            f"scraped={scraper.scraped_count} errores={scraper.error_count}",
            duracion,
        )
    except Exception as e:
        duracion = time.perf_counter() - t0
        logger.error(f"  ❌ Error: {e}")
        registrar("BronzeIngestion", "FALLO", str(e)[:120], duracion)


# ─────────────────────────────────────────────────────────────
# TEST 7: DAK.GG CONNECTOR (Corea)
# ─────────────────────────────────────────────────────────────
async def test_dakgg():
    imprimir_separador("TEST 7 · DAK.GG CONNECTOR (Korea)")
    t0 = time.perf_counter()
    try:
        from RegionalConnectors import DakGGConnector

        async with DakGGConnector(use_proxy=False) as conector:
            perfil = await conector.scrape_player("Faker", game="lol")

        duracion = time.perf_counter() - t0
        if perfil:
            logger.success(f"  ✅ Scraped: {perfil.nickname}")
            logger.info(f"     Rank     : {perfil.rank}")
            logger.info(f"     WinRate  : {perfil.stats.win_rate}%")
            logger.info(f"     KDA      : {perfil.stats.kda}")
            if perfil.top_champions:
                logger.info(f"     Top Champ: {perfil.top_champions[0].name}")
            registrar("DakGG", "OK", f"Jugador: {perfil.nickname}", duracion)
        else:
            logger.warning("  ⚠️  No se obtuvo perfil")
            registrar("DakGG", "VACÍO", "Perfil None", duracion)

    except Exception as e:
        duracion = time.perf_counter() - t0
        logger.error(f"  ❌ Error: {e}")
        registrar("DakGG", "FALLO", str(e)[:120], duracion)


# ─────────────────────────────────────────────────────────────
# TEST 8: SCOREGG CONNECTOR (China) — sin proxy
# ─────────────────────────────────────────────────────────────
async def test_scoregg():
    imprimir_separador("TEST 8 · SCOREGG CONNECTOR (China, sin proxy)")
    t0 = time.perf_counter()
    try:
        from RegionalConnectors import ScoreGGConnector

        async with ScoreGGConnector(use_proxy=False) as conector:
            perfil = await conector.scrape_player("Knight", game="lol")

        duracion = time.perf_counter() - t0
        if perfil:
            logger.success(f"  ✅ Scraped: {perfil.nickname}")
            logger.info(f"     Rank     : {perfil.rank}")
            logger.info(f"     WinRate  : {perfil.stats.win_rate}%")
            registrar("ScoreGG", "OK", f"Jugador: {perfil.nickname}", duracion)
        else:
            logger.warning("  ⚠️  Sin proxy: probable bloqueo GFW o estructura cambiada")
            registrar("ScoreGG", "VACÍO", "Perfil None (esperado sin proxy)", duracion)

    except Exception as e:
        duracion = time.perf_counter() - t0
        logger.error(f"  ❌ Error: {e}")
        registrar("ScoreGG", "FALLO", str(e)[:120], duracion)


# ─────────────────────────────────────────────────────────────
# TEST 9: STRATEGIC ADAPTERS (httpx, sin browser)
# ─────────────────────────────────────────────────────────────
async def test_strategic_adapters():
    imprimir_separador("TEST 9 · STRATEGIC ADAPTERS (httpx)")
    t0 = time.perf_counter()

    try:
        import httpx
        from StrategicAdapters import (
            StrategicAdapterFactory,
            RegionProfile,
            WanplusAdapter,
            TheEsportsClubAdapter,
            SohaGameAdapter,
            LootBetAdapter,
        )

        # Prueba instanciar cada adapter y hacer fetch de 1 jugador
        adapters_config = [
            ("Wanplus (China)",        WanplusAdapter,         "Knight"),
            ("TheEsportsClub (India)", TheEsportsClubAdapter,  "Shadow"),
            ("SohaGame (Vietnam)",     SohaGameAdapter,        "SofM"),
            ("LootBet (Global)",       LootBetAdapter,         "T1"),
        ]

        ok = 0
        fallo = 0

        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            for nombre_adapter, AdapterClass, jugador in adapters_config:
                try:
                    adapter = AdapterClass(client=client)
                    resultado = await adapter.fetch_player(jugador, game="lol")
                    if resultado:
                        nick = resultado.get("nickname", "?")
                        logger.success(f"  ✅ {nombre_adapter:25} → {nick}")
                        ok += 1
                    else:
                        logger.warning(f"  ⚠️  {nombre_adapter:25} → Sin datos")
                        fallo += 1
                except Exception as e:
                    logger.error(f"  ❌ {nombre_adapter:25} → {str(e)[:80]}")
                    fallo += 1

        duracion = time.perf_counter() - t0
        estado = "OK" if ok > 0 else "FALLO"
        registrar("StrategicAdapters", estado, f"{ok}/{ok+fallo} regiones OK", duracion)

    except Exception as e:
        duracion = time.perf_counter() - t0
        logger.error(f"  ❌ Error general: {e}")
        registrar("StrategicAdapters", "FALLO", str(e)[:120], duracion)


# ─────────────────────────────────────────────────────────────
# TEST 10: UNIVERSAL AGGREGATOR (con fallback)
# ─────────────────────────────────────────────────────────────
async def test_universal_aggregator():
    imprimir_separador("TEST 10 · UNIVERSAL AGGREGATOR")
    t0 = time.perf_counter()
    try:
        from UniversalAggregator import UniversalAggregator

        async with UniversalAggregator() as aggregator:
            data = await aggregator.fetch_player(
                "Faker",
                preferred_sources=["opgg", "dakgg", "liquipedia"],
                region="kr",
                use_fallback=True,
            )

        duracion = time.perf_counter() - t0
        if data:
            logger.success(f"  ✅ Datos obtenidos")
            logger.info(f"     Fuente  : {data.get('source', '?')}")
            logger.info(f"     Nickname: {data.get('nickname', '?')}")
            logger.info(f"     WinRate : {data.get('win_rate', '?')}%")
            logger.info(f"     Rank    : {data.get('rank', '?')}")
            registrar("UniversalAggregator", "OK", f"source={data.get('source','?')}", duracion)
        else:
            logger.warning("  ⚠️  No se obtuvieron datos de ninguna fuente")
            registrar("UniversalAggregator", "VACÍO", "Todas las fuentes sin datos", duracion)

    except Exception as e:
        duracion = time.perf_counter() - t0
        logger.error(f"  ❌ Error: {e}")
        registrar("UniversalAggregator", "FALLO", str(e)[:120], duracion)


# ─────────────────────────────────────────────────────────────
# TEST 11: RIOT API CLIENT
# ─────────────────────────────────────────────────────────────
async def test_riot_api():
    imprimir_separador("TEST 11 · RIOT API CLIENT")
    t0 = time.perf_counter()
    try:
        from riot_api_client import RiotAPIClient
        from config import settings

        api_key = settings.riot_api_key
        if api_key == "your-riot-api-key-here" or not api_key:
            logger.warning("  ⚠️  RIOT_API_KEY no configurada en .env")
            logger.info("      → Obten tu key en https://developer.riotgames.com/")
            registrar("RiotAPI", "SKIP", "API key no configurada", 0)
            return

        client = RiotAPIClient(api_key=api_key, region="KR")
        # Obtener top 3 jugadores del servidor KR
        jugadores = await client.get_challenger_players(queue="RANKED_SOLO_5x5", limit=3)

        duracion = time.perf_counter() - t0
        if jugadores:
            logger.success(f"  ✅ {len(jugadores)} jugadores Challenger obtenidos")
            for j in jugadores:
                nombre = j.get("summonerName", j.get("nickname", "?"))
                logger.info(f"     - {nombre}")
            registrar("RiotAPI", "OK", f"{len(jugadores)} jugadores", duracion)
        else:
            logger.warning("  ⚠️  Respuesta vacía")
            registrar("RiotAPI", "VACÍO", "Sin jugadores", duracion)

    except Exception as e:
        duracion = time.perf_counter() - t0
        logger.error(f"  ❌ Error: {e}")
        registrar("RiotAPI", "FALLO", str(e)[:120], duracion)


# ─────────────────────────────────────────────────────────────
# TEST 12: MULTI-REGION INGESTOR (1 región, 2 jugadores)
# ─────────────────────────────────────────────────────────────
async def test_multi_region_ingestor():
    imprimir_separador("TEST 12 · MULTI-REGION INGESTOR")
    t0 = time.perf_counter()
    try:
        from MultiRegionIngestor import MultiRegionIngestor, IngestionConfig
        from StrategicAdapters import RegionProfile

        config = IngestionConfig(
            max_concurrent_requests=2,
            enable_fallback=True,
            total_timeout=60,
            log_to_supabase=False,   # No requiere Supabase
            log_to_file=False,
        )

        jugadores = ["Faker", "Showmaker"]

        logger.info(f"  🌍 Ingesting {len(jugadores)} jugadores (región: korea)...")
        exitosos = 0
        fallbacks_total = 0

        async with MultiRegionIngestor(config=config) as ingestor:
            for jugador in jugadores:
                resultado = await ingestor.ingest_player(
                    identifier=jugador,
                    region=RegionProfile.KOREA,
                    game="lol",
                )
                if resultado.success:
                    exitosos += 1
                    logger.success(f"     ✅ {jugador} → fuente: {resultado.source}")
                else:
                    logger.warning(f"     ⚠️  {jugador} → {resultado.error}")
                if resultado.fallback_used:
                    fallbacks_total += 1

        duracion = time.perf_counter() - t0
        fallidos = len(jugadores) - exitosos

        logger.success(f"  ✅ Ingestion completado")
        logger.info(f"     Exitosos  : {exitosos}")
        logger.info(f"     Fallidos  : {fallidos}")
        logger.info(f"     Fallbacks : {fallbacks_total}")
        logger.info(f"     Duración  : {duracion:.1f}s")

        registrar(
            "MultiRegionIngestor",
            "OK" if exitosos > 0 else "VACÍO",
            f"ok={exitosos} fail={fallidos} fallbacks={fallbacks_total}",
            duracion,
        )
    except Exception as e:
        duracion = time.perf_counter() - t0
        logger.error(f"  ❌ Error: {e}")
        registrar("MultiRegionIngestor", "FALLO", str(e)[:120], duracion)


# ─────────────────────────────────────────────────────────────
# RESUMEN FINAL
# ─────────────────────────────────────────────────────────────
def imprimir_resumen():
    imprimir_separador("RESUMEN DE DIAGNÓSTICO")

    iconos = {
        "OK":      "✅",
        "VACÍO":   "⚠️ ",
        "SKIP":    "⏭️ ",
        "PARCIAL": "🟡",
        "FALLO":   "❌",
    }

    col_nombre  = max(len(r["nombre"]) for r in resultados) + 2
    col_estado  = 8
    col_duracion = 8

    header = f"  {'SCRAPER':<{col_nombre}} {'ESTADO':<{col_estado}} {'TIEMPO':>{col_duracion}}   DETALLE"
    print(header)
    print("  " + "─" * (col_nombre + col_estado + col_duracion + 20))

    ok_total    = 0
    fallo_total = 0
    skip_total  = 0

    for r in resultados:
        estado  = r["estado"]
        icono   = iconos.get(estado, "❓")
        tiempo  = f"{r['duracion']:.1f}s" if r["duracion"] > 0 else "─"
        detalle = r["detalle"][:60] if r["detalle"] else ""

        print(f"  {icono} {r['nombre']:<{col_nombre}} {estado:<{col_estado}} {tiempo:>{col_duracion}}   {detalle}")

        if estado == "OK":
            ok_total += 1
        elif estado == "SKIP":
            skip_total += 1
        else:
            fallo_total += 1

    total = ok_total + fallo_total
    print()
    print(f"  Total: {ok_total}/{total} scrapers OK  |  {fallo_total} con problemas  |  {skip_total} omitidos")
    imprimir_separador()


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────
async def main():
    inicio = datetime.now()
    imprimir_separador(f"DIAGNÓSTICO SCRAPERS — {inicio.strftime('%Y-%m-%d %H:%M:%S')}")

    # Correr importaciones primero; si falla gravemente, advertir pero continuar
    imports_ok = await test_importaciones()

    await test_country_detector()
    await test_modelos()
    await test_liquipedia()
    await test_cnn_brasil()
    await test_bronze_ingestion()
    await test_dakgg()
    await test_scoregg()
    await test_strategic_adapters()
    await test_universal_aggregator()
    await test_riot_api()
    await test_multi_region_ingestor()

    imprimir_resumen()
    fin = datetime.now()
    print(f"  Tiempo total: {(fin - inicio).total_seconds():.1f}s\n")


if __name__ == "__main__":
    asyncio.run(main())
