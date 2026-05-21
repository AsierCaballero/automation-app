# 📖 API Reference

## Base URL

```
http://localhost:8000
```

## Authentication

Actualmente la API no requiere autenticación. Para producción, se recomienda usar un reverse proxy con autenticación.

---

## Endpoints

---

### GET /

Retorna el dashboard HTML.

**Response:** `text/html`

---

### GET /tasks

Lista todos los tasks.

**Response:** `application/json`

```json
[
  {
    "id": 1,
    "name": "backup",
    "description": "Backup diario",
    "command": "tar -czf backup.tar.gz ./data",
    "task_type": "shell",
    "status": "success",
    "last_output": "Backup completado exitosamente",
    "last_run": "2024-01-15T02:00:00",
    "active": true,
    "created_at": "2024-01-01T00:00:00"
  }
]
```

---

### POST /tasks

Crea un nuevo task.

**Request Body:**

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| name | string | ✅ | Identificador único |
| command | string | ✅ | Comando shell a ejecutar |
| description | string | ❌ | Descripción opcional |
| task_type | string | ❌ | Tipo de task (default: "shell") |

**Request Example:**

```json
{
  "name": "backup",
  "command": "tar -czf backup.tar.gz ./data",
  "description": "Backup diario de archivos",
  "task_type": "shell"
}
```

**Response:** `201 Created`

```json
{
  "id": 1,
  "name": "backup",
  "description": "Backup diario de archivos",
  "command": "tar -czf backup.tar.gz ./data",
  "task_type": "shell",
  "status": "idle",
  "last_output": null,
  "last_run": null,
  "active": true,
  "created_at": "2024-01-15T10:30:00"
}
```

**Error Responses:**

- `400 Bad Request` - Task ya existe
- `422 Unprocessable Entity` - Datos inválidos

---

### GET /tasks/{name}

Obtiene detalles de un task específico.

**Parameters:**

| Nombre | Tipo | Descripción |
|--------|------|-------------|
| name | string | Nombre del task |

**Response:** `200 OK`

```json
{
  "id": 1,
  "name": "backup",
  "description": "Backup diario",
  "command": "tar -czf backup.tar.gz ./data",
  "task_type": "shell",
  "status": "success",
  "last_output": "tar: removing leading '/' from member names\n...",
  "last_run": "2024-01-15T02:00:00",
  "active": true,
  "created_at": "2024-01-01T00:00:00"
}
```

**Error Responses:**

- `404 Not Found` - Task no encontrado

---

### POST /tasks/{name}/run

Ejecuta un task.

**Parameters:**

| Nombre | Tipo | Descripción |
|--------|------|-------------|
| name | string | Nombre del task |

**Response:** `200 OK`

```json
{
  "status": "success",
  "output": "Backup completado"
}
```

**Posibles estados:**
- `success` - Ejecución exitosa
- `failed` - Error en ejecución
- `timeout` - Tiempo excedido
- `error` - Error general

**Error Responses:**

- `404 Not Found` - Task no encontrado

---

### DELETE /tasks/{name}

Elimina un task.

**Parameters:**

| Nombre | Tipo | Descripción |
|--------|------|-------------|
| name | string | Nombre del task |

**Response:** `200 OK`

```json
{
  "message": "Task 'backup' eliminado"
}
```

**Error Responses:**

- `404 Not Found` - Task no encontrado

---

## Status Codes

| Code | Descripción |
|------|-------------|
| 200 | OK |
| 201 | Creado |
| 400 | Bad Request |
| 404 | Not Found |
| 422 | Unprocessable Entity |
| 500 | Internal Server Error |

---

## Rate Limits

No hay límites configurados por defecto. Para producción, usar nginx o similar.

---

## WebSocket (futuro)

En desarrollo para ejecución en tiempo real.
