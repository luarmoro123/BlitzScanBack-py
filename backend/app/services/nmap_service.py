"""
NmapService - Enumeración profunda de servicios y versiones.
Usa Nmap para detección de servicios, versiones y scripts NSE.
"""

import re
import xml.etree.ElementTree as ET
from typing import Dict, Any, List
from app.services.base_scanner import BaseScanner


class NmapService(BaseScanner):
    tool_name = "nmap"

    def build_command(self, target: str, **options) -> List[str]:
        cmd = [self.binary_path]

        # Tipo de escaneo
        scan_type = options.get("scan_type", "version")
        if scan_type == "version":
            cmd.append("-sV")   # Detección de versiones
        elif scan_type == "aggressive":
            cmd.append("-A")    # Agresivo: OS, versión, scripts, traceroute
        elif scan_type == "quick":
            cmd.append("-F")    # Fast scan (top 100 puertos)
        elif scan_type == "stealth":
            cmd.append("-sS")   # SYN stealth scan

        # Puertos específicos
        if options.get("ports"):
            cmd.extend(["-p", options["ports"]])

        # Output en XML para parseo estructurado
        cmd.extend(["-oX", "-"])

        # Target
        cmd.append(target)

        return cmd

    def parse_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        hosts = []

        try:
            root = ET.fromstring(stdout)

            for host_elem in root.findall("host"):
                host_data = {
                    "status": "unknown",
                    "addresses": [],
                    "hostnames": [],
                    "ports": [],
                    "os": [],
                }

                # Estado del host
                status = host_elem.find("status")
                if status is not None:
                    host_data["status"] = status.get("state", "unknown")

                # Direcciones
                for addr in host_elem.findall("address"):
                    host_data["addresses"].append({
                        "addr": addr.get("addr", ""),
                        "type": addr.get("addrtype", ""),
                    })

                # Hostnames
                hostnames_elem = host_elem.find("hostnames")
                if hostnames_elem is not None:
                    for hn in hostnames_elem.findall("hostname"):
                        host_data["hostnames"].append({
                            "name": hn.get("name", ""),
                            "type": hn.get("type", ""),
                        })

                # Puertos y servicios
                ports_elem = host_elem.find("ports")
                if ports_elem is not None:
                    for port in ports_elem.findall("port"):
                        state = port.find("state")
                        service = port.find("service")

                        port_data = {
                            "port": int(port.get("portid", 0)),
                            "protocol": port.get("protocol", "tcp"),
                            "state": state.get("state", "") if state is not None else "",
                            "service": service.get("name", "") if service is not None else "",
                            "version": service.get("version", "") if service is not None else "",
                            "product": service.get("product", "") if service is not None else "",
                        }
                        host_data["ports"].append(port_data)

                # Detección de SO
                os_elem = host_elem.find("os")
                if os_elem is not None:
                    for osmatch in os_elem.findall("osmatch"):
                        host_data["os"].append({
                            "name": osmatch.get("name", ""),
                            "accuracy": osmatch.get("accuracy", ""),
                        })

                hosts.append(host_data)

        except ET.ParseError:
            # Fallback: parseo de texto plano
            return self._parse_text_output(stdout)

        return {
            "hosts": hosts,
            "host_count": len(hosts),
        }

    def _parse_text_output(self, output: str) -> Dict[str, Any]:
        """Parseo fallback cuando el XML falla"""
        ports = []
        for line in output.split("\n"):
            match = re.search(
                r"(\d+)/(tcp|udp)\s+(\w+)\s+(\S+)(?:\s+(.*))?", line
            )
            if match:
                ports.append({
                    "port": int(match.group(1)),
                    "protocol": match.group(2),
                    "state": match.group(3),
                    "service": match.group(4),
                    "version": match.group(5) or "",
                })

        return {
            "hosts": [{"ports": ports}],
            "host_count": 1,
        }
