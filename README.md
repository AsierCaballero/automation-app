# Automation App ⚡

App de automatización DevOps con CLI + Web Dashboard.

## Despliegue Rápido

### Docker (Recomendado)
```bash
docker-compose up -d
```

### Local
```bash
pip install -r requirements.txt
python cli.py web
```

## CLI Commands

```bash
# Dashboard web
python cli.py web --host 0.0.0.0 --port 8000

# Gestionar tasks
python cli.py add backup "tar -czf backup.tar.gz ./data"
python cli.py list
python cli.py run --name backup
python cli.py logs --name backup
python cli.py delete --name backup
```

## API Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/tasks` | Listar tasks |
| POST | `/tasks` | Crear task |
| GET | `/tasks/{name}` | Ver task |
| POST | `/tasks/{name}/run` | Ejecutar |
| DELETE | `/tasks/{name}` | Eliminar |

## Variables de Entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./automation.db` | Conexión BD |
| `APP_PORT` | `8000` | Puerto |
| `LOG_LEVEL` | `INFO` | Nivel de logs |
| `DEFAULT_TIMEOUT` | `300` | Timeout (seg) |

## Volumes (Docker)

- `./data` - Datos
- `./scripts` - Scripts personalizados
- `./logs` - Logs
