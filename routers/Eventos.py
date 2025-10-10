from fastapi import APIRouter, HTTPException
from utils.enumeraciones import TipoEvento
from modelos.Equipos import Equipo
from modelos.Estadisticas_Jugadores import Estadisticas_J
from modelos.Estadisticas_Equipos import Estadisticas_E
from modelos.Partidos import Partido
from modelos.Jugadores import Jugador
from modelos.Eventos import Evento, EventoCrear
from db import SessionDep

router = APIRouter(prefix="/eventos", tags=["eventos"])

@router.post("/", response_model=Evento)
async def create_evento(new_evento: EventoCrear, session: SessionDep):
    evento = Evento.model_validate(new_evento)
    partido = session.get(Partido, evento.partido_id)
    jugador = session.get(Jugador, evento.jugador_id)
    jugador_asociado = session.get(Jugador, evento.jugador_asociado_id) if evento.jugador_asociado_id else None
    estadistica = session.get(Estadisticas_E, evento.equipo_id)
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

    if evento.jugador_id != evento.equipo_id:
        raise HTTPException(status_code=400, detail="El jugador no pertenece al equipo del evento")



    if evento.tipo == TipoEvento.GOL:
        if evento.equipo_id == partido.equipo_local_id:
            partido.goles_local = (partido.goles_local or 0) + 1
        else:
            partido.goles_visitante = (partido.goles_visitante or 0) + 1
        session.add(partido)
        session.commit()
        session.refresh(partido)
        if estadistica:
            estadistica.goles_favor = (estadistica.goles_favor or 0) + 1
            session.add(estadistica)
            session.commit()
            session.refresh(estadistica)
        if estadistica_jugador:
            estadistica_jugador.goles = (estadistica_jugador.goles or 0) + 1
            session.add(estadistica_jugador)
            session.commit()
            session.refresh(estadistica_jugador)

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


