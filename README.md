# ⚽ Gol a Gol API – Endpoints

**Versión:** 0.1.0  
**Especificación:** OAS 3.1  
**OpenAPI:** `/openapi.json`

---

## 🏠 Default
| Método | Endpoint | Descripción |
|---------|-----------|-------------|
| `GET` | `/` | Read Root |
| `GET` | `/health` | Health Check |

---

## 🏟️ Equipos
| Método | Endpoint | Descripción |
|---------|-----------|-------------|
| `GET` | `/equipos/` | Obtener todos los equipos |
| `POST` | `/equipos/` | Crear nuevo equipo |
| `GET` | `/equipos/{equipo_id}` | Obtener equipo por ID |
| `PATCH` | `/equipos/{equipo_id}` | Actualizar equipo |
| `DELETE` | `/equipos/{equipo_id}` | Eliminar equipo |

---

## ⚽ Partidos
| Método | Endpoint | Descripción |
|---------|-----------|-------------|
| `GET` | `/partidos/` | Obtener todos los partidos |
| `POST` | `/partidos/` | Crear nuevo partido |
| `GET` | `/partidos/{partido_id}` | Obtener partido por ID |
| `PATCH` | `/partidos/{partido_id}` | Cambiar estado del partido |
| `GET` | `/partidos/equipo/{equipo_id}` | Obtener partidos de un equipo |
| `GET` | `/partidos/{estado}/` | Obtener partidos por estado |

---

## 🧾 Eventos
| Método | Endpoint | Descripción |
|---------|-----------|-------------|
| `GET` | `/eventos/` | Obtener todos los eventos |
| `POST` | `/eventos/` | Crear nuevo evento |
| `GET` | `/eventos/{evento}/` | Obtener eventos por tipo (`TipoEvento`) |

---

## 👟 Jugadores
| Método | Endpoint | Descripción |
|---------|-----------|-------------|
| `GET` | `/jugadores/` | Obtener todos los jugadores |
| `POST` | `/jugadores/` | Crear nuevo jugador |
| `GET` | `/jugadores/{jugador_id}` | Obtener jugador por ID |
| `PATCH` | `/jugadores/{jugador_id}` | Actualizar jugador |
| `GET` | `/jugadores/{Posicion}/` | Obtener jugadores por posición |

---

## 🏆 Temporadas
| Método | Endpoint | Descripción |
|---------|-----------|-------------|
| `GET` | `/temporadas/` | Obtener todas las temporadas |
| `POST` | `/temporadas/` | Crear nueva temporada |

---

## 📊 Estadísticas de Equipos
| Método | Endpoint | Descripción |
|---------|-----------|-------------|
| `GET` | `/estadisticas_equipos/` | Obtener todas las estadísticas de equipos |
| `GET` | `/estadisticas_equipos/eqipo/{equipo_id}` | Obtener estadísticas de un equipo |
| `GET` | `/estadisticas_equipos/eqipo/{equipo_id}/{temporada}` | Obtener estadísticas de un equipo por temporada |

---

## 🧮 Estadísticas de Jugadores
| Método | Endpoint | Descripción |
|---------|-----------|-------------|
| `GET` | `/estadisticas_jugadores/` | Obtener todas las estadísticas de jugadores |
| `GET` | `/estadisticas_jugadores/{equipo_id}` | Obtener estadísticas de jugadores de un equipo |
| `GET` | `/estadisticas_jugadores/{equipo_id}/{temporada}` | Obtener estadísticas de jugadores de un equipo por temporada |
