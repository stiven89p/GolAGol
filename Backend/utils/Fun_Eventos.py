# python
def procesar_gol(session, evento, partido, Estadisticas_E, estadistica_jugador=None):
    """
    Actualiza partido y estadísticas cuando ocurre un gol.
    - session: sesión de SQLAlchemy/SQLModel
    - evento: objeto evento con .equipo_id
    - partido: objeto partido con .equipo_local_id, .equipo_visitante_id, .goles_local, .goles_visitante
    - Estadisticas_E: clase modelo de estadísticas de equipo
    - estadistica_jugador: objeto de estadísticas del jugador (opcional)
    """
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

    # Persistir cambios en una sola transacción
    session.add_all([partido, estadistica, estadistica_rival])
    session.commit()

    # Refrescar entidades para obtener valores actualizados
    session.refresh(partido)
    session.refresh(estadistica)
    session.refresh(estadistica_rival)
    if estadistica_jugador:
        session.refresh(estadistica_jugador)

    return {
        "partido": partido,
        "estadistica": estadistica,
        "estadistica_rival": estadistica_rival,
        "estadistica_jugador": estadistica_jugador,
    }