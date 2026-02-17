"""
SubfinderService - Descubrimiento pasivo de subdominios.
Usa subfinder de ProjectDiscovery para enumerar subdominios de un dominio objetivo.
"""

import json
from typing import Dict, Any, List
from app.services.base_scanner import BaseScanner


class SubfinderService(BaseScanner):
    tool_name = "subfinder"

    def build_command(self, target: str, **options) -> List[str]:
        cmd = [
            self.binary_path,
            "-d", target,
            "-silent",
        ]
        # Output en JSON para parseo estructurado
        if options.get("json_output", True):
            cmd.append("-json")

        # Fuentes específicas
        if options.get("sources"):
            cmd.extend(["-sources", options["sources"]])

        # Resolver subdominios
        if options.get("resolve", False):
            cmd.append("-nW")

        return cmd

    def parse_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        subdomains = []
        raw_entries = []

        for line in stdout.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                host = data.get("host", "")
                if host:
                    subdomains.append(host)
                    raw_entries.append(data)
            except json.JSONDecodeError:
                # Si no es JSON, tratar como texto plano
                if line and "." in line:
                    subdomains.append(line)

        # Eliminar duplicados manteniendo orden
        seen = set()
        unique = []
        for s in subdomains:
            if s not in seen:
                seen.add(s)
                unique.append(s)

        return {
            "subdomains": unique,
            "count": len(unique),
            "sources": raw_entries,
        }
