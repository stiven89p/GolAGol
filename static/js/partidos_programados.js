document.addEventListener("DOMContentLoaded", () => {
    const lista = document.getElementById("partidos-lista");
    const ultimosLista = document.getElementById("ultimos-lista");
    const isDetailPage = !!document.querySelector('.match-detail');
    const toggleBtn = document.getElementById("toggle-partidos");

    let showAll = false;
    let programadosCache = [];
    let finalizadosCache = [];

    const renderProgramados = () => {
        if (!lista) return;
        lista.innerHTML = "";

        const activeIdAttr = lista && lista.dataset && lista.dataset.activeId
            ? Number(lista.dataset.activeId)
            : null;

        // En página de detalle mostramos FINALIZADOS en el sidebar
        const source = isDetailPage ? finalizadosCache : programadosCache;
        const data = (!isDetailPage && showAll) ? source : source.slice(0, 5);

        data.forEach(p => {
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
            if (activeIdAttr && Number(p.partido_id) === activeIdAttr) {
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

        // Actualizar texto del botón (solo aplica cuando NO es detalle)
        if (!isDetailPage && toggleBtn) toggleBtn.textContent = showAll ? 'Ver menos' : 'Ver todos';
    };
    
    const renderUltimos = () => {
        if (!ultimosLista) return;
        ultimosLista.innerHTML = "";

        const data = finalizadosCache.slice(0, 5);

        data.forEach(p => {
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
            centro.textContent = `${p.goles_local ?? 0} - ${p.goles_visitante ?? 0}`;

            const visitante = document.createElement("span");
            visitante.className = "eq-name";
            visitante.textContent = p.equipo_visitante_nombre;

            marcador.append(local, centro, visitante);
            row.append(imgLocal, marcador, imgVisitante);

            const fecha = document.createElement("small");
            fecha.className = "fecha-hora";

            const d = new Date(p.fecha);
            fecha.textContent = d.toLocaleDateString("es-ES");

            const lugar = document.createElement("p");
            lugar.className = "lugar";
            if (p.lugar) lugar.textContent = `📍 ${p.lugar}`;

            card.append(row, fecha, lugar);
            // Click navega al detalle del partido
            card.style.cursor = 'pointer';
            card.addEventListener('click', () => {
                if (p.partido_id != null) {
                    window.location.href = `/partido/${encodeURIComponent(p.partido_id)}`;
                }
            });

            ultimosLista.appendChild(card);
        });
    };

    const cargarPartidos = async () => {
        try {

            // Cargar partidos programados
            const resProgramados = await fetch("/partidos/programado/");
            if (!resProgramados.ok) throw new Error("Error al obtener partidos programados");
            const programados = await resProgramados.json();

            // Cargar partidos finalizados
            const resFinalizados = await fetch("/partidos/finalizado/");
            if (!resFinalizados.ok) throw new Error("Error al obtener partidos finalizados");
            const finalizados = await resFinalizados.json();

            // Ordenar por fecha y hora
            const sortDesc = (a, b) => {
                const dateA = new Date(a.fecha + (a.hora ? ' ' + a.hora : ''));
                const dateB = new Date(b.fecha + (b.hora ? ' ' + b.hora : ''));
                return dateB - dateA; // más recientes primero
            };

            programados.sort(sortDesc);
            finalizados.sort(sortDesc);

            programadosCache = programados;
            finalizadosCache = finalizados;

            // En home renderizamos programados (y 'ultimos' si existe la sección)
            // En detalle, el sidebar usa finalizados así que reusamos renderProgramados con isDetailPage
            renderProgramados();
            if (ultimosLista) renderUltimos();
        } catch (err) {
            console.error(err);
            lista.innerHTML = `<p>Error al cargar los partidos</p>`;
            if (ultimosLista) ultimosLista.innerHTML = `<p>Error al cargar los partidos</p>`;
        }
    };

    if (toggleBtn && !isDetailPage) {
        toggleBtn.addEventListener('click', () => {
            showAll = !showAll;
            renderProgramados();
        });
    }

    cargarPartidos();
});
