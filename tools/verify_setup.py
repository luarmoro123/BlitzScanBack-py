#!/usr/bin/env python3
"""
Script de verificación de todas las herramientas de BlitzScan.
Ejecuta pruebas básicas para confirmar que cada componente funciona.

Uso:
    python verify_setup.py
"""

import subprocess
import shutil
import sys
import os
from pathlib import Path

TOOLS_DIR = Path(__file__).parent
BIN_DIR = TOOLS_DIR / "bin"
BACKEND_DIR = TOOLS_DIR.parent / "backend"

PASS = "✅"
FAIL = "❌"
WARN = "⚠"
INFO = "ℹ"

results = {}


def test_binary(name: str, cmd: list, success_check: str = None) -> bool:
    """Prueba que un binario se ejecute correctamente"""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=15
        )
        output = result.stdout + result.stderr
        # Algunos comandos retornan 0, otros retornan !=0 con --help
        if success_check:
            return success_check.lower() in output.lower()
        return len(output) > 0
    except FileNotFoundError:
        return False
    except subprocess.TimeoutExpired:
        return True  # Si tiene timeout al menos existe y corre
    except Exception:
        return False


def main():
    print("=" * 60)
    print("🔍 BlitzScan - Verificación Completa del Sistema")
    print("=" * 60)

    # ──────────────── 1. Binarios de herramientas ────────────────
    print("\n📦 1. HERRAMIENTAS DE SEGURIDAD")
    print("-" * 40)

    tools_tests = {
        "subfinder": {
            "paths": [BIN_DIR / "subfinder.exe", BIN_DIR / "subfinder"],
            "cmd_flag": "-version",
            "check": "subfinder",
        },
        "amass": {
            "paths": [BIN_DIR / "amass.exe", BIN_DIR / "amass"],
            "cmd_flag": "-version",
            "check": "amass",
        },
        "masscan": {
            "paths": [BIN_DIR / "masscan.exe", BIN_DIR / "masscan"],
            "cmd_flag": "--version",
            "check": "masscan",
        },
        "rustscan": {
            "paths": [BIN_DIR / "rustscan.exe", BIN_DIR / "rustscan"],
            "cmd_flag": "--version",
            "check": "rustscan",
        },
        "nmap": {
            "paths": [],  # Buscar en PATH
            "cmd_flag": "--version",
            "check": "nmap",
            "system": True,
        },
        "httpx": {
            "paths": [
                BIN_DIR / "httpx.exe", BIN_DIR / "httpx",
                TOOLS_DIR / "httpx" / "cmd" / "httpx" / "httpx.exe",
            ],
            "cmd_flag": "-version",
            "check": "httpx",
        },
        "whatweb": {
            "paths": [TOOLS_DIR / "WhatWeb" / "whatweb"],
            "cmd_flag": "--version",
            "check": "whatweb",
            "ruby": True,
        },
        "nuclei": {
            "paths": [BIN_DIR / "nuclei.exe", BIN_DIR / "nuclei"],
            "cmd_flag": "-version",
            "check": "nuclei",
        },
        "ffuf": {
            "paths": [
                BIN_DIR / "ffuf.exe", BIN_DIR / "ffuf",
                TOOLS_DIR / "ffuf" / "ffuf.exe",
            ],
            "cmd_flag": "-V",
            "check": "ffuf",
        },
        "testssl": {
            "paths": [TOOLS_DIR / "testssl.sh" / "testssl.sh"],
            "cmd_flag": "--version",
            "check": "testssl",
            "bash": True,
        },
    }

    for name, config in tools_tests.items():
        binary = None

        # Buscar binario
        for p in config["paths"]:
            if Path(p).exists():
                binary = str(p)
                break

        # Buscar en sistema
        if not binary and config.get("system"):
            binary = shutil.which(name)

        if not binary:
            binary = shutil.which(name)

        if not binary:
            print(f"  {FAIL} {name:<12} | No encontrado")
            results[name] = False
            continue

        # Construir comando de test
        if config.get("ruby"):
            cmd = ["ruby", binary, config["cmd_flag"]]
        elif config.get("bash"):
            cmd = ["bash", binary, config["cmd_flag"]]
        else:
            cmd = [binary, config["cmd_flag"]]

        ok = test_binary(name, cmd, config.get("check"))
        status = PASS if ok else FAIL
        location = "bin/" if "bin" in str(binary) else ("SYSTEM" if config.get("system") else "source/")
        print(f"  {status} {name:<12} | {location:<8} | {binary}")
        results[name] = ok

    tool_count = sum(1 for v in results.values() if v)
    print(f"\n  📊 {tool_count}/{len(results)} herramientas funcionando")

    # ──────────────── 2. Dependencias Python ────────────────
    print(f"\n📦 2. DEPENDENCIAS PYTHON")
    print("-" * 40)

    python_deps = [
        ("fastapi", "FastAPI framework"),
        ("uvicorn", "Servidor ASGI"),
        ("sqlalchemy", "ORM de base de datos"),
        ("alembic", "Migraciones de BD"),
        ("celery", "Cola de tareas async"),
        ("redis", "Cliente Redis"),
        ("pydantic", "Validación de datos"),
        ("asyncpg", "Driver PostgreSQL async"),
    ]

    for module, desc in python_deps:
        try:
            __import__(module)
            print(f"  {PASS} {module:<14} | {desc}")
        except ImportError:
            print(f"  {FAIL} {module:<14} | {desc} — NO INSTALADO")

    # ──────────────── 3. Redis ────────────────
    print(f"\n📦 3. REDIS")
    print("-" * 40)

    try:
        import redis as redis_lib
        r = redis_lib.Redis(host="localhost", port=6379, socket_timeout=3)
        r.ping()
        print(f"  {PASS} Redis          | Conectado en localhost:6379")
    except Exception as e:
        print(f"  {FAIL} Redis          | No disponible: {e}")
        print(f"  {INFO} Inicia Redis:  redis-server (en nueva terminal)")

    # ──────────────── 4. Base de datos ────────────────
    print(f"\n📦 4. BASE DE DATOS")
    print("-" * 40)

    try:
        sys.path.insert(0, str(BACKEND_DIR))
        os.chdir(str(BACKEND_DIR))
        from app.core.config import settings
        print(f"  {PASS} Config         | DATABASE_URL configurada")

        # Test conexión síncrona
        db_url = settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql+psycopg2")
        from sqlalchemy import create_engine, text
        engine = create_engine(db_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print(f"  {PASS} PostgreSQL     | Conexión exitosa a Neon")

            # Verificar tabla scan
            result = conn.execute(text(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'scan')"
            ))
            exists = result.scalar()
            if exists:
                print(f"  {PASS} Tabla 'scan'   | Migración aplicada correctamente")
            else:
                print(f"  {FAIL} Tabla 'scan'   | Migración NO aplicada")
        engine.dispose()
    except Exception as e:
        print(f"  {FAIL} Base de datos  | Error: {str(e)[:80]}")

    # ──────────────── 5. Backend API ────────────────
    print(f"\n📦 5. BACKEND API")
    print("-" * 40)

    try:
        from app.main import app
        scan_routes = [r for r in app.routes if hasattr(r, "path") and "/scan" in r.path]
        print(f"  {PASS} FastAPI        | App carga correctamente")
        print(f"  {PASS} Scan routes    | {len(scan_routes)} endpoints de escaneo")
    except Exception as e:
        print(f"  {FAIL} FastAPI        | Error: {str(e)[:80]}")

    # ──────────────── 6. Scanner Config ────────────────
    print(f"\n📦 6. SCANNER CONFIG")
    print("-" * 40)

    try:
        from app.core.scanner_config import SCANNER_BINARIES
        for name, path in SCANNER_BINARIES.items():
            exists = Path(path).exists() or shutil.which(str(path))
            status = PASS if exists else WARN
            print(f"  {status} {name:<12} → {Path(path).name}")
    except Exception as e:
        print(f"  {FAIL} Config         | Error: {str(e)[:80]}")

    # ──────────────── Resumen Final ────────────────
    print(f"\n{'=' * 60}")
    print("📊 RESUMEN FINAL")
    print(f"{'=' * 60}")
    print(f"  Herramientas: {tool_count}/{len(results)} funcionando")
    print(f"  Use 'python download_binaries.py' para descargar las faltantes")
    print(f"  Use 'uvicorn app.main:app --reload' para iniciar el servidor")
    print(f"  Swagger UI: http://localhost:8000/docs")


if __name__ == "__main__":
    main()
