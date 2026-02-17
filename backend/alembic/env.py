
import asyncio
from logging.config import fileConfig
import os
import sys

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# -------------------------------------------------------------
# TRUCO PRO: Añadir el directorio actual al path de Python
# Esto evita el error "ModuleNotFoundError: No module named 'app'"
# -------------------------------------------------------------
sys.path.append(os.getcwd())

# Importar tus configuraciones y modelos
from app.core.config import settings
from app.db.base import Base

# Importar TODOS los modelos aquí para que Alembic los detecte
from app.models.user import User  # noqa
from app.models.scan import Scan  # noqa

# Configuración de Alembic
config = context.config

# Configurar Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadatos para las migraciones (tablas)
target_metadata = Base.metadata

# -------------------------------------------------------------
# SOBREESCRIBIR LA URL CON LA DE TU .ENV
# Esto es vital para que use la conexión a Neon y no la de alembic.ini
# -------------------------------------------------------------
config.set_main_option("sqlalchemy.url", str(settings.DATABASE_URL))


def run_migrations_offline() -> None:
    """Ejecuta migraciones en modo 'offline'."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Ejecuta migraciones en modo 'online' (conectado a Neon)."""
    
    # Crea el motor usando la configuración inyectada
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
