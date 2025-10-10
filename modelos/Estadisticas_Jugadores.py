from typing import Optional
from sqlmodel import SQLModel, Field

class Estadisticas_JBase(SQLModel):
    jugador_id: int = Field(foreign_key="jugador.jugador_id", nullable=False, description="ID del jugador asociado")
    temporada: int = Field(foreign_key="temporada.temporada_id",nullable=False, description="Temporada de la estadística (e.g., '2023/2024')")
    equipo_id: Optional[int] = Field(foreign_key="equipo.equipo_id", nullable=True, description="ID del equipo asociado en esta temporada")
    partidos_jugados: int = Field(default=0, nullable=False, description="Número de partidos jugados en la temporada")
    goles: int = Field(default=0, nullable=False, description="Número de goles anotados en la temporada")
    asistencias: int = Field(default=0, nullable=False, description="Número de asistencias en la temporada")
    tarjetas_amarillas: int = Field(default=0, nullable=False, description="Número de tarjetas amarillas recibidas en la temporada")
    tarjetas_rojas: int = Field(default=0, nullable=False, description="Número de tarjetas rojas recibidas en la temporada")

class Estadisticas_J(Estadisticas_JBase , table=True):
    id_estadistica: Optional[int] = Field(default=None, primary_key=True)
    pass

class EstadisticasCrear(Estadisticas_JBase):
    pass

class EstadisticasActualizar(SQLModel):
    jugador_id: Optional[int] = None
    temporada: Optional[str] = None
    equipo_id: Optional[int] = None
    partidos_jugados: Optional[int] = None
    goles: Optional[int] = None
    asistencias: Optional[int] = None
    tarjetas_amarillas: Optional[int] = None
    tarjetas_rojas: Optional[int] = None

