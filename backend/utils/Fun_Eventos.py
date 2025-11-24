
# python
def procesar_gol(session, evento, partido, Estadisticas_E, estadistica_jugador,estadistica_jugador_asociado=None):
    # Determinar equipo y rival y actualizar goles del partido
    if evento.equipo_id == partido.equipo_local_id:
        partido.goles_local = (partido.goles_local or 0) + 1
        equipo_id = partido.equipo_local_id
        rival_id = partido.equipo_visitante_id
    else:
        partido.goles_visitante = (partido.goles_visitante or 0) + 1
        equipo_id = partido.equipo_visitante_id
        rival_id = partido.equipo_local_id

    # Obtener o crear estadísticas del equipo y del rival
    estadistica = session.query(Estadisticas_E).filter_by(equipo_id=equipo_id).first()
    estadistica_rival = session.query(Estadisticas_E).filter_by(equipo_id=rival_id).first()

    if estadistica is None:
        estadistica = Estadisticas_E(equipo_id=equipo_id)
    if estadistica_rival is None:
        estadistica_rival = Estadisticas_E(equipo_id=rival_id)

    # Actualizar goles a favor y en contra
    estadistica.goles_favor = (estadistica.goles_favor or 0) + 1
    estadistica_rival.goles_contra = (estadistica_rival.goles_contra or 0) + 1

    # Actualizar estadística del jugador si aplica
    if estadistica_jugador:
        estadistica_jugador.goles = (estadistica_jugador.goles or 0) + 1
        session.add(estadistica_jugador)

    # Actualizar estadística del jugador asociado si aplica
    if estadistica_jugador_asociado:
        estadistica_jugador_asociado.asistencias = (estadistica_jugador_asociado.asistencias or 0) + 1
        session.add(estadistica_jugador_asociado)

    # Persistir cambios en una sola transacción
    session.add_all([partido, estadistica, estadistica_rival])
    session.commit()

    # Refrescar entidades para obtener valores actualizados
    session.refresh(partido)
    session.refresh(estadistica)
    session.refresh(estadistica_rival)
    if estadistica_jugador:
        session.refresh(estadistica_jugador)

def procesar_tarjeta(session, evento, partido, Estadisticas_E, TipoEvento, estadistica_jugador):
    """
    Actualiza estadísticas cuando ocurre una tarjeta (amarilla o roja).
    """
    # Determinar equipo
    if evento.equipo_id == partido.equipo_local_id:
        equipo_id = partido.equipo_local_id
    else:
        equipo_id = partido.equipo_visitante_id

    # Obtener o crear estadísticas del equipo
    estadistica = session.query(Estadisticas_E).filter_by(equipo_id=equipo_id, Temporada = partido.temporada_id).first()
    if estadistica is None:
        estadistica = Estadisticas_E(equipo_id=equipo_id)

    # Actualizar según el tipo de evento
    if evento.tipo == TipoEvento.TARJETA_AMARILLA:
        estadistica.tarjetas_amarillas = (estadistica.tarjetas_amarillas or 0) + 1
        if estadistica_jugador:
            estadistica_jugador.tarjetas_amarillas = (estadistica_jugador.tarjetas_amarillas or 0) + 1
            session.add(estadistica_jugador)

    elif evento.tipo == TipoEvento.TARJETA_ROJA:
        estadistica.tarjetas_rojas = (estadistica.tarjetas_rojas or 0) + 1
        if estadistica_jugador:
            estadistica_jugador.tarjetas_rojas = (estadistica_jugador.tarjetas_rojas or 0) + 1
            session.add(estadistica_jugador)

    # Guardar cambios
    session.add_all([partido, estadistica])
    session.commit()

    # Refrescar
    session.refresh(partido)
    session.refresh(estadistica)
    if estadistica_jugador:
        session.refresh(estadistica_jugador)

def anular_gol(session, evento, partido, Estadisticas_E, estadistica_jugador,estadistica_jugador_asociado=None):
    if evento.equipo_id == partido.equipo_local_id:
        partido.goles_local = (partido.goles_local or 0) - 1
        equipo_id = partido.equipo_local_id
        rival_id = partido.equipo_visitante_id
    else:
        partido.goles_visitante = (partido.goles_visitante or 0) - 1
        equipo_id = partido.equipo_visitante_id
        rival_id = partido.equipo_local_id

    # Obtener o crear estadísticas del equipo y del rival
    estadistica = session.query(Estadisticas_E).filter_by(equipo_id=equipo_id, Temporada=partido.temporada_id).first()
    estadistica_rival = session.query(Estadisticas_E).filter_by(equipo_id=rival_id, Temporada=partido.temporada_id).first()

    if estadistica is None:
        estadistica = Estadisticas_E(equipo_id=equipo_id)
    if estadistica_rival is None:
        estadistica_rival = Estadisticas_E(equipo_id=rival_id)

    # Actualizar goles a favor y en contra
    estadistica.goles_favor = (estadistica.goles_favor or 0) - 1
    estadistica_rival.goles_contra = (estadistica_rival.goles_contra or 0) - 1

    # Actualizar estadística del jugador si aplica
    if estadistica_jugador:
        estadistica_jugador.goles = (estadistica_jugador.goles or 0) - 1
        session.add(estadistica_jugador)

    # Actualizar estadística del jugador asociado si aplica
    if estadistica_jugador_asociado:
        estadistica_jugador_asociado.asistencias = (estadistica_jugador_asociado.asistencias or 0) - 1
        session.add(estadistica_jugador_asociado)

    # Persistir cambios en una sola transacción
    session.add_all([partido, estadistica, estadistica_rival])
    session.commit()

    # Refrescar entidades para obtener valores actualizados
    session.refresh(partido)
    session.refresh(estadistica)
    session.refresh(estadistica_rival)
    if estadistica_jugador:
        session.refresh(estadistica_jugador)

def anular_tarjeta(session, evento, partido, Estadisticas_E, TipoEvento, estadistica_jugador):
    """
    Actualiza estadísticas cuando ocurre una tarjeta (amarilla o roja).
    """
    # Determinar equipo
    if evento.equipo_id == partido.equipo_local_id:
        equipo_id = partido.equipo_local_id
    else:
        equipo_id = partido.equipo_visitante_id

    # Obtener o crear estadísticas del equipo
    estadistica = session.query(Estadisticas_E).filter_by(equipo_id=equipo_id, Temporada = partido.temporada_id).first()
    if estadistica is None:
        estadistica = Estadisticas_E(equipo_id=equipo_id)

    # Actualizar según el tipo de evento
    if evento.tipo == TipoEvento.TARJETA_AMARILLA:
        estadistica.tarjetas_amarillas = (estadistica.tarjetas_amarillas or 0) - 1
        if estadistica_jugador:
            estadistica_jugador.tarjetas_amarillas = (estadistica_jugador.tarjetas_amarillas or 0) - 1
            session.add(estadistica_jugador)

    elif evento.tipo == TipoEvento.TARJETA_ROJA:
        estadistica.tarjetas_rojas = (estadistica.tarjetas_rojas or 0) - 1
        if estadistica_jugador:
            estadistica_jugador.tarjetas_rojas = (estadistica_jugador.tarjetas_rojas or 0) - 1
            session.add(estadistica_jugador)

    # Guardar cambios
    session.add_all([partido, estadistica])
    session.commit()

    # Refrescar
    session.refresh(partido)
    session.refresh(estadistica)
    if estadistica_jugador:
        session.refresh(estadistica_jugador)

def validar_sustitucion(session, evento, partido, TipoEvento):
    """
    Valida que una sustitución cumpla las reglas:
    - jugador_id (sale) debe estar actualmente en cancha (titular inicial o entró por sustitución previa).
    - jugador_asociado_id (entra) debe ser suplente inicial que nunca haya entrado.
    """
    from backend.modelos.Formaciones import FormacionJugador
    from backend.modelos.Eventos import Evento
    from fastapi import HTTPException
    
    if not evento.jugador_asociado_id:
        raise HTTPException(status_code=400, detail="Debe enviar jugador_asociado_id para una sustitución (jugador que entra)")
    
    # Obtener formación correspondiente
    formacion_id = None
    if evento.equipo_id == partido.equipo_local_id:
        formacion_id = partido.formacion_local_id
    elif evento.equipo_id == partido.equipo_visitante_id:
        formacion_id = partido.formacion_visitante_id
    if not formacion_id:
        raise HTTPException(status_code=400, detail="No hay formación asignada para este equipo en el partido")

    # Titulares y suplentes iniciales
    formacion_jugadores = session.query(FormacionJugador).filter(FormacionJugador.formacion_id == formacion_id).all()
    titulares_iniciales = {fj.jugador_id for fj in formacion_jugadores if fj.titular}
    suplentes_iniciales = {fj.jugador_id for fj in formacion_jugadores if not fj.titular}
    
    if evento.jugador_id not in titulares_iniciales:
        raise HTTPException(status_code=400, detail="El jugador que sale no está entre los titulares iniciales")
    if evento.jugador_asociado_id not in suplentes_iniciales:
        raise HTTPException(status_code=400, detail="El jugador que entra no está entre los suplentes iniciales")

    # Construir estado actual del campo según sustituciones previas
    sustituciones_previas = session.query(Evento).filter(
        Evento.partido_id == evento.partido_id,
        Evento.equipo_id == evento.equipo_id,
        Evento.tipo == TipoEvento.SUSTITUCION
    ).order_by(Evento.minuto.asc()).all()

    en_campo = set(titulares_iniciales)
    for ev in sustituciones_previas:
        if ev.jugador_id in en_campo:
            en_campo.remove(ev.jugador_id)
        en_campo.add(ev.jugador_asociado_id)

    # Validar estado actual
    if evento.jugador_id not in en_campo:
        raise HTTPException(status_code=400, detail="El jugador que sale ya no está en el campo")
    if evento.jugador_asociado_id in en_campo:
        raise HTTPException(status_code=400, detail="El jugador que entra ya está en el campo")