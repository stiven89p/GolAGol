from fastapi import APIRouter, HTTPException, Form
from sqlalchemy.orm import aliased
from datetime import date, time
from backend.modelos.Equipos import Equipo
from backend.modelos.Partidos import Partido, PartidoCrear, PartidoDTO
from backend.modelos.Estadisticas_Equipos import Estadisticas_E
from backend.modelos.Temporada import Temporada
from backend.utils.enumeraciones import EstadoPartidos
from backend.db import SessionDep

router = APIRouter(prefix="/partidos", tags=["partidos"])

@router.post("/", response_model=Partido)
async def crear_partido(
        session: SessionDep,
        fecha: date = Form(...),
        hora: time = Form(...),
        jornada: int = Form(...),
        temporada_id: int = Form(...),
        estadio: str = Form(...),
        equipo_local_id: int = Form(...),
        equipo_visitante_id: int = Form(...)
        ):
    new_partido = PartidoCrear(
        fecha=fecha,
        hora=hora,
        jornada=jornada,
        estadio=estadio,
        equipo_local_id=equipo_local_id,
        equipo_visitante_id=equipo_visitante_id,
        temporada_id=temporada_id,
    )
    partido = Partido.model_validate(new_partido)
    estadistica_local = session.get(Estadisticas_E, partido.equipo_local_id)
    estadistica_visitante = session.get(Estadisticas_E, partido.equipo_visitante_id)
    temporada= session.get(Temporada, partido.temporada_id)

    if not temporada:
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

# python
@router.get("/", response_model=list[PartidoDTO])
async def obtener_partidos(session: SessionDep):
    equipo_local = aliased(Equipo)
    equipo_visitante = aliased(Equipo)

    rows = (
        session.query(Partido, equipo_local, equipo_visitante)
        .join(equipo_local, Partido.equipo_local_id == equipo_local.equipo_id)
        .join(equipo_visitante, Partido.equipo_visitante_id == equipo_visitante.equipo_id)
        .order_by(Partido.fecha.asc())
        .all()
    )

    if not rows:
        raise HTTPException(status_code=404, detail="No se encontraron partidos programados")

    dto_list: list[PartidoDTO] = []
    for partido, el, ev in rows:
        dto = PartidoDTO(
            partido_id=partido.partido_id,
            equipo_local_nombre=getattr(el, "nombre", "") if el else "",
            equipo_local_logo=getattr(el, "logo", None) if el else None,
            equipo_visitante_nombre=getattr(ev, "nombre", "") if ev else "",
            equipo_visitante_logo=getattr(ev, "logo", None) if ev else None,
            fecha=partido.fecha,
            hora=partido.hora.strftime("%H:%M") if partido.hora else None,
            lugar=partido.estadio,
            estado=partido.estado,
            goles_local=partido.goles_local,
            goles_visitante=partido.goles_visitante,
        )
        dto_list.append(dto)

    return dto_list


@router.get("/equipo/{equipo_id}", response_model=list[PartidoDTO])
async def obtener_partidos_equipo(equipo_id: int, session: SessionDep):
    equipo_local = aliased(Equipo)
    equipo_visitante = aliased(Equipo)

    rows = (
        session.query(Partido, equipo_local, equipo_visitante)
        .join(equipo_local, Partido.equipo_local_id == equipo_local.equipo_id)
        .join(equipo_visitante, Partido.equipo_visitante_id == equipo_visitante.equipo_id)
        .filter(
            ((Partido.equipo_local_id == equipo_id) | (Partido.equipo_visitante_id == equipo_id))
            & (Partido.estado == EstadoPartidos.PROGRAMADO)
        )
        .order_by(Partido.fecha.asc())
        .all()
    )

    if not rows:
        raise HTTPException(status_code=404, detail="No se encontraron partidos para este equipo")

    dto_list: list[PartidoDTO] = []
    for partido, el, ev in rows:
        dto = PartidoDTO(
            partido_id=partido.partido_id,
            equipo_local_nombre=getattr(el, "nombre", "") if el else "",
            equipo_local_logo=getattr(el, "logo", None) if el else None,
            equipo_visitante_nombre=getattr(ev, "nombre", "") if ev else "",
            equipo_visitante_logo=getattr(ev, "logo", None) if ev else None,
            fecha=partido.fecha,
            hora=partido.hora.strftime("%H:%M") if partido.hora else None,
            lugar=partido.estadio,
            estado=partido.estado,
            goles_local=partido.goles_local,
            goles_visitante=partido.goles_visitante,
        )
        dto_list.append(dto)

    return dto_list

@router.get("/{estado}/", response_model=list[Partido])
async def obtener_partidos_equipo(estado: EstadoPartidos, session: SessionDep):
    partidos = session.query(Partido).filter(Partido.estado == estado).all()
    if not partidos:
        raise HTTPException(status_code=404, detail="No se encontraron partidos para este equipo")
    return partidos


@router.patch("/{partido_id}", response_model=Partido)
async def cambiar_estado_partido(partido_id: int, estado:EstadoPartidos, session: SessionDep):
    partido = session.get(Partido, partido_id)

    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")

    if estado == EstadoPartidos.FINALIZADO:
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

@router.delete("/{partido_id}", response_model=Partido)
async def eliminar_partido(partido_id: int, session: SessionDep):
    partido = session.get(Partido, partido_id)
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")

    partido.estado = "CANCELADO"
    session.add(partido)
    session.commit()
    session.refresh(partido)