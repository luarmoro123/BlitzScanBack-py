#!/usr/bin/env python3
"""
🚀 BlitzScan — Script Maestro de Instalación
=============================================
Configura automáticamente todo el entorno de desarrollo.

Uso:
    python setup.py                 # Instalación completa
    python setup.py --check         # Solo verificar estado
    python setup.py --tools-only    # Solo herramientas de seguridad
    python setup.py --backend-only  # Solo dependencias del backend
"""

import os
import sys
import subprocess
import shutil
import platform
import secrets
from pathlib import Path

# ═══════════════════════════════════════════════════
#  Rutas del proyecto
# ═══════════════════════════════════════════════════
PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = PROJECT_ROOT / "backend"
TOOLS_DIR = PROJECT_ROOT / "tools"
ENV_FILE = BACKEND_DIR / ".env"
ENV_TEMPLATE = BACKEND_DIR / ".env.template"

IS_WINDOWS = platform.system() == "Windows"

PASS = "✅"
FAIL = "❌"
WARN = "⚠️"
INFO = "ℹ️"
STEP = "➤"


def print_header(text: str):
    print(f"\n{'═'*60}")
    print(f"  {text}")
    print(f"{'═'*60}")


def print_step(n: int, text: str):
    print(f"\n{STEP} Paso {n}: {text}")
    print(f"{'─'*50}")


def run_cmd(cmd: list | str, cwd: str = None, check: bool = True, shell: bool = False) -> subprocess.CompletedProcess:
    """Ejecuta un comando y muestra el resultado"""
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True,
            timeout=300, check=False, shell=shell
        )
        return result
    except subprocess.TimeoutExpired:
        print(f"  {WARN} Timeout ejecutando: {cmd}")
        return None
    except FileNotFoundError:
        print(f"  {FAIL} Comando no encontrado: {cmd[0] if isinstance(cmd, list) else cmd}")
        return None


# ═══════════════════════════════════════════════════
#  Funciones de verificación
# ═══════════════════════════════════════════════════

def check_python() -> bool:
    """Verifica Python >= 3.10"""
    v = sys.version_info
    ok = v.major == 3 and v.minor >= 10
    status = PASS if ok else FAIL
    print(f"  {status} Python {v.major}.{v.minor}.{v.micro}", end="")
    if not ok:
        print(" (se requiere >= 3.10)")
    else:
        print()
    return ok


def check_pip() -> bool:
    """Verifica que pip esté disponible"""
    result = run_cmd([sys.executable, "-m", "pip", "--version"])
    ok = result and result.returncode == 0
    if ok:
        version = result.stdout.split()[1] if result.stdout else "?"
        print(f"  {PASS} pip {version}")
    else:
        print(f"  {FAIL} pip no disponible")
    return ok


def check_redis() -> bool:
    """Verifica que Redis esté corriendo"""
    try:
        import redis as redis_lib
        r = redis_lib.Redis(host="localhost", port=6379, socket_timeout=2)
        r.ping()
        print(f"  {PASS} Redis — conectado en localhost:6379")
        return True
    except ImportError:
        print(f"  {WARN} Redis (módulo python no instalado, se instalará)")
        return False
    except Exception:
        print(f"  {FAIL} Redis — no está corriendo en localhost:6379")
        if IS_WINDOWS:
            print(f"      Solución: abre otra terminal y ejecuta: redis-server")
            print(f"      Si no lo tienes: winget install Redis.Redis")
        else:
            print(f"      Solución: sudo apt install redis-server && sudo service redis-server start")
        return False


def check_nmap() -> bool:
    """Verifica que Nmap esté instalado"""
    nmap_path = shutil.which("nmap")
    if nmap_path:
        result = run_cmd(["nmap", "--version"])
        version = result.stdout.split("\n")[0] if result and result.stdout else "?"
        print(f"  {PASS} Nmap — {version}")
        return True
    else:
        print(f"  {FAIL} Nmap — no encontrado")
        if IS_WINDOWS:
            print(f"      Descarga: https://nmap.org/download#windows")
        else:
            print(f"      Instalar: sudo apt install nmap")
        return False


def check_ruby() -> bool:
    """Verifica Ruby (para WhatWeb)"""
    ruby_path = shutil.which("ruby")
    if ruby_path:
        result = run_cmd(["ruby", "--version"])
        version = result.stdout.strip() if result and result.stdout else "?"
        print(f"  {PASS} Ruby — {version}")
        return True
    else:
        print(f"  {WARN} Ruby — no encontrado (necesario para WhatWeb)")
        if IS_WINDOWS:
            print(f"      Instalar: winget install RubyInstallerTeam.Ruby.3.3")
        else:
            print(f"      Instalar: sudo apt install ruby")
        return False


def check_bash() -> bool:
    """Verifica Bash (para testssl.sh)"""
    bash_path = shutil.which("bash")
    if bash_path:
        print(f"  {PASS} Bash — disponible (para testssl.sh)")
        return True
    else:
        print(f"  {WARN} Bash — no encontrado (necesario para testssl.sh)")
        if IS_WINDOWS:
            print(f"      Git Bash incluye bash. Instalar: https://git-scm.com/download/win")
        return False


def check_env_file() -> bool:
    """Verifica que .env exista y tenga valores válidos"""
    if ENV_FILE.exists():
        content = ENV_FILE.read_text()
        if "CAMBIAR_POR" in content or "CHANGE_ME" in content:
            print(f"  {WARN} .env existe pero tiene valores por defecto — edítalo")
            return False
        print(f"  {PASS} .env — configurado")
        return True
    print(f"  {FAIL} .env — no existe")
    return False


# ═══════════════════════════════════════════════════
#  Funciones de instalación
# ═══════════════════════════════════════════════════

def install_python_deps():
    """Instala dependencias Python del backend"""
    print(f"  📦 Instalando dependencias Python...")
    result = run_cmd(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q"],
        cwd=str(BACKEND_DIR)
    )
    if result and result.returncode == 0:
        print(f"  {PASS} Dependencias Python instaladas")
        return True
    else:
        error = result.stderr if result else "Error desconocido"
        print(f"  {FAIL} Error instalando dependencias: {error[:200]}")
        return False


def setup_env_file():
    """Crea .env a partir del template si no existe"""
    if ENV_FILE.exists():
        print(f"  {PASS} .env ya existe — no se modifica")
        return True

    if ENV_TEMPLATE.exists():
        content = ENV_TEMPLATE.read_text()
        # Generar SECRET_KEY aleatorio
        secret = secrets.token_urlsafe(32)
        content = content.replace("CAMBIAR_POR_UNA_CLAVE_ALEATORIA", secret)
        ENV_FILE.write_text(content)
        print(f"  {PASS} .env creado desde template con SECRET_KEY aleatorio")
        print(f"  {WARN} IMPORTANTE: edita .env y configura tu DATABASE_URL")
        return True
    else:
        print(f"  {FAIL} No se encontró .env.template")
        return False


def download_security_tools():
    """Descarga binarios de las herramientas de seguridad"""
    download_script = TOOLS_DIR / "download_binaries.py"
    if not download_script.exists():
        print(f"  {FAIL} No se encontró tools/download_binaries.py")
        return False

    print(f"  📦 Descargando herramientas de seguridad desde GitHub...")
    result = run_cmd(
        [sys.executable, str(download_script)],
        cwd=str(TOOLS_DIR)
    )
    if result:
        print(result.stdout)
        return result.returncode == 0
    return False


def run_migrations():
    """Ejecuta migraciones de Alembic"""
    if not check_env_file():
        print(f"  {WARN} Saltando migraciones — configura .env primero")
        return False

    print(f"  🔄 Ejecutando migraciones...")
    result = run_cmd(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=str(BACKEND_DIR)
    )
    if result and result.returncode == 0:
        print(f"  {PASS} Migraciones aplicadas correctamente")
        return True
    else:
        error = result.stderr if result else "Error desconocido"
        print(f"  {FAIL} Error en migraciones: {error[:200]}")
        print(f"      Asegúrate de que DATABASE_URL en .env es correcta")
        return False


def run_verification():
    """Ejecuta el script de verificación"""
    verify_script = TOOLS_DIR / "verify_setup.py"
    if verify_script.exists():
        result = run_cmd(
            [sys.executable, str(verify_script)],
            cwd=str(TOOLS_DIR)
        )
        if result:
            print(result.stdout)


# ═══════════════════════════════════════════════════
#  Modos de ejecución
# ═══════════════════════════════════════════════════

def check_only():
    """Solo verifica el estado sin instalar nada"""
    print_header("🔍 BlitzScan — Verificación de Estado")

    print("\n📋 SISTEMA:")
    check_python()
    check_pip()
    check_redis()
    check_nmap()
    check_ruby()
    check_bash()

    print("\n📋 BACKEND:")
    check_env_file()

    # Verificar dependencias Python
    deps = ["fastapi", "uvicorn", "sqlalchemy", "celery", "redis", "asyncpg", "alembic", "pydantic"]
    for dep in deps:
        try:
            __import__(dep)
            print(f"  {PASS} {dep}")
        except ImportError:
            print(f"  {FAIL} {dep} — no instalado")

    print("\n📋 HERRAMIENTAS:")
    bin_dir = TOOLS_DIR / "bin"
    tools_list = ["subfinder", "amass", "rustscan", "nuclei", "httpx", "ffuf"]
    ext = ".exe" if IS_WINDOWS else ""
    for tool in tools_list:
        p = bin_dir / f"{tool}{ext}"
        if p.exists():
            size = p.stat().st_size / (1024*1024)
            print(f"  {PASS} {tool:<12} | {size:.1f} MB")
        else:
            print(f"  {FAIL} {tool:<12} | no descargado")

    # WhatWeb y testssl
    if (TOOLS_DIR / "WhatWeb" / "whatweb").exists():
        print(f"  {PASS} {'whatweb':<12} | script Ruby")
    if (TOOLS_DIR / "testssl.sh" / "testssl.sh").exists():
        print(f"  {PASS} {'testssl':<12} | script Bash")

    check_nmap()


def install_tools_only():
    """Solo instala herramientas de seguridad"""
    print_header("📦 BlitzScan — Herramientas de Seguridad")
    download_security_tools()


def install_backend_only():
    """Solo instala el backend"""
    print_header("📦 BlitzScan — Backend")
    print_step(1, "Verificar Python")
    if not check_python():
        print(f"\n{FAIL} Python 3.10+ es requerido. Abortando.")
        sys.exit(1)

    print_step(2, "Instalar dependencias")
    install_python_deps()

    print_step(3, "Configurar .env")
    setup_env_file()

    print_step(4, "Migraciones de BD")
    run_migrations()


def full_install():
    """Instalación completa"""
    print_header("🚀 BlitzScan — Instalación Completa")
    print(f"   OS: {platform.system()} | Arch: {platform.machine()}")
    print(f"   Python: {sys.version.split()[0]}")
    print(f"   Proyecto: {PROJECT_ROOT}")

    # ─── Paso 1: Python ───
    print_step(1, "Verificar Python")
    if not check_python():
        print(f"\n{FAIL} Python 3.10+ es requerido. Abortando.")
        sys.exit(1)
    check_pip()

    # ─── Paso 2: Dependencias Python ───
    print_step(2, "Instalar dependencias Python")
    install_python_deps()

    # ─── Paso 3: .env ───
    print_step(3, "Configurar variables de entorno")
    setup_env_file()

    # ─── Paso 4: Herramientas de seguridad ───
    print_step(4, "Descargar herramientas de seguridad")
    download_security_tools()

    # ─── Paso 5: Dependencias del sistema ───
    print_step(5, "Verificar dependencias del sistema")
    nmap_ok = check_nmap()
    ruby_ok = check_ruby()
    bash_ok = check_bash()
    redis_ok = check_redis()

    # ─── Paso 6: Migraciones ───
    print_step(6, "Migraciones de base de datos")
    run_migrations()

    # ─── Paso 7: Verificación final ───
    print_step(7, "Verificación final")

    print_header("📊 RESUMEN DE INSTALACIÓN")

    todos = []
    # Herramientas
    bin_dir = TOOLS_DIR / "bin"
    ext = ".exe" if IS_WINDOWS else ""
    for tool in ["subfinder", "amass", "rustscan", "nuclei", "httpx", "ffuf"]:
        ok = (bin_dir / f"{tool}{ext}").exists()
        todos.append(ok)
        print(f"  {PASS if ok else FAIL} {tool}")

    for name, ok in [("nmap", nmap_ok), ("ruby (whatweb)", ruby_ok), ("bash (testssl)", bash_ok), ("redis", redis_ok)]:
        todos.append(ok)
        print(f"  {PASS if ok else WARN} {name}")

    ready = sum(todos)
    total = len(todos)
    print(f"\n  📊 {ready}/{total} componentes listos")

    # Instrucciones finales
    print(f"\n{'═'*60}")
    print(f"  🎯 PRÓXIMOS PASOS")
    print(f"{'═'*60}")

    if not check_env_file():
        print(f"  1. Edita backend/.env con tu DATABASE_URL y SECRET_KEY")

    if not redis_ok:
        print(f"  2. Inicia Redis: redis-server (nueva terminal)")

    print(f"""
  Para iniciar el sistema completo (3 terminales):

  Terminal 1 — Redis:
    redis-server

  Terminal 2 — Celery Worker:
    cd backend
    celery -A app.core.celery_app worker --loglevel=info

  Terminal 3 — FastAPI:
    cd backend
    uvicorn app.main:app --reload

  Swagger UI: http://localhost:8000/docs
""")


# ═══════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════

def main():
    args = sys.argv[1:]

    if "--check" in args:
        check_only()
    elif "--tools-only" in args:
        install_tools_only()
    elif "--backend-only" in args:
        install_backend_only()
    elif "--help" in args or "-h" in args:
        print(__doc__)
    else:
        full_install()


if __name__ == "__main__":
    main()
