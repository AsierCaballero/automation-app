# 📚 Automation App - Documentación Completa

## Tabla de Contenidos
1. [Introducción](#introducción)
2. [Instalación](#instalación)
3. [Configuración](#configuración)
4. [CLI](#cli)
5. [API REST](#api-rest)
6. [Dashboard Web](#dashboard-web)
7. [Ejemplos de Automatización](#ejemplos-de-automatización)
8. [Despliegue](#despliegue)

---

## Introducción

Automation App es una herramienta de automatización de tareas DevOps que proporciona:

- **CLI** para gestión desde terminal
- **API REST** para integración con otros sistemas
- **Dashboard Web** para gestión visual
- **Base de datos** para persistencia de tareas y logs

### Requisitos
- Python 3.11+
- Docker (opcional)

---

## Instalación

### Opción 1: Docker (Recomendado)

```bash
# Clonar o copiar el proyecto
cd automation-app

# Crear archivo de configuración
cp .env.example .env

# Iniciar con Docker Compose
docker-compose up -d
```

### Opción 2: Python Local

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt

# Iniciar servidor
python cli.py web --port 8000
```

---

## Configuración

### Variables de Entorno

Crear archivo `.env`:

```env
DATABASE_URL=sqlite:///./automation.db
APP_PORT=8000
LOG_LEVEL=INFO
DEFAULT_TIMEOUT=300
MAX_CONCURRENT=5
```

### Variables Docker Compose

```yaml
services:
  automation:
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/automation
      - LOG_LEVEL=DEBUG
      - DEFAULT_TIMEOUT=600
```

### Tipos de Base de Datos Soportados

| Tipo | URL |
|------|-----|
| SQLite | `sqlite:///./automation.db` |
| PostgreSQL | `postgresql://user:pass@host:5432/db` |
| MySQL | `mysql://user:pass@host:3306/db` |

---

## CLI

### help

```bash
python cli.py --help
```

```
 Usage: cli.py [OPTIONS] COMMAND [ARGS]...

╭ Commands ──────────────────────────────────────╮
│  add      Agrega un nuevo task                  │
│  delete   Elimina un task                        │
│  list     Lista todos los tasks                  │
│  logs     Muestra logs de un task               │
│  run      Ejecuta un task por nombre            │
│  web      Inicia el dashboard web               │
╰─────────────────────────────────────────────────╯
```

---

### add - Crear Task

```bash
python cli.py add <nombre> <comando> [opciones]
```

**Argumentos:**
- `nombre` - Identificador único del task
- `comando` - Comando shell a ejecutar

**Opciones:**
- `--task-type` - Tipo de task (default: shell)

**Ejemplos:**

```bash
# Backup de archivos
python cli.py add backup "tar -czf backup.tar.gz ./data"

# Sincronizar con servidor
python cli.py add sync "rsync -avz /data/ user@server:/backup/"

# Verificar SSL
python cli.py add ssl-check "bash scripts/check-ssl.sh example.com"

# Deploy con Docker
python cli.py add deploy "cd /app && docker-compose up -d --build"
```

---

### list - Listar Tasks

```bash
python cli.py list
```

**Salida:**
```
╭ Tasks de Automatización ───────────────────────╮
│ Nombre        │ Tipo   │ Estado   │ Última Ejecución        │
├───────────────┼────────┼──────────┼─────────────────────────┤
│ backup        │ shell  │ success  │ 2024-01-15 02:00:00     │
│ sync          │ shell  │ idle     │ 2024-01-14 03:00:00     │
│ deploy        │ shell  │ failed   │ 2024-01-15 06:00:00     │
╰────────────────────────────────────────────────╯
```

---

### run - Ejecutar Task

```bash
python cli.py run --name <nombre>
```

**Ejemplos:**

```bash
# Ejecutar un task
python cli.py run --name backup

# Capturar salida
python cli.py run --name backup && echo "OK"
```

---

### logs - Ver Logs

```bash
python cli.py logs <nombre> [opciones]
```

**Opciones:**
- `--lines` - Número de líneas a mostrar (default: 20)

**Ejemplos:**

```bash
# Ver últimas 20 líneas
python cli.py logs backup

# Ver últimas 50 líneas
python cli.py logs backup --lines 50

# Ver todo el output
python cli.py logs backup --lines 1000
```

---

### delete - Eliminar Task

```bash
python cli.py delete <nombre>
```

**Ejemplos:**

```bash
python cli.py delete backup
python cli.py delete sync
```

---

### web - Dashboard Web

```bash
python cli.py web [opciones]
```

**Opciones:**
- `--host` - Host del servidor (default: 0.0.0.0)
- `--port` - Puerto (default: 8000)

**Ejemplos:**

```bash
# Iniciar en puerto default
python cli.py web

# Puerto personalizado
python cli.py web --port 9000

# Solo localhost
python cli.py web --host 127.0.0.1 --port 8080
```

---

## API REST

### Endpoints

| Método | Endpoint | Descripción | Body |
|--------|----------|-------------|------|
| GET | `/` | Dashboard HTML | - |
| GET | `/tasks` | Listar todos | - |
| POST | `/tasks` | Crear task | JSON |
| GET | `/tasks/{name}` | Ver task | - |
| POST | `/tasks/{name}/run` | Ejecutar | - |
| DELETE | `/tasks/{name}` | Eliminar | - |

---

### GET /

Retorna el dashboard HTML.

```bash
curl http://localhost:8000/
```

---

### GET /tasks

Lista todos los tasks.

```bash
curl http://localhost:8000/tasks
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "backup",
    "description": null,
    "command": "tar -czf backup.tar.gz ./data",
    "task_type": "shell",
    "status": "success",
    "last_output": "...",
    "last_run": "2024-01-15T02:00:00",
    "active": true
  }
]
```

---

### POST /tasks

Crea un nuevo task.

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "backup",
    "command": "tar -czf backup.tar.gz ./data",
    "description": "Backup diario",
    "task_type": "shell"
  }'
```

**Campos del body:**
| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `name` | string | Sí | Identificador único |
| `command` | string | Sí | Comando a ejecutar |
| `description` | string | No | Descripción |
| `task_type` | string | No | Tipo (default: shell) |

---

### GET /tasks/{name}

Obtiene detalles de un task.

```bash
curl http://localhost:8000/tasks/backup
```

---

### POST /tasks/{name}/run

Ejecuta un task.

```bash
curl -X POST http://localhost:8000/tasks/backup/run
```

**Response:**
```json
{
  "status": "success",
  "output": "Backup completado"
}
```

---

### DELETE /tasks/{name}

Elimina un task.

```bash
curl -X DELETE http://localhost:8000/tasks/backup
```

---

## Dashboard Web

Accede a `http://localhost:8000` o `http://localhost:8000/dashboard`

### Funciones

1. **Crear Task** - Click en "+ Nuevo Task"
2. **Ejecutar** - Click en "▶ Ejecutar"
3. **Ver Logs** - Click en "📄 Logs"
4. **Eliminar** - Click en "🗑"

### Capturas de Pantalla

```
┌─────────────────────────────────────────────────────┐
│ ⚡ Automation Dashboard                    [+ Nuevo]│
├─────────────────────────────────────────────────────┤
│ Tareas                                             │
│ ┌──────────┬──────┬──────────┬───────────────────┐  │
│ │ Nombre   │ Tipo │ Estado   │ Acciones          │  │
│ ├──────────┼──────┼──────────┼───────────────────┤  │
│ │ backup   │shell │ success  │ ▶ 📄 🗑           │  │
│ │ deploy   │shell │ failed   │ ▶ 📄 🗑           │  │
│ └──────────┴──────┴──────────┴───────────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## Ejemplos de Automatización

### 1. Backup de Base de Datos

```bash
# PostgreSQL
python cli.py add backup-db "pg_dump -U postgres mydb > /backups/db-$(date +%Y%m%d).sql"

# MySQL
python cli.py add backup-db "mysqldump -u root -p mydb > /backups/db-$(date +%Y%m%d).sql"
```

### 2. Sincronización de Archivos

```bash
python cli.py add sync-files "rsync -avz /data/ user@server:/backup/"
python cli.py add sync-remote "rsync -avz user@server:/data/ /local/backup/"
```

### 3. Limpieza Automática

```bash
# Limpiar archivos temporales
python cli.py add clean-tmp "find /tmp -type f -mtime +7 -delete"

# Limpiar logs antiguos
python cli.py add clean-logs "find /var/log -name '*.log' -mtime +30 -delete"

# Limpiar Docker
python cli.py add docker-clean "docker image prune -af && docker container prune -f"
```

### 4. Despliegue Automático

```bash
python cli.py add deploy-app "cd /app && git pull && docker-compose up -d --build"
python cli.py add restart-service "systemctl restart nginx"
```

### 5. Monitoreo

```bash
# Health check
python cli.py add health-check "curl -sf http://localhost:8080/health || echo 'DOWN'"

# Verificar SSL
python cli.py add ssl-check "echo | openssl s_client -servername example.com -connect example.com:443 2>/dev/null | openssl x509 -noout -dates"

# Espacio en disco
python cli.py add disk-check "df -h | awk 'NR==2 {print \$5}' | sed 's/%//'"
```

### 6. Mantenimiento del Sistema

```bash
# Actualizar paquetes (Debian/Ubuntu)
python cli.py add update-system "apt update && apt upgrade -y"

# Reiniciar si servicio caído
python cli.py add nginx-watch "pgrep nginx > /dev/null || systemctl restart nginx"
```

### 7. Reportes

```bash
# Log de errores
python cli.py add error-report "grep -i error /var/log/app.log | tail -50"

# Métricas diarias
python cli.py add daily-metrics "df -h && free -h && uptime"
```

---

## Despliegue

### Docker Compose Completo

```yaml
version: '3.8'

services:
  automation:
    build: .
    container_name: automation-app
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./scripts:/app/scripts
      - ./logs:/app/logs
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - DATABASE_URL=sqlite:///./automation.db
      - LOG_LEVEL=INFO
    restart: unless-stopped
```

### Producción con PostgreSQL

```yaml
version: '3.8'

services:
  automation:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/automation
    depends_on:
      - postgres

  postgres:
    image: postgres:15
    volumes:
      - pgdata:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=automation

volumes:
  pgdata:
```

### Nginx como Reverse Proxy

```nginx
server {
    listen 80;
    server_name automation.example.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Systemd Service (Linux)

```ini
[Unit]
Description=Automation App
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/automation-app
ExecStart=/opt/automation-app/venv/bin/python cli.py web --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

### Integración con Cron

```bash
# Ejecutar task cada día a las 2am
0 2 * * * cd /opt/automation-app && python cli.py run --name backup

# Ejecutar task cada hora
0 * * * * cd /opt/automation-app && python cli.py run --name health-check

# Docker
0 2 * * * docker exec automation-app python cli.py run --name backup
```

---

## Solución de Problemas

### Error de permisos en Docker

```bash
# Agregar usuario al grupo docker
sudo usermod -aG docker $USER
```

### Base de datos bloqueada

```env
DATABASE_URL=sqlite:///./automation.db?check_same_thread=false
```

### Timeout en comandos largos

```env
DEFAULT_TIMEOUT=600
```

### Ver logs de la aplicación

```bash
# Docker
docker logs automation-app

# Python
python cli.py web 2>&1 | tee app.log
```

---

## Seguridad

### Recomendaciones

1. **No exponer puertos** en producción sin firewall
2. **Usar autenticación** si la API es accesible públicamente
3. **Validar comandos** antes de ejecutarlos
4. **Limitar timeout** para evitar comandos colgados
5. **Backups de BD** regulares

### Autenticación Basic Auth (futuro)

```python
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBasicCredentials

def verify_auth(credentials: HTTPBasicCredentials = Depends(...)):
    if credentials.username != "admin" or credentials.password != "secret":
        raise HTTPException(status_code=401)
```

---

## Licencia

MIT License
