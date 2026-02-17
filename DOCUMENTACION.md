# 📋 BlitzScan Backend — Documentación Técnica

## Índice

1. [Descripción General](#descripción-general)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Estructura del Proyecto](#estructura-del-proyecto)
4. [Configuración del Entorno](#configuración-del-entorno)
5. [Herramientas de Seguridad](#herramientas-de-seguridad)
6. [API Endpoints](#api-endpoints)
7. [Base de Datos](#base-de-datos)
8. [Sistema de Tareas Asíncronas](#sistema-de-tareas-asíncronas)
9. [Guía de Instalación y Despliegue](#guía-de-instalación-y-despliegue)
10. [Solución de Problemas](#solución-de-problemas)

---

## 1. Descripción General

**BlitzScan** es una plataforma de escaneo de seguridad que integra 10 herramientas de seguridad ofensiva de código abierto dentro de un backend API construido con FastAPI. Permite ejecutar escaneos de subdominios, puertos, servicios, vulnerabilidades y auditorías SSL/TLS a través de una API REST, con procesamiento asíncrono usando Celery + Redis.

### Stack Tecnológico

| Componente      | Tecnología               |
| --------------- | ------------------------ |
| Framework Web   | FastAPI (Python 3.13)    |
| Base de Datos   | PostgreSQL (Neon, cloud) |
| ORM             | SQLAlchemy 2.0+ (async)  |
| Migraciones     | Alembic                  |
| Cola de Tareas  | Celery 5.x               |
| Message Broker  | Redis                    |
| Driver BD Async | asyncpg                  |
| Driver BD Sync  | psycopg2 (para Celery)   |
| Autenticación   | JWT (python-jose)        |
| Validación      | Pydantic v2              |

---

## 2. Arquitectura del Sistema

```
┌──────────────┐     HTTP/REST      ┌──────────────┐
│   Frontend   │ ──────────────────▶│   FastAPI     │
│   (React)    │◀──────────────────│   Backend     │
└──────────────┘                    └──────┬───────┘
                                           │
                         ┌─────────────────┼─────────────────┐
                         │                 │                 │
                         ▼                 ▼                 ▼
                  ┌────────────┐   ┌────────────┐   ┌────────────┐
                  │ PostgreSQL │   │   Redis     │   │  Celery    │
                  │  (Neon)    │   │  (Broker)   │   │  Worker    │
                  └────────────┘   └────────────┘   └─────┬──────┘
                                                          │
                                                          ▼
                                                  ┌──────────────┐
                                                  │  Herramientas │
                                                  │  de Seguridad │
                                                  │  (tools/bin/) │
                                                  └──────────────┘
```

### Flujo de un Escaneo

1. El usuario envía un `POST /api/v1/scan/{tipo}` con el target
2. FastAPI crea un registro `Scan` en PostgreSQL con estado `pending`
3. Se lanza una tarea Celery (run_scan_task) y se devuelve el `scan_id`
4. El worker Celery toma la tarea, ejecuta el binario de la herramienta
5. El servicio parsea la salida y guarda los resultados en la BD
6. El usuario consulta `GET /api/v1/scan/{id}/results` para obtener resultados

---

## 3. Estructura del Proyecto

```
BlitzScanBack-py/
├── backend/
│   ├── alembic/                    # Migraciones de base de datos
│   │   ├── versions/               # Archivos de migración generados
│   │   └── env.py                  # Configuración de Alembic
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── auth.py         # Endpoints de autenticación (JWT)
│   │   │   │   ├── users.py        # CRUD de usuarios
│   │   │   │   └── scan.py         # ★ Endpoints de escaneo (10 rutas)
│   │   │   └── router.py           # Router principal v1
│   │   ├── core/
│   │   │   ├── config.py           # Settings (Pydantic v2)
│   │   │   ├── celery_app.py       # Configuración de Celery/Redis
│   │   │   └── scanner_config.py   # ★ Rutas a binarios y timeouts
│   │   ├── db/
│   │   │   ├── base.py             # Base declarativa SQLAlchemy
│   │   │   └── session.py          # Motor async y sesión de BD
│   │   ├── models/
│   │   │   ├── user.py             # Modelo de usuario
│   │   │   └── scan.py             # ★ Modelo de escaneo
│   │   ├── schemas/
│   │   │   ├── user.py             # Schemas de usuario
│   │   │   ├── token.py            # Schema de JWT token
│   │   │   └── scanner.py          # ★ Schemas de escaneo
│   │   ├── services/               # ★ Servicios de scanner
│   │   │   ├── base_scanner.py     # Clase abstracta base
│   │   │   ├── subfinder_service.py
│   │   │   ├── amass_service.py
│   │   │   ├── masscan_service.py
│   │   │   ├── rustscan_service.py
│   │   │   ├── nmap_service.py
│   │   │   ├── httpx_service.py
│   │   │   ├── whatweb_service.py
│   │   │   ├── nuclei_service.py
│   │   │   ├── ffuf_service.py
│   │   │   ├── testssl_service.py
│   │   │   └── tasks.py            # Tareas Celery
│   │   └── main.py                 # Punto de entrada de la app
│   ├── .env                        # Variables de entorno (NO en git)
│   ├── alembic.ini                 # Config de Alembic
│   └── requirements.txt            # Dependencias Python
│
├── tools/                          # ★ Herramientas de seguridad
│   ├── bin/                        # Binarios pre-compilados
│   │   ├── subfinder.exe
│   │   ├── amass.exe
│   │   ├── nuclei.exe
│   │   ├── httpx.exe
│   │   ├── ffuf.exe
│   │   └── rustscan.exe
│   ├── subfinder/                  # Código fuente (clonado de GitHub)
│   ├── amass/
│   ├── masscan/
│   ├── rustscan/
│   ├── nmap/
│   ├── httpx/
│   ├── WhatWeb/
│   ├── nuclei/
│   ├── ffuf/
│   ├── testssl.sh/
│   ├── download_binaries.py        # ★ Descarga automática de binarios
│   ├── build_tools.py              # Compilación desde fuente
│   ├── verify_setup.py             # Verificación del sistema
│   └── README.md
│
└── scan_results/                   # Resultados temporales de escaneos
```

---

## 4. Configuración del Entorno

### Variables de Entorno (`.env`)

```env
PROJECT_NAME=BlitzScan Backend
SECRET_KEY=<clave-secreta-larga-aleatoria>
DATABASE_URL=postgresql+asyncpg://usuario:pass@host/db?ssl=require
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:5173
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
```

### Instalación de Dependencias

```bash
cd backend
pip install -r requirements.txt
```

**Dependencias principales:**

| Paquete                     | Uso                    |
| --------------------------- | ---------------------- |
| `fastapi`                   | Framework web async    |
| `uvicorn[standard]`         | Servidor ASGI          |
| `sqlalchemy` + `asyncpg`    | BD async               |
| `alembic`                   | Migraciones            |
| `celery[redis]` + `redis`   | Tareas async           |
| `psycopg2-binary`           | BD sync (para Celery)  |
| `python-jose[cryptography]` | Tokens JWT             |
| `passlib[bcrypt]`           | Hashing de contraseñas |
| `pydantic[email]`           | Validación con email   |

---

## 5. Herramientas de Seguridad

### 5.1 Subfinder — Descubrimiento de Subdominios

| Propiedad       | Detalle                                                                                               |
| --------------- | ----------------------------------------------------------------------------------------------------- |
| **Repositorio** | [projectdiscovery/subfinder](https://github.com/projectdiscovery/subfinder)                           |
| **Lenguaje**    | Go                                                                                                    |
| **Función**     | Descubrimiento pasivo de subdominios usando múltiples fuentes (APIs, certificados, DNSdumpster, etc.) |
| **Endpoint**    | `POST /api/v1/scan/subdomain?tool=subfinder`                                                          |
| **Servicio**    | `app/services/subfinder_service.py`                                                                   |

**Opciones:**

- `json_output` (bool): Salida en JSON para parseo automático
- `sources` (str): Fuentes específicas a consultar
- `resolve` (bool): Resolver subdominios a IPs

**Ejemplo de resultado:**

```json
{
  "subdomains": ["mail.example.com", "api.example.com", "dev.example.com"],
  "count": 3,
  "sources": [{ "host": "mail.example.com", "source": "crtsh" }]
}
```

---

### 5.2 Amass — Mapeo de Red y Enumeración Activa

| Propiedad       | Detalle                                                                   |
| --------------- | ------------------------------------------------------------------------- |
| **Repositorio** | [owasp-amass/amass](https://github.com/owasp-amass/amass)                 |
| **Lenguaje**    | Go                                                                        |
| **Función**     | Enumeración activa y pasiva de subdominios con mapeo de relaciones de red |
| **Endpoint**    | `POST /api/v1/scan/subdomain?tool=amass`                                  |
| **Servicio**    | `app/services/amass_service.py`                                           |

**Opciones:**

- `passive` (bool): Modo pasivo (más sigiloso, por defecto)
- `timeout_minutes` (int): Timeout máximo en minutos

**Diferencia con Subfinder:** Amass es más completo pero más lento. Ideal para auditorías exhaustivas. Subfinder es más rápido para reconocimiento inicial.

---

### 5.3 Masscan — Escaneo Masivo de Puertos

| Propiedad       | Detalle                                                                     |
| --------------- | --------------------------------------------------------------------------- |
| **Repositorio** | [robertdavidgraham/masscan](https://github.com/robertdavidgraham/masscan)   |
| **Lenguaje**    | C                                                                           |
| **Función**     | Escaneo de puertos a la velocidad más alta posible (hasta 10M paquetes/seg) |
| **Endpoint**    | `POST /api/v1/scan/ports?tool=masscan`                                      |
| **Servicio**    | `app/services/masscan_service.py`                                           |

**Opciones:**

- `ports` (str): Rango de puertos (ej: `"1-1000"`, `"80,443,8080"`)
- `rate` (int): Paquetes por segundo (default: 1000)

**Nota:** Requiere privilegios de administrador. No disponible como binario pre-compilado en Windows; usar con WSL o Docker.

**Ejemplo de resultado:**

```json
{
  "open_ports": [
    { "ip": "192.168.1.1", "port": 80, "protocol": "tcp", "status": "open" },
    { "ip": "192.168.1.1", "port": 443, "protocol": "tcp", "status": "open" }
  ],
  "count": 2
}
```

---

### 5.4 RustScan — Escaneo Rápido de Puertos

| Propiedad       | Detalle                                                   |
| --------------- | --------------------------------------------------------- |
| **Repositorio** | [RustScan/RustScan](https://github.com/RustScan/RustScan) |
| **Lenguaje**    | Rust                                                      |
| **Función**     | Escaneo ultrarrápido de puertos con integración Nmap      |
| **Endpoint**    | `POST /api/v1/scan/ports?tool=rustscan`                   |
| **Servicio**    | `app/services/rustscan_service.py`                        |

**Opciones:**

- `ports` (str): Puertos a escanear
- `batch_size` (int): Puertos simultáneos (default: 2500)
- `timeout` (int): Timeout por conexión en ms

**Diferencia con Masscan:** RustScan es más moderno y no requiere privilegios de administrador. Masscan es más rápido a nivel de red pero necesita root.

---

### 5.5 Nmap — Enumeración Profunda de Servicios

| Propiedad       | Detalle                                                            |
| --------------- | ------------------------------------------------------------------ |
| **Repositorio** | [nmap/nmap](https://github.com/nmap/nmap)                          |
| **Lenguaje**    | C/C++                                                              |
| **Función**     | Detección de servicios, versiones, sistema operativo y scripts NSE |
| **Endpoint**    | `POST /api/v1/scan/services`                                       |
| **Servicio**    | `app/services/nmap_service.py`                                     |

**Tipos de escaneo:**

| Tipo         | Flag  | Descripción                         |
| ------------ | ----- | ----------------------------------- |
| `version`    | `-sV` | Detección de versiones de servicios |
| `aggressive` | `-A`  | OS, versión, scripts y traceroute   |
| `quick`      | `-F`  | Top 100 puertos (rápido)            |
| `stealth`    | `-sS` | SYN stealth scan (sigiloso)         |

**Opciones:**

- `scan_type` (str): Tipo de escaneo (ver tabla arriba)
- `ports` (str): Puertos específicos

**Ejemplo de resultado:**

```json
{
  "hosts": [
    {
      "status": "up",
      "addresses": [{ "addr": "93.184.216.34", "type": "ipv4" }],
      "ports": [
        {
          "port": 80,
          "protocol": "tcp",
          "state": "open",
          "service": "http",
          "product": "nginx",
          "version": "1.25.3"
        },
        {
          "port": 443,
          "protocol": "tcp",
          "state": "open",
          "service": "https",
          "product": "nginx",
          "version": "1.25.3"
        }
      ],
      "os": [{ "name": "Linux 5.x", "accuracy": "95" }]
    }
  ],
  "host_count": 1
}
```

---

### 5.6 httpx — Detección y Fingerprinting HTTP

| Propiedad       | Detalle                                                             |
| --------------- | ------------------------------------------------------------------- |
| **Repositorio** | [projectdiscovery/httpx](https://github.com/projectdiscovery/httpx) |
| **Lenguaje**    | Go                                                                  |
| **Función**     | Probar endpoints HTTP, detectar tecnologías, status codes, títulos  |
| **Endpoint**    | `POST /api/v1/scan/web?tool=httpx`                                  |
| **Servicio**    | `app/services/httpx_service.py`                                     |

**Opciones:**

- `tech_detect` (bool): Detectar tecnologías web
- `status_code` (bool): Mostrar código HTTP
- `title` (bool): Mostrar título de la página
- `cdn` (bool): Detectar CDN
- `follow_redirects` (bool): Seguir redirecciones

**Ejemplo de resultado:**

```json
{
  "endpoints": [
    {
      "url": "https://example.com",
      "status_code": 200,
      "title": "Example Domain",
      "tech": ["Nginx", "CloudFlare"],
      "webserver": "nginx/1.25",
      "cdn": true
    }
  ],
  "count": 1
}
```

---

### 5.7 WhatWeb — Identificación de Tecnologías Web

| Propiedad       | Detalle                                                                 |
| --------------- | ----------------------------------------------------------------------- |
| **Repositorio** | [urbanadventurer/WhatWeb](https://github.com/urbanadventurer/WhatWeb)   |
| **Lenguaje**    | Ruby                                                                    |
| **Función**     | Detectar CMS, frameworks, servidores, plugins y versiones de sitios web |
| **Endpoint**    | `POST /api/v1/scan/web?tool=whatweb`                                    |
| **Servicio**    | `app/services/whatweb_service.py`                                       |

**Opciones:**

- `aggression` (int): Nivel de agresividad (1=pasivo, 3=agresivo)

**Diferencia con httpx:** WhatWeb es más detallado en la detección de CMS y plugins. httpx es más rápido y multi-propósito.

---

### 5.8 Nuclei — Detección de Vulnerabilidades

| Propiedad       | Detalle                                                                                   |
| --------------- | ----------------------------------------------------------------------------------------- |
| **Repositorio** | [projectdiscovery/nuclei](https://github.com/projectdiscovery/nuclei)                     |
| **Lenguaje**    | Go                                                                                        |
| **Función**     | Escaneo de vulnerabilidades basado en plantillas YAML (CVEs, misconfigs, XSS, SQLi, etc.) |
| **Endpoint**    | `POST /api/v1/scan/vulnerabilities`                                                       |
| **Servicio**    | `app/services/nuclei_service.py`                                                          |

**Opciones:**

- `severity` (str): Severidades a buscar: `"info,low,medium,high,critical"`
- `templates` (list): Templates específicos a ejecutar
- `tags` (str): Tags de templates (ej: `"cve,xss"`)
- `rate_limit` (int): Requests por segundo

**Ejemplo de resultado:**

```json
{
  "vulnerabilities": [
    {
      "template_id": "cve-2021-44228",
      "name": "Apache Log4j - Remote Code Execution",
      "severity": "critical",
      "matched_at": "https://example.com/api",
      "tags": ["cve", "rce", "log4j"]
    }
  ],
  "count": 1,
  "by_severity": { "critical": 1, "high": 0, "medium": 0, "low": 0, "info": 0 }
}
```

---

### 5.9 ffuf — Fuzzing Web

| Propiedad       | Detalle                                                                            |
| --------------- | ---------------------------------------------------------------------------------- |
| **Repositorio** | [ffuf/ffuf](https://github.com/ffuf/ffuf)                                          |
| **Lenguaje**    | Go                                                                                 |
| **Función**     | Descubrimiento de directorios, archivos y parámetros ocultos mediante fuerza bruta |
| **Endpoint**    | `POST /api/v1/scan/fuzz`                                                           |
| **Servicio**    | `app/services/ffuf_service.py`                                                     |

**Opciones:**

- `wordlist` (str): Wordlist a usar (`"common"`, `"big"`, `"directory-list-medium"`)
- `extensions` (str): Extensiones a probar (ej: `"php,html,js"`)
- `match_codes` (str): Códigos HTTP a aceptar (default: `"200,301,302,403"`)
- `threads` (int): Hilos concurrentes (default: 40)

**Ejemplo de resultado:**

```json
{
  "discovered": [
    { "url": "https://example.com/admin", "status": 403, "length": 1234 },
    { "url": "https://example.com/api", "status": 200, "length": 5678 },
    { "url": "https://example.com/login", "status": 301, "length": 0 }
  ],
  "count": 3
}
```

---

### 5.10 testssl.sh — Auditoría SSL/TLS

| Propiedad       | Detalle                                                                                           |
| --------------- | ------------------------------------------------------------------------------------------------- |
| **Repositorio** | [drwetter/testssl.sh](https://github.com/drwetter/testssl.sh)                                     |
| **Lenguaje**    | Bash                                                                                              |
| **Función**     | Auditoría completa de configuración SSL/TLS: certificados, protocolos, cifrados, vulnerabilidades |
| **Endpoint**    | `POST /api/v1/scan/ssl`                                                                           |
| **Servicio**    | `app/services/testssl_service.py`                                                                 |

**Opciones:**

- `full_check` (bool): Ejecutar todas las comprobaciones
- `check_vulnerabilities` (bool): Buscar vulnerabilidades conocidas (Heartbleed, POODLE, etc.)

**Ejemplo de resultado:**

```json
{
  "findings": [
    { "id": "TLS1_3", "severity": "OK", "finding": "offered (OK)" },
    { "id": "TLS1_0", "severity": "LOW", "finding": "offered (deprecated)" }
  ],
  "certificates": [
    {
      "id": "cert_expirationStatus",
      "severity": "OK",
      "finding": "365 >= 60 days"
    }
  ],
  "vulnerabilities": [
    { "id": "heartbleed", "severity": "OK", "finding": "not vulnerable" }
  ]
}
```

---

### Tabla Comparativa de Herramientas

| Herramienta | Categoría        | Velocidad             | Requiere Root | Lenguaje |
| ----------- | ---------------- | --------------------- | ------------- | -------- |
| Subfinder   | Subdominios      | ⚡⚡⚡ Rápido         | No            | Go       |
| Amass       | Subdominios      | ⚡ Lento              | No            | Go       |
| Masscan     | Puertos          | ⚡⚡⚡⚡ Ultra-rápido | Sí            | C        |
| RustScan    | Puertos          | ⚡⚡⚡ Rápido         | No            | Rust     |
| Nmap        | Servicios        | ⚡⚡ Medio            | Sí (para SYN) | C/C++    |
| httpx       | Web              | ⚡⚡⚡ Rápido         | No            | Go       |
| WhatWeb     | Web              | ⚡⚡ Medio            | No            | Ruby     |
| Nuclei      | Vulnerabilidades | ⚡⚡ Medio            | No            | Go       |
| ffuf        | Fuzzing          | ⚡⚡⚡ Rápido         | No            | Go       |
| testssl.sh  | SSL/TLS          | ⚡ Lento              | No            | Bash     |

---

## 6. API Endpoints

### Autenticación

| Método | Ruta                         | Descripción       |
| ------ | ---------------------------- | ----------------- |
| `POST` | `/api/v1/login/access-token` | Obtener token JWT |

### Usuarios

| Método | Ruta             | Descripción     |
| ------ | ---------------- | --------------- |
| `GET`  | `/api/v1/users/` | Listar usuarios |
| `POST` | `/api/v1/users/` | Crear usuario   |

### Escaneos

| Método | Ruta                           | Descripción                   | Herramientas      |
| ------ | ------------------------------ | ----------------------------- | ----------------- |
| `POST` | `/api/v1/scan/subdomain`       | Descubrimiento de subdominios | subfinder, amass  |
| `POST` | `/api/v1/scan/ports`           | Escaneo de puertos            | masscan, rustscan |
| `POST` | `/api/v1/scan/services`        | Enumeración de servicios      | nmap              |
| `POST` | `/api/v1/scan/web`             | Fingerprinting web            | httpx, whatweb    |
| `POST` | `/api/v1/scan/vulnerabilities` | Detección de vulnerabilidades | nuclei            |
| `POST` | `/api/v1/scan/ssl`             | Auditoría SSL/TLS             | testssl.sh        |
| `POST` | `/api/v1/scan/fuzz`            | Fuzzing web                   | ffuf              |
| `GET`  | `/api/v1/scan/{id}`            | Estado de un escaneo          | —                 |
| `GET`  | `/api/v1/scan/{id}/results`    | Resultados del escaneo        | —                 |
| `GET`  | `/api/v1/scan/`                | Listar todos los escaneos     | —                 |

### Ejemplo de Uso

```bash
# 1. Iniciar escaneo de subdominios
curl -X POST http://localhost:8000/api/v1/scan/subdomain \
  -H "Content-Type: application/json" \
  -d '{"target": "example.com"}'

# Respuesta:
# {"scan_id": 1, "status": "pending", "message": "Escaneo de subdominios iniciado con subfinder"}

# 2. Consultar estado
curl http://localhost:8000/api/v1/scan/1

# 3. Obtener resultados
curl http://localhost:8000/api/v1/scan/1/results
```

---

## 7. Base de Datos

### Modelo `User`

| Columna           | Tipo            | Descripción                  |
| ----------------- | --------------- | ---------------------------- |
| `id`              | Integer (PK)    | Identificador único          |
| `email`           | String (unique) | Correo electrónico           |
| `hashed_password` | String          | Contraseña hasheada (bcrypt) |
| `is_active`       | Boolean         | Usuario activo               |
| `is_superuser`    | Boolean         | Permisos de administrador    |

### Modelo `Scan`

| Columna          | Tipo         | Descripción                                       |
| ---------------- | ------------ | ------------------------------------------------- |
| `id`             | Integer (PK) | Identificador único                               |
| `user_id`        | Integer (FK) | Usuario que inició el scan                        |
| `scan_type`      | Enum         | subdomain, port, service, web, vulnerability, ssl |
| `target`         | String(500)  | Dominio, IP o URL escaneado                       |
| `tool_used`      | String(100)  | Herramienta usada (subfinder, nmap, etc.)         |
| `status`         | Enum         | pending, running, completed, failed, cancelled    |
| `started_at`     | DateTime     | Fecha/hora de inicio                              |
| `completed_at`   | DateTime     | Fecha/hora de finalización                        |
| `results`        | Text (JSON)  | Resultados parseados en JSON                      |
| `raw_output`     | Text         | Salida cruda del comando                          |
| `error_message`  | Text         | Mensaje de error (si falló)                       |
| `celery_task_id` | String(255)  | ID de la tarea en Celery                          |

---

## 8. Sistema de Tareas Asíncronas

### ¿Por qué Celery?

Los escaneos de seguridad pueden tomar minutos u horas. Celery permite:

- Ejecutar tareas en background sin bloquear la API
- Escalar con múltiples workers
- Reintentar tareas fallidas automáticamente
- Monitorear progreso en tiempo real

### Componentes

```
FastAPI ──▶ Redis (Broker) ──▶ Celery Worker ──▶ Herramientas
   │                                │
   │                                ▼
   └──────── PostgreSQL ◀──── Guardar Resultados
```

### Archivos Clave

- **`app/core/celery_app.py`**: Configura Celery con Redis como broker
- **`app/services/tasks.py`**: Define la tarea `run_scan_task` que ejecuta los scanners
- **`app/core/scanner_config.py`**: Rutas a binarios y timeouts

### Comandos

```bash
# Iniciar worker
celery -A app.core.celery_app worker --loglevel=info

# Monitorear tareas (Flower)
pip install flower
celery -A app.core.celery_app flower
# Abrir http://localhost:5555
```

---

## 9. Guía de Instalación y Despliegue

### Requisitos Previos

- Python 3.10+
- Redis
- PostgreSQL (o cuenta en Neon)
- Git

### Paso 1: Clonar e Instalar

```bash
git clone <repo-url>
cd BlitzScanBack-py

# Dependencias Python
cd backend
pip install -r requirements.txt

# Descargar binarios de seguridad
cd ../tools
python download_binaries.py
```

### Paso 2: Configurar `.env`

```bash
cd backend
# Crear .env con tus credenciales (ver sección 4)
```

### Paso 3: Migraciones

```bash
cd backend
alembic upgrade head
```

### Paso 4: Iniciar Servicios

```bash
# Terminal 1: Redis (si no está corriendo como servicio)
redis-server

# Terminal 2: Celery Worker
cd backend
celery -A app.core.celery_app worker --loglevel=info

# Terminal 3: FastAPI
cd backend
uvicorn app.main:app --reload
```

### Paso 5: Verificar

```bash
# Verificación automática
cd tools
python verify_setup.py

# O abrir Swagger UI
# http://localhost:8000/docs
```

---

## 10. Solución de Problemas

### Error: `ModuleNotFoundError: No module named 'celery'`

```bash
pip install celery[redis] redis psycopg2-binary
```

### Error: `connection refused` en Redis

```bash
# Verificar que Redis está corriendo
redis-cli ping
# Si no responde, iniciar Redis:
redis-server
```

### Error: `cc1.exe: 64-bit mode not compiled in`

Tu compilador GCC es de 32 bits. Usa `python download_binaries.py` para descargar los binarios ya compilados.

### Error: Herramienta no encontrada

```bash
# Verificar estado
cd tools
python download_binaries.py --check

# Descargar las faltantes
python download_binaries.py
```

### Error: `ssl` parameter en psycopg2

psycopg2 síncrono usa `sslmode=require` en vez de `ssl=require`. El módulo `tasks.py` maneja esta conversión automáticamente.

---

> **⚠ ADVERTENCIA ÉTICA:** Estas herramientas deben usarse **únicamente con autorización explícita** del propietario del sistema objetivo. El uso no autorizado es ilegal en la mayoría de jurisdicciones. BlitzScan está diseñado para profesionales de seguridad en auditorías autorizadas y pentesting ético.

---

_Documentación generada el 17 de Febrero de 2026_
_BlitzScan Backend v1.0_
