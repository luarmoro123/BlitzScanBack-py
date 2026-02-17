"""
MasscanService - Escaneo masivo y ultra-rápido de puertos.
Usa masscan para detectar puertos abiertos a alta velocidad.
"""

import re
import json
from typing import Dict, Any, List
from app.services.base_scanner import BaseScanner


class MasscanService(BaseScanner):
    tool_name = "masscan"

    def build_command(self, target: str, **options) -> List[str]:
        cmd = [self.binary_path]

        # Target (IP o rango CIDR)
        cmd.append(target)

        # Puertos a escanear
        ports = options.get("ports", "1-1000")
        cmd.extend(["-p", ports])

        # Velocidad de paquetes por segundo
        rate = options.get("rate", 1000)
        cmd.extend(["--rate", str(rate)])

        # Output en JSON
        cmd.extend(["--output-format", "json", "--output-filename", "-"])

        return cmd

    def parse_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        open_ports = []

        # Masscan produce JSON con comas finales, intentar parsear
        try:
            # Limpiar output de masscan (a veces tiene formato irregular)
            cleaned = stdout.strip()
            if cleaned.startswith("["):
                # Remover coma final antes de ]
                cleaned = re.sub(r",\s*]", "]", cleaned)
                data = json.loads(cleaned)
                for entry in data:
                    port_info = entry.get("ports", [{}])[0]
                    open_ports.append({
                        "ip": entry.get("ip", ""),
                        "port": port_info.get("port", 0),
                        "protocol": port_info.get("proto", "tcp"),
                        "status": port_info.get("status", "open"),
                    })
        except (json.JSONDecodeError, IndexError):
            # Fallback: parsear formato texto
            for line in stdout.split("\n"):
                match = re.search(
                    r"Discovered open port (\d+)/(tcp|udp) on ([\d.]+)", line
                )
                if match:
                    open_ports.append({
                        "port": int(match.group(1)),
                        "protocol": match.group(2),
                        "ip": match.group(3),
                        "status": "open",
                    })

        return {
            "open_ports": open_ports,
            "count": len(open_ports),
        }
