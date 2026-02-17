#!/usr/bin/env python3
"""
Descarga binarios pre-compilados de las herramientas de seguridad
desde los releases oficiales de GitHub.

Uso:
    python download_binaries.py            # Descargar todos
    python download_binaries.py subfinder  # Descargar uno solo
    python download_binaries.py --check    # Verificar estado
"""

import os
import sys
import platform
import zipfile
import tarfile
import shutil
import urllib.request
import json
from pathlib import Path

TOOLS_DIR = Path(__file__).parent
BIN_DIR = TOOLS_DIR / "bin"
BIN_DIR.mkdir(exist_ok=True)

IS_WINDOWS = platform.system() == "Windows"
ARCH = "amd64" if platform.machine() in ("x86_64", "AMD64") else "arm64"
OS_NAME = "windows" if IS_WINDOWS else "linux" if platform.system() == "Linux" else "darwin"
EXE = ".exe" if IS_WINDOWS else ""


def get_latest_release_url(repo: str) -> dict:
    """Obtiene info del último release de un repositorio de GitHub"""
    api_url = f"https://api.github.com/repos/{repo}/releases/latest"
    try:
        req = urllib.request.Request(api_url, headers={"User-Agent": "BlitzScan"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"  ⚠ Error consultando GitHub API: {e}")
        return {}


def find_asset(assets: list, keywords: list) -> dict:
    """Busca el asset correcto para el OS/arch actual"""
    for asset in assets:
        name = asset["name"].lower()
        if all(kw in name for kw in keywords):
            return asset
    return {}


def download_file(url: str, dest: Path) -> bool:
    """Descarga un archivo con barra de progreso"""
    try:
        print(f"  ⬇ Descargando: {url.split('/')[-1]}")
        urllib.request.urlretrieve(url, str(dest))
        return True
    except Exception as e:
        print(f"  ⚠ Error descargando: {e}")
        return False


def extract_binary(archive_path: Path, binary_name: str, dest_dir: Path) -> bool:
    """Extrae el binario de un archivo zip o tar.gz"""
    try:
        if str(archive_path).endswith(".zip"):
            with zipfile.ZipFile(archive_path, "r") as zf:
                for name in zf.namelist():
                    basename = Path(name).name
                    if basename == binary_name or basename == binary_name + ".exe":
                        # Extraer directamente al dest
                        data = zf.read(name)
                        out = dest_dir / basename
                        out.write_bytes(data)
                        if not IS_WINDOWS:
                            os.chmod(str(out), 0o755)
                        return True
                # Si no encontramos el binario exacto, extraer todo
                zf.extractall(str(dest_dir))
                return True

        elif str(archive_path).endswith((".tar.gz", ".tgz")):
            with tarfile.open(archive_path, "r:gz") as tf:
                for member in tf.getmembers():
                    basename = Path(member.name).name
                    if basename == binary_name or basename == binary_name + ".exe":
                        member.name = basename
                        tf.extract(member, str(dest_dir))
                        out = dest_dir / basename
                        if not IS_WINDOWS:
                            os.chmod(str(out), 0o755)
                        return True
                tf.extractall(str(dest_dir))
                return True

        return False
    except Exception as e:
        print(f"  ⚠ Error extrayendo: {e}")
        return False


# ═══════════════════════════════════════════════════
#  Herramientas y sus releases de GitHub
# ═══════════════════════════════════════════════════

TOOLS = {
    "subfinder": {
        "repo": "projectdiscovery/subfinder",
        "binary": f"subfinder{EXE}",
        "keywords": [OS_NAME, ARCH],
        "description": "Descubrimiento pasivo de subdominios",
    },
    "amass": {
        "repo": "owasp-amass/amass",
        "binary": f"amass{EXE}",
        "keywords": [OS_NAME, ARCH],
        "description": "Mapeo de red y descubrimiento de activos",
    },
    "masscan": {
        "repo": "robertdavidgraham/masscan",
        "binary": f"masscan{EXE}",
        "keywords": [OS_NAME] if IS_WINDOWS else ["linux"],
        "description": "Escáner masivo de puertos",
    },
    "rustscan": {
        "repo": "RustScan/RustScan",
        "binary": f"rustscan{EXE}",
        "keywords": ["windows" if IS_WINDOWS else "linux", "64"],
        "description": "Escáner rápido de puertos (Rust)",
    },
    "nuclei": {
        "repo": "projectdiscovery/nuclei",
        "binary": f"nuclei{EXE}",
        "keywords": [OS_NAME, ARCH],
        "description": "Escáner de vulnerabilidades con plantillas",
    },
    "httpx": {
        "repo": "projectdiscovery/httpx",
        "binary": f"httpx{EXE}",
        "keywords": [OS_NAME, ARCH],
        "description": "Toolkit HTTP multi-propósito",
    },
    "ffuf": {
        "repo": "ffuf/ffuf",
        "binary": f"ffuf{EXE}",
        "keywords": [OS_NAME, ARCH],
        "description": "Fuzzer web rápido",
    },
    "nmap": {
        "repo": None,  # Nmap se instala a nivel de sistema
        "binary": f"nmap{EXE}",
        "keywords": [],
        "description": "Escáner de red (instalar manualmente: https://nmap.org/download)",
    },
}


def download_tool(name: str) -> bool:
    """Descarga un binario pre-compilado de GitHub releases"""
    tool = TOOLS[name]

    print(f"\n{'='*50}")
    print(f"📦 {name} - {tool['description']}")
    print(f"{'='*50}")

    # Verificar si ya existe
    binary_path = BIN_DIR / tool["binary"]
    if binary_path.exists():
        size_mb = binary_path.stat().st_size / (1024 * 1024)
        print(f"  ✅ Ya descargado: bin/{tool['binary']} ({size_mb:.1f} MB)")
        return True

    # Herramientas sin release automático
    if tool["repo"] is None:
        print(f"  ℹ {name} debe instalarse manualmente")
        print(f"    Descarga desde: https://nmap.org/download")
        # Verificar si está en el PATH del sistema
        if shutil.which(name):
            print(f"  ✅ Encontrado en PATH del sistema")
            return True
        return False

    # Obtener último release
    print(f"  🔍 Buscando último release de {tool['repo']}...")
    release = get_latest_release_url(tool["repo"])
    if not release:
        print(f"  ❌ No se pudo obtener el release")
        return False

    version = release.get("tag_name", "unknown")
    print(f"  📋 Última versión: {version}")

    # Buscar el asset correcto
    assets = release.get("assets", [])
    asset = find_asset(assets, tool["keywords"])

    if not asset:
        print(f"  ❌ No se encontró binario para {OS_NAME}/{ARCH}")
        print(f"     Assets disponibles:")
        for a in assets[:5]:
            print(f"       - {a['name']}")
        return False

    # Descargar
    download_url = asset["browser_download_url"]
    filename = asset["name"]
    tmp_file = BIN_DIR / filename

    if not download_file(download_url, tmp_file):
        return False

    # Extraer binario
    print(f"  📂 Extrayendo binario...")
    if filename.endswith((".zip", ".tar.gz", ".tgz")):
        success = extract_binary(tmp_file, name, BIN_DIR)
        # Limpiar archivo temporal
        tmp_file.unlink(missing_ok=True)
        if not success:
            print(f"  ❌ Error al extraer {filename}")
            return False
    else:
        # El archivo ya es el binario
        final = BIN_DIR / tool["binary"]
        tmp_file.rename(final)
        if not IS_WINDOWS:
            os.chmod(str(final), 0o755)

    # Verificar
    binary_path = BIN_DIR / tool["binary"]
    if binary_path.exists():
        size_mb = binary_path.stat().st_size / (1024 * 1024)
        print(f"  ✅ Descargado exitosamente: bin/{tool['binary']} ({size_mb:.1f} MB)")
        return True
    else:
        # Buscar si se extrajo con otro nombre
        for f in BIN_DIR.iterdir():
            if name in f.name.lower() and f.is_file():
                f.rename(binary_path)
                print(f"  ✅ Renombrado y listo: bin/{tool['binary']}")
                return True
        print(f"  ❌ Binario no encontrado después de extraer")
        return False


def check_all():
    """Verifica el estado de todos los binarios"""
    print("\n📋 Estado de binarios pre-compilados:")
    print(f"   Directorio: {BIN_DIR}")
    print(f"{'─'*60}")

    results = {}
    for name, tool in TOOLS.items():
        binary_path = BIN_DIR / tool["binary"]
        if binary_path.exists():
            size_mb = binary_path.stat().st_size / (1024 * 1024)
            print(f"  ✅ {name:<12} | {size_mb:>6.1f} MB | {tool['description']}")
            results[name] = True
        elif tool["repo"] is None and shutil.which(name):
            print(f"  ✅ {name:<12} | SYSTEM   | {tool['description']}")
            results[name] = True
        else:
            print(f"  ❌ {name:<12} |          | {tool['description']}")
            results[name] = False

    # WhatWeb y testssl (no necesitan download)
    for extra in [("whatweb", "WhatWeb/whatweb"), ("testssl", "testssl.sh/testssl.sh")]:
        if (TOOLS_DIR / extra[1]).exists():
            print(f"  ✅ {extra[0]:<12} | SOURCE   | Script (no requiere binario)")

    ready = sum(1 for v in results.values() if v)
    print(f"\n  📊 {ready}/{len(results)} binarios listos")
    return results


def main():
    print("🚀 BlitzScan - Descarga de binarios pre-compilados")
    print(f"   OS: {OS_NAME} | Arch: {ARCH}")
    print(f"   Destino: {BIN_DIR}")

    if "--check" in sys.argv:
        check_all()
        return

    # Descargar uno solo
    if len(sys.argv) > 1 and sys.argv[1] not in ("--check",):
        name = sys.argv[1].lower()
        if name not in TOOLS:
            print(f"❌ '{name}' no reconocido. Disponibles: {', '.join(TOOLS.keys())}")
            sys.exit(1)
        success = download_tool(name)
        sys.exit(0 if success else 1)

    # Descargar todos
    print("\n📦 Descargando todos los binarios...")
    results = {}
    for name in TOOLS:
        results[name] = download_tool(name)

    # Resumen
    print(f"\n{'═'*50}")
    print("📊 Resumen de descargas")
    print(f"{'═'*50}")
    for name, success in results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {name}")

    ready = sum(1 for v in results.values() if v)
    print(f"\n  Total: {ready}/{len(results)} binarios descargados")

    if ready >= len(results) - 1:  # nmap puede ser manual
        print("\n🎉 ¡Binarios listos!")
    else:
        print("\n⚠ Algunos binarios no se descargaron.")


if __name__ == "__main__":
    main()
