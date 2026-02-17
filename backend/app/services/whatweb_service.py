"""
WhatWebService - Identificación de tecnologías web.
Usa WhatWeb para detectar CMS, frameworks, servidores y plugins de un sitio web.
"""

import json
import re
from typing import Dict, Any, List
from app.services.base_scanner import BaseScanner


class WhatWebService(BaseScanner):
    tool_name = "whatweb"

    def build_command(self, target: str, **options) -> List[str]:
        cmd = [
            "ruby",
            self.binary_path,
            target,
            "--log-json=-",  # JSON a stdout
        ]

        # Nivel de agresividad (1=pasivo, 3=agresivo)
        aggression = options.get("aggression", 1)
        cmd.extend(["-a", str(aggression)])

        return cmd

    def parse_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        technologies = []

        for line in stdout.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                if isinstance(data, list):
                    for item in data:
                        technologies.append(self._extract_tech(item))
                elif isinstance(data, dict):
                    technologies.append(self._extract_tech(data))
            except json.JSONDecodeError:
                continue

        return {
            "technologies": technologies,
            "count": len(technologies),
        }

    def _extract_tech(self, data: dict) -> dict:
        """Extrae información de tecnologías de un resultado WhatWeb"""
        plugins = data.get("plugins", {})
        tech_list = []

        for plugin_name, plugin_data in plugins.items():
            entry = {"name": plugin_name}
            if isinstance(plugin_data, dict):
                if "version" in plugin_data:
                    entry["version"] = plugin_data["version"]
                if "string" in plugin_data:
                    entry["details"] = plugin_data["string"]
            tech_list.append(entry)

        return {
            "target": data.get("target", ""),
            "http_status": data.get("http_status", 0),
            "plugins": tech_list,
        }
