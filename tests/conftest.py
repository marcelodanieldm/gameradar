# ============================================================
# GameRadar AI - Configuración de Playwright
# Configuración centralizada para tests E2E
# ============================================================

import pathlib
import sys

from playwright.sync_api import Playwright, sync_playwright
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

def pytest_configure(config):
    """Configuración global de pytest para Playwright"""
    config.addinivalue_line(
        "markers", "asyncio: mark test as requiring asyncio"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )

# Configuración de Playwright
PLAYWRIGHT_CONFIG = {
    "headless": True,  # Cambiar a False para debugging visual
    "slow_mo": 0,      # ms de delay entre acciones (útil para debugging)
    "viewport": {
        "width": 1920,
        "height": 1080
    },
    "user_agent": "GameRadar-E2E-Tests/1.0",
}

# Timeouts
DEFAULT_TIMEOUT = 30000  # 30 segundos
NAVIGATION_TIMEOUT = 60000  # 60 segundos para navegación

# URLs
FRONTEND_URL = "http://localhost:3000"
API_URL = "http://localhost:8000"
