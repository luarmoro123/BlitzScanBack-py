"""
RustScanService - Escaneo rápido de puertos con integración Nmap.
Usa RustScan para descubrimiento ultrarrápido de puertos.
"""

import re
from typing import Dict, Any, List
from app.services.base_scanner import BaseScanner


class RustScanService(BaseScanner):
    tool_name = "rustscan"

    def build_command(self, target: str, **options) -> List[str]:
        cmd = [
            self.binary_path,
            "-a", target,
            "--ulimit", "5000",
            "-g",  # Greppable output
        ]

        # Rango de puertos
        if options.get("ports"):
            cmd.extend(["-p", options["ports"]])

        # Batch size (puertos simultáneos)
        batch = options.get("batch_size", 2500)
        cmd.extend(["-b", str(batch)])

        # Timeout por conexión
        timeout = options.get("timeout", 1500)
        cmd.extend(["--timeout", str(timeout)])

        return cmd

    def parse_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        open_ports = []

        for line in stdout.strip().split("\n"):
            line = line.strip()
            if not line:
                continue

            # Formato greppable: IP -> [ports]
            match = re.search(r"([\d.]+)\s*->\s*\[(.+)\]", line)
            if match:
                ip = match.group(1)
                ports_str = match.group(2)
                for port in ports_str.split(","):
                    port = port.strip()
                    if port.isdigit():
                        open_ports.append({
                            "ip": ip,
                            "port": int(port),
                            "protocol": "tcp",
                            "status": "open",
                        })

        return {
            "open_ports": open_ports,
            "count": len(open_ports),
        }
