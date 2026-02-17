# Guía de Instalación - Herramientas de Seguridad

Esta guía te ayudará a compilar e instalar las herramientas de seguridad clonadas.

## 📋 Requisitos Previos

Antes de compilar, asegúrate de tener instalado:

- **Go** (1.21+) - Para herramientas de ProjectDiscovery, Amass
- **Rust** (1.70+) - Para RustScan, ffuf
- **GCC/Clang** - Para Masscan, Nmap
- **Ruby** - Para WhatWeb
- **Bash** - Para testssl.sh

## 🔧 Instalación por Herramienta

### 1. Subfinder (Go)

```bash
cd subfinder/v2/cmd/subfinder
go build .
# El binario estará en: subfinder/v2/cmd/subfinder/subfinder
```

### 2. Amass (Go)

```bash
cd amass
go install ./...
# O usa los binarios pre-compilados en releases
```

### 3. Masscan (C)

```bash
cd masscan
make
# El binario estará en: masscan/bin/masscan
```

### 4. RustScan (Rust)

```bash
cd rustscan
cargo build --release
# El binario estará en: rustscan/target/release/rustscan
```

### 5. Nmap (C/C++)

```bash
cd nmap
./configure
make
# El binario estará en: nmap/nmap
```

### 6. httpx (Go)

```bash
cd httpx/cmd/httpx
go build .
# El binario estará en: httpx/cmd/httpx/httpx
```

### 7. WhatWeb (Ruby)

```bash
cd WhatWeb
# No requiere compilación, usa directamente:
# ruby whatweb <url>
```

### 8. Nuclei (Go)

```bash
cd nuclei/v3/cmd/nuclei
go build .
# El binario estará en: nuclei/v3/cmd/nuclei/nuclei
```

### 9. ffuf (Go)

```bash
cd ffuf
go build .
# El binario estará en: ffuf/ffuf
```

### 10. testssl.sh (Bash)

```bash
cd testssl.sh
# No requiere compilación, usa directamente:
# ./testssl.sh <url>
chmod +x testssl.sh
```

## 🚀 Uso Desde el Backend

El backend de FastAPI podrá ejecutar estas herramientas usando `subprocess`:

```python
import subprocess

# Ejemplo: Ejecutar subfinder
result = subprocess.run(
    ["./tools/subfinder/v2/cmd/subfinder/subfinder", "-d", "example.com"],
    capture_output=True,
    text=True
)
print(result.stdout)
```

## ⚠️ Notas Importantes

1. **Permisos**: En Linux/Mac necesitarás permisos de ejecución (`chmod +x`)
2. **PATH**: Considera agregar los binarios al PATH del sistema
3. **Dependencias**: Algunas herramientas requieren librerías adicionales
4. **Actualizaciones**: Usa `git pull` en cada directorio para actualizar

## 📚 Documentación

Cada herramienta tiene su propia documentación en su respectivo README:

- `subfinder/README.md`
- `amass/README.md`
- etc.
