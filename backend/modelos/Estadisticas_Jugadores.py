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
    minutos_jugados: int = Field(default=0, nullable=False, description="Número de minutos jugados en la temporada")
    balones_perdidos: int = Field(default=0, nullable=False, description="Número de balones perdidos en la temporada")
    penales_cobrados: int = Field(default=0, nullable=False, description="Número de penales cobrados en la temporada")
    penales_fallados: int = Field(default=0, nullable=False, description="Número de penales fallados en la temporada")
    tiros_totales: int = Field(default=0, nullable=False, description="Número de tiros totales en la temporada")
    tiros_a_puerta: int = Field(default=0, nullable=False, description="Número de tiros a puerta en la temporada")
    entradas: int = Field(default=0, nullable=False, description="Número de entradas realizadas en la temporada")
    intercepciones: int = Field(default=0, nullable=False, description="Número de intercepciones realizadas en la temporada")
    goles_contra: int = Field(default=0, nullable=False, description="Número de goles en contra recibidos en la temporada auto-goles")
    goles_concedidos: int = Field(default=0, nullable=False, description="Número de goles concedidos en la temporada (para porteros)")
    paradas: int = Field(default=0, nullable=False, description="Número de paradas realizadas en la temporada (para porteros)")
    penales_tapados: int = Field(default=0, nullable=False, description="Número de penales tapados en la temporada (para porteros)")

class Estadisticas_J(Estadisticas_JBase , table=True):
    id_estadistica: Optional[int] = Field(default=None, primary_key=True)


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

