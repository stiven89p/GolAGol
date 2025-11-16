document.addEventListener("DOMContentLoaded", () => {
    const lista = document.getElementById("partidos-lista");

    const cargarPartidos = async () => {
        try {
            const res = await fetch("/partidos");
            if (!res.ok) throw new Error("Error al obtener partidos");

            const partidos = await res.json();
            
            // Ordenar por fecha y hora, más recientes primero
            partidos.sort((a, b) => {
                const dateA = new Date(a.fecha + (a.hora ? ' ' + a.hora : ''));
                const dateB = new Date(b.fecha + (b.hora ? ' ' + b.hora : ''));
                return dateB - dateA;
            });
            
            lista.innerHTML = "";

            const activeContainer = document.getElementById("partidos-lista");
            const activeId = activeContainer && activeContainer.dataset && activeContainer.dataset.activeId
                ? Number(activeContainer.dataset.activeId)
                : null;

            partidos.forEach(p => {
                const card = document.createElement("div");
                card.className = "match-card";
                card.dataset.id = p.partido_id;

                const row = document.createElement("div");
                row.className = "match-row";

                const imgLocal = document.createElement("img");
                imgLocal.className = "escudo local";
                imgLocal.src = p.equipo_local_logo ? `/static/img/${p.equipo_local_logo}` : "/static/img/default_logo.png";

                const imgVisitante = document.createElement("img");
                imgVisitante.className = "escudo visitante";
                imgVisitante.src = p.equipo_visitante_logo ? `/static/img/${p.equipo_visitante_logo}` : "/static/img/default_logo.png";

                const marcador = document.createElement("div");
                marcador.className = "marcador";

                const local = document.createElement("span");
                local.className = "eq-name";
                local.textContent = p.equipo_local_nombre;

                const centro = document.createElement("strong");
                centro.className = "resultado";
                centro.textContent = p.estado !== "PROGRAMADO"
                    ? `${p.goles_local} - ${p.goles_visitante}`
                    : "VS";

                const visitante = document.createElement("span");
                visitante.className = "eq-name";
                visitante.textContent = p.equipo_visitante_nombre;

                marcador.append(local, centro, visitante);
                row.append(imgLocal, marcador, imgVisitante);

                const fecha = document.createElement("small");
                fecha.className = "fecha-hora";

                const d = new Date(p.fecha);
                fecha.textContent = p.hora
                    ? `${d.toLocaleDateString("es-ES")} • ${p.hora}`
                    : d.toLocaleDateString("es-ES");

                const lugar = document.createElement("p");
                lugar.className = "lugar";
                if (p.lugar) lugar.textContent = `📍 ${p.lugar}`;

                card.append(row, fecha, lugar);
                if (activeId && Number(p.partido_id) === activeId) {
                    card.classList.add('active');
                }
                // Navegar al detalle del partido al hacer click
                card.style.cursor = 'pointer';
                card.addEventListener('click', () => {
                    if (p.partido_id != null) {
                        window.location.href = `/partido/${encodeURIComponent(p.partido_id)}`;
                    }
                });
                lista.appendChild(card);
            });

        } catch (err) {
            console.error(err);
            lista.innerHTML = `<p>Error al cargar los partidos</p>`;
        }
    };

    cargarPartidos();
});
