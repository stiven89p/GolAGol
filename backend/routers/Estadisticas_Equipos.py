from typing import List
from fastapi import APIRouter, HTTPException
from backend.modelos.Estadisticas_Equipos import Estadisticas_E, Estadisticas_EDTO
from backend.modelos.Equipos import Equipo
from backend.db import SessionDep

router = APIRouter(prefix="/estadisticas_equipos", tags=["estadisticas_equipos"])

@router.get("/", response_model=List[Estadisticas_E])
async def obtener_estadistica_equipos(session: SessionDep):
    return session.query(Estadisticas_E).all()


@router.get("/temporada/{temporada_id}", response_model=List[Estadisticas_EDTO])
async def obtener_estadistica_equipos(temporada_id: int, session: SessionDep):
    rows = (
        session.query(Estadisticas_E, Equipo)
        .join(Equipo, Estadisticas_E.equipo_id == Equipo.equipo_id)
        .filter(Estadisticas_E.temporada == temporada_id)
        .all()
    )

    if not rows:
        raise HTTPException(status_code=404, detail="No se encontraron estadísticas para la temporada")

    dto_list: List[Estadisticas_EDTO] = []
    for estad, equipo in rows:
        dto = Estadisticas_EDTO(
            equipo_id=estad.equipo_id,
            equipo_logo=getattr(equipo, "logo", None),
            temporada=estad.temporada,
            partidos_jugados=estad.partidos_jugados,
            victorias=estad.victorias,
            empates=estad.empates,
            derrotas=estad.derrotas,
            goles_favor=estad.goles_favor,
            goles_contra=estad.goles_contra,
            puntos=estad.puntos,
            tarjetas_amarillas=estad.tarjetas_amarillas,
            tarjetas_rojas=estad.tarjetas_rojas,
        )
        dto_list.append(dto)

    return dto_list


@router.get("/equipo/{equipo_id}", response_model=List[Estadisticas_E])
async def obtener_estadistica_equipo(equipo_id: int, session: SessionDep):
    return session.query(Estadisticas_E).filter(Estadisticas_E.equipo_id == equipo_id).all()

@router.get("/equipo/{equipo_id}/{temporada}", response_model=List[Estadisticas_E])
async def obtener_estadistica_equipo_temporada(equipo_id: int,temporada: int , session: SessionDep):
    return session.query(Estadisticas_E).filter(
        Estadisticas_E.equipo_id == equipo_id,
        Estadisticas_E.temporada == temporada
    ).all()

