# 🚀 BlitzScan Backend — Guía de Instalación

Guía paso a paso para configurar el proyecto después de clonar el repositorio.

## Requisitos Previos

Antes de empezar, asegúrate de tener instalado:

| Software   | Versión    | Cómo verificar     | Instalación                                     |
| ---------- | ---------- | ------------------ | ----------------------------------------------- |
| **Python** | ≥ 3.10     | `python --version` | [python.org](https://www.python.org/downloads/) |
| **Git**    | cualquiera | `git --version`    | [git-scm.com](https://git-scm.com/download/win) |
| **Nmap**   | ≥ 7.0      | `nmap --version`   | [nmap.org](https://nmap.org/download#windows)   |
| **Redis**  | cualquiera | `redis-cli ping`   | `winget install Redis.Redis`                    |
| **Ruby**   | ≥ 3.0      | `ruby --version`   | `winget install RubyInstallerTeam.Ruby.3.3`     |

> ⚠️ **Redis** y **Nmap** son necesarios. **Ruby** solo se necesita para WhatWeb.

---

## Instalación Rápida (1 comando)

```bash
git clone https://github.com/luarmoro123/BlitzScanBack-py.git
cd BlitzScanBack-py
python setup.py
```

El script `setup.py` hace todo automáticamente:

1. ✅ Instala dependencias Python
2. ✅ Crea `.env` desde el template
3. ✅ Descarga las herramientas de seguridad
4. ✅ Verifica dependencias del sistema
5. ✅ Ejecuta migraciones de BD

---

## Instalación Manual (paso a paso)

Si prefieres hacerlo manualmente:

### Paso 1 — Clonar el repositorio

```bash
git clone https://github.com/luarmoro123/BlitzScanBack-py.git
cd BlitzScanBack-py
```

### Paso 2 — Instalar dependencias Python

```bash
cd backend
pip install -r requirements.txt
```

### Paso 3 — Configurar variables de entorno

```bash
cp .env.template .env
```

Edita `backend/.env` y configura:

```env
# Genera una clave secreta:
# python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=tu_clave_secreta_aqui

# Base de datos PostgreSQL (pedir al admin del proyecto)
DATABASE_URL=postgresql+asyncpg://usuario:pass@host/dbname?ssl=require

# Redis (dejar localhost si es local)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
```

> 🔑 **Pide las credenciales de la base de datos al administrador del proyecto.**

### Paso 4 — Descargar herramientas de seguridad

```bash
cd ../tools
python download_binaries.py
```

Esto descarga 6 binarios (~130 MB total):

- subfinder, amass, rustscan, nuclei, httpx, ffuf

### Paso 5 — Exclusión de Antivirus (Windows)

Windows Defender puede detectar las herramientas de seguridad como amenazas y eliminarlas. Abre **PowerShell como Administrador** y ejecuta:

```powershell
Add-MpPreference -ExclusionPath "C:\RUTA\AL\PROYECTO\BlitzScanBack-py\tools\bin"
```

Después vuelve a descargar las herramientas:

```bash
python download_binaries.py
```

### Paso 6 — Migraciones de base de datos

```bash
cd ../backend
alembic upgrade head
```

### Paso 7 — Verificar instalación

```bash
cd ..
python setup.py --check
```

Deberías ver todo en ✅:

```
📋 SISTEMA:
  ✅ Python 3.13.x
  ✅ Redis — conectado
  ✅ Nmap — version 7.x
  ✅ Ruby — version 3.x

📋 HERRAMIENTAS:
  ✅ subfinder, amass, rustscan, nuclei, httpx, ffuf
  ✅ whatweb, testssl
```

---

## Iniciar el Sistema

Se necesitan **3 terminales** abiertas:

### Terminal 1 — Redis

```bash
redis-server
```

### Terminal 2 — Celery Worker (procesa escaneos)

```bash
cd backend
celery -A app.core.celery_app worker --loglevel=info
```

### Terminal 3 — Servidor API

```bash
cd backend
uvicorn app.main:app --reload
```

### Acceder

- **API Docs (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **API Base:** [http://localhost:8000/api/v1](http://localhost:8000/api/v1)

---

## Comandos Útiles

| Comando                                     | Qué hace                    |
| ------------------------------------------- | --------------------------- |
| `python setup.py`                           | Instalación completa        |
| `python setup.py --check`                   | Verificar estado            |
| `python setup.py --tools-only`              | Solo descargar herramientas |
| `python setup.py --backend-only`            | Solo configurar backend     |
| `python tools/download_binaries.py --check` | Ver estado de binarios      |

---

## Solución de Problemas

### Redis no conecta

```bash
# Verificar si está corriendo:
redis-cli ping
# Si responde PONG, está OK

# Si no responde, iniciar:
redis-server
```

### Error en migraciones

```
Verifica que DATABASE_URL en backend/.env sea correcta.
El formato correcto es:
postgresql+asyncpg://usuario:contraseña@host/basedatos?ssl=require
```

### Windows Defender elimina binarios

```powershell
# Ejecutar como Administrador:
Add-MpPreference -ExclusionPath "C:\RUTA\tools\bin"
# Después re-descargar:
python tools/download_binaries.py
```

### Nmap no encontrado

Instalar desde [nmap.org](https://nmap.org/download#windows).  
Asegúrate de marcar "Add to PATH" durante la instalación.
