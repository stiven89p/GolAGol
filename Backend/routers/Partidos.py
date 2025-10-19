from fastapi import APIRouter, HTTPException
from Backend.modelos.Equipos import Equipo
from Backend.modelos.Partidos import Partido, PartidoCrear
from Backend.modelos.Estadisticas_Equipos import Estadisticas_E
from Backend.modelos.Temporada import Temporada
from Backend.db import SessionDep

router = APIRouter(prefix="/partidos", tags=["partidos"])

@router.post("/", response_model=Partido)
async def create_partido(new_partido: PartidoCrear, session: SessionDep):
    partido = Partido.model_validate(new_partido)
    estadistica_local = session.get(Estadisticas_E, partido.equipo_local_id)
    estadistica_visitante = session.get(Estadisticas_E, partido.equipo_visitante_id)
    temporado = session.get(Temporada, partido.temporada_id)

    if not temporado:
        raise HTTPException(status_code=404, detail="La temporada no existe")

    equipo_local = session.get(Equipo, partido.equipo_local_id)
    if not equipo_local:
        raise HTTPException(status_code=404, detail="El equipo local no existe")

    equipo_visitante = session.get(Equipo, partido.equipo_visitante_id)
    if not equipo_visitante:
        raise HTTPException(status_code=404, detail="El equipo visitante no existe")

    if partido.equipo_local_id == partido.equipo_visitante_id:
        raise HTTPException(status_code=400, detail="Un equipo no puede jugar contra sí mismo")

    session.add(partido)
    session.commit()
    session.refresh(partido)

    estadistica_local.partidos_jugados = (estadistica_local.partidos_jugados or 0) + 1
    estadistica_visitante.partidos_jugados = (estadistica_visitante.partidos_jugados or 0) + 1
    session.add(estadistica_local)
    session.add(estadistica_visitante)
    session.commit()
    session.refresh(estadistica_local)
    session.refresh(estadistica_visitante)

    return partido

@router.get("/", response_model=list[Partido])
async def read_partido(session: SessionDep):
    return session.query(Partido).all()


@router.get("/{partido_id}", response_model=Partido)
async def get_partido(partido_id: int, session: SessionDep):
    partido = session.get(Partido, partido_id)
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")
    return partido


@router.get("/equipo/{equipo_id}", response_model=list[Partido])
async def get_partidos_por_equipo(equipo_id: int, session: SessionDep):
    partidos = session.query(Partido).filter((Partido.equipo_local_id == equipo_id) | (Partido.equipo_visitante_id == equipo_id)).all()
    if not partidos:
        raise HTTPException(status_code=404, detail="No se encontraron partidos para este equipo")
    return partidos

@router.patch("/{partido_id}", response_model=Partido)
async def cambiar_estado_partido(partido_id: int, estado: str, session: SessionDep):
    partido = session.get(Partido, partido_id)

    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")

    if estado not in ["programado", "en curso", "finalizado", "suspendido", "cancelado"]:
        raise HTTPException(status_code=400, detail="Estado inválido")

    if estado == "finalizado":
        estadistica = session.query(Estadisticas_E).filter_by(equipo_id=partido.equipo_local_id,temporada=partido.temporada_id).first()
        estadistica_rival = session.query(Estadisticas_E).filter_by(equipo_id=partido.equipo_visitante_id,temporada=partido.temporada_id).first()

        if partido.goles_local > partido.goles_visitante:
            estadistica.victorias += 1
            estadistica_rival.derrotas += 1
            estadistica.puntos += 3

        elif partido.goles_local < partido.goles_visitante:
            estadistica.derrotas += 1
            estadistica_rival.victorias += 1
            estadistica_rival.puntos += 3

        else:
            estadistica.empates += 1
            estadistica_rival.empates += 1
            estadistica.puntos += 1
            estadistica_rival.puntos += 1

        session.add_all([estadistica, estadistica_rival])


    partido.estado = estado
    session.add(partido)
    session.commit()
    session.refresh(partido)
    return partido
