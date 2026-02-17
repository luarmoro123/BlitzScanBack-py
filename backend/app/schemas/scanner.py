"""
Schemas Pydantic para requests y responses de escaneos.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


# ──────────────────────────── Requests ────────────────────────────

class ScanRequest(BaseModel):
    """Request base para iniciar un escaneo"""
    target: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Dominio, IP o URL a escanear",
        examples=["example.com", "192.168.1.1"]
    )
    options: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Opciones adicionales para la herramienta"
    )


class PortScanRequest(ScanRequest):
    """Request para escaneo de puertos con opciones adicionales"""
    ports: Optional[str] = Field(
        default=None,
        description="Puertos a escanear (ej: '1-1000', '80,443,8080')"
    )
    scan_speed: Optional[int] = Field(
        default=3,
        ge=1, le=5,
        description="Velocidad de escaneo (1=lento/sigiloso, 5=rápido)"
    )


class VulnScanRequest(ScanRequest):
    """Request para escaneo de vulnerabilidades"""
    severity: Optional[str] = Field(
        default="medium,high,critical",
        description="Severidades a buscar: info, low, medium, high, critical"
    )
    templates: Optional[List[str]] = Field(
        default=None,
        description="Templates específicos de nuclei a usar"
    )


class SSLScanRequest(ScanRequest):
    """Request para auditoría SSL/TLS"""
    full_check: Optional[bool] = Field(
        default=False,
        description="Ejecutar todas las comprobaciones SSL"
    )


class FuzzerRequest(ScanRequest):
    """Request para fuzzing web con ffuf"""
    wordlist: Optional[str] = Field(
        default="common",
        description="Wordlist a usar: common, big, directory-list"
    )
    extensions: Optional[str] = Field(
        default=None,
        description="Extensiones de archivo a probar: php,html,js"
    )


# ──────────────────────────── Responses ────────────────────────────

class ScanResponse(BaseModel):
    """Response al iniciar un escaneo"""
    scan_id: int
    status: str
    message: str = "Escaneo iniciado correctamente"

    model_config = {"from_attributes": True}


class ScanStatusResponse(BaseModel):
    """Response con el estado actual de un escaneo"""
    scan_id: int
    scan_type: str
    target: str
    tool_used: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}


class ScanResultResponse(ScanStatusResponse):
    """Response con resultados completos del escaneo"""
    results: Optional[Dict[str, Any]] = None


class ScanListResponse(BaseModel):
    """Response con lista de escaneos"""
    total: int
    scans: List[ScanStatusResponse]
