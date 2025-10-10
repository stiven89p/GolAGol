from typing import Optional
from sqlmodel import SQLModel, Field

class Estadisticas_EBase(SQLModel):
    equipo_id: int = Field(foreign_key="equipo.equipo_id", nullable=False, description="ID del equipo asociado")
    temporada: int = Field(foreign_key="temporada.temporada_id", description="Temporada de la estadística (e.g., '2023/2024')")
    partidos_jugados: int = Field(default=0, nullable=False, description="Número de partidos jugados en la temporada")
    victorias: int = Field(default=0, nullable=False, description="Número de victorias en la temporada")
    empates: int = Field(default=0, nullable=False, description="Número de empates en la temporada")
    derrotas: int = Field(default=0, nullable=False, description="Número de derrotas en la temporada")
    goles_favor: int = Field(default=0, nullable=False, description="Número de goles a favor en la temporada")
    goles_contra: int = Field(default=0, nullable=False, description="Número de goles en contra en la temporada")
    puntos: int = Field(default=0, nullable=False, description="Número de puntos acumulados en la temporada")

class Estadisticas_E(Estadisticas_EBase , table=True):
    id_estadistica: Optional[int] = Field(default=None, primary_key=True)
    pass

class EstadisticasCrear(Estadisticas_EBase):
    pass

class EstadisticasActualizar(SQLModel):
    equipo_id: Optional[int] = None
    temporada: Optional[str] = None
    partidos_jugados: Optional[int] = None
    victorias: Optional[int] = None
    empates: Optional[int] = None
    derrotas: Optional[int] = None
    goles_favor: Optional[int] = None
    goles_contra: Optional[int] = None
    puntos: Optional[int] = None