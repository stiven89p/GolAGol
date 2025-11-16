import os
import sys
import uuid
import shutil
from pathlib import Path
from typing import Optional
from datetime import date

# Asegura que el proyecto raíz esté en sys.path al ejecutar este script directamente
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlmodel import Session, SQLModel, select

from backend.db import engine
from backend.modelos.Jugadores import Jugador
from backend.modelos.Equipos import Equipo
from backend.utils.enumeraciones import PosicionJugador

STATIC_IMG_DIR = Path("static/img")
STATIC_IMG_DIR.mkdir(parents=True, exist_ok=True)


def _safe_copy_foto(src_path: Optional[str]) -> Optional[str]:
    """Copia el archivo de foto a static/img y devuelve el nombre de archivo destino."""
    if not src_path:
        return None
    src = Path(src_path)
    if not src.exists() or not src.is_file():
        print(f"[seed] Aviso: foto no encontrada -> {src}")
        return None

    new_name = f"{uuid.uuid4().hex}_{src.name}"
    dest = STATIC_IMG_DIR / new_name
    with src.open("rb") as fsrc, dest.open("wb") as fdst:
        shutil.copyfileobj(fsrc, fdst)
    return new_name


def get_equipo_id_by_name(session: Session, nombre: str) -> Optional[int]:
    """Obtiene el equipo_id dado el nombre del equipo."""
    equipo = session.exec(select(Equipo).where(Equipo.nombre == nombre)).first()
    return equipo.equipo_id if equipo else None


def upsert_jugador(
    session: Session,
    *,
    nombre: str,
    apellido: str,
    fecha_nacimiento: date,
    posicion: PosicionJugador,
    nacionalidad: str,
    equipo_id: int,
    foto_path: Optional[str] = None,
) -> Jugador:
    """Crea o actualiza un jugador por nombre completo y equipo."""
    existing = session.exec(
        select(Jugador)
        .where(Jugador.nombre == nombre)
        .where(Jugador.apellido == apellido)
        .where(Jugador.equipo_id == equipo_id)
    ).first()

    foto_file = _safe_copy_foto(foto_path)

    if existing:
        existing.fecha_nacimiento = fecha_nacimiento
        existing.posicion = posicion
        existing.nacionalidad = nacionalidad
        if foto_file is not None:
            existing.foto = foto_file
        session.add(existing)
        session.commit()
        session.refresh(existing)
        print(f"[seed] Actualizado: {existing.nombre} {existing.apellido} (id={existing.jugador_id})")
        return existing
    else:
        jugador = Jugador(
            nombre=nombre,
            apellido=apellido,
            fecha_nacimiento=fecha_nacimiento,
            posicion=posicion,
            nacionalidad=nacionalidad,
            equipo_id=equipo_id,
            foto=foto_file,
        )
        session.add(jugador)
        session.commit()
        session.refresh(jugador)
        print(f"[seed] Creado: {jugador.nombre} {jugador.apellido} (id={jugador.jugador_id})")
        return jugador


def main() -> None:
    SQLModel.metadata.create_all(engine)

    # Base path de las fotos
    base_path = Path(r"C:\Users\eposa\OneDrive\Escritorio\jugadores")

    # Configuración de jugadores por equipo
    # Formato: {"Equipo": [{"archivo": "...", "nombre": "...", "apellido": "...", "posicion": ..., "nacionalidad": "...", "fecha_nacimiento": date(año, mes, día)}]}
    jugadores_config = {
        "Santa Fe": [
            {"archivo": "Hugo Rodallega.png", "nombre": "Hugo", "apellido": "Rodallega", "posicion": PosicionJugador.DELANTERO, "nacionalidad": "Colombia", "fecha_nacimiento": date(1985, 7, 25)},
            {"archivo": "Jorge Arias.png", "nombre": "Jorge", "apellido": "Arias", "posicion": PosicionJugador.DEFENSOR, "nacionalidad": "Colombia", "fecha_nacimiento": date(1991, 7, 21)},
            {"archivo": "Stiven Vega.png", "nombre": "Stiven", "apellido": "Vega", "posicion": PosicionJugador.MEDIOCAMPISTA, "nacionalidad": "Colombia", "fecha_nacimiento": date(1997, 2, 14)},
            {"archivo": "Beckham Castro.png", "nombre": "Beckham", "apellido": "Castro", "posicion": PosicionJugador.MEDIOCAMPISTA, "nacionalidad": "Colombia", "fecha_nacimiento": date(1996, 4, 10)},
            {"archivo": "Jorge Soto.png", "nombre": "Jorge", "apellido": "Soto", "posicion": PosicionJugador.PORTERO, "nacionalidad": "Colombia", "fecha_nacimiento": date(1990, 3, 15)},
        ],
        "Junior": [
            {"archivo": "Carlos Bacca.png", "nombre": "Carlos", "apellido": "Bacca", "posicion": PosicionJugador.DELANTERO, "nacionalidad": "Colombia", "fecha_nacimiento": date(1986, 9, 8)},
            {"archivo": "Teofilo Gutierrez.png", "nombre": "Teófilo", "apellido": "Gutiérrez", "posicion": PosicionJugador.DELANTERO, "nacionalidad": "Colombia", "fecha_nacimiento": date(1985, 5, 17)},
            {"archivo": "Didier Moreno.png", "nombre": "Didier", "apellido": "Moreno", "posicion": PosicionJugador.MEDIOCAMPISTA, "nacionalidad": "Colombia", "fecha_nacimiento": date(1992, 8, 20)},
            {"archivo": "Yimmi Chará.png", "nombre": "Yimmi", "apellido": "Chará", "posicion": PosicionJugador.MEDIOCAMPISTA, "nacionalidad": "Colombia", "fecha_nacimiento": date(1991, 4, 2)},
            {"archivo": "Edwin Herrera.png", "nombre": "Edwin", "apellido": "Herrera", "posicion": PosicionJugador.DEFENSOR, "nacionalidad": "Colombia", "fecha_nacimiento": date(1992, 1, 13)},
        ],
        "Independiente Medellín": [
            {"archivo": "Jan Lucumi.png", "nombre": "Jan", "apellido": "Lucumí", "posicion": PosicionJugador.MEDIOCAMPISTA, "nacionalidad": "Colombia", "fecha_nacimiento": date(1998, 5, 10)},
            {"archivo": "Omar Bertel.png", "nombre": "Omar", "apellido": "Bertel", "posicion": PosicionJugador.DEFENSOR, "nacionalidad": "Colombia", "fecha_nacimiento": date(1998, 8, 22)},
            {"archivo": "Cristian Barrios.png", "nombre": "Cristian", "apellido": "Barrios", "posicion": PosicionJugador.MEDIOCAMPISTA, "nacionalidad": "Colombia", "fecha_nacimiento": date(2000, 3, 5)},
            {"archivo": "Luis Ramos.png", "nombre": "Luis", "apellido": "Ramos", "posicion": PosicionJugador.PORTERO, "nacionalidad": "Colombia", "fecha_nacimiento": date(1996, 7, 18)},
            {"archivo": "Esneyder Mena.png", "nombre": "Esneyder", "apellido": "Mena", "posicion": PosicionJugador.DELANTERO, "nacionalidad": "Colombia", "fecha_nacimiento": date(1999, 11, 12)},
        ],
        "Atlético Nacional": [
            {"archivo": "Jarlan Barrera.png", "nombre": "Jarlan", "apellido": "Barrera", "posicion": PosicionJugador.MEDIOCAMPISTA, "nacionalidad": "Colombia", "fecha_nacimiento": date(1993, 10, 12)},
            {"archivo": "Alexis Serna.png", "nombre": "Alexis", "apellido": "Serna", "posicion": PosicionJugador.MEDIOCAMPISTA, "nacionalidad": "Colombia", "fecha_nacimiento": date(1997, 6, 25)},
            {"archivo": "Jaime Alvarado.png", "nombre": "Jaime", "apellido": "Alvarado", "posicion": PosicionJugador.MEDIOCAMPISTA, "nacionalidad": "Ecuador", "fecha_nacimiento": date(1992, 4, 8)},
            {"archivo": "Bryan León.png", "nombre": "Bryan", "apellido": "León", "posicion": PosicionJugador.DELANTERO, "nacionalidad": "Colombia", "fecha_nacimiento": date(1999, 1, 30)},
            {"archivo": "David Ospina.png", "nombre": "David", "apellido": "Ospina", "posicion": PosicionJugador.PORTERO, "nacionalidad": "Colombia", "fecha_nacimiento": date(1988, 8, 31)},
        ],
        "Millonarios": [
            {"archivo": "David Silva.png", "nombre": "David", "apellido": "Silva", "posicion": PosicionJugador.MEDIOCAMPISTA, "nacionalidad": "Colombia", "fecha_nacimiento": date(1987, 9, 2)},
            {"archivo": "Leonardo Castro.png", "nombre": "Leonardo", "apellido": "Castro", "posicion": PosicionJugador.DELANTERO, "nacionalidad": "Colombia", "fecha_nacimiento": date(1989, 2, 2)},
            {"archivo": "Daniel Torres.png", "nombre": "Daniel", "apellido": "Torres", "posicion": PosicionJugador.MEDIOCAMPISTA, "nacionalidad": "Colombia", "fecha_nacimiento": date(1993, 5, 13)},
            {"archivo": "Alexis Zapata.png", "nombre": "Alexis", "apellido": "Zapata", "posicion": PosicionJugador.PORTERO, "nacionalidad": "Colombia", "fecha_nacimiento": date(1995, 12, 7)},
            {"archivo": "Elvis Perlaza.png", "nombre": "Elvis", "apellido": "Perlaza", "posicion": PosicionJugador.DEFENSOR, "nacionalidad": "Colombia", "fecha_nacimiento": date(1995, 3, 22)},
        ],
        "América de Cali": [
            {"archivo": "Andres Sarmiento.png", "nombre": "Andrés", "apellido": "Sarmiento", "posicion": PosicionJugador.DELANTERO, "nacionalidad": "Colombia", "fecha_nacimiento": date(2001, 7, 15)},
            {"archivo": "Matheus Uribe.png", "nombre": "Matheus", "apellido": "Uribe", "posicion": PosicionJugador.MEDIOCAMPISTA, "nacionalidad": "Brasil", "fecha_nacimiento": date(1991, 3, 28)},
            {"archivo": "Alfredo Morelos.png", "nombre": "Alfredo", "apellido": "Morelos", "posicion": PosicionJugador.DELANTERO, "nacionalidad": "Colombia", "fecha_nacimiento": date(1996, 6, 21)},
            {"archivo": "Edwin Cardona.png", "nombre": "Edwin", "apellido": "Cardona", "posicion": PosicionJugador.MEDIOCAMPISTA, "nacionalidad": "Colombia", "fecha_nacimiento": date(1992, 12, 8)},
            {"archivo": "Santiago Mosquera.png", "nombre": "Santiago", "apellido": "Mosquera", "posicion": PosicionJugador.DEFENSOR, "nacionalidad": "Colombia", "fecha_nacimiento": date(1999, 9, 4)},
        ],
    }

    with Session(engine) as session:
        for equipo_nombre, jugadores in jugadores_config.items():
            # Mapear nombre de carpeta
            carpeta_map = {
                "Santa Fe": "Santa fe",
                "Junior": "Junior",
                "Independiente Medellín": "Medellin",
                "Atlético Nacional": "Nacional",
                "Millonarios": "Millonarios",
                "América de Cali": "America",
            }
            carpeta_nombre = carpeta_map.get(equipo_nombre, equipo_nombre)
            carpeta_path = base_path / carpeta_nombre

            equipo_id = get_equipo_id_by_name(session, equipo_nombre)
            if not equipo_id:
                print(f"[seed] ERROR: No se encontró el equipo '{equipo_nombre}' en la BD. Saltando jugadores.")
                continue

            for jugador_data in jugadores:
                foto_path = carpeta_path / jugador_data["archivo"]
                upsert_jugador(
                    session,
                    nombre=jugador_data["nombre"],
                    apellido=jugador_data["apellido"],
                    fecha_nacimiento=jugador_data["fecha_nacimiento"],
                    posicion=jugador_data["posicion"],
                    nacionalidad=jugador_data["nacionalidad"],
                    equipo_id=equipo_id,
                    foto_path=str(foto_path) if foto_path.exists() else None,
                )


if __name__ == "__main__":
    main()
