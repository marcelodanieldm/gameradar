"""Compatibility wrapper for the packaged CNN Brasil scraper."""
import asyncio

from scraping.cnn_brasil_scraper import main


if __name__ == "__main__":
    asyncio.run(main())
