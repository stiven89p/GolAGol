document.addEventListener("DOMContentLoaded", () => {
    const tbody = document.getElementById("tabla-body");
    const TEMPORADA_ID = 1;  // <-- CAMBIA ESTO SEGÚN TU TEMPORADA

    const cargarTabla = async () => {
        try {
            const res = await fetch(`/estadisticas_equipos/temporada/${TEMPORADA_ID}`);

            if (!res.ok) throw new Error("No se pudo obtener las estadísticas");

            const data = await res.json();

            // ordenar posiciones por puntos > diferencia de gol > goles a favor
            data.sort((a, b) => {
                if (b.puntos !== a.puntos) return b.puntos - a.puntos;
                const difA = a.goles_favor - a.goles_contra;
                const difB = b.goles_favor - b.goles_contra;
                if (difB !== difA) return difB - difA;
                return b.goles_favor - a.goles_favor;
            });

            tbody.innerHTML = "";

            data.forEach((team, index) => {
                const tr = document.createElement("tr");

                tr.innerHTML = `
                    <td>${index + 1}</td>
                    <td style="display:flex;align-items:center;gap:10px;">
                        <img src="/static/img/${team.equipo_logo}" 
                             onerror="this.src='/static/img/default_logo.png'"
                             style="width:28px;height:28px;object-fit:contain;">
                    </td>
                    <td>${team.partidos_jugados}</td>
                    <td>${team.victorias}</td>
                    <td>${team.empates}</td>
                    <td>${team.derrotas}</td>
                    <td>${team.goles_favor}</td>
                    <td>${team.goles_contra}</td>
                    <td><strong>${team.puntos}</strong></td>
                `;

                tbody.appendChild(tr);
            });

        } catch (err) {
            console.error(err);
            tbody.innerHTML = `<tr><td colspan="9">Error al cargar la tabla</td></tr>`;
        }
    };

    cargarTabla();
});
