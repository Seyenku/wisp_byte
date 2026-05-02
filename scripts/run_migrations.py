#!/usr/bin/env python3
"""
Database migration script for WispChat.
Run this script to apply all pending migrations before starting the application.

Usage:
    python scripts/run_migrations.py
"""

import os
import sys
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alembic.config import Config
from alembic import command
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_current_revision():
    """Get the current database revision."""
    from app.database import engine
    
    with engine.connect() as connection:
        context = MigrationContext.configure(connection)
        return context.get_current_revision()


def get_head_revision():
    """Get the latest available revision."""
    alembic_cfg = Config("alembic.ini")
    script = ScriptDirectory.from_config(alembic_cfg)
    return script.get_current_head()


def run_migrations():
    """Run all pending database migrations."""
    logger.info("Starting database migrations...")
    
    try:
        # Check current and head revisions
        current_rev = get_current_revision()
        head_rev = get_head_revision()
        
        if current_rev == head_rev:
            logger.info("Database is already up to date (revision: %s)", current_rev)
            return True
        
        logger.info("Current revision: %s", current_rev or "None (empty database)")
        logger.info("Target revision: %s", head_rev)
        
        # Run migrations
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        
        logger.info("Database migrations completed successfully!")
        return True
        
    except Exception as e:
        logger.error("Failed to run migrations: %s", str(e))
        return False


if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1)
