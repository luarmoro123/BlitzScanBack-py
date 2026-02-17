"""
Tareas Celery para ejecución asíncrona de escaneos.
Cada tarea invoca el servicio correspondiente y guarda resultados en la BD.
"""

import json
import logging
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.celery_app import celery_app
from app.core.config import settings
from app.models.scan import ScanStatus

# Crear engine síncrono para Celery (Celery no soporta async directamente)
# Reemplazar asyncpg por psycopg2 para conexión síncrona
sync_db_url = settings.DATABASE_URL.replace(
    "postgresql+asyncpg", "postgresql+psycopg2"
)
sync_engine = create_engine(sync_db_url)
SyncSession = sessionmaker(bind=sync_engine)

logger = logging.getLogger(__name__)


# Mapa de herramientas a sus servicios
SCANNER_MAP = {
    "subfinder": "app.services.subfinder_service.SubfinderService",
    "amass": "app.services.amass_service.AmassService",
    "masscan": "app.services.masscan_service.MasscanService",
    "rustscan": "app.services.rustscan_service.RustScanService",
    "nmap": "app.services.nmap_service.NmapService",
    "httpx": "app.services.httpx_service.HttpxService",
    "whatweb": "app.services.whatweb_service.WhatWebService",
    "nuclei": "app.services.nuclei_service.NucleiService",
    "ffuf": "app.services.ffuf_service.FfufService",
    "testssl": "app.services.testssl_service.TestSSLService",
}


def _get_scanner(tool_name: str):
    """Instancia dinámica del servicio de scanner"""
    import importlib

    module_path, class_name = SCANNER_MAP[tool_name].rsplit(".", 1)
    module = importlib.import_module(module_path)
    scanner_class = getattr(module, class_name)
    return scanner_class()


def _update_scan_status(scan_id: int, status: ScanStatus, **kwargs):
    """Actualiza el estado de un scan en la BD"""
    from app.models.scan import Scan

    session = SyncSession()
    try:
        scan = session.query(Scan).filter(Scan.id == scan_id).first()
        if scan:
            scan.status = status
            for key, value in kwargs.items():
                if hasattr(scan, key):
                    setattr(scan, key, value)
            session.commit()
    finally:
        session.close()


@celery_app.task(bind=True, name="run_scan")
def run_scan_task(self, scan_id: int, tool_name: str, target: str, options: dict = None):
    """
    Tarea Celery principal para ejecutar un escaneo.
    Se ejecuta en un worker separado del servidor FastAPI.
    """
    import asyncio

    options = options or {}
    logger.info(f"[Task {self.request.id}] Iniciando {tool_name} scan en {target}")

    # Marcar como running
    _update_scan_status(
        scan_id,
        ScanStatus.RUNNING,
        celery_task_id=self.request.id,
        started_at=datetime.now(timezone.utc),
    )

    try:
        # Obtener el scanner
        scanner = _get_scanner(tool_name)

        # Ejecutar (asyncio.run porque Celery no es async)
        result = asyncio.run(scanner.execute(target, **options))

        # Guardar resultados
        _update_scan_status(
            scan_id,
            ScanStatus.COMPLETED,
            results=json.dumps(result, default=str),
            raw_output=json.dumps(result.get("_meta", {}), default=str),
            completed_at=datetime.now(timezone.utc),
        )

        logger.info(f"[Task {self.request.id}] {tool_name} completado exitosamente")
        return {"status": "completed", "scan_id": scan_id}

    except Exception as e:
        error_msg = str(e)
        logger.error(f"[Task {self.request.id}] Error en {tool_name}: {error_msg}")

        _update_scan_status(
            scan_id,
            ScanStatus.FAILED,
            error_message=error_msg,
            completed_at=datetime.now(timezone.utc),
        )

        return {"status": "failed", "scan_id": scan_id, "error": error_msg}
