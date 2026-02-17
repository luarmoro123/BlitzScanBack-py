"""
NucleiService - Escaneo de vulnerabilidades basado en plantillas.
Usa Nuclei de ProjectDiscovery para detectar CVEs, misconfigs, y vulnerabilidades.
"""

import json
from typing import Dict, Any, List
from app.services.base_scanner import BaseScanner


class NucleiService(BaseScanner):
    tool_name = "nuclei"

    def build_command(self, target: str, **options) -> List[str]:
        cmd = [
            self.binary_path,
            "-u", target,
            "-silent",
            "-json",
        ]

        # Filtrar por severidad
        severity = options.get("severity", "medium,high,critical")
        if severity:
            cmd.extend(["-severity", severity])

        # Templates específicos
        if options.get("templates"):
            for template in options["templates"]:
                cmd.extend(["-t", template])

        # Tags de templates
        if options.get("tags"):
            cmd.extend(["-tags", options["tags"]])

        # Excluir templates
        if options.get("exclude_tags"):
            cmd.extend(["-etags", options["exclude_tags"]])

        # Rate limit
        rate = options.get("rate_limit", 150)
        cmd.extend(["-rl", str(rate)])

        return cmd

    def parse_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        vulnerabilities = []

        for line in stdout.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                info = data.get("info", {})

                vuln = {
                    "template_id": data.get("template-id", ""),
                    "name": info.get("name", ""),
                    "severity": info.get("severity", "unknown"),
                    "description": info.get("description", ""),
                    "tags": info.get("tags", []),
                    "reference": info.get("reference", []),
                    "matched_at": data.get("matched-at", ""),
                    "matcher_name": data.get("matcher-name", ""),
                    "type": data.get("type", ""),
                    "host": data.get("host", ""),
                    "curl_command": data.get("curl-command", ""),
                }
                vulnerabilities.append(vuln)
            except json.JSONDecodeError:
                continue

        # Agrupar por severidad
        by_severity = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
            "info": [],
        }
        for v in vulnerabilities:
            sev = v.get("severity", "info").lower()
            if sev in by_severity:
                by_severity[sev].append(v)

        return {
            "vulnerabilities": vulnerabilities,
            "count": len(vulnerabilities),
            "by_severity": {k: len(v) for k, v in by_severity.items()},
            "details_by_severity": by_severity,
        }
