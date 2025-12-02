document.addEventListener("DOMContentLoaded", () => {
    const tbody = document.getElementById("goleadores-body");

    const cargarGoleadores = async () => {
        try {
            // Asumiendo temporada_id = 1 (puedes hacerlo dinámico después)
            const res = await fetch("/estadisticas_jugadores/temporada/1/goleadores?limit=5");
            if (!res.ok) throw new Error("Error al obtener goleadores");

            const goleadores = await res.json();
            // Forzar tope local a 5 por si el backend ignora el parámetro
            const lista = Array.isArray(goleadores) ? goleadores.slice(0, 5) : [];
            
            if (lista.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" class="loading">No hay goleadores registrados</td></tr>';
                return;
            }

            tbody.innerHTML = "";

            lista.forEach(g => {
                const tr = document.createElement("tr");

                const tdPos = document.createElement("td");
                tdPos.textContent = g.posicion;

                const tdJugador = document.createElement("td");
                tdJugador.style.textAlign = "left";
                tdJugador.style.display = "flex";
                tdJugador.style.alignItems = "center";
                tdJugador.style.gap = "8px";

                const imgJugador = document.createElement("img");
                imgJugador.src = g.jugador_foto ? `/static/img/${g.jugador_foto}` : '/static/img/default-player.png';
                imgJugador.alt = `${g.jugador_nombre} ${g.jugador_apellido}`;
                imgJugador.style.width = "32px";
                imgJugador.style.height = "32px";
                imgJugador.style.borderRadius = "50%";
                imgJugador.style.objectFit = "cover";
                imgJugador.onerror = function() {
                    if (this.src !== '/static/img/default-player.png') {
                        this.src = '/static/img/default-player.png';
                    }
                };

                // Solo mostrar el nombre del jugador como span, sin link
                const spanNombre = document.createElement("span");
                spanNombre.textContent = `${g.jugador_nombre} ${g.jugador_apellido}`;
                tdJugador.append(imgJugador, spanNombre);

                const tdEquipo = document.createElement("td");
                tdEquipo.textContent = g.equipo_nombre;
                tdEquipo.style.textAlign = "left";

                const tdGoles = document.createElement("td");
                tdGoles.textContent = g.goles;
                tdGoles.style.fontWeight = "bold";
                tdGoles.style.color = "#58a6ff";

                tr.append(tdPos, tdJugador, tdEquipo, tdGoles);
                tbody.appendChild(tr);
            });

        } catch (err) {
            console.error(err);
            tbody.innerHTML = '<tr><td colspan="4" style="color: #f85149;">Error al cargar goleadores</td></tr>';
        }
    };

    cargarGoleadores();
});
