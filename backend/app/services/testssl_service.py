"""
TestSSLService - Auditoría completa de TLS/SSL.
Usa testssl.sh para analizar la configuración SSL/TLS de un servidor.
"""

import json
import re
from typing import Dict, Any, List
from app.services.base_scanner import BaseScanner


class TestSSLService(BaseScanner):
    tool_name = "testssl"

    def build_command(self, target: str, **options) -> List[str]:
        cmd = [
            "bash",
            self.binary_path,
            "--jsonfile", "-",   # JSON a stdout
            "--warnings", "off",
        ]

        # Comprobaciones específicas
        if options.get("full_check", False):
            # Todas las comprobaciones
            pass  # testssl ya hace todo por defecto
        else:
            # Comprobaciones rápidas
            cmd.append("--fast")

        # Comprobar vulnerabilidades específicas
        if options.get("check_vulnerabilities", True):
            cmd.append("-U")  # Vulnerabilidades conocidas

        # Target
        cmd.append(target)

        return cmd

    def parse_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        findings = []
        certificates = []
        vulnerabilities = []

        try:
            data = json.loads(stdout)

            if isinstance(data, list):
                for entry in data:
                    finding = {
                        "id": entry.get("id", ""),
                        "severity": entry.get("severity", ""),
                        "finding": entry.get("finding", ""),
                    }

                    # Clasificar hallazgos
                    entry_id = finding["id"].lower()
                    if "cert" in entry_id or "chain" in entry_id:
                        certificates.append(finding)
                    elif entry.get("severity", "").upper() in [
                        "CRITICAL", "HIGH", "MEDIUM", "LOW"
                    ]:
                        vulnerabilities.append(finding)
                    else:
                        findings.append(finding)

        except json.JSONDecodeError:
            # Parseo texto si JSON falla
            for line in stdout.split("\n"):
                line = line.strip()
                if line and not line.startswith("#"):
                    findings.append({"raw": line})

        return {
            "findings": findings,
            "certificates": certificates,
            "vulnerabilities": vulnerabilities,
            "total_findings": len(findings),
            "total_vulnerabilities": len(vulnerabilities),
        }
