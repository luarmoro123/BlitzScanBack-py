
from typing import List, Optional, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "BlitzScan Backend"
    API_V1_STR: str = "/api/v1"
    
    # SEGURIDAD: Cambia esto por un string aleatorio largo en tu .env
    SECRET_KEY: str = "changethis" 
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 días
    
    # DATABASE_URL se cargará desde el .env
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/blitzscan"

    # Celery / Redis para tareas asíncronas
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # CORS origins como string que se convertirá a lista
    BACKEND_CORS_ORIGINS: str = ""

    @field_validator("BACKEND_CORS_ORIGINS", mode="after")
    @classmethod
    def parse_cors_origins(cls, v: str) -> List[str]:
        """Convierte el string CSV a lista de URLs"""
        if isinstance(v, str) and v:
            return [origin.strip() for origin in v.split(",")]
        return []

    # Configuración moderna de Pydantic V2
    model_config = SettingsConfigDict(
        case_sensitive=True, 
        env_file=".env",
        extra="ignore"  # Ignora variables extra en el .env sin tronar
    )

settings = Settings()
