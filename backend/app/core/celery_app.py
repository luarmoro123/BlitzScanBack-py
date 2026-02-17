"""
Configuración del worker Celery para tareas asíncronas de escaneo.
Usa Redis como broker y backend de resultados.
"""

from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "blitzscan",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Evitar que un task bloquee el worker para siempre
    task_soft_time_limit=900,   # 15 min soft limit
    task_time_limit=1200,       # 20 min hard limit
    # Reintentos
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# Auto-descubrir tareas en el módulo de tasks
celery_app.autodiscover_tasks(["app.services"])
