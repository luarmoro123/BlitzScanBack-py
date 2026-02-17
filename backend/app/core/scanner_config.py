"""
Configuración de rutas a las herramientas de seguridad.
Define las rutas a los binarios y opciones globales de los scanners.
Busca binarios en: 1) tools/bin/ (pre-compilados) 2) paths de compilación 3) PATH del sistema
"""

import shutil
import platform
from pathlib import Path

# Raíz del proyecto (BlitzScanBack-py/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Directorio de herramientas
TOOLS_DIR = PROJECT_ROOT / "tools"

# Directorio de binarios pre-compilados
BIN_DIR = TOOLS_DIR / "bin"

IS_WINDOWS = platform.system() == "Windows"
EXE = ".exe" if IS_WINDOWS else ""


def _find_binary(name: str, *fallback_paths: Path) -> str:
    """
    Busca un binario en orden de prioridad:
    1. tools/bin/ (binarios pre-compilados descargados)
    2. Paths de compilación desde fuente (fallbacks)
    3. PATH del sistema
    """
    # 1. Buscar en bin/
    bin_path = BIN_DIR / f"{name}{EXE}"
    if bin_path.exists():
        return str(bin_path)

    # 2. Buscar en paths de compilación
    for path in fallback_paths:
        if path.exists():
            return str(path)

    # 3. Buscar en PATH del sistema
    system_path = shutil.which(name)
    if system_path:
        return system_path

    # Retornar path esperado en bin/ (dará error descriptivo al ejecutar)
    return str(bin_path)


# Rutas a los binarios de cada herramienta
SCANNER_BINARIES = {
    "subfinder": _find_binary(
        "subfinder",
        TOOLS_DIR / "subfinder" / "cmd" / "subfinder" / f"subfinder{EXE}",
    ),
    "amass": _find_binary(
        "amass",
        TOOLS_DIR / "amass" / "cmd" / "amass" / f"amass{EXE}",
    ),
    "masscan": _find_binary(
        "masscan",
        TOOLS_DIR / "masscan" / "bin" / f"masscan{EXE}",
    ),
    "rustscan": _find_binary(
        "rustscan",
        TOOLS_DIR / "rustscan" / "target" / "release" / f"rustscan{EXE}",
    ),
    "nmap": _find_binary("nmap"),
    "httpx": _find_binary(
        "httpx",
        TOOLS_DIR / "httpx" / "cmd" / "httpx" / f"httpx{EXE}",
    ),
    "whatweb": str(TOOLS_DIR / "WhatWeb" / "whatweb"),
    "nuclei": _find_binary(
        "nuclei",
        TOOLS_DIR / "nuclei" / "cmd" / "nuclei" / f"nuclei{EXE}",
    ),
    "ffuf": _find_binary(
        "ffuf",
        TOOLS_DIR / "ffuf" / f"ffuf{EXE}",
    ),
    "testssl": str(TOOLS_DIR / "testssl.sh" / "testssl.sh"),
}

# Timeouts por herramienta (en segundos)
SCANNER_TIMEOUTS = {
    "subfinder": 300,      # 5 min
    "amass": 600,          # 10 min
    "masscan": 300,        # 5 min
    "rustscan": 120,       # 2 min
    "nmap": 600,           # 10 min
    "httpx": 300,          # 5 min
    "whatweb": 120,        # 2 min
    "nuclei": 900,         # 15 min
    "ffuf": 300,           # 5 min
    "testssl": 300,        # 5 min
}

# Directorio temporal para resultados
SCAN_RESULTS_DIR = PROJECT_ROOT / "scan_results"
SCAN_RESULTS_DIR.mkdir(exist_ok=True)

