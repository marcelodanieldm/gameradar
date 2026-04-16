"""
Multi-Region Ingestor - Orquestador de Grado Militar para GameRadar AI
=======================================================================

Sistema de ingesta multi-fuente con:
- ✅ Fallback automático (fuente primaria → secundaria)
- ✅ Segmentación regional (micro-metrics vs social sentiment)
- ✅ Logging detallado a Supabase
- ✅ Diseñado para GitHub Actions (Serverless)
- ✅ Costo operativo cercano a cero

Author: GameRadar AI Team
Version: 1.0.0 (Military-Grade)
"""

import asyncio
import os
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import httpx
from loguru import logger
import json

# Imports locales
from StrategicAdapters import (
    BaseStrategicAdapter,
    StrategicAdapterFactory,
    RegionProfile,
    DataPriority,
    WanplusAdapter,
    TheEsportsClubAdapter,
    SohaGameAdapter,
    SteamWebAPIAdapter,
    LootBetAdapter,
    RiotGamesShardAdapter
)
from UniversalAggregator import (
    UniversalAggregator,
    CircuitBreaker,
    SimpleCache
)

# Intentar importar supabase_client
try:
    from supabase_client import SupabaseClient
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logger.warning("⚠️ Supabase client not available - logging to file only")


# ============================================================================
# CONFIGURACIÓN
# ============================================================================

@dataclass
class IngestionConfig:
    """Configuración global de ingesta"""
    
    # Concurrencia
    max_concurrent_requests: int = 10
    max_concurrent_per_source: int = 3
    
    # Reintentos
    max_retries_per_source: int = 3
    
    # Timeouts
    request_timeout: int = 30
    total_timeout: int = 300  # 5 minutos max
    
    # Fallback
    enable_fallback: bool = True
    fallback_strategy: str = "cascade"  # cascade, parallel, smart
    
    # Cache
    cache_ttl: int = 300  # 5 minutos
    enable_cache: bool = True
    
    # Circuit Breaker
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60
    
    # Logging
    log_to_supabase: bool = True
    log_to_file: bool = True
    log_level: str = "INFO"
    
    # API Keys (leer de environment)
    riot_api_key: Optional[str] = field(default_factory=lambda: os.getenv("RIOT_API_KEY"))
    steam_api_key: Optional[str] = field(default_factory=lambda: os.getenv("STEAM_API_KEY"))
    
    # Regiones activas
    active_regions: List[RegionProfile] = field(default_factory=lambda: [
        RegionProfile.CHINA,
        RegionProfile.KOREA,
        RegionProfile.INDIA,
        RegionProfile.VIETNAM,
        RegionProfile.JAPAN,
        RegionProfile.SEA,
    ])


@dataclass
class IngestionResult:
    """Resultado de una ingesta"""
    player_identifier: str
    source: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    duration_ms: float = 0.0
    fallback_used: bool = False
    fallback_source: Optional[str] = None


@dataclass
class IngestionReport:
    """Reporte completo de una sesión de ingesta"""
    session_id: str
    start_time: datetime
    end_time: datetime
    total_players: int
    successful_ingestions: int
    failed_ingestions: int
    total_fallbacks: int
    results: List[IngestionResult] = field(default_factory=list)
    source_metrics: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Tasa de éxito"""
        if self.total_players == 0:
            return 0.0
        return (self.successful_ingestions / self.total_players) * 100
    
    @property
    def duration_seconds(self) -> float:
        """Duración total en segundos"""
        return (self.end_time - self.start_time).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario para logging"""
        return {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_seconds": self.duration_seconds,
            "total_players": self.total_players,
            "successful": self.successful_ingestions,
            "failed": self.failed_ingestions,
            "success_rate": round(self.success_rate, 2),
            "total_fallbacks": self.total_fallbacks,
            "source_metrics": self.source_metrics,
            "errors": self.errors[:10]  # Limitar a 10 errores
        }


# ============================================================================
# FALLBACK STRATEGIES
# ============================================================================

class FallbackStrategy:
    """Estrategias de fallback"""
    
    # Definir cadenas de fallback por región
    FALLBACK_CHAINS = {
        RegionProfile.CHINA: [
            "wanplus",           # Primaria
            "riot_api_kr",       # Asume jugador también juega en KR
            "loot_bet"           # Última opción (odds)
        ],
        RegionProfile.KOREA: [
            "riot_api_kr",       # API oficial
            "dakgg",             # Regional Connector (ya existente)
            "opgg",              # Universal Aggregator
            "loot_bet"
        ],
        RegionProfile.JAPAN: [
            "riot_api_jp",
            "opgg",
            "loot_bet"
        ],
        RegionProfile.INDIA: [
            "tec_india",         # Primaria para India
            "riot_api_kr",       # Muchos indios juegan en KR
            "loot_bet"
        ],
        RegionProfile.VIETNAM: [
            "soha_game",         # Primaria
            "opgg",
            "loot_bet"
        ],
        RegionProfile.SEA: [
            "steam_web_api",     # Para Dota 2
            "opgg",              # Para LoL
            "loot_bet"
        ],
        RegionProfile.GLOBAL: [
            "riot_api_kr",
            "opgg",
            "dakgg",
            "loot_bet"
        ]
    }
    
    @classmethod
    def get_chain(cls, region: RegionProfile) -> List[str]:
        """Obtener cadena de fallback para una región"""
        return cls.FALLBACK_CHAINS.get(region, cls.FALLBACK_CHAINS[RegionProfile.GLOBAL])


# ============================================================================
# MULTI-REGION INGESTOR
# ============================================================================

class MultiRegionIngestor:
    """
    Orquestador de grado militar para ingesta multi-fuente
    
    Características:
    - Maneja múltiples fuentes simultáneamente
    - Fallback automático entre fuentes
    - Segmentación por región y prioridad
    - Logging detallado a Supabase
    - Compatible con GitHub Actions
    """
    
    def __init__(self, config: Optional[IngestionConfig] = None):
        self.config = config or IngestionConfig()
        
        # HTTP Client
        self.client: Optional[httpx.AsyncClient] = None
        
        # Universal Aggregator (para fuentes ya existentes como OP.GG, Dak.gg)
        self.aggregator: Optional[UniversalAggregator] = None
        
        # Adapters estratégicos
        self.adapters: Dict[str, BaseStrategicAdapter] = {}
        
        # Circuit Breaker compartido
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=self.config.circuit_breaker_threshold,
            timeout=self.config.circuit_breaker_timeout
        )
        
        # Cache compartido
        self.cache = SimpleCache(ttl=self.config.cache_ttl) if self.config.enable_cache else None
        
        # Supabase client para logging
        self.supabase_client = None
        if SUPABASE_AVAILABLE and self.config.log_to_supabase:
            try:
                self.supabase_client = SupabaseClient()
            except Exception as e:
                logger.warning(f"⚠️ No se pudo inicializar Supabase: {e}")
        
        # Métricas
        self.session_metrics: Dict[str, Any] = {
            "total_requests": 0,
            "total_successes": 0,
            "total_failures": 0,
            "total_fallbacks": 0,
            "sources_used": {},
        }
        
        # Logger
        self._setup_logging()
    
    def _setup_logging(self):
        """Configurar logging"""
        if self.config.log_to_file:
            logger.add(
                "multi_region_ingestor_{time}.log",
                rotation="50 MB",
                level=self.config.log_level,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
            )
    
    async def __aenter__(self):
        """Context manager entry"""
        # Inicializar HTTP client
        self.client = httpx.AsyncClient(
            http2=True,
            limits=httpx.Limits(
                max_connections=self.config.max_concurrent_requests,
                max_keepalive_connections=self.config.max_concurrent_requests // 2
            ),
            timeout=httpx.Timeout(self.config.request_timeout)
        )
        
        # Inicializar Universal Aggregator
        self.aggregator = UniversalAggregator(
            cache_ttl=self.config.cache_ttl,
            circuit_breaker_threshold=self.config.circuit_breaker_threshold
        )
        await self.aggregator.__aenter__()
        
        # Inicializar adapters estratégicos
        self._initialize_adapters()
        
        logger.success("🚀 MultiRegionIngestor initialized")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.aggregator:
            await self.aggregator.__aexit__(exc_type, exc_val, exc_tb)
        
        if self.client:
            await self.client.aclose()
        
        logger.success("🛑 MultiRegionIngestor closed")
    
    def _initialize_adapters(self):
        """Inicializar todos los adapters estratégicos"""
        # Wanplus (China)
        self.adapters["wanplus"] = WanplusAdapter(client=self.client)
        
        # The Esports Club (India)
        self.adapters["tec_india"] = TheEsportsClubAdapter(client=self.client)
        
        # Soha Game (Vietnam)
        self.adapters["soha_game"] = SohaGameAdapter(client=self.client)
        
        # Steam Web API (Dota 2 SEA)
        if self.config.steam_api_key:
            self.adapters["steam_web_api"] = SteamWebAPIAdapter(
                client=self.client,
                api_key=self.config.steam_api_key
            )
        
        # Loot.bet (Global odds)
        self.adapters["loot_bet"] = LootBetAdapter(client=self.client)
        
        # Riot Games Shards
        if self.config.riot_api_key:
            self.adapters["riot_api_kr"] = RiotGamesShardAdapter(
                client=self.client,
                api_key=self.config.riot_api_key,
                shard="kr"
            )
            self.adapters["riot_api_jp"] = RiotGamesShardAdapter(
                client=self.client,
                api_key=self.config.riot_api_key,
                shard="jp"
            )
        
        logger.info(f"📦 Initialized {len(self.adapters)} strategic adapters")
    
    async def ingest_player(
        self,
        identifier: str,
        region: RegionProfile,
        game: str = "lol",
        preferred_sources: Optional[List[str]] = None
    ) -> IngestionResult:
        """
        Ingerir un jugador con fallback automático
        
        Args:
            identifier: Nombre/ID del jugador
            region: Región geográfica
            game: Juego (lol, dota2, etc)
            preferred_sources: Fuentes preferidas (None = usar fallback chain)
        
        Returns:
            IngestionResult con datos o error
        """
        start_time = datetime.utcnow()
        
        # Determinar sources a usar
        if preferred_sources is None:
            sources = FallbackStrategy.get_chain(region)
        else:
            sources = preferred_sources
        
        logger.info(f"🎯 Ingesting player: {identifier} (region: {region}, sources: {sources})")
        
        # Intentar cada fuente en orden
        last_error = None
        fallback_used = False
        fallback_source = None
        
        for idx, source in enumerate(sources):
            # Verificar circuit breaker
            if self.circuit_breaker.is_open(source):
                logger.warning(f"⚡ Circuit breaker open for {source}, skipping...")
                continue
            
            try:
                # Fetch data
                data = await self._fetch_from_source(source, identifier, game, region)
                
                if data:
                    # Éxito!
                    duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                    
                    if idx > 0:
                        fallback_used = True
                        fallback_source = source
                        self.session_metrics["total_fallbacks"] += 1
                    
                    self.session_metrics["total_successes"] += 1
                    self.session_metrics["total_requests"] += 1
                    
                    # Insertar en Bronze
                    if self.supabase_client:
                        await self._insert_to_bronze(data)
                    
                    result = IngestionResult(
                        player_identifier=identifier,
                        source=source,
                        success=True,
                        data=data,
                        timestamp=datetime.utcnow(),
                        duration_ms=duration_ms,
                        fallback_used=fallback_used,
                        fallback_source=fallback_source
                    )
                    
                    logger.success(f"✅ Ingested {identifier} from {source} ({duration_ms:.0f}ms)")
                    return result
                
            except Exception as e:
                last_error = str(e)
                logger.error(f"❌ Error fetching {identifier} from {source}: {e}")
                self.circuit_breaker.record_failure(source)
                
                # Si no es la última fuente, continuar con fallback
                if idx < len(sources) - 1 and self.config.enable_fallback:
                    logger.info(f"🔄 Fallback to next source: {sources[idx+1]}")
                    continue
        
        # Todos los sources fallaron
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        self.session_metrics["total_failures"] += 1
        self.session_metrics["total_requests"] += 1
        
        result = IngestionResult(
            player_identifier=identifier,
            source="all_failed",
            success=False,
            error=last_error or "All sources failed",
            timestamp=datetime.utcnow(),
            duration_ms=duration_ms
        )
        
        logger.error(f"❌ Failed to ingest {identifier} from all sources")
        return result
    
    async def _fetch_from_source(
        self,
        source: str,
        identifier: str,
        game: str,
        region: RegionProfile
    ) -> Optional[Dict[str, Any]]:
        """Fetch desde una fuente específica"""
        
        # Verificar si es un adapter estratégico
        if source in self.adapters:
            adapter = self.adapters[source]
            return await adapter.fetch_player(identifier, game=game)
        
        # Si no, usar el Universal Aggregator (para OP.GG, Dak.gg, etc)
        if self.aggregator:
            return await self.aggregator.fetch_player(
                identifier,
                preferred_sources=[source],
                region=region.value,
                use_fallback=False
            )
        
        logger.warning(f"⚠️ Source '{source}' not found")
        return None
    
    async def _insert_to_bronze(self, data: Dict[str, Any]):
        """Insertar datos en capa Bronze de Supabase"""
        try:
            if not self.supabase_client:
                return
            
            # Insertar usando método de SupabaseClient
            # (asume que existe método insert_bronze_player)
            if hasattr(self.supabase_client, 'insert_bronze_player'):
                self.supabase_client.insert_bronze_player(data)
                logger.debug(f"📦 Inserted to Bronze: {data.get('nickname')}")
            else:
                # Fallback: insertar directo
                self.supabase_client.supabase.table("bronze_players").insert(data).execute()
                logger.debug(f"📦 Inserted to Bronze (direct): {data.get('nickname')}")
        
        except Exception as e:
            logger.error(f"❌ Error inserting to Bronze: {e}")
    
    async def ingest_players_batch(
        self,
        players: List[Tuple[str, RegionProfile]],  # [(identifier, region), ...]
        game: str = "lol"
    ) -> IngestionReport:
        """
        Ingerir múltiples jugadores en batch
        
        Args:
            players: Lista de (identifier, region)
            game: Juego
        
        Returns:
            IngestionReport con resultados detallados
        """
        import uuid
        
        session_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        logger.info(f"🚀 Starting batch ingestion: {len(players)} players (session: {session_id})")
        
        # Crear semáforo para limitar concurrencia
        semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)
        
        async def ingest_with_semaphore(player_data):
            async with semaphore:
                identifier, region = player_data
                return await self.ingest_player(identifier, region, game)
        
        # Ejecutar todos en paralelo con límite de concurrencia
        results = await asyncio.gather(
            *[ingest_with_semaphore(p) for p in players],
            return_exceptions=True
        )
        
        # Procesar resultados
        successful = sum(1 for r in results if isinstance(r, IngestionResult) and r.success)
        failed = len(results) - successful
        total_fallbacks = sum(1 for r in results if isinstance(r, IngestionResult) and r.fallback_used)
        
        # Métricas por fuente
        source_metrics = {}
        for result in results:
            if isinstance(result, IngestionResult):
                source = result.source
                if source not in source_metrics:
                    source_metrics[source] = {
                        "requests": 0,
                        "successes": 0,
                        "failures": 0,
                        "avg_duration_ms": 0.0
                    }
                
                source_metrics[source]["requests"] += 1
                if result.success:
                    source_metrics[source]["successes"] += 1
                else:
                    source_metrics[source]["failures"] += 1
                
                # Promedio de duración
                prev_avg = source_metrics[source]["avg_duration_ms"]
                n = source_metrics[source]["requests"]
                source_metrics[source]["avg_duration_ms"] = (
                    (prev_avg * (n - 1) + result.duration_ms) / n
                )
        
        # Errores
        errors = [r.error for r in results if isinstance(r, IngestionResult) and r.error]
        
        end_time = datetime.utcnow()
        
        report = IngestionReport(
            session_id=session_id,
            start_time=start_time,
            end_time=end_time,
            total_players=len(players),
            successful_ingestions=successful,
            failed_ingestions=failed,
            total_fallbacks=total_fallbacks,
            results=[r for r in results if isinstance(r, IngestionResult)],
            source_metrics=source_metrics,
            errors=errors
        )
        
        # Log del reporte
        logger.success(f"✅ Batch ingestion completed:")
        logger.info(f"   Total: {report.total_players}")
        logger.info(f"   Successful: {report.successful_ingestions}")
        logger.info(f"   Failed: {report.failed_ingestions}")
        logger.info(f"   Success Rate: {report.success_rate:.2f}%")
        logger.info(f"   Fallbacks: {report.total_fallbacks}")
        logger.info(f"   Duration: {report.duration_seconds:.2f}s")
        
        # Guardar reporte en Supabase
        if self.supabase_client and self.config.log_to_supabase:
            await self._log_report_to_supabase(report)
        
        return report
    
    async def _log_report_to_supabase(self, report: IngestionReport):
        """Guardar reporte de ingesta en Supabase"""
        try:
            # Crear tabla para logs si no existe
            log_entry = {
                "session_id": report.session_id,
                "start_time": report.start_time.isoformat(),
                "end_time": report.end_time.isoformat(),
                "duration_seconds": report.duration_seconds,
                "total_players": report.total_players,
                "successful": report.successful_ingestions,
                "failed": report.failed_ingestions,
                "success_rate": report.success_rate,
                "total_fallbacks": report.total_fallbacks,
                "source_metrics": report.source_metrics,
                "errors": report.errors[:10],  # Limitar
                "created_at": datetime.utcnow().isoformat()
            }
            
            self.supabase_client.supabase.table("ingestion_logs").insert(log_entry).execute()
            logger.debug(f"📝 Logged report to Supabase: {report.session_id}")
            
        except Exception as e:
            logger.error(f"❌ Error logging report to Supabase: {e}")
    
    async def ingest_by_region_priority(
        self,
        players_by_region: Dict[RegionProfile, List[str]],
        game: str = "lol"
    ) -> Dict[RegionProfile, IngestionReport]:
        """
        Ingerir jugadores segmentados por región con prioridades específicas
        
        Regiones de MICRO_METRICS (Korea/China): Prioriza APM, Gold/Min, DMG%
        Regiones de SOCIAL_SENTIMENT (India/Vietnam): Prioriza Consistency, Social
        
        Args:
            players_by_region: {RegionProfile.CHINA: ['player1', 'player2'], ...}
            game: Juego
        
        Returns:
            Reportes por región
        """
        logger.info("🌍 Starting region-priority ingestion")
        
        reports = {}
        
        for region, players in players_by_region.items():
            logger.info(f"📍 Processing region: {region} ({len(players)} players)")
            
            # Convertir a formato (identifier, region)
            player_tuples = [(p, region) for p in players]
            
            # Ingerir batch
            report = await self.ingest_players_batch(player_tuples, game)
            reports[region] = report
        
        # Resumen global
        total_players = sum(r.total_players for r in reports.values())
        total_successful = sum(r.successful_ingestions for r in reports.values())
        
        logger.success(f"🎉 Region-priority ingestion completed:")
        logger.info(f"   Total regions: {len(reports)}")
        logger.info(f"   Total players: {total_players}")
        logger.info(f"   Total successful: {total_successful}")
        logger.info(f"   Global success rate: {(total_successful/total_players*100):.2f}%")
        
        return reports


# ============================================================================
# FUNCIONES DE CONVENIENCIA PARA GITHUB ACTIONS
# ============================================================================

async def run_scheduled_ingestion(
    config_file: Optional[str] = None,
    players_file: Optional[str] = None
):
    """
    Función para ejecutar desde GitHub Actions
    
    Leer configuración y jugadores desde archivos JSON
    """
    # Leer config
    if config_file and os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config_data = json.load(f)
            config = IngestionConfig(**config_data)
    else:
        config = IngestionConfig()
    
    # Leer players
    players_by_region = {}
    
    if players_file and os.path.exists(players_file):
        with open(players_file, 'r', encoding='utf-8') as f:
            players_data = json.load(f)
            
            # Convertir strings a RegionProfile
            for region_str, players in players_data.items():
                try:
                    region = RegionProfile(region_str.lower())
                    players_by_region[region] = players
                except ValueError:
                    logger.warning(f"⚠️ Unknown region: {region_str}")
    else:
        # Datos de ejemplo
        players_by_region = {
            RegionProfile.KOREA: ["Faker", "ShowMaker", "Chovy"],
            RegionProfile.CHINA: ["JackeyLove", "TheShy"],
            RegionProfile.INDIA: ["IndianPro1", "IndianPro2"],
        }
    
    # Ejecutar ingesta
    async with MultiRegionIngestor(config) as ingestor:
        reports = await ingestor.ingest_by_region_priority(
            players_by_region,
            game="lol"
        )
        
        # Guardar reportes
        for region, report in reports.items():
            output_file = f"ingestion_report_{region.value}_{report.session_id}.json"
            with open(output_file, 'w') as f:
                json.dump(report.to_dict(), f, indent=2)
            
            logger.info(f"📄 Saved report: {output_file}")
    
    logger.success("🎊 Scheduled ingestion completed successfully!")


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

async def example_usage():
    """Ejemplo de uso del Multi-Region Ingestor"""
    
    # Configuración personalizada
    config = IngestionConfig(
        max_concurrent_requests=10,
        enable_fallback=True,
        log_to_supabase=True
    )
    
    async with MultiRegionIngestor(config) as ingestor:
        
        # Ejemplo 1: Ingest single player
        result = await ingestor.ingest_player(
            "Faker",
            region=RegionProfile.KOREA,
            game="lol"
        )
        
        if result.success:
            logger.info(f"✅ Success: {result.data['nickname']}")
        else:
            logger.error(f"❌ Failed: {result.error}")
        
        # Ejemplo 2: Batch ingestion
        korean_players = [
            ("Faker", RegionProfile.KOREA),
            ("ShowMaker", RegionProfile.KOREA),
            ("Chovy", RegionProfile.KOREA),
        ]
        
        report = await ingestor.ingest_players_batch(korean_players, game="lol")
        
        logger.info(f"📊 Report:")
        logger.info(f"  Success Rate: {report.success_rate:.2f}%")
        logger.info(f"  Duration: {report.duration_seconds:.2f}s")
        
        # Ejemplo 3: Region-priority ingestion
        players_by_region = {
            RegionProfile.KOREA: ["Faker", "ShowMaker", "Chovy"],
            RegionProfile.CHINA: ["JackeyLove", "TheShy", "Ming"],
            RegionProfile.INDIA: ["IndianPro1", "IndianPro2"],
            RegionProfile.VIETNAM: ["VietnamPro1"],
        }
        
        reports = await ingestor.ingest_by_region_priority(
            players_by_region,
            game="lol"
        )
        
        for region, region_report in reports.items():
            logger.info(f"📍 {region}: {region_report.success_rate:.2f}% success")


if __name__ == "__main__":
    # Para desarrollo local
    asyncio.run(example_usage())
    
    # Para GitHub Actions (comentar línea anterior, descomentar esta)
    # asyncio.run(run_scheduled_ingestion(
    #     config_file="ingestion_config.json",
    #     players_file="players_to_ingest.json"
    # ))
