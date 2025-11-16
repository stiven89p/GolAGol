import os
import sys
import uuid
import shutil
from pathlib import Path
from typing import Optional, Iterable

# Asegura que el proyecto raíz esté en sys.path al ejecutar este script directamente
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlmodel import Session, SQLModel, select

# Usa el engine real configurado con variables de entorno (PostgreSQL por defecto)
from backend.db import engine
from backend.modelos.Equipos import Equipo

STATIC_IMG_DIR = Path("static/img")
STATIC_IMG_DIR.mkdir(parents=True, exist_ok=True)


def _safe_copy_logo(src_path: Optional[str]) -> Optional[str]:
    """Copia el archivo de logo a static/img y devuelve el nombre de archivo destino.
    Si la ruta origen no existe o es None, devuelve None sin fallar.
    """
    if not src_path:
        return None
    src = Path(src_path)
    if not src.exists() or not src.is_file():
        print(f"[seed] Aviso: logo no encontrado -> {src}")
        return None

    new_name = f"{uuid.uuid4().hex}_{src.name}"
    dest = STATIC_IMG_DIR / new_name
    with src.open("rb") as fsrc, dest.open("wb") as fdst:
        shutil.copyfileobj(fsrc, fdst)
    return new_name


def upsert_equipo(
    session: Session,
    *,
    nombre: str,
    ciudad: str,
    estadio: str,
    anio_fundacion: int,
    titulos: int = 0,
    logo_path: Optional[str] = None,
) -> Equipo:
    """Crea o actualiza un equipo por nombre. Copia logo si se provee ruta."""
    existing = session.exec(select(Equipo).where(Equipo.nombre == nombre)).first()
    logo_file = _safe_copy_logo(logo_path)

    if existing:
        existing.ciudad = ciudad
        existing.estadio = estadio
        existing.anio_fundacion = anio_fundacion
        existing.titulos = titulos
        existing.activo = True
        if logo_file is not None:
            existing.logo = logo_file
        session.add(existing)
        session.commit()
        session.refresh(existing)
        print(f"[seed] Actualizado: {existing.nombre} (id={existing.equipo_id})")
        return existing
    else:
        equipo = Equipo(
            nombre=nombre,
            ciudad=ciudad,
            estadio=estadio,
            anio_fundacion=anio_fundacion,
            titulos=titulos,
            logo=logo_file,
            activo=True,
        )
        session.add(equipo)
        session.commit()
        session.refresh(equipo)
        print(f"[seed] Creado: {equipo.nombre} (id={equipo.equipo_id})")
        return equipo


def seed_bulk(session: Session, items: Iterable[dict]) -> None:
    for item in items:
        upsert_equipo(session, **item)


def main() -> None:
    # Asegura tablas
    SQLModel.metadata.create_all(engine)

    # Configura aquí tus equipos y rutas locales de escudos
    equipos = [
        {
            "nombre": "Santa Fe",
            "ciudad": "Bogotá",
            "estadio": "El Campín",
            "anio_fundacion": 1941,
            "titulos": 9,
            "logo_path": r"C:\\Users\\eposa\\OneDrive\\Escritorio\\escudos\\santafe.png",
        },
        {
            "nombre": "Junior",
            "ciudad": "Barranquilla",
            "estadio": "Metropolitano",
            "anio_fundacion": 1924,
            "titulos": 9,
            "logo_path": r"C:\\Users\\eposa\\OneDrive\\Escritorio\\escudos\\junior.png",
        },
        {
            "nombre": "Independiente Medellín",
            "ciudad": "Medellín",
            "estadio": "Atanasio Girardot",
            "anio_fundacion": 1913,
            "titulos": 6,
            "logo_path": r"C:\\Users\\eposa\\OneDrive\\Escritorio\\escudos\\medelli n.png",
        },
        {
            "nombre": "América de Cali",
            "ciudad": "Cali",
            "estadio": "Pascual Guerrero",
            "anio_fundacion": 1927,
            "titulos": 15,
            "logo_path": r"C:\\Users\\eposa\\OneDrive\\Escritorio\\escudos\\merica.png",
        },
        {
            "nombre": "Millonarios",
            "ciudad": "Bogotá",
            "estadio": "El Campín",
            "anio_fundacion": 1946,
            "titulos": 16,
            "logo_path": r"C:\\Users\\eposa\\OneDrive\\Escritorio\\escudos\\millonarios.png",
        },
        {
            "nombre": "Atlético Nacional",
            "ciudad": "Medellín",
            "estadio": "Atanasio Girardot",
            "anio_fundacion": 1947,
            "titulos": 17,
            "logo_path": r"C:\\Users\\eposa\\OneDrive\\Escritorio\\escudos\\nacional.png",
        },
    ]

    with Session(engine) as session:
        seed_bulk(session, equipos)


if __name__ == "__main__":
    main()
