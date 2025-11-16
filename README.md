<div align="center">

# ⚽ Gol a Gol

Plataforma web para gestionar y visualizar equipos, jugadores, partidos y estadísticas del fútbol colombiano. API en FastAPI con vistas Jinja2, PostgreSQL y SQLModel.

[![FastAPI](https://img.shields.io/badge/FastAPI-%20-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-%20-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-%20-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![SQLModel](https://img.shields.io/badge/SQLModel-%20-1E7B85)](https://sqlmodel.tiangolo.com/)
[![Uvicorn](https://img.shields.io/badge/Uvicorn-%20-000000)](https://www.uvicorn.org/)

<img src="static/img/default_logo.png" alt="Gol a Gol" width="90" />

</div>

---

**Docs Rápidas**
- Versión API: 0.1.0
- OpenAPI: `/openapi.json` · Swagger: `/docs` · ReDoc: `/redoc`
- App: `main:app` (FastAPI) · Estáticos: `/static` · Home: `/`

---

**¿Qué es?**
- Gestión de equipos, jugadores, temporadas, partidos y eventos.
- Vistas HTML para detalle de partidos y equipos.
- Endpoints para tablas de posiciones, goleadores y estadísticas.

**Stack**
- FastAPI, SQLModel/SQLAlchemy, PostgreSQL, Jinja2, Uvicorn, httpx/pytest.

---

## 🚀 Arranque Rápido (Windows / PowerShell)

1) Crear entorno e instalar deps

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2) Configurar variables de entorno (.env)

```dotenv
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=golagol
```

3) Levantar PostgreSQL (opcional con Docker)

```powershell
docker run -d --name pg-golagol -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=golagol -p 5432:5432 postgres:15-alpine
```

4) Ejecutar el servidor

```powershell
uvicorn main:app --reload --port 8000
```

Abrir: `http://127.0.0.1:8000/` · API: `/docs`

---

## 🗂️ Estructura

```
backend/
	db.py                 # Conexión SQLModel + PostgreSQL
	routers/              # Routers FastAPI (equipos, partidos, etc.)
	modelos/              # Modelos SQLModel
	utils/                # Utilidades (bucket, enums, helpers)
scripts/                # Seeds de datos (equipos, jugadores)
static/                 # CSS/JS/imagenes
templates/              # Vistas Jinja2 (home, equipo, partido)
tests/                  # Pruebas (pytest)
main.py                 # App FastAPI + templates + static
```

---

## 🧪 Datos de Ejemplo (Seeds)

- Ejecutar seeds (ajusta rutas locales de imágenes en los scripts):

```powershell
python .\scripts\seed_equipos.py
python .\scripts\seed_jugadores.py
```

Nota: Los scripts copian imágenes a `static/img`. Edita `logo_path` y `base_path` si usas otras rutas.

---

## 📚 Endpoints Principales

### 🏠 Default
| Método | Endpoint    | Descripción      |
|--------|-------------|------------------|
| GET    | `/`         | Página de inicio |

### 🏟️ Equipos
| Método | Endpoint                | Descripción                |
|--------|-------------------------|----------------------------|
| GET    | `/equipos/`             | Obtener todos los equipos  |
| POST   | `/equipos/`             | Crear nuevo equipo         |
| GET    | `/equipos/{equipo_id}`  | Obtener equipo por ID      |
| PATCH  | `/equipos/{equipo_id}`  | Actualizar equipo          |
| DELETE | `/equipos/{equipo_id}`  | Eliminar equipo            |

### ⚽ Partidos
| Método | Endpoint                          | Descripción                         |
|--------|-----------------------------------|-------------------------------------|
| GET    | `/partidos/`                      | Listar partidos                     |
| POST   | `/partidos/`                      | Crear partido                       |
| GET    | `/partidos/{partido_id}`          | Obtener partido por ID              |
| PATCH  | `/partidos/{partido_id}`          | Cambiar estado del partido          |
| GET    | `/partidos/equipo/{equipo_id}`    | Partidos de un equipo               |
| GET    | `/partidos/{estado}/`             | Partidos por estado                 |

### 🧾 Eventos
| Método | Endpoint               | Descripción                                  |
|--------|------------------------|----------------------------------------------|
| GET    | `/eventos/`            | Obtener todos los eventos                    |
| POST   | `/eventos/`            | Crear nuevo evento                           |
| GET    | `/eventos/{evento}/`   | Eventos por tipo (`TipoEvento`)              |

### 👟 Jugadores
| Método | Endpoint                          | Descripción                             |
|--------|-----------------------------------|-----------------------------------------|
| GET    | `/jugadores/`                     | Obtener todos los jugadores             |
| POST   | `/jugadores/`                     | Crear nuevo jugador                     |
| GET    | `/jugadores/{jugador_id}`         | Obtener jugador por ID                  |
| PATCH  | `/jugadores/{jugador_id}`         | Actualizar jugador                      |
| GET    | `/jugadores/{Posicion}/`          | Obtener jugadores por posición          |

### 🏆 Temporadas
| Método | Endpoint         | Descripción                    |
|--------|------------------|--------------------------------|
| GET    | `/temporadas/`   | Obtener todas las temporadas   |
| POST   | `/temporadas/`   | Crear nueva temporada          |

### 📊 Estadísticas de Equipos
| Método | Endpoint                                            | Descripción                                      |
|--------|-----------------------------------------------------|--------------------------------------------------|
| GET    | `/estadisticas_equipos/`                            | Todas las estadísticas de equipos                |
| GET    | `/estadisticas_equipos/temporada/{temporada_id}`    | Estadísticas por temporada (DTO con logos)       |
| GET    | `/estadisticas_equipos/equipo/{equipo_id}`          | Estadísticas de un equipo                        |
| GET    | `/estadisticas_equipos/equipo/{equipo_id}/{temporada}` | Estadísticas de un equipo por temporada       |

### 🧮 Estadísticas de Jugadores
| Método | Endpoint                                                       | Descripción                                              |
|--------|----------------------------------------------------------------|----------------------------------------------------------|
| GET    | `/estadisticas_jugadores/`                                     | Todas las estadísticas de jugadores                      |
| GET    | `/estadisticas_jugadores/{equipo_id}`                          | Estadísticas de jugadores de un equipo                   |
| GET    | `/estadisticas_jugadores/{equipo_id}/{temporada}`              | Estadísticas de un equipo por temporada                  |
| GET    | `/estadisticas_jugadores/temporada/{temporada_id}/goleadores`  | Top goleadores por temporada                             |
| GET    | `/estadisticas_jugadores/temporada/{temporada_id}/{equipo_id}/goleadores` | Top goleadores por temporada y equipo         |

---

## ⚙️ Configuración y Notas

- Base de datos: se crean las tablas automáticamente al iniciar la app (`SQLModel.metadata.create_all`).
- CORS: configurado vía FastAPI según necesidades del frontend.
- Estáticos/Media: imágenes referenciadas desde `static/img`.
- Producción: considera `uvicorn[standard]`, reverse proxy y variables seguras.

---

## 🧪 Tests

```powershell
pytest -q
```

Nota: Algunos tests referencian rutas locales de imágenes. Ajusta los paths o deshabilita esos casos para CI.

---

## 💡 Roadmap Rápido

- [ ] Docker Compose (API + PostgreSQL)
- [ ] Autenticación y roles
- [ ] Métricas avanzadas (xG, asistencias esperadas)
- [ ] Jobs de actualización automática de resultados

---

Hecho con ❤️ para el fútbol.
