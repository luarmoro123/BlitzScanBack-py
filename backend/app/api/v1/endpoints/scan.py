"""
Endpoints para ejecutar escaneos de seguridad.
Cada endpoint crea un registro en la BD y lanza una tarea Celery.
"""

import json
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from app.db.session import get_db
from app.models.scan import Scan, ScanType, ScanStatus
from app.schemas.scanner import (
    ScanRequest,
    PortScanRequest,
    VulnScanRequest,
    SSLScanRequest,
    FuzzerRequest,
    ScanResponse,
    ScanStatusResponse,
    ScanResultResponse,
    ScanListResponse,
)
from app.services.tasks import run_scan_task

router = APIRouter()


# ─────────────────── Helpers ───────────────────

async def _create_and_launch_scan(
    db: AsyncSession,
    scan_type: ScanType,
    tool_name: str,
    target: str,
    options: dict = None,
) -> Scan:
    """Crea un registro de Scan y lanza la tarea Celery"""
    scan = Scan(
        scan_type=scan_type,
        target=target,
        tool_used=tool_name,
        status=ScanStatus.PENDING,
    )
    db.add(scan)
    await db.commit()
    await db.refresh(scan)

    # Lanzar tarea Celery
    task = run_scan_task.delay(scan.id, tool_name, target, options or {})

    # Guardar el task_id de Celery
    scan.celery_task_id = task.id
    await db.commit()

    return scan


# ─────────────── Subdomain Discovery ───────────────

@router.post("/subdomain", response_model=ScanResponse)
async def scan_subdomains(
    request: ScanRequest,
    tool: str = Query(
        default="subfinder",
        enum=["subfinder", "amass"],
        description="Herramienta a usar"
    ),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Descubrimiento de subdominios.
    Herramientas: subfinder (rápido, pasivo) o amass (completo, activo+pasivo).
    """
    scan = await _create_and_launch_scan(
        db, ScanType.SUBDOMAIN, tool, request.target, request.options
    )
    return ScanResponse(
        scan_id=scan.id,
        status="pending",
        message=f"Escaneo de subdominios iniciado con {tool}",
    )


# ──────────────── Port Scanning ────────────────

@router.post("/ports", response_model=ScanResponse)
async def scan_ports(
    request: PortScanRequest,
    tool: str = Query(
        default="rustscan",
        enum=["masscan", "rustscan"],
        description="Herramienta a usar"
    ),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Escaneo de puertos.
    Herramientas: masscan (masivo, rápido) o rustscan (moderno, flexible).
    """
    options = request.options or {}
    if request.ports:
        options["ports"] = request.ports
    if request.scan_speed:
        options["rate"] = request.scan_speed * 500  # Escalar velocidad

    scan = await _create_and_launch_scan(
        db, ScanType.PORT, tool, request.target, options
    )
    return ScanResponse(
        scan_id=scan.id,
        status="pending",
        message=f"Escaneo de puertos iniciado con {tool}",
    )


# ─────────────── Service Enumeration ───────────────

@router.post("/services", response_model=ScanResponse)
async def scan_services(
    request: ScanRequest,
    scan_type: str = Query(
        default="version",
        enum=["version", "aggressive", "quick", "stealth"],
        description="Tipo de escaneo Nmap"
    ),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Enumeración de servicios con Nmap.
    Detecta servicios, versiones, y opcionalmente sistema operativo.
    """
    options = request.options or {}
    options["scan_type"] = scan_type

    scan = await _create_and_launch_scan(
        db, ScanType.SERVICE, "nmap", request.target, options
    )
    return ScanResponse(
        scan_id=scan.id,
        status="pending",
        message=f"Escaneo de servicios iniciado con nmap ({scan_type})",
    )


# ──────────────── Web Fingerprinting ────────────────

@router.post("/web", response_model=ScanResponse)
async def scan_web(
    request: ScanRequest,
    tool: str = Query(
        default="httpx",
        enum=["httpx", "whatweb"],
        description="Herramienta a usar"
    ),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Detección y fingerprinting web.
    Herramientas: httpx (rápido, multi-propósito) o whatweb (detallado, CMS).
    """
    scan = await _create_and_launch_scan(
        db, ScanType.WEB, tool, request.target, request.options
    )
    return ScanResponse(
        scan_id=scan.id,
        status="pending",
        message=f"Escaneo web iniciado con {tool}",
    )


# ─────────────── Vulnerability Detection ───────────────

@router.post("/vulnerabilities", response_model=ScanResponse)
async def scan_vulnerabilities(
    request: VulnScanRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Detección de vulnerabilidades con Nuclei.
    Usa plantillas para detectar CVEs, misconfigs, y vulnerabilidades.
    """
    options = request.options or {}
    if request.severity:
        options["severity"] = request.severity
    if request.templates:
        options["templates"] = request.templates

    scan = await _create_and_launch_scan(
        db, ScanType.VULNERABILITY, "nuclei", request.target, options
    )
    return ScanResponse(
        scan_id=scan.id,
        status="pending",
        message="Escaneo de vulnerabilidades iniciado con nuclei",
    )


# ──────────────── SSL/TLS Audit ────────────────

@router.post("/ssl", response_model=ScanResponse)
async def scan_ssl(
    request: SSLScanRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Auditoría SSL/TLS con testssl.sh.
    Analiza certificados, protocolos, cifrados y vulnerabilidades SSL.
    """
    options = request.options or {}
    if request.full_check:
        options["full_check"] = True

    scan = await _create_and_launch_scan(
        db, ScanType.SSL, "testssl", request.target, options
    )
    return ScanResponse(
        scan_id=scan.id,
        status="pending",
        message="Auditoría SSL/TLS iniciada con testssl.sh",
    )


# ──────────────── Fuzzing ────────────────

@router.post("/fuzz", response_model=ScanResponse)
async def scan_fuzz(
    request: FuzzerRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Fuzzing web con ffuf.
    Descubre directorios, archivos y parámetros ocultos.
    """
    options = request.options or {}
    if request.wordlist:
        options["wordlist"] = request.wordlist
    if request.extensions:
        options["extensions"] = request.extensions

    scan = await _create_and_launch_scan(
        db, ScanType.WEB, "ffuf", request.target, options
    )
    return ScanResponse(
        scan_id=scan.id,
        status="pending",
        message="Fuzzing web iniciado con ffuf",
    )


# ──────────────── Status & Results ────────────────

@router.get("/{scan_id}", response_model=ScanStatusResponse)
async def get_scan_status(
    scan_id: int,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Obtiene el estado actual de un escaneo"""
    result = await db.execute(select(Scan).where(Scan.id == scan_id))
    scan = result.scalar_one_or_none()

    if not scan:
        raise HTTPException(status_code=404, detail="Escaneo no encontrado")

    return scan


@router.get("/{scan_id}/results", response_model=ScanResultResponse)
async def get_scan_results(
    scan_id: int,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Obtiene los resultados completos de un escaneo"""
    result = await db.execute(select(Scan).where(Scan.id == scan_id))
    scan = result.scalar_one_or_none()

    if not scan:
        raise HTTPException(status_code=404, detail="Escaneo no encontrado")

    # Parsear JSON de resultados
    results_dict = None
    if scan.results:
        try:
            results_dict = json.loads(scan.results)
        except json.JSONDecodeError:
            results_dict = {"raw": scan.results}

    return ScanResultResponse(
        scan_id=scan.id,
        scan_type=scan.scan_type.value if scan.scan_type else "",
        target=scan.target,
        tool_used=scan.tool_used,
        status=scan.status.value if scan.status else "",
        started_at=scan.started_at,
        completed_at=scan.completed_at,
        error_message=scan.error_message,
        results=results_dict,
    )


@router.get("/", response_model=ScanListResponse)
async def list_scans(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    status: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Lista todos los escaneos con paginación y filtro"""
    query = select(Scan).order_by(desc(Scan.started_at))

    if status:
        query = query.where(Scan.status == status)

    # Contar total
    from sqlalchemy import func
    count_result = await db.execute(select(func.count(Scan.id)))
    total = count_result.scalar()

    # Obtener página
    result = await db.execute(query.offset(skip).limit(limit))
    scans = result.scalars().all()

    return ScanListResponse(
        total=total,
        scans=[
            ScanStatusResponse(
                scan_id=s.id,
                scan_type=s.scan_type.value if s.scan_type else "",
                target=s.target,
                tool_used=s.tool_used,
                status=s.status.value if s.status else "",
                started_at=s.started_at,
                completed_at=s.completed_at,
                error_message=s.error_message,
            )
            for s in scans
        ],
    )
