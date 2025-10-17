from fastapi import APIRouter, HTTPException
from Backend.utils.enumeraciones import TipoEvento
from Backend.utils.Fun_Eventos import *
from Backend.modelos.Equipos import Equipo
from Backend.modelos.Estadisticas_Jugadores import Estadisticas_J
from Backend.modelos.Estadisticas_Equipos import Estadisticas_E
from Backend.modelos.Partidos import Partido
from Backend.modelos.Jugadores import Jugador
from Backend.modelos.Eventos import Evento, EventoCrear
from Backend.db import SessionDep

router = APIRouter(prefix="/eventos", tags=["eventos"])

@router.post("/", response_model=Evento)
async def create_evento(new_evento: EventoCrear, session: SessionDep):
    global estadistica_jugador_asociado
    evento = Evento.model_validate(new_evento)
    partido = session.get(Partido, evento.partido_id)
    jugador = session.get(Jugador, evento.jugador_id)
    jugador_asociado = session.get(Jugador, evento.jugador_asociado_id) if evento.jugador_asociado_id else None
    estadistica_jugador = session.get(Estadisticas_J, evento.jugador_id)


    if not partido:
        raise HTTPException(status_code=404, detail="El partido no existe")

    equipo = session.get(Equipo, evento.equipo_id)
    if not equipo:
        raise HTTPException(status_code=404, detail="El equipo no existe")

    if evento.equipo_id not in [partido.equipo_local_id, partido.equipo_visitante_id]:
        raise HTTPException(status_code=400, detail="El equipo no está participando en el partido")

    if evento.jugador_id and not jugador:
        raise HTTPException(status_code=404, detail="El jugador no existe")

    if evento.jugador_id and jugador.equipo_id not in [partido.equipo_local_id, partido.equipo_visitante_id]:
        raise HTTPException(status_code=400, detail="El jugador no pertenece al equipo que está participando en el partido")

    if evento.jugador_asociado_id:
        if evento.jugador_asociado_id and not jugador:
            raise HTTPException(status_code=404, detail="El jugador no existe")
        if evento.jugador_asociado_id and jugador_asociado.equipo_id not in [partido.equipo_local_id, partido.equipo_visitante_id]:
            raise HTTPException(status_code=400, detail="El jugador asociado no pertenece al equipo que está participando en el partido")
        estadistica_jugador_asociado = session.get(Estadisticas_J, evento.jugador_asociado_id)

    if jugador.equipo_id != evento.equipo_id:
        raise HTTPException(status_code=400, detail="El jugador no pertenece al equipo del evento")



    if evento.tipo == TipoEvento.GOL:
        if evento.jugador_asociado_id:
            procesar_gol(session, evento, partido, Estadisticas_E, estadistica_jugador, estadistica_jugador_asociado)
        procesar_gol(session, evento, partido, Estadisticas_E, estadistica_jugador)
    elif evento.tipo == TipoEvento.TARJETA_AMARILLA or evento.tipo == TipoEvento.TARJETA_ROJA:
        procesar_tarjeta(session, evento, partido, Estadisticas_E, TipoEvento , estadistica_jugador)

    session.add(evento)
    session.commit()
    session.refresh(evento)
    return evento


@router.get("/", response_model=list[Evento])
async def read_eventos(session: SessionDep):
    eventos = session.query(Evento).all()
    if not eventos:
        raise HTTPException(status_code=404, detail="No se encontraron eventos")
    return eventos


@router.get("/goles/", response_model=list[Evento])
async def read_goles(session: SessionDep):
    eventos = session.query(Evento).filter(Evento.tipo == TipoEvento.GOL).all()
    if not eventos:
        raise HTTPException(status_code=404, detail="No se encontraron eventos")
    return eventos
