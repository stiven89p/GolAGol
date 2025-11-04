from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_crear_equipos():
    equipos = [
        {
            "nombre": "Millonarios",
            "ciudad": "Bogotá",
            "estadio": "El Campín",
            "anio_fundacion": 1946,
            "titulos": 16
        },
        {
            "nombre": "Santa Fe",
            "ciudad": "Bogotá",
            "estadio": "El Campín",
            "anio_fundacion": 1941,
            "titulos": 10
        },
        {
            "nombre": "Atlético Nacional",
            "ciudad": "Medellín",
            "estadio": "Atanasio Girardot",
            "anio_fundacion": 1947,
            "titulos": 17
        },
        {
            "nombre": "Deportivo Cali",
            "ciudad": "Cali",
            "estadio": "Palmaseca",
            "anio_fundacion": 1912,
            "titulos": 10
        },
        {
            "nombre": "Junior",
            "ciudad": "Barranquilla",
            "estadio": "Metropolitano",
            "anio_fundacion": 1924,
            "titulos": 9
        }
    ]

    for equipo in equipos:
        response = client.post("/equipos/", data=equipo)
        assert response.status_code == 200, f"Error creando equipo: {equipo['nombre']}"
        result = response.json()
        assert result["nombre"] == equipo["nombre"]
        assert result["ciudad"] == equipo["ciudad"]

# python
def test_crear_un_jugador():
    mapping_posicion = {
        "Portero": "portero",
        "Defensa": "defensor",
        "Mediocampista": "mediocampista",
        "Delantero": "delantero",
    }

    jugador = {
        "nombre": "Prueba",
        "apellido": "Jugador",
        "posicion": "Portero",
        "nacionalidad": "Colombiana",
        "fecha_nacimiento": "1995-01-01",
        "equipo_id": 1,
    }

    jugador_data = {
        "nombre": jugador["nombre"],
        "apellido": jugador["apellido"],
        "fecha_nacimiento": jugador["fecha_nacimiento"],
        "posicion": mapping_posicion[jugador["posicion"]],
        "nacionalidad": jugador["nacionalidad"],
        "equipo_id": str(jugador["equipo_id"]),  # enviar como string en formulario
    }

    response = client.post("/jugadores/", data=jugador_data)
    assert response.status_code in (200, 201), f"Error creando jugador: {response.status_code} - {response.text}"
    result = response.json()
    assert result.get("nombre") == jugador["nombre"]
    assert int(result.get("equipo_id")) == jugador["equipo_id"]


# python
def test_crear_jugadores():
    mapping_posicion = {
        "Portero": "portero",
        "Defensa": "defensor",
        "Mediocampista": "mediocampista",
        "Delantero": "delantero",
    }

    jugadores_por_equipo = {
        1: [  # Millonarios
            {"nombre": "Álvaro", "apellido": "Montero", "posicion": "Portero", "nacionalidad": "Colombiana"},
            {"nombre": "Andrés", "apellido": "Llinás", "posicion": "Defensa", "nacionalidad": "Colombiana"},
            {"nombre": "David", "apellido": "Mackalister", "posicion": "Mediocampista", "nacionalidad": "Colombiana"},
            {"nombre": "Leonardo", "apellido": "Castro", "posicion": "Delantero", "nacionalidad": "Colombiana"},
            {"nombre": "Juan", "apellido": "Pereira", "posicion": "Defensa", "nacionalidad": "Colombiana"},
        ],
        2: [  # Santa Fe
            {"nombre": "Anthony", "apellido": "Silva", "posicion": "Portero", "nacionalidad": "Paraguaya"},
            {"nombre": "Carlos", "apellido": "Ramírez", "posicion": "Defensa", "nacionalidad": "Colombiana"},
            {"nombre": "Fabián", "apellido": "Sambueza", "posicion": "Mediocampista", "nacionalidad": "Argentina"},
            {"nombre": "José", "apellido": "Enamorado", "posicion": "Delantero", "nacionalidad": "Colombiana"},
            {"nombre": "Wilson", "apellido": "Morelo", "posicion": "Delantero", "nacionalidad": "Colombiana"},
        ],
        3: [  # Atlético Nacional
            {"nombre": "Sergio", "apellido": "Rochet", "posicion": "Portero", "nacionalidad": "Uruguaya"},
            {"nombre": "Juan", "apellido": "Duque", "posicion": "Mediocampista", "nacionalidad": "Colombiana"},
            {"nombre": "Eric", "apellido": "Ramírez", "posicion": "Delantero", "nacionalidad": "Venezolana"},
            {"nombre": "Daniel", "apellido": "Mantilla", "posicion": "Mediocampista", "nacionalidad": "Colombiana"},
            {"nombre": "Cristian", "apellido": "Castro", "posicion": "Defensa", "nacionalidad": "Colombiana"},
        ],
        4: [  # Deportivo Cali
            {"nombre": "Kevin", "apellido": "Dawson", "posicion": "Portero", "nacionalidad": "Uruguaya"},
            {"nombre": "Jhon", "apellido": "Vásquez", "posicion": "Delantero", "nacionalidad": "Colombiana"},
            {"nombre": "Luis", "apellido": "Sandoval", "posicion": "Delantero", "nacionalidad": "Colombiana"},
            {"nombre": "Germán", "apellido": "Mera", "posicion": "Defensa", "nacionalidad": "Colombiana"},
            {"nombre": "Juan", "apellido": "Frías", "posicion": "Mediocampista", "nacionalidad": "Colombiana"},
        ],
        5: [  # Junior
            {"nombre": "Sebastián", "apellido": "Viera", "posicion": "Portero", "nacionalidad": "Uruguaya"},
            {"nombre": "Víctor", "apellido": "Cantillo", "posicion": "Mediocampista", "nacionalidad": "Colombiana"},
            {"nombre": "Carlos", "apellido": "Bacca", "posicion": "Delantero", "nacionalidad": "Colombiana"},
            {"nombre": "Homer", "apellido": "Martínez", "posicion": "Defensa", "nacionalidad": "Colombiana"},
            {"nombre": "Johan", "apellido": "Bocanegra", "posicion": "Mediocampista", "nacionalidad": "Colombiana"},
        ],
    }

    for equipo_id, jugadores in jugadores_por_equipo.items():
        for jugador in jugadores:
            posicion_enum = mapping_posicion[jugador["posicion"]]
            jugador_data = {
                "nombre": jugador["nombre"],
                "apellido": jugador["apellido"],
                "fecha_nacimiento": "1995-01-01",
                "posicion": posicion_enum,
                "nacionalidad": jugador["nacionalidad"],
                "equipo_id": str(equipo_id),  # Form fields deben ser strings en algunos clientes
            }
            response = client.post("/jugadores/", data=jugador_data)
            assert response.status_code in (200, 201), f"Error creando jugador {jugador['nombre']}: {response.status_code} - {response.text}"
            result = response.json()
            assert "nombre" in result and "equipo_id" in result
            assert result["nombre"] == jugador["nombre"]
            assert int(result["equipo_id"]) == equipo_id

# python
def test_crear_temporada():
    temporada = {
        "fecha_inicio": "2025-07-01",
        "fecha_fin": "2026-06-30"
    }

    response = client.post("/temporadas/", json=temporada)
    assert response.status_code in (200, 201), f"Error creando temporada: {response.status_code} - {response.text}"
    result = response.json()

    # Validaciones mínimas
    assert "temporada_id" in result, f"Falta 'temporada_id' en respuesta: {result}"
    assert result.get("nombre") == temporada["nombre"]
    assert result.get("fecha_inicio") == temporada["fecha_inicio"]
    assert result.get("fecha_fin") == temporada["fecha_fin"]