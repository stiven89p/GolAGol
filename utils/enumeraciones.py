from enum import Enum

class TipoEvento(Enum):
    GOL = "gol"
    ASISTENCIA = "asistencia"
    SUSTITUCION = "sustitucion"
    TARJETA_AMARILLA = "tarjeta_amarilla"
    TARJETA_ROJA = "tarjeta_roja"