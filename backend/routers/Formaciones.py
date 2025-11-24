from fastapi import APIRouter, HTTPException
from backend.db import SessionDep
from backend.modelos.Formaciones import Formacion, FormacionCrear, FormacionDTO, FormacionJugador
from backend.modelos.Jugadores import Jugador
from backend.utils.enumeraciones import PosicionJugador

router = APIRouter(prefix="/formaciones", tags=["formaciones"])


def validar_suma(defensas: int, mediocampistas: int, delanteros: int) -> None:
    if defensas + mediocampistas + delanteros != 10:  # 10 + 1 portero = 11
        raise HTTPException(status_code=400, detail="La suma de defensas, mediocampistas y delanteros debe ser 10 (total 11 con el portero)")
    if any(v < 0 for v in [defensas, mediocampistas, delanteros]):
        raise HTTPException(status_code=400, detail="Los valores no pueden ser negativos")


@router.post("/", response_model=FormacionDTO)
async def crear_formacion(
    data: FormacionCrear,
    titulares: list[int],
    suplentes: list[int],
    session: SessionDep
):
    # Validar cantidades de listas
    if len(titulares) != 11:
        raise HTTPException(status_code=400, detail="Debe enviar exactamente 11 jugadores titulares")
    if len(suplentes) > 9:
        raise HTTPException(status_code=400, detail=f"Puede enviar como máximo 9 jugadores suplentes (recibidos {len(suplentes)})")

    # Validar unicidad
    repetidos = set(titulares) & set(suplentes)
    if repetidos:
        raise HTTPException(status_code=400, detail=f"Jugadores repetidos entre titulares y suplentes: {sorted(list(repetidos))}")

    validar_suma(data.defensas, data.mediocampistas, data.delanteros)

    # Validar portero
    portero = session.get(Jugador, data.portero_id)
    if not portero or portero.equipo_id != data.equipo_id:
        raise HTTPException(status_code=404, detail="Portero no encontrado en el equipo")
    if portero.posicion != PosicionJugador.PORTERO:
        raise HTTPException(status_code=400, detail="El jugador seleccionado no es portero")
    if portero.jugador_id not in titulares:
        raise HTTPException(status_code=400, detail="El portero debe estar incluido en la lista de titulares")

    # Cargar todos los jugadores involucrados
    todos_ids = list(set(titulares + suplentes))
    jugadores = session.query(Jugador).filter(Jugador.jugador_id.in_(todos_ids)).all()
    if len(jugadores) != len(todos_ids):
        raise HTTPException(status_code=404, detail="Algún jugador no existe")

    # Validar que pertenecen al equipo
    for j in jugadores:
        if j.equipo_id != data.equipo_id:
            raise HTTPException(status_code=400, detail=f"El jugador {j.jugador_id} no pertenece al equipo {data.equipo_id}")

    # Contar posiciones titulares
    def count_pos(pos):
        return sum(1 for j in jugadores if j.jugador_id in titulares and j.posicion == pos)

    if count_pos(PosicionJugador.DEFENSOR) != data.defensas:
        raise HTTPException(status_code=400, detail="Cantidad de defensas titulares no coincide con la formación")
    if count_pos(PosicionJugador.MEDIOCAMPISTA) != data.mediocampistas:
        raise HTTPException(status_code=400, detail="Cantidad de mediocampistas titulares no coincide con la formación")
    if count_pos(PosicionJugador.DELANTERO) != data.delanteros:
        raise HTTPException(status_code=400, detail="Cantidad de delanteros titulares no coincide con la formación")
    # Validar único portero entre titulares
    if count_pos(PosicionJugador.PORTERO) != 1:
        raise HTTPException(status_code=400, detail="Debe haber exactamente un portero titular")

    formacion = Formacion.model_validate(data)
    session.add(formacion)
    session.commit()
    session.refresh(formacion)

    # Crear registros de jugadores
    for j in jugadores:
        fj = FormacionJugador(
            formacion_id=formacion.formacion_id,
            jugador_id=j.jugador_id,
            titular=(j.jugador_id in titulares),
            posicion=j.posicion.value if hasattr(j.posicion, 'value') else str(j.posicion)
        )
        session.add(fj)
    session.commit()

    titulares_info = [
        {"jugador_id": j.jugador_id, "nombre": f"{j.nombre} {j.apellido}", "posicion": j.posicion.value if hasattr(j.posicion, 'value') else str(j.posicion)}
        for j in jugadores if j.jugador_id in titulares
    ]
    suplentes_info = [
        {"jugador_id": j.jugador_id, "nombre": f"{j.nombre} {j.apellido}", "posicion": j.posicion.value if hasattr(j.posicion, 'value') else str(j.posicion)}
        for j in jugadores if j.jugador_id in suplentes
    ]

    return FormacionDTO(
        formacion_id=formacion.formacion_id,
        equipo_id=formacion.equipo_id,
        portero_id=formacion.portero_id,
        defensas=formacion.defensas,
        mediocampistas=formacion.mediocampistas,
        delanteros=formacion.delanteros,
        titulares=titulares_info,
        suplentes=suplentes_info,
        total=11,
    )


@router.get("/equipo/{equipo_id}", response_model=list[FormacionDTO])
async def listar_formaciones_equipo(equipo_id: int, session: SessionDep):
    rows = session.query(Formacion).filter(Formacion.equipo_id == equipo_id).all()
    result: list[FormacionDTO] = []
    for f in rows:
        jugadores = session.query(FormacionJugador).filter(FormacionJugador.formacion_id == f.formacion_id).all()
        titulares_info = [
            {"jugador_id": j.jugador_id, "posicion": j.posicion}
            for j in jugadores if j.titular
        ]
        suplentes_info = [
            {"jugador_id": j.jugador_id, "posicion": j.posicion}
            for j in jugadores if not j.titular
        ]
        result.append(
            FormacionDTO(
                formacion_id=f.formacion_id,
                equipo_id=f.equipo_id,
                portero_id=f.portero_id,
                defensas=f.defensas,
                mediocampistas=f.mediocampistas,
                delanteros=f.delanteros,
                titulares=titulares_info,
                suplentes=suplentes_info,
                total=11,
            )
        )
    return result
