"""
Elimina todos los datos de todas las tablas de la base de datos.
Pide confirmación antes de proceder.

Uso: python tests/limpiar_bd.py
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from sqlmodel import SQLModel, Session, text
from backend.db import engine

import backend.modelos.Estadisticas_Jugadores
import backend.modelos.Estadisticas_Equipos
import backend.modelos.Eventos
import backend.modelos.Formaciones
import backend.modelos.Jugadores
import backend.modelos.Partidos
import backend.modelos.Equipos
import backend.modelos.Temporada

TABLAS = [
    "estadisticas_j",
    "estadisticas_e",
    "evento",
    "formacionjugador",
    "formacion",
    "jugador",
    "partido",
    "equipo",
    "temporada",
]


def main():
    print("ADVERTENCIA: Esto eliminará TODOS los datos de la base de datos.")
    confirmacion = input("Escribe 'CONFIRMAR' para continuar: ").strip()
    if confirmacion != "CONFIRMAR":
        print("Cancelado.")
        return

    with Session(engine) as session:
        for tabla in TABLAS:
            try:
                result = session.exec(text(f"DELETE FROM {tabla}"))
                session.commit()
                print(f"  OK   {tabla} ({result.rowcount} filas eliminadas)")
            except Exception as e:
                session.rollback()
                print(f"  ERR  {tabla}: {e}")

    print("\nBase de datos limpia.")


if __name__ == "__main__":
    main()
