"""
Database schema bootstrap (single source of truth).

Runs every `migrations/*.sql` file in lexical order against PostgreSQL on
startup. All migrations are written to be idempotent (CREATE ... IF NOT EXISTS,
CREATE OR REPLACE), so this is safe to run on every boot and on a fresh DB
alike — replacing the old "create tables by hand then patch with fix_*.py"
workflow. If the database is deleted, a single startup recreates it correctly.
"""

import os
import logging
from pathlib import Path

import asyncpg

logger = logging.getLogger(__name__)

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def get_database_url() -> str:
    return os.getenv(
        "DATABASE_URL",
        "postgresql://inmyhead_user:dev_password_123@localhost:5432/inmyhead",
    )


async def run_migrations(db_url: str | None = None) -> int:
    """
    Apply all SQL migrations in order. Returns the number of files applied.
    Failures are logged but do not crash startup (the RAG/ingest paths work
    without the DB; conversations degrade clearly if it is unavailable).
    """
    db_url = db_url or get_database_url()

    if not MIGRATIONS_DIR.is_dir():
        logger.warning("No migrations directory at %s", MIGRATIONS_DIR)
        return 0

    sql_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not sql_files:
        logger.info("No migration files found in %s", MIGRATIONS_DIR)
        return 0

    try:
        conn = await asyncpg.connect(db_url)
    except Exception as e:
        logger.warning("Skipping migrations — could not connect to DB: %s", e)
        return 0

    applied = 0
    try:
        for sql_file in sql_files:
            sql = sql_file.read_text(encoding="utf-8")
            try:
                await conn.execute(sql)
                applied += 1
                logger.info("Applied migration: %s", sql_file.name)
            except Exception as e:
                logger.error("Migration %s failed: %s", sql_file.name, e)
    finally:
        await conn.close()

    logger.info("Database migrations complete (%d/%d applied)", applied, len(sql_files))
    return applied
