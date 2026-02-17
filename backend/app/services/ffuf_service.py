"""
FfufService - Fuzzing web rápido.
Usa ffuf para descubrimiento de directorios, archivos y parámetros ocultos.
"""

import json
from typing import Dict, Any, List
from app.services.base_scanner import BaseScanner
from app.core.scanner_config import TOOLS_DIR


# Wordlists incluidas o rutas comunes
WORDLISTS = {
    "common": "/usr/share/seclists/Discovery/Web-Content/common.txt",
    "big": "/usr/share/seclists/Discovery/Web-Content/big.txt",
    "directory-list-medium": "/usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt",
}


class FfufService(BaseScanner):
    tool_name = "ffuf"

    def build_command(self, target: str, **options) -> List[str]:
        # Asegurar que el target tenga FUZZ para inyección
        if "FUZZ" not in target:
            target = target.rstrip("/") + "/FUZZ"

        cmd = [
            self.binary_path,
            "-u", target,
            "-o", "-",         # Output a stdout
            "-of", "json",     # Formato JSON
            "-s",              # Silent
        ]

        # Wordlist
        wordlist = options.get("wordlist", "common")
        wordlist_path = WORDLISTS.get(wordlist, wordlist)
        cmd.extend(["-w", wordlist_path])

        # Extensiones de archivo
        if options.get("extensions"):
            cmd.extend(["-e", options["extensions"]])

        # Filtrar por status code
        if options.get("match_codes"):
            cmd.extend(["-mc", options["match_codes"]])
        else:
            cmd.extend(["-mc", "200,301,302,403"])

        # Filtrar por tamaño
        if options.get("filter_size"):
            cmd.extend(["-fs", options["filter_size"]])

        # Hilos
        threads = options.get("threads", 40)
        cmd.extend(["-t", str(threads)])

        return cmd

    def parse_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        discovered = []

        try:
            data = json.loads(stdout)
            results = data.get("results", [])

            for entry in results:
                discovered.append({
                    "url": entry.get("url", ""),
                    "status": entry.get("status", 0),
                    "length": entry.get("length", 0),
                    "words": entry.get("words", 0),
                    "lines": entry.get("lines", 0),
                    "content_type": entry.get("content-type", ""),
                    "redirect_location": entry.get("redirectlocation", ""),
                })
        except json.JSONDecodeError:
            # Parsear línea por línea si el JSON global falla
            for line in stdout.strip().split("\n"):
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    discovered.append({
                        "url": entry.get("url", ""),
                        "status": entry.get("status", 0),
                        "length": entry.get("length", 0),
                    })
                except json.JSONDecodeError:
                    continue

        return {
            "discovered": discovered,
            "count": len(discovered),
        }
