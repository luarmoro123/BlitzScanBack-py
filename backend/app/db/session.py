
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.core.config import settings

# El motor asíncrono que usa la URL de tu .env
engine = create_async_engine(
    settings.DATABASE_URL, 
    echo=True, # Muestra el SQL en la consola (ideal para desarrollo)
    future=True
)

# Nueva forma recomendada en SQLAlchemy 2.0+
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

async def get_db():
    """
    Dependencia para FastAPI que proporciona una sesión de BD por cada petición.
    Se cierra automáticamente al terminar la función gracias al context manager 'async with'.
    """
    async with AsyncSessionLocal() as session:
        yield session
