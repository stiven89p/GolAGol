
# python
from backend.modelos.Estadisticas_Jugadores import Estadisticas_J
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
    estadistica = session.query(Estadisticas_E).filter_by(equipo_id=equipo_id, temporada=partido.temporada_id).first()
    estadistica_rival = session.query(Estadisticas_E).filter_by(equipo_id=rival_id, temporada=partido.temporada_id).first()

    if estadistica is None:
        estadistica = Estadisticas_E(equipo_id=equipo_id, temporada=partido.temporada_id)
    if estadistica_rival is None:
        estadistica_rival = Estadisticas_E(equipo_id=rival_id, temporada=partido.temporada_id)

    # Actualizar goles a favor y en contra
    estadistica.goles_favor = (estadistica.goles_favor or 0) + 1
    estadistica_rival.goles_contra = (estadistica_rival.goles_contra or 0) + 1

    # Actualizar estadística del jugador si aplica
    if estadistica_jugador:
        estadistica_jugador.goles = (estadistica_jugador.goles or 0) + 1
        # Si el gol viene de un penal, contar penal cobrado
        try:
            from backend.utils.enumeraciones import TipoEvento
            if hasattr(evento, 'tipo') and evento.tipo == TipoEvento.PENAL:
                estadistica_jugador.penales_cobrados = (estadistica_jugador.penales_cobrados or 0) + 1
        except Exception:
            pass
        session.add(estadistica_jugador)

    # Actualizar estadística del jugador asociado si aplica
    if estadistica_jugador_asociado:
        estadistica_jugador_asociado.asistencias = (estadistica_jugador_asociado.asistencias or 0) + 1
        session.add(estadistica_jugador_asociado)

    # Persistir cambios en una sola transacción
    # Además, incrementar 'goles_concedidos' para el portero rival
    try:
        from backend.modelos.Formaciones import Formacion
        # Determinar id de la formación del rival
        formacion_rival_id = None
        if equipo_id == partido.equipo_local_id:
            # rival es visitante
            formacion_rival_id = getattr(partido, 'formacion_visitante_id', None)
        else:
            formacion_rival_id = getattr(partido, 'formacion_local_id', None)

        portero_id = None
        formacion_rival = None
        if formacion_rival_id:
            formacion_rival = session.get(Formacion, formacion_rival_id)
        if not formacion_rival:
            # fallback: buscar por equipo
            formacion_rival = session.query(Formacion).filter_by(equipo_id=rival_id).first()
        if formacion_rival:
            portero_id = getattr(formacion_rival, 'portero_id', None)

        if portero_id:
            estad_portero = session.query(Estadisticas_J).filter_by(jugador_id=portero_id, temporada=partido.temporada_id).first()
            if estad_portero is None:
                estad_portero = Estadisticas_J(jugador_id=portero_id, temporada=partido.temporada_id)
            estad_portero.goles_concedidos = (estad_portero.goles_concedidos or 0) + 1
            session.add(estad_portero)
    except Exception:
        # No bloquear el flujo principal si no podemos encontrar la formación/portero
        pass

    session.add_all([partido, estadistica, estadistica_rival])
    session.commit()

    # Refrescar entidades para obtener valores actualizados
    session.refresh(partido)
    session.refresh(estadistica)
    session.refresh(estadistica_rival)
    if estadistica_jugador:
        session.refresh(estadistica_jugador)


def procesar_penal_fallado(session, evento, partido, Estadisticas_J, estadistica_jugador, estadistica_portero=None):
    # Penal fallado: incrementa penales_fallados del ejecutor y, si es posible, penales_tapados del portero rival
    if not estadistica_jugador:
        estadistica_jugador = session.query(Estadisticas_J).filter_by(jugador_id=evento.jugador_id, temporada=partido.temporada_id).first()
        if estadistica_jugador is None:
            estadistica_jugador = Estadisticas_J(jugador_id=evento.jugador_id, temporada=partido.temporada_id)
    estadistica_jugador.penales_fallados = (estadistica_jugador.penales_fallados or 0) + 1
    session.add(estadistica_jugador)

    # Si no nos pasaron la estadística del portero (jugador_asociado), intentar derivarla desde la formación rival
    if not estadistica_portero:
        try:
            from backend.modelos.Formaciones import Formacion
            # Equipo del ejecutor y su rival
            equipo_ejecutor = evento.equipo_id
            equipo_rival = partido.equipo_visitante_id if equipo_ejecutor == partido.equipo_local_id else partido.equipo_local_id

            # Intentar usar la formación del rival asignada al partido; si no existe, fallback por equipo
            formacion_rival_id = None
            if equipo_rival == partido.equipo_local_id:
                formacion_rival_id = getattr(partido, 'formacion_local_id', None)
            else:
                formacion_rival_id = getattr(partido, 'formacion_visitante_id', None)

            formacion_rival = None
            if formacion_rival_id:
                formacion_rival = session.get(Formacion, formacion_rival_id)
            if not formacion_rival:
                formacion_rival = session.query(Formacion).filter_by(equipo_id=equipo_rival).first()

            portero_id = getattr(formacion_rival, 'portero_id', None) if formacion_rival else None
            if portero_id:
                estadistica_portero = session.query(Estadisticas_J).filter_by(jugador_id=portero_id, temporada=partido.temporada_id).first()
                if estadistica_portero is None:
                    estadistica_portero = Estadisticas_J(jugador_id=portero_id, temporada=partido.temporada_id)
        except Exception:
            # No bloquear si no podemos identificar al portero
            estadistica_portero = None

    if estadistica_portero:
        estadistica_portero.penales_tapados = (estadistica_portero.penales_tapados or 0) + 1
        session.add(estadistica_portero)

    session.commit()
    session.refresh(estadistica_jugador)
    if estadistica_portero:
        session.refresh(estadistica_portero)


def procesar_tiro(session, evento, partido, Estadisticas_J, estadistica_jugador, a_puerta=False):
    # Cuenta tiro total y opcional tiro a puerta
    if not estadistica_jugador:
        estadistica_jugador = session.query(Estadisticas_J).filter_by(jugador_id=evento.jugador_id, temporada=partido.temporada_id).first()
        if estadistica_jugador is None:
            estadistica_jugador = Estadisticas_J(jugador_id=evento.jugador_id, temporada=partido.temporada_id)
    estadistica_jugador.tiros_totales = (estadistica_jugador.tiros_totales or 0) + 1
    if a_puerta:
        estadistica_jugador.tiros_a_puerta = (estadistica_jugador.tiros_a_puerta or 0) + 1
    session.add(estadistica_jugador)
    session.commit()
    session.refresh(estadistica_jugador)


def procesar_parada(session, evento, partido, Estadisticas_J, estadistica_portero):
    # Portero que realiza la parada (jugador_asociado_id)
    if not estadistica_portero:
        estadistica_portero = session.query(Estadisticas_J).filter_by(jugador_id=evento.jugador_asociado_id, temporada=partido.temporada_id).first()
        if estadistica_portero is None:
            estadistica_portero = Estadisticas_J(jugador_id=evento.jugador_asociado_id, temporada=partido.temporada_id)
    estadistica_portero.paradas = (estadistica_portero.paradas or 0) + 1
    session.add(estadistica_portero)
    session.commit()
    session.refresh(estadistica_portero)


def procesar_entrada(session, evento, partido, Estadisticas_J, estadistica_jugador, estadistica_jugador_asociado=None):
    if not estadistica_jugador:
        estadistica_jugador = session.query(Estadisticas_J).filter_by(jugador_id=evento.jugador_id, temporada=partido.temporada_id).first()
        if estadistica_jugador is None:
            estadistica_jugador = Estadisticas_J(jugador_id=evento.jugador_id, temporada=partido.temporada_id)
    estadistica_jugador.entradas = (estadistica_jugador.entradas or 0) + 1
    session.add(estadistica_jugador)
    session.commit()
    session.refresh(estadistica_jugador)

    # Si hay jugador asociado (por ejemplo, quien pierde el balón), aumentar balones_perdidos
    if getattr(evento, 'jugador_asociado_id', None):
        estad_assoc = estadistica_jugador_asociado if estadistica_jugador_asociado else session.query(Estadisticas_J).filter_by(jugador_id=evento.jugador_asociado_id, temporada=partido.temporada_id).first()
        if estad_assoc is None:
            estad_assoc = Estadisticas_J(jugador_id=evento.jugador_asociado_id, temporada=partido.temporada_id)
        estad_assoc.balones_perdidos = (estad_assoc.balones_perdidos or 0) + 1
        session.add(estad_assoc)
        session.commit()
        session.refresh(estad_assoc)


def procesar_intercepcion(session, evento, partido, Estadisticas_J, estadistica_jugador, estadistica_jugador_asociado=None):
    if not estadistica_jugador:
        estadistica_jugador = session.query(Estadisticas_J).filter_by(jugador_id=evento.jugador_id, temporada=partido.temporada_id).first()
        if estadistica_jugador is None:
            estadistica_jugador = Estadisticas_J(jugador_id=evento.jugador_id, temporada=partido.temporada_id)
    estadistica_jugador.intercepciones = (estadistica_jugador.intercepciones or 0) + 1
    session.add(estadistica_jugador)
    session.commit()
    session.refresh(estadistica_jugador)

    # Si hay jugador asociado (quien pierde el balón por la intercepción), aumentar balones_perdidos
    if getattr(evento, 'jugador_asociado_id', None):
        estad_assoc = estadistica_jugador_asociado if estadistica_jugador_asociado else session.query(Estadisticas_J).filter_by(jugador_id=evento.jugador_asociado_id, temporada=partido.temporada_id).first()
        if estad_assoc is None:
            estad_assoc = Estadisticas_J(jugador_id=evento.jugador_asociado_id, temporada=partido.temporada_id)
        estad_assoc.balones_perdidos = (estad_assoc.balones_perdidos or 0) + 1
        session.add(estad_assoc)
        session.commit()
        session.refresh(estad_assoc)

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
    estadistica = session.query(Estadisticas_E).filter_by(equipo_id=equipo_id, temporada=partido.temporada_id).first()
    if estadistica is None:
        estadistica = Estadisticas_E(equipo_id=equipo_id, temporada=partido.temporada_id)

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
    estadistica = session.query(Estadisticas_E).filter_by(equipo_id=equipo_id, temporada=partido.temporada_id).first()
    estadistica_rival = session.query(Estadisticas_E).filter_by(equipo_id=rival_id, temporada=partido.temporada_id).first()

    if estadistica is None:
        estadistica = Estadisticas_E(equipo_id=equipo_id, temporada=partido.temporada_id)
    if estadistica_rival is None:
        estadistica_rival = Estadisticas_E(equipo_id=rival_id, temporada=partido.temporada_id)

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
    # Además, decrementar 'goles_concedidos' del portero rival
    try:
        from backend.modelos.Formaciones import Formacion
        # determinar rival
        if evento.equipo_id == partido.equipo_local_id:
            rival_id = partido.equipo_visitante_id
            formacion_rival_id = getattr(partido, 'formacion_visitante_id', None)
        else:
            rival_id = partido.equipo_local_id
            formacion_rival_id = getattr(partido, 'formacion_local_id', None)

        formacion_rival = None
        portero_id = None
        if formacion_rival_id:
            formacion_rival = session.get(Formacion, formacion_rival_id)
        if not formacion_rival:
            formacion_rival = session.query(Formacion).filter_by(equipo_id=rival_id).first()
        if formacion_rival:
            portero_id = getattr(formacion_rival, 'portero_id', None)

        if portero_id:
            estad_portero = session.query(Estadisticas_J).filter_by(jugador_id=portero_id, temporada=partido.temporada_id).first()
            if estad_portero:
                estad_portero.goles_concedidos = max((estad_portero.goles_concedidos or 0) - 1, 0)
                session.add(estad_portero)
    except Exception:
        pass

    session.add_all([partido, estadistica, estadistica_rival])
    session.commit()

    # Refrescar entidades para obtener valores actualizados
    session.refresh(partido)
    session.refresh(estadistica)
    session.refresh(estadistica_rival)
    if estadistica_jugador:
        session.refresh(estadistica_jugador)


def procesar_gol_en_contra(session, evento, partido, Estadisticas_E, estadistica_jugador):
    """Procesa un gol en contra (autogol).
    `evento.equipo_id` es el equipo del jugador que cometió el autogol; el gol cuenta para el rival.
    No incrementa goles del autor en sus estadísticas personales (no es un gol a favor).
    """
    # Determinar equipo que recibió el autogol (rival)
    if evento.equipo_id == partido.equipo_local_id:
        # el autogol lo cometió el local -> sumar gol al visitante
        partido.goles_visitante = (partido.goles_visitante or 0) + 1
        equipo_autogol = partido.equipo_local_id
        equipo_rival = partido.equipo_visitante_id
    else:
        partido.goles_local = (partido.goles_local or 0) + 1
        equipo_autogol = partido.equipo_visitante_id
        equipo_rival = partido.equipo_local_id

    # Obtener o crear estadísticas del equipo receptor (rival) y del equipo que sufrió el autogol
    estadistica_rival = session.query(Estadisticas_E).filter_by(equipo_id=equipo_rival, temporada=partido.temporada_id).first()
    estadistica_autogol = session.query(Estadisticas_E).filter_by(equipo_id=equipo_autogol, temporada=partido.temporada_id).first()

    if estadistica_rival is None:
        estadistica_rival = Estadisticas_E(equipo_id=equipo_rival, temporada=partido.temporada_id)
    if estadistica_autogol is None:
        estadistica_autogol = Estadisticas_E(equipo_id=equipo_autogol, temporada=partido.temporada_id)

    # actualizar: rival goles a favor, autogol equipo goles en contra
    estadistica_rival.goles_favor = (estadistica_rival.goles_favor or 0) + 1
    estadistica_autogol.goles_contra = (estadistica_autogol.goles_contra or 0) + 1

    # Incrementar 'goles_concedidos' al portero del equipo que sufrió el autogol
    try:
        from backend.modelos.Formaciones import Formacion
        formacion_autogol = session.query(Formacion).filter_by(equipo_id=equipo_autogol).first()
        portero_id = getattr(formacion_autogol, 'portero_id', None) if formacion_autogol else None
        if portero_id:
            estad_portero = session.query(Estadisticas_J).filter_by(jugador_id=portero_id, temporada=partido.temporada_id).first()
            if estad_portero is None:
                estad_portero = Estadisticas_J(jugador_id=portero_id, temporada=partido.temporada_id)
            estad_portero.goles_concedidos = (estad_portero.goles_concedidos or 0) + 1
            session.add(estad_portero)
    except Exception:
        pass

    # Persistir
    session.add_all([partido, estadistica_rival, estadistica_autogol])
    session.commit()
    session.refresh(partido)
    session.refresh(estadistica_rival)
    session.refresh(estadistica_autogol)


def anular_gol_en_contra(session, evento, partido, Estadisticas_E, estadistica_jugador=None):
    """Revertir un autogol: resta el gol al rival y actualiza estadísticas de equipos."""
    # Si el autor del autogol es local, el gol fue al visitante
    if evento.equipo_id == partido.equipo_local_id:
        partido.goles_visitante = max((partido.goles_visitante or 0) - 1, 0)
        equipo_autogol = partido.equipo_local_id
        equipo_rival = partido.equipo_visitante_id
    else:
        partido.goles_local = max((partido.goles_local or 0) - 1, 0)
        equipo_autogol = partido.equipo_visitante_id
        equipo_rival = partido.equipo_local_id

    estadistica_rival = session.query(Estadisticas_E).filter_by(equipo_id=equipo_rival, temporada=partido.temporada_id).first()
    estadistica_autogol = session.query(Estadisticas_E).filter_by(equipo_id=equipo_autogol, temporada=partido.temporada_id).first()

    if estadistica_rival:
        estadistica_rival.goles_favor = max((estadistica_rival.goles_favor or 0) - 1, 0)
        session.add(estadistica_rival)
    if estadistica_autogol:
        estadistica_autogol.goles_contra = max((estadistica_autogol.goles_contra or 0) - 1, 0)
        session.add(estadistica_autogol)

    # Decrementar goles_concedidos del portero del equipo que sufrió el autogol
    try:
        from backend.modelos.Formaciones import Formacion
        formacion_autogol = session.query(Formacion).filter_by(equipo_id=equipo_autogol).first()
        portero_id = getattr(formacion_autogol, 'portero_id', None) if formacion_autogol else None
        if portero_id:
            estad_portero = session.query(Estadisticas_J).filter_by(jugador_id=portero_id, temporada=partido.temporada_id).first()
            if estad_portero:
                estad_portero.goles_concedidos = max((estad_portero.goles_concedidos or 0) - 1, 0)
                session.add(estad_portero)
    except Exception:
        pass

    session.add(partido)
    session.commit()
    session.refresh(partido)
    if estadistica_rival:
        session.refresh(estadistica_rival)
    if estadistica_autogol:
        session.refresh(estadistica_autogol)

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
    estadistica = session.query(Estadisticas_E).filter_by(equipo_id=equipo_id, temporada=partido.temporada_id).first()
    if estadistica is None:
        estadistica = Estadisticas_E(equipo_id=equipo_id, temporada=partido.temporada_id)

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