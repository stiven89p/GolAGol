from enum import Enum

class TipoEvento(Enum):
    GOL = "gol"
    SUSTITUCION = "sustitucion"
    TARJETA_AMARILLA = "tarjeta_amarilla"
    TARJETA_ROJA = "tarjeta_roja"

class EstadoPartidos(Enum):
    PROGRAMADO = "programado"
    EN_CURSO = "en curso"
    FINALIZADO = "finalizado"
    SUSPENDIDO = "suspendido"
    CANCELADO = "cancelado"

class PosicionJugador(Enum):
    PORTERO = "portero"
    DEFENSOR = "defensor"
    MEDIOCAMPISTA = "mediocampista"
    DELANTERO = "delantero"