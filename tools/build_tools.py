#!/usr/bin/env python3
"""
Script de compilación automática de herramientas de seguridad.
Detecta el SO, compila cada herramienta y verifica que los binarios se crearon.

Uso:
    python build_tools.py           # Compilar todas
    python build_tools.py subfinder # Compilar una sola
    python build_tools.py --check   # Solo verificar cuáles están listas
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path

# Directorio base de herramientas
TOOLS_DIR = Path(__file__).parent
IS_WINDOWS = platform.system() == "Windows"
EXE = ".exe" if IS_WINDOWS else ""


def run_cmd(cmd: list, cwd: str = None, check: bool = True) -> bool:
    """Ejecuta un comando y retorna True si tuvo éxito"""
    print(f"  → Ejecutando: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=600
        )
        if result.returncode != 0:
            print(f"  ⚠ Error: {result.stderr[:300]}")
            return False
        return True
    except subprocess.TimeoutExpired:
        print("  ⚠ Timeout (10 min)")
        return False
    except FileNotFoundError:
        print(f"  ⚠ Comando no encontrado: {cmd[0]}")
        return False


def check_dependency(cmd: str) -> bool:
    """Verifica si un comando está disponible"""
    return shutil.which(cmd) is not None


# ═══════════════════════════════════════════════════
#  Definición de herramientas y sus pasos de build
# ═══════════════════════════════════════════════════

TOOLS = {
    "subfinder": {
        "requires": ["go"],
        "build_dir": "subfinder/v2/cmd/subfinder",
        "build_cmd": ["go", "build", "-o", f"subfinder{EXE}", "."],
        "binary": f"subfinder/v2/cmd/subfinder/subfinder{EXE}",
        "description": "Descubrimiento pasivo de subdominios",
    },
    "amass": {
        "requires": ["go"],
        "build_dir": "amass/cmd/amass",
        "build_cmd": ["go", "build", "-o", f"amass{EXE}", "."],
        "binary": f"amass/cmd/amass/amass{EXE}",
        "description": "Mapeo de red y descubrimiento de activos",
    },
    "masscan": {
        "requires": ["make", "gcc"] if not IS_WINDOWS else ["make"],
        "build_dir": "masscan",
        "build_cmd": ["make", "-j4"] if not IS_WINDOWS else ["make"],
        "binary": f"masscan/bin/masscan{EXE}",
        "description": "Escáner masivo de puertos",
    },
    "rustscan": {
        "requires": ["cargo"],
        "build_dir": "rustscan",
        "build_cmd": ["cargo", "build", "--release"],
        "binary": f"rustscan/target/release/rustscan{EXE}",
        "description": "Escáner rápido de puertos (Rust)",
    },
    "httpx": {
        "requires": ["go"],
        "build_dir": "httpx/cmd/httpx",
        "build_cmd": ["go", "build", "-o", f"httpx{EXE}", "."],
        "binary": f"httpx/cmd/httpx/httpx{EXE}",
        "description": "Toolkit HTTP multi-propósito",
    },
    "nuclei": {
        "requires": ["go"],
        "build_dir": "nuclei/cmd/nuclei",
        "build_cmd": ["go", "build", "-o", f"nuclei{EXE}", "."],
        "binary": f"nuclei/cmd/nuclei/nuclei{EXE}",
        "description": "Escáner de vulnerabilidades con plantillas",
    },
    "ffuf": {
        "requires": ["go"],
        "build_dir": "ffuf",
        "build_cmd": ["go", "build", "-o", f"ffuf{EXE}", "."],
        "binary": f"ffuf/ffuf{EXE}",
        "description": "Fuzzer web rápido",
    },
    "whatweb": {
        "requires": ["ruby"],
        "build_dir": None,  # No requiere compilación
        "build_cmd": None,
        "binary": "WhatWeb/whatweb",
        "description": "Identificador de tecnologías web (Ruby)",
    },
    "testssl": {
        "requires": ["bash"] if not IS_WINDOWS else [],
        "build_dir": None,  # No requiere compilación
        "build_cmd": None,
        "binary": "testssl.sh/testssl.sh",
        "description": "Auditoría TLS/SSL (Bash)",
    },
}


def check_tool(name: str) -> bool:
    """Verifica si un binario ya está compilado"""
    tool = TOOLS[name]
    binary = TOOLS_DIR / tool["binary"]
    return binary.exists()


def build_tool(name: str) -> bool:
    """Compila una herramienta individual"""
    tool = TOOLS[name]

    print(f"\n{'='*50}")
    print(f"🔧 {name} - {tool['description']}")
    print(f"{'='*50}")

    # Verificar si ya está compilado
    if check_tool(name):
        print(f"  ✅ Ya compilado: {tool['binary']}")
        return True

    # No requiere compilación (whatweb, testssl)
    if tool["build_cmd"] is None:
        binary = TOOLS_DIR / tool["binary"]
        if binary.exists():
            print(f"  ✅ Listo (no requiere compilación)")
            return True
        else:
            print(f"  ⚠ No se encontró: {tool['binary']}")
            return False

    # Verificar dependencias
    missing = [dep for dep in tool["requires"] if not check_dependency(dep)]
    if missing:
        print(f"  ❌ Faltan dependencias: {', '.join(missing)}")
        print(f"     Instálalas: {', '.join(missing)}")
        return False

    # Compilar
    build_dir = str(TOOLS_DIR / tool["build_dir"])
    if not Path(build_dir).exists():
        print(f"  ❌ Directorio no encontrado: {build_dir}")
        return False

    # Verificar go.mod para herramientas Go
    if "go" in tool["requires"]:
        go_mod = Path(build_dir)
        # Buscar go.mod subiendo directorios
        while go_mod != TOOLS_DIR and not (go_mod / "go.mod").exists():
            go_mod = go_mod.parent
        if (go_mod / "go.mod").exists():
            print(f"  📦 Descargando dependencias Go...")
            run_cmd(["go", "mod", "download"], cwd=str(go_mod), check=False)

    print(f"  🔨 Compilando...")
    success = run_cmd(tool["build_cmd"], cwd=build_dir)

    if success and check_tool(name):
        print(f"  ✅ Compilado exitosamente: {tool['binary']}")
        return True
    else:
        print(f"  ❌ Error al compilar {name}")
        return False


def check_all():
    """Verifica el estado de todas las herramientas"""
    print("\n📋 Estado de herramientas:")
    print(f"{'─'*60}")

    results = {}
    for name, tool in TOOLS.items():
        status = "✅" if check_tool(name) else "❌"
        deps_ok = all(check_dependency(d) for d in tool["requires"])
        deps_status = "✅" if deps_ok else "⚠"

        print(f"  {status} {name:<12} | Deps: {deps_status} | {tool['description']}")
        results[name] = check_tool(name)

    compiled = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"\n  📊 {compiled}/{total} herramientas listas")

    return results


def main():
    print("🚀 BlitzScan - Script de compilación de herramientas")
    print(f"   OS: {platform.system()} | Arch: {platform.machine()}")
    print(f"   Tools dir: {TOOLS_DIR}")

    # Solo verificar
    if "--check" in sys.argv:
        check_all()
        return

    # Compilar una herramienta específica
    if len(sys.argv) > 1 and sys.argv[1] != "--check":
        tool_name = sys.argv[1].lower()
        if tool_name not in TOOLS:
            print(f"❌ Herramienta '{tool_name}' no reconocida")
            print(f"   Disponibles: {', '.join(TOOLS.keys())}")
            sys.exit(1)
        success = build_tool(tool_name)
        sys.exit(0 if success else 1)

    # Compilar todas
    print("\n📦 Compilando todas las herramientas...")

    # Primero verificar dependencias globales
    print("\n🔍 Verificando dependencias del sistema:")
    all_deps = set()
    for tool in TOOLS.values():
        all_deps.update(tool["requires"])
    for dep in sorted(all_deps):
        status = "✅" if check_dependency(dep) else "❌"
        print(f"  {status} {dep}")

    # Compilar cada una
    results = {}
    for name in TOOLS:
        results[name] = build_tool(name)

    # Resumen final
    print(f"\n{'═'*50}")
    print("📊 Resumen de compilación")
    print(f"{'═'*50}")
    for name, success in results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {name}")

    compiled = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"\n  Total: {compiled}/{total} herramientas compiladas")

    if compiled < total:
        print("\n⚠ Algunas herramientas no se compilaron.")
        print("  Verifica que las dependencias estén instaladas.")
        sys.exit(1)
    else:
        print("\n🎉 ¡Todas las herramientas compiladas exitosamente!")


if __name__ == "__main__":
    main()
