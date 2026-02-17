"""
Modelo de escaneo - Almacena información y resultados de cada escaneo ejecutado.
"""

import enum
from sqlalchemy import (
    Column, Integer, String, DateTime, Text,
    ForeignKey, Enum as SAEnum
)
from sqlalchemy.sql import func
from app.db.base import Base


class ScanType(str, enum.Enum):
    """Tipos de escaneo disponibles"""
    SUBDOMAIN = "subdomain"
    PORT = "port"
    SERVICE = "service"
    WEB = "web"
    VULNERABILITY = "vulnerability"
    SSL = "ssl"
    FULL = "full"


class ScanStatus(str, enum.Enum):
    """Estados posibles de un escaneo"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Scan(Base):
    """
    Modelo principal para almacenar escaneos.
    Cada fila representa un escaneo individual ejecutado por una herramienta.
    """
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True)

    # Información del escaneo
    scan_type = Column(SAEnum(ScanType), nullable=False)
    target = Column(String(500), nullable=False)  # Dominio, IP, URL
    tool_used = Column(String(100), nullable=False)  # subfinder, nmap, etc.

    # Estado y tiempos
    status = Column(SAEnum(ScanStatus), default=ScanStatus.PENDING, nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Resultados
    results = Column(Text, nullable=True)  # JSON string con resultados parseados
    raw_output = Column(Text, nullable=True)  # Salida cruda del comando
    error_message = Column(Text, nullable=True)

    # Celery task id para seguimiento
    celery_task_id = Column(String(255), nullable=True, index=True)
