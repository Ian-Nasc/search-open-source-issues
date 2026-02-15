#!/usr/bin/env python
"""Standalone embeddings script for cron jobs.

Usage:
    cd backend && python -m scripts.generate_embeddings
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.tasks.embeddings import generate_missing_embeddings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

if __name__ == "__main__":
    asyncio.run(generate_missing_embeddings())
