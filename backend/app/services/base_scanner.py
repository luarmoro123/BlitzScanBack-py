"""
BaseScanner - Clase abstracta base para todas las herramientas de escaneo.
Define la interfaz común que cada servicio de scanner debe implementar.
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from app.core.scanner_config import SCANNER_BINARIES, SCANNER_TIMEOUTS

logger = logging.getLogger(__name__)


class BaseScanner(ABC):
    """
    Clase base para todos los servicios de escaneo.
    Cada herramienta (subfinder, nmap, etc.) hereda de esta clase
    e implementa build_command() y parse_output().
    """

    # Nombre de la herramienta (se sobreescribe en cada subclase)
    tool_name: str = "base"

    def __init__(self):
        self.binary_path = str(SCANNER_BINARIES.get(self.tool_name, self.tool_name))
        self.timeout = SCANNER_TIMEOUTS.get(self.tool_name, 300)

    @abstractmethod
    def build_command(self, target: str, **options) -> List[str]:
        """
        Construye la lista de argumentos del comando a ejecutar.
        Cada herramienta implementa su propia versión.
        """
        pass

    @abstractmethod
    def parse_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """
        Parsea la salida del comando y devuelve un diccionario estructurado.
        Cada herramienta implementa su propio parser.
        """
        pass

    def validate_target(self, target: str) -> bool:
        """
        Validación básica del target (dominio/IP/URL).
        Puede ser sobrescrita por scanners que necesiten validación especial.
        """
        if not target or len(target) > 500:
            return False
        # Evitar inyección de comandos
        dangerous_chars = [";", "&", "|", "`", "$", "(", ")", "{", "}", "<", ">", "\\"]
        for char in dangerous_chars:
            if char in target:
                return False
        return True

    async def execute(self, target: str, **options) -> Dict[str, Any]:
        """
        Ejecuta el scanner de forma asíncrona.
        1. Valida el target
        2. Construye el comando
        3. Ejecuta con timeout
        4. Parsea los resultados
        """
        # Validar target
        if not self.validate_target(target):
            raise ValueError(f"Target inválido o con caracteres peligrosos: {target}")

        # Construir comando
        cmd = self.build_command(target, **options)
        logger.info(f"[{self.tool_name}] Ejecutando: {' '.join(cmd)}")

        try:
            # Ejecutar de forma asíncrona con timeout
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout
            )

            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")

            logger.info(
                f"[{self.tool_name}] Terminado con código: {process.returncode}"
            )

            # Parsear resultados
            result = self.parse_output(stdout, stderr)
            result["_meta"] = {
                "tool": self.tool_name,
                "target": target,
                "return_code": process.returncode,
                "timestamp": datetime.utcnow().isoformat(),
            }
            return result

        except asyncio.TimeoutError:
            logger.error(f"[{self.tool_name}] Timeout después de {self.timeout}s")
            raise TimeoutError(
                f"{self.tool_name} excedió el timeout de {self.timeout} segundos"
            )
        except FileNotFoundError:
            logger.error(f"[{self.tool_name}] Binario no encontrado: {self.binary_path}")
            raise FileNotFoundError(
                f"Binario de {self.tool_name} no encontrado en: {self.binary_path}. "
                f"Ejecuta el script de compilación: python tools/build_tools.py"
            )
        except Exception as e:
            logger.error(f"[{self.tool_name}] Error: {str(e)}")
            raise
