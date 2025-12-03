from typing import List
from fastapi import APIRouter, HTTPException
from sqlmodel import select
from backend.modelos.Estadisticas_Jugadores import Estadisticas_J
from backend.modelos.Estadisticas_Equipos import Estadisticas_E
from backend.modelos.Jugadores import Jugador
from backend.modelos.Equipos import Equipo
from backend.db import SessionDep
from pydantic import BaseModel

class GoleadorDTO(BaseModel):
    posicion: int
    jugador_nombre: str
    jugador_apellido: str
    jugador_foto: str | None
    equipo_nombre: str
    goles: int

router = APIRouter(prefix="/estadisticas_jugadores", tags=["estadisticas_jugadores"])

@router.get("/", response_model=List[Estadisticas_J])
async def obtener_estadistica_jugadores(session: SessionDep):
    return session.query(Estadisticas_J).all()

@router.get("/{equipo_id}", response_model=List[Estadisticas_J])
async def obtener_estadisticas_jugador(equipo_id: int, session: SessionDep):
    estadistica = session.query(Estadisticas_J).filter(Estadisticas_J.equipo_id == equipo_id).all()
    if not estadistica:
        raise HTTPException(status_code=404, detail="La estadística del jugador no existe")
    return estadistica

@router.get("/{equipo_id}/{temporada}", response_model=List[Estadisticas_J])
async def obtener_estadistica_jugador_temporada(equipo_id: int,temporada: int , session: SessionDep):
    estadistica = session.query(Estadisticas_J).filter(Estadisticas_J.equipo_id == equipo_id,Estadisticas_J.temporada == temporada).all()
    if not estadistica:
        raise HTTPException(status_code=404, detail="La estadística del jugador no existe")
    return estadistica

@router.get("/equipo/{equipo_id}/temporada/{temporada}")
async def obtener_estadisticas_equipo_y_jugadores(equipo_id: int, temporada: int, session: SessionDep):
    """Subdivisión: estadísticas del equipo y estadísticas de jugadores para la temporada.

    Devuelve `equipo` con Estadisticas_E y `jugadores` como una lista con campos enriquecidos
    necesarios para el frontend: nombre, apellido, foto y métricas de la temporada.
    """
    stats_equipo = session.query(Estadisticas_E).filter(
        Estadisticas_E.equipo_id == equipo_id,
        Estadisticas_E.temporada == temporada
    ).first()

    # Unir con Jugador para obtener nombre/apellido/foto
    registros = session.exec(
        select(Estadisticas_J, Jugador)
        .join(Jugador, Estadisticas_J.jugador_id == Jugador.jugador_id)
        .where(Estadisticas_J.equipo_id == equipo_id)
        .where(Estadisticas_J.temporada == temporada)
    ).all()

    if not stats_equipo and not registros:
        raise HTTPException(status_code=404, detail="No hay estadísticas para el equipo en la temporada indicada")

    jugadores_enriquecidos = [
        {
            "jugador_id": est.jugador_id,
            "jugador_nombre": jug.nombre,
            "jugador_apellido": jug.apellido,
            "jugador_foto": jug.foto,
            "posicion": jug.posicion,
            "partidos_jugados": est.partidos_jugados,
            "goles": est.goles,
            "asistencias": est.asistencias,
            "tarjetas_amarillas": est.tarjetas_amarillas,
            "tarjetas_rojas": est.tarjetas_rojas,
            "minutos_jugados": est.minutos_jugados,
            "balones_perdidos": est.balones_perdidos,
            "penales_cobrados": est.penales_cobrados,
            "penales_fallados": est.penales_fallados,
            "tiros_totales": est.tiros_totales,
            "tiros_a_puerta": est.tiros_a_puerta,
            "entradas": est.entradas,
            "intercepciones": est.intercepciones,
            "goles_contra": est.goles_contra,
            "goles_concedidos": est.goles_concedidos,
            "paradas": est.paradas,
            "penales_tapados": est.penales_tapados,
        }
        for est, jug in registros
    ]

    return {
        "equipo": stats_equipo,
        "jugadores": jugadores_enriquecidos,
    }

@router.get("/temporada/{temporada_id}/goleadores", response_model=List[GoleadorDTO])
async def obtener_goleadores_temporada(temporada_id: int, session: SessionDep, limit: int = 10):
    """Obtiene los goleadores de una temporada ordenados por cantidad de goles"""
    
    # Query con joins para obtener info del jugador y equipo
    estadisticas = session.exec(
        select(Estadisticas_J, Jugador, Equipo)
        .join(Jugador, Estadisticas_J.jugador_id == Jugador.jugador_id)
        .join(Equipo, Estadisticas_J.equipo_id == Equipo.equipo_id)
        .where(Estadisticas_J.temporada == temporada_id)
        .where(Estadisticas_J.goles > 0)
        .order_by(Estadisticas_J.goles.desc())
    ).all()
    
    if not estadisticas:
        return []
    
    # Construir DTOs con posición
    goleadores = []
    for idx, (est, jugador, equipo) in enumerate(estadisticas[:limit], start=1):
        goleadores.append(GoleadorDTO(
            posicion=idx,
            jugador_nombre=jugador.nombre,
            jugador_apellido=jugador.apellido,
            jugador_foto=jugador.foto,
            equipo_nombre=equipo.nombre,
            goles=est.goles
        ))
    
    return goleadores



@router.get("/temporada/{temporada_id}/{equipo_id}/goleadores", response_model=List[GoleadorDTO])
async def obtener_goleadores_temporada_equipo(temporada_id: int, equipo_id: int, session: SessionDep, limit: int = 10):
    """Obtiene los goleadores de una temporada y equipo ordenados por cantidad de goles"""
    
    # Query con joins para obtener info del jugador y equipo
    estadisticas = session.exec(
        select(Estadisticas_J, Jugador, Equipo)
        .join(Jugador, Estadisticas_J.jugador_id == Jugador.jugador_id)
        .join(Equipo, Estadisticas_J.equipo_id == Equipo.equipo_id)
        .where(Estadisticas_J.temporada == temporada_id)
        .where(Estadisticas_J.equipo_id == equipo_id)
        .where(Estadisticas_J.goles > 0)
        .order_by(Estadisticas_J.goles.desc())
    ).all()
    
    if not estadisticas:
        return []
    
    # Construir DTOs con posición
    goleadores = []
    for idx, (est, jugador, equipo) in enumerate(estadisticas[:limit], start=1):
        goleadores.append(GoleadorDTO(
            posicion=idx,
            jugador_nombre=jugador.nombre,
            jugador_apellido=jugador.apellido,
            jugador_foto=jugador.foto,
            equipo_nombre=equipo.nombre,
            goles=est.goles
        ))
    
    return goleadores


@router.get("/temporada/{temporada_id}/top-stats")
async def obtener_top_estadisticas(temporada_id: int, session: SessionDep, limit: int = 10):
    """Obtiene los tops en diferentes categorías de estadísticas"""
    
    # Top Goleadores
    goleadores = session.exec(
        select(Estadisticas_J, Jugador, Equipo)
        .join(Jugador, Estadisticas_J.jugador_id == Jugador.jugador_id)
        .join(Equipo, Estadisticas_J.equipo_id == Equipo.equipo_id)
        .where(Estadisticas_J.temporada == temporada_id)
        .where(Estadisticas_J.goles > 0)
        .order_by(Estadisticas_J.goles.desc())
        .limit(limit)
    ).all()
    
    # Top Asistencias
    asistidores = session.exec(
        select(Estadisticas_J, Jugador, Equipo)
        .join(Jugador, Estadisticas_J.jugador_id == Jugador.jugador_id)
        .join(Equipo, Estadisticas_J.equipo_id == Equipo.equipo_id)
        .where(Estadisticas_J.temporada == temporada_id)
        .where(Estadisticas_J.asistencias > 0)
        .order_by(Estadisticas_J.asistencias.desc())
        .limit(limit)
    ).all()
    
    # Top Goles + Asistencias
    goles_asistencias = session.exec(
        select(Estadisticas_J, Jugador, Equipo)
        .join(Jugador, Estadisticas_J.jugador_id == Jugador.jugador_id)
        .join(Equipo, Estadisticas_J.equipo_id == Equipo.equipo_id)
        .where(Estadisticas_J.temporada == temporada_id)
        .order_by((Estadisticas_J.goles + Estadisticas_J.asistencias).desc())
        .limit(limit)
    ).all()
    
    # Top Tarjetas Amarillas
    amarillas = session.exec(
        select(Estadisticas_J, Jugador, Equipo)
        .join(Jugador, Estadisticas_J.jugador_id == Jugador.jugador_id)
        .join(Equipo, Estadisticas_J.equipo_id == Equipo.equipo_id)
        .where(Estadisticas_J.temporada == temporada_id)
        .where(Estadisticas_J.tarjetas_amarillas > 0)
        .order_by(Estadisticas_J.tarjetas_amarillas.desc())
        .limit(limit)
    ).all()
    
    # Top Tarjetas Rojas
    rojas = session.exec(
        select(Estadisticas_J, Jugador, Equipo)
        .join(Jugador, Estadisticas_J.jugador_id == Jugador.jugador_id)
        .join(Equipo, Estadisticas_J.equipo_id == Equipo.equipo_id)
        .where(Estadisticas_J.temporada == temporada_id)
        .where(Estadisticas_J.tarjetas_rojas > 0)
        .order_by(Estadisticas_J.tarjetas_rojas.desc())
        .limit(limit)
    ).all()
    
    def format_stat(data, stat_field):
        return [
            {
                "jugador_nombre": f"{jugador.nombre} {jugador.apellido}",
                "jugador_foto": jugador.foto,
                "equipo_nombre": equipo.nombre,
                "posicion": jugador.posicion,
                "valor": getattr(est, stat_field) if stat_field != "goles_asistencias" else (est.goles + est.asistencias)
            }
            for est, jugador, equipo in data
        ]
    
    return {
        "goleadores": format_stat(goleadores, "goles"),
        "asistencias": format_stat(asistidores, "asistencias"),
        "goles_asistencias": format_stat(goles_asistencias, "goles_asistencias"),
        "tarjetas_amarillas": format_stat(amarillas, "tarjetas_amarillas"),
        "tarjetas_rojas": format_stat(rojas, "tarjetas_rojas")
    }