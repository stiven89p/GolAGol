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