from typing import Optional
from fastapi import APIRouter, HTTPException, Form
from backend.utils.enumeraciones import TipoEvento
from backend.utils.Fun_Eventos import procesar_gol, procesar_tarjeta, anular_gol, anular_tarjeta, validar_sustitucion, anular_gol_en_contra
from backend.modelos.Equipos import Equipo
from backend.modelos.Estadisticas_Jugadores import Estadisticas_J
from backend.modelos.Estadisticas_Equipos import Estadisticas_E
from backend.modelos.Partidos import Partido
from backend.modelos.Jugadores import Jugador
from backend.modelos.Eventos import Evento, EventoCrear
from backend.db import SessionDep

router = APIRouter(prefix="/eventos", tags=["eventos"])

@router.post("/", response_model=Evento)
async def crear_evento(session: SessionDep,
                       minuto: int = Form(...),
                       tipo: TipoEvento = Form(...),
                       descripcion: Optional[str] = Form(None),
                       partido_id: int = Form(...),
                       equipo_id: int = Form(...),
                       jugador_id: int = Form(...),
                       jugador_asociado_id: Optional[int] = Form(None)
                       ):
    # Normalizar jugador_asociado_id: valores 0, '', None se interpretan como ausencia
    if jugador_asociado_id in (0, '', None):
        jugador_asociado_id = None

    # Usar directamente el Enum `TipoEvento` para que SQLAlchemy/psycopg serialicen el valor correcto en la BD
    tipo_valor = tipo if isinstance(tipo, TipoEvento) else TipoEvento(str(tipo).lower())

    new_evento = EventoCrear(
        minuto=minuto,
        tipo=tipo_valor,
        descripcion=descripcion,
        partido_id=partido_id,
        equipo_id=equipo_id,
        jugador_id=jugador_id,
        jugador_asociado_id=jugador_asociado_id
    )
    global estadistica_jugador_asociado
    evento = Evento.model_validate(new_evento)
    # Asegurar que `evento.tipo` es una instancia de `TipoEvento` para comparaciones y persistencia correctas
    try:
        if not isinstance(evento.tipo, TipoEvento):
            evento.tipo = TipoEvento(str(evento.tipo).lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Tipo de evento inválido: {evento.tipo}")
    partido = session.get(Partido, evento.partido_id)
    jugador = session.get(Jugador, evento.jugador_id)
    jugador_asociado = session.get(Jugador, evento.jugador_asociado_id) if evento.jugador_asociado_id else None
    # Obtener o crear fila de estadísticas del jugador para la temporada del partido
    estadistica_jugador = None
    estadistica_jugador_asociado = None
    if partido:
        estadistica_jugador = session.query(Estadisticas_J).filter_by(jugador_id=evento.jugador_id, temporada=partido.temporada_id).first()
        if not estadistica_jugador:
            estadistica_jugador = Estadisticas_J(jugador_id=evento.jugador_id, temporada=partido.temporada_id)
        if evento.jugador_asociado_id:
            estadistica_jugador_asociado = session.query(Estadisticas_J).filter_by(jugador_id=evento.jugador_asociado_id, temporada=partido.temporada_id).first()
            if not estadistica_jugador_asociado:
                estadistica_jugador_asociado = Estadisticas_J(jugador_id=evento.jugador_asociado_id, temporada=partido.temporada_id)


    if not partido:
        raise HTTPException(status_code=404, detail="El partido no existe")

    equipo = session.get(Equipo, evento.equipo_id)
    if not equipo:
        raise HTTPException(status_code=404, detail="El equipo no existe")

    if partido.estado != "EN_CURSO":
        if partido.estado == "PROGRAMADO":
            raise HTTPException(status_code=400, detail="No se pueden agregar eventos a un partido programado")

        if partido.estado == "FINALIZADO":
            raise HTTPException(status_code=400, detail="No se pueden agregar eventos a un partido finalizado")

        if partido.estado == "SUSPENDIDO":
            raise HTTPException(status_code=400, detail="No se pueden agregar eventos a un partido suspendido")

        if partido.estado == "CANCELADO":
            raise HTTPException(status_code=400, detail="No se pueden agregar eventos a un partido cancelado")


    
    if evento.equipo_id not in [partido.equipo_local_id, partido.equipo_visitante_id]:
        raise HTTPException(status_code=400, detail="El equipo no está participando en el partido")

    if evento.jugador_id and not jugador:
        raise HTTPException(status_code=404, detail="El jugador no existe")

    if evento.jugador_id and jugador.equipo_id not in [partido.equipo_local_id, partido.equipo_visitante_id]:
        raise HTTPException(status_code=400, detail="El jugador no pertenece al equipo que está participando en el partido")

    if evento.jugador_asociado_id:
        # Validar jugador asociado usando la variable correcta
        if not jugador_asociado:
            raise HTTPException(status_code=404, detail="El jugador asociado no existe")
        if jugador_asociado.equipo_id not in [partido.equipo_local_id, partido.equipo_visitante_id]:
            raise HTTPException(status_code=400, detail="El jugador asociado no pertenece a un equipo del partido")
        estadistica_jugador_asociado = session.get(Estadisticas_J, evento.jugador_asociado_id)

    if jugador.equipo_id != evento.equipo_id:
        raise HTTPException(status_code=400, detail="El jugador no pertenece al equipo del evento")

    # Convertir a Enum para comparaciones seguras
    tipo_enum = evento.tipo

    # Validación específica para sustituciones
    if tipo_enum == TipoEvento.SUSTITUCION:
        if not jugador_asociado:
            raise HTTPException(status_code=404, detail="El jugador que entra no existe")
        if jugador_asociado.equipo_id != evento.equipo_id:
            raise HTTPException(status_code=400, detail="El jugador que entra no pertenece al equipo del evento")
        validar_sustitucion(session, evento, partido, TipoEvento)

    # Mapear tipos adicionales a sus procesadores
    from backend.utils.Fun_Eventos import (
        procesar_gol, procesar_tarjeta, anular_gol, anular_tarjeta,
        procesar_penal_fallado, procesar_tiro, procesar_parada, procesar_entrada, procesar_intercepcion,
        procesar_gol_en_contra
    )

    if tipo_enum in (TipoEvento.GOL, TipoEvento.PENAL):
        # Penal anotado: igual que gol; procesar_gol maneja penales_cobrados
        if evento.jugador_asociado_id:
            procesar_gol(session, evento, partido , Estadisticas_E, estadistica_jugador, estadistica_jugador_asociado)
        else:
            procesar_gol(session, evento, partido, Estadisticas_E, estadistica_jugador)

    elif tipo_enum == TipoEvento.PENAL_FALLADO:
        # Penal fallado: incrementar penales_fallados y, si hay portero asociado, penales_tapados
        procesar_penal_fallado(session, evento, partido, Estadisticas_J, estadistica_jugador, estadistica_jugador_asociado)

    elif tipo_enum == TipoEvento.GOL_EN_CONTRA:
        # procesar gol en contra (autogol)
        procesar_gol_en_contra(session, evento, partido, Estadisticas_E, estadistica_jugador)

    elif tipo_enum == TipoEvento.TIRO:
        procesar_tiro(session, evento, partido, Estadisticas_J, estadistica_jugador, a_puerta=False)

    elif tipo_enum == TipoEvento.TIRO_A_PUERTA:
        procesar_tiro(session, evento, partido, Estadisticas_J, estadistica_jugador, a_puerta=True)

    elif tipo_enum == TipoEvento.ENTRADA:
        procesar_entrada(session, evento, partido, Estadisticas_J, estadistica_jugador)

    elif tipo_enum == TipoEvento.INTERCEPCION:
        procesar_intercepcion(session, evento, partido, Estadisticas_J, estadistica_jugador)

    elif tipo_enum == TipoEvento.TARJETA_AMARILLA or tipo_enum == TipoEvento.TARJETA_ROJA:
        procesar_tarjeta(session, evento, partido, Estadisticas_E, TipoEvento, estadistica_jugador)

    # En este punto, `evento.tipo` es TipoEvento y serializará al valor correcto (minúsculas)
    session.add(evento)
    session.commit()
    session.refresh(evento)
    return evento


@router.get("/", response_model=list[Evento])
async def obtener_eventos(session: SessionDep):
    eventos = session.query(Evento).all()
    if not eventos:
        raise HTTPException(status_code=404, detail="No se encontraron eventos")
    return eventos


@router.get("/{evento}/", response_model=list[Evento])
async def obtener_eventos_tipo(session: SessionDep, evento: TipoEvento):
    if not evento in TipoEvento:
        raise HTTPException(status_code=400, detail="El tipo de evento no es válido")
    eventos = session.query(Evento).filter(Evento.tipo == evento).all()
    if not eventos:
        raise HTTPException(status_code=404, detail="No se encontraron eventos")
    return eventos

@router.get("/partido/{partido_id}")
async def obtener_eventos_partido(partido_id: int, session: SessionDep):
    """Devuelve los eventos de un partido enriquecidos con nombres de jugadores.

    Formato de respuesta por evento:
    {
        id_evento, minuto, tipo, descripcion, equipo_id,
        jugador_id, jugador_nombre, jugador_asociado_id, jugador_asociado_nombre
    }
    """
    partido = session.get(Partido, partido_id)
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")

    eventos = (
        session.query(Evento)
        .filter(Evento.partido_id == partido_id)
        .order_by(Evento.minuto.asc(), Evento.id_evento.asc())
        .all()
    )
    if not eventos:
        raise HTTPException(status_code=404, detail="No hay eventos para este partido")

    respuesta = []
    for e in eventos:
        jugador = session.get(Jugador, e.jugador_id)
        jugador_asociado = session.get(Jugador, e.jugador_asociado_id) if e.jugador_asociado_id else None
        
        # Construir URLs completas para las fotos
        jugador_foto_url = None
        if jugador:
            jugador_foto_url = f"/static/img/{jugador.foto}" if jugador.foto else "/static/img/default-player.png"
        
        jugador_asociado_foto_url = None
        if jugador_asociado:
            jugador_asociado_foto_url = f"/static/img/{jugador_asociado.foto}" if jugador_asociado.foto else "/static/img/default-player.png"
        
        respuesta.append({
            "id_evento": e.id_evento,
            "minuto": e.minuto,
            # Usamos directamente el value para coincidir con el JS (gol, sustitucion, tarjeta_amarilla, ...)
            "tipo": e.tipo.value if hasattr(e.tipo, 'value') else str(e.tipo),
            "descripcion": e.descripcion,
            "partido_id": e.partido_id,
            "equipo_id": e.equipo_id,
            "jugador_id": e.jugador_id,
            "jugador_nombre": jugador.nombre if jugador else None,
            "jugador_foto": jugador_foto_url,
            "jugador_asociado_id": e.jugador_asociado_id,
            "jugador_asociado_nombre": jugador_asociado.nombre if jugador_asociado else None,
            "jugador_asociado_foto": jugador_asociado_foto_url
        })

    return respuesta


@router.get("/jugador/{jugador_id}")
async def obtener_eventos_jugador(session: SessionDep, jugador_id: int):
    """Obtiene todos los eventos en los que participó un jugador"""
    from sqlalchemy.orm import aliased
    
    jugador = session.get(Jugador, jugador_id)
    if not jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    
    # Obtener eventos donde el jugador es protagonista o asociado
    eventos = (
        session.query(Evento)
        .filter(
            (Evento.jugador_id == jugador_id) | 
            (Evento.jugador_asociado_id == jugador_id)
        )
        .order_by(Evento.id_evento.desc())
        .limit(50)  # Últimos 50 eventos
        .all()
    )
    
    respuesta = []
    for e in eventos:
        # Obtener información del partido
        partido = session.get(Partido, e.partido_id)
        if not partido:
            continue
        
        equipo_local = aliased(Equipo, name="equipo_local")
        equipo_visitante = aliased(Equipo, name="equipo_visitante")
        
        partido_info = (
            session.query(Partido, equipo_local, equipo_visitante)
            .select_from(Partido)
            .join(equipo_local, Partido.equipo_local_id == equipo_local.equipo_id)
            .join(equipo_visitante, Partido.equipo_visitante_id == equipo_visitante.equipo_id)
            .filter(Partido.partido_id == e.partido_id)
            .first()
        )
        
        if not partido_info:
            continue
        
        _, el, ev = partido_info
        
        respuesta.append({
            "id_evento": e.id_evento,
            "minuto": e.minuto,
            "tipo": e.tipo.value if hasattr(e.tipo, 'value') else str(e.tipo),
            "descripcion": e.descripcion,
            "partido_id": e.partido_id,
            "partido_fecha": str(partido.fecha) if partido.fecha else None,
            "partido_local": el.nombre if el else "Local",
            "partido_visitante": ev.nombre if ev else "Visitante"
        })
    
    return respuesta


@router.delete("/{evento_id}/", response_model=list[Evento])
async def anular_evento(session: SessionDep, evento_id: int):
    evento = session.query(Evento).filter(Evento.id == evento_id).first()
    if not evento:
        raise HTTPException(status_code=404, detail="No se encontraron evento")

    if evento.tipo in (TipoEvento.GOL, TipoEvento.PENAL):
        anular_gol(session, evento, session.get(Partido, evento.partido_id), Estadisticas_E, session.get(Estadisticas_J, evento.jugador_id), session.get(Estadisticas_J, evento.jugador_asociado_id) if evento.jugador_asociado_id else None)
    elif evento.tipo == TipoEvento.PENAL_FALLADO:
        # Nada que revertir (solo se eliminará el evento)
        pass
    elif evento.tipo == TipoEvento.GOL_EN_CONTRA:
        # Revertir autogol
        anular_gol_en_contra(session, evento, session.get(Partido, evento.partido_id), Estadisticas_E, session.get(Estadisticas_J, evento.jugador_id) if evento.jugador_id else None)
    elif evento.tipo == TipoEvento.TARJETA_AMARILLA or evento.tipo == TipoEvento.TARJETA_ROJA:
        anular_tarjeta(session, evento, session.get(Partido, evento.partido_id), Estadisticas_E, session.get(Estadisticas_J, evento.jugador_id))