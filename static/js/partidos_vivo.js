document.addEventListener("DOMContentLoaded", () => {
    const vivoLista = document.getElementById("partidos-vivo-lista");
    if (!vivoLista) return;

    const renderVivo = (partidos) => {
        vivoLista.innerHTML = "";
        if (!partidos.length) {
            vivoLista.innerHTML = '<p class="no-vivo">No hay partidos en vivo</p>';
            return;
        }
        partidos.forEach(p => {
            const card = document.createElement("div");
            card.className = "match-card vivo";
            card.dataset.id = p.partido_id;

            const row = document.createElement("div");
            row.className = "match-row";

            const imgLocal = document.createElement("img");
            imgLocal.className = "escudo local";
            imgLocal.src = p.equipo_local_logo ? (/^https?:\/\//.test(p.equipo_local_logo) ? p.equipo_local_logo : `/static/img/${p.equipo_local_logo}`) : "/static/img/default_logo.png";

            const imgVisitante = document.createElement("img");
            imgVisitante.className = "escudo visitante";
            imgVisitante.src = p.equipo_visitante_logo ? (/^https?:\/\//.test(p.equipo_visitante_logo) ? p.equipo_visitante_logo : `/static/img/${p.equipo_visitante_logo}`) : "/static/img/default_logo.png";

            const marcador = document.createElement("div");
            marcador.className = "marcador vivo";

            const local = document.createElement("span");
            local.className = "eq-name";
            local.textContent = p.equipo_local_nombre;

            const centro = document.createElement("strong");
            centro.className = "resultado vivo";
            centro.textContent = `${p.goles_local} - ${p.goles_visitante}`;

            const visitante = document.createElement("span");
            visitante.className = "eq-name";
            visitante.textContent = p.equipo_visitante_nombre;

            marcador.append(local, centro, visitante);
            row.append(imgLocal, marcador, imgVisitante);

            const meta = document.createElement("small");
            meta.className = "meta live-badge";
            meta.textContent = "🔴 EN VIVO";

            card.append(row, meta);
            card.style.cursor = 'pointer';
            card.addEventListener('click', () => {
                if (p.partido_id != null) {
                    window.location.href = `/partido/${encodeURIComponent(p.partido_id)}`;
                }
            });
            vivoLista.appendChild(card);
        });
    };

    const cargarVivo = async () => {
        try {
            // Usar el endpoint sin espacios para evitar problemas de URL
            const res = await fetch("/partidos/en%20curso/");
            if (!res.ok) throw new Error("Error al obtener partidos en vivo");
            const partidos = await res.json();
            renderVivo(partidos);
        } catch (err) {
            console.error(err);
            vivoLista.innerHTML = `<p>Error al cargar partidos en vivo</p>`;
        }
    };

    cargarVivo();
    // Opcional: recargar cada 30s
    setInterval(cargarVivo, 30000);
});
