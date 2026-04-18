"""Compatibility wrapper for the packaged ingestion entry point."""
import argparse
import asyncio

from ingestion.ingest_bronze_targets import ALL_SOURCES, main


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GameRadar Bronze Ingestion")
    parser.add_argument(
        "--sources",
        nargs="+",
        choices=ALL_SOURCES,
        default=ALL_SOURCES,
        help="Fuentes a scrapear (por defecto: todas)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Ejecutar sin escribir archivos",
    )
    args = parser.parse_args()
    asyncio.run(main(sources=args.sources, dry_run=args.dry_run))
