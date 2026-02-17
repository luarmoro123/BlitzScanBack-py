"""
HttpxService - Detección y fingerprinting HTTP.
Usa httpx de ProjectDiscovery para probar endpoints HTTP y detectar tecnologías.
"""

import json
from typing import Dict, Any, List
from app.services.base_scanner import BaseScanner


class HttpxService(BaseScanner):
    tool_name = "httpx"

    def build_command(self, target: str, **options) -> List[str]:
        cmd = [
            self.binary_path,
            "-u", target,
            "-silent",
            "-json",
        ]

        # Detección de tecnologías
        if options.get("tech_detect", True):
            cmd.append("-td")

        # Status code
        if options.get("status_code", True):
            cmd.append("-sc")

        # Título de la página
        if options.get("title", True):
            cmd.append("-title")

        # Detección de CDN
        if options.get("cdn", False):
            cmd.append("-cdn")

        # Seguir redirecciones
        if options.get("follow_redirects", True):
            cmd.append("-follow-redirects")

        return cmd

    def parse_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        results = []

        for line in stdout.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                results.append({
                    "url": data.get("url", ""),
                    "status_code": data.get("status_code", 0),
                    "title": data.get("title", ""),
                    "tech": data.get("tech", []),
                    "content_type": data.get("content_type", ""),
                    "content_length": data.get("content_length", 0),
                    "webserver": data.get("webserver", ""),
                    "cdn": data.get("cdn", False),
                    "host": data.get("host", ""),
                })
            except json.JSONDecodeError:
                continue

        return {
            "endpoints": results,
            "count": len(results),
        }
