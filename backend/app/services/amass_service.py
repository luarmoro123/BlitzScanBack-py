"""
AmassService - Descubrimiento de subdominios y mapeo de red.
Usa OWASP Amass para enumeración activa y pasiva de subdominios.
"""

import json
from typing import Dict, Any, List
from app.services.base_scanner import BaseScanner


class AmassService(BaseScanner):
    tool_name = "amass"

    def build_command(self, target: str, **options) -> List[str]:
        cmd = [
            self.binary_path,
            "enum",
            "-d", target,
        ]

        # Modo pasivo (más lento pero más sigiloso)
        if options.get("passive", True):
            cmd.append("-passive")

        # Output en JSON
        if options.get("json_output", True):
            cmd.extend(["-json", "-"])

        # Timeout máximo
        timeout_min = options.get("timeout_minutes", 5)
        cmd.extend(["-timeout", str(timeout_min)])

        return cmd

    def parse_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        subdomains = []
        sources = []

        for line in stdout.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                name = data.get("name", "")
                if name:
                    subdomains.append(name)
                    sources.append({
                        "name": name,
                        "domain": data.get("domain", ""),
                        "addresses": data.get("addresses", []),
                        "source": data.get("source", ""),
                    })
            except json.JSONDecodeError:
                if line and "." in line:
                    subdomains.append(line)

        unique = list(dict.fromkeys(subdomains))

        return {
            "subdomains": unique,
            "count": len(unique),
            "details": sources,
        }
