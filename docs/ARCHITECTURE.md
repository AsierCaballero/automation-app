# 🏗 Arquitectura

## Visión General

```
┌─────────────────────────────────────────────────────────┐
│                    Automation App                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │     CLI      │  │  Web UI      │  │   API REST   │ │
│  │   (Typer)    │  │  (HTML/JS)   │  │  (FastAPI)   │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
│         │                  │                  │         │
│         └──────────────────┼──────────────────┘         │
│                            │                            │
│                    ┌───────▼───────┐                    │
│                    │    Services   │                    │
│                    │   (Executor)  │                    │
│                    └───────┬───────┘                    │
│                            │                            │
│                    ┌───────▼───────┐                    │
│                    │   Database    │                    │
│                    │   (SQLAlchemy)│                    │
│                    └───────────────┘                    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Componentes

### CLI (`cli.py`)

- **Framework**: Typer + Rich
- **Responsabilidad**: Interfaz de línea de comandos
- **Funciones**: CRUD de tasks, ejecución, logs

### API (`app/api/main.py`)

- **Framework**: FastAPI
- **Responsabilidad**: API REST + serving del dashboard
- **Endpoints**: CRUD tasks, ejecución

### Services (`app/services/`)

- **Executor**: Ejecuta comandos shell
- **Futuro**: Scheduling, notifications, workers

### Database (`app/core/database.py`)

- **ORM**: SQLAlchemy
- **Modelos**: Task, Log, Schedule (futuro)
- **Soporte**: SQLite, PostgreSQL, MySQL

### Dashboard (`dashboard.html`)

- **Frontend**: HTML/CSS/JS vanilla
- **Comunicación**: Fetch API con REST
- **Responsabilidad**: UI visual

---

## Modelo de Datos

```
┌─────────────────┐
│      Task       │
├─────────────────┤
│ id (PK)         │
│ name (UNIQUE)   │
│ description     │
│ command         │
│ task_type       │
│ status          │
│ last_output     │
│ last_run        │
│ created_at      │
│ active          │
└─────────────────┘
```

### Campos de Task

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Integer | Primary key |
| name | String(100) | Identificador único |
| description | Text | Descripción opcional |
| command | Text | Comando shell |
| task_type | String(50) | Tipo de ejecución |
| status | String(20) | Estado actual |
| last_output | Text | Último output |
| last_run | DateTime | Última ejecución |
| created_at | DateTime | Fecha creación |
| active | Boolean | Activo/inactivo |

---

## Flujo de Ejecución

```
1. User → CLI/API → create_task()
2. Task → Database (SQLAlchemy)
3. User → CLI/API → execute_task()
4. Executor → subprocess.run(command)
5. Result → Database (status, output)
6. Response → User
```

---

## Dependencias

```
fastapi          # API REST
uvicorn          # ASGI server
typer            # CLI framework
rich             # CLI styling
sqlalchemy       # ORM
pydantic         # Validation
apscheduler      # Future: scheduling
```

---

## Futuras Mejoras

1. **Scheduling** - Ejecución programada con APScheduler
2. **Workers** - Ejecución asíncrona con Celery/Redis
3. **Auth** - Autenticación JWT/Basic
4. **Logs** - Sistema de logs centralizado
5. **Webhooks** - Notificaciones externas
6. **Grupos** - Organizar tasks en grupos
7. **History** - Historial de ejecuciones
