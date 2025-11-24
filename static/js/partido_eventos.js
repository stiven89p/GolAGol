// Cargar y mostrar eventos del partido en timeline
async function cargarEventosPartido() {
    const container = document.getElementById('eventos-container');
    if (!container) return;

    try {
        const response = await fetch(`/eventos/partido/${partidoId}`);
        if (!response.ok) {
            container.innerHTML = '<p class="no-data">No hay eventos registrados para este partido</p>';
            return;
        }

        const eventos = await response.json();
        if (!eventos || eventos.length === 0) {
            container.innerHTML = '<p class="no-data">No hay eventos registrados</p>';
            return;
        }

        // Ordenar eventos por minuto
        eventos.sort((a, b) => a.minuto - b.minuto);

        // Agrupar por tiempo (primer tiempo / descanso / segundo tiempo)
        const primerTiempo = eventos.filter(e => e.minuto <= 45);
        const segundoTiempo = eventos.filter(e => e.minuto > 45);

        let html = '';

        // Primer tiempo
        if (primerTiempo.length > 0) {
            html += '<div class="tiempo-section"><h3>Primer Tiempo</h3>';
            html += renderEventos(primerTiempo);
            html += '</div>';
        }

        // Descanso
        if (primerTiempo.length > 0 && segundoTiempo.length > 0) {
            html += '<div class="descanso-marker">DESCANSO</div>';
        }

        // Segundo tiempo
        if (segundoTiempo.length > 0) {
            html += '<div class="tiempo-section"><h3>Segundo Tiempo</h3>';
            html += renderEventos(segundoTiempo);
            html += '</div>';
        }

        container.innerHTML = html;
    } catch (error) {
        console.error('Error cargando eventos:', error);
        container.innerHTML = '<p class="error">Error al cargar eventos del partido</p>';
    }
}

function renderEventos(eventos) {
    return eventos.map(evento => {
        const esLocal = evento.equipo_id === equipoLocalId;
        const alineacion = esLocal ? 'left' : 'right';
        
        let icono = '';
        let descripcion = '';
        let className = 'evento-item';
        let fotoHTML = '';

        switch(evento.tipo) {
            case 'gol':
            case 'GOL':
                icono = '⚽';
                className += ' evento-gol';
                descripcion = evento.descripcion || `Gol de ${evento.jugador_nombre || 'Jugador'}`;
                if (evento.jugador_foto) {
                    fotoHTML = `<img src="${evento.jugador_foto}" alt="${evento.jugador_nombre}" class="evento-jugador-foto">`;
                }
                if (evento.jugador_asociado_nombre) {
                    descripcion += ` (Asistencia: ${evento.jugador_asociado_nombre})`;
                }
                break;
            case 'sustitucion':
            case 'SUSTITUCION':
                icono = '🔄';
                className += ' evento-sustitucion';
                descripcion = `${evento.jugador_nombre || 'Jugador'} sale`;
                if (evento.jugador_asociado_nombre) {
                    descripcion += ` → ${evento.jugador_asociado_nombre} entra`;
                }
                break;
            case 'tarjeta_amarilla':
            case 'TARJETA_AMARILLA':
                icono = '🟨';
                className += ' evento-tarjeta-amarilla';
                descripcion = `Tarjeta amarilla para ${evento.jugador_nombre || 'Jugador'}`;
                break;
            case 'tarjeta_roja':
            case 'TARJETA_ROJA':
                icono = '🟥';
                className += ' evento-tarjeta-roja';
                descripcion = `Tarjeta roja para ${evento.jugador_nombre || 'Jugador'}`;
                break;
            default:
                icono = '•';
                descripcion = evento.descripcion || 'Evento';
        }

        return `
            <div class="${className} ${alineacion}">
                <div class="evento-minuto">${evento.minuto}'</div>
                <div class="evento-contenido">
                    ${fotoHTML}
                    <span class="evento-icono">${icono}</span>
                    <div class="evento-detalles">
                        <strong>${descripcion}</strong>
                        ${evento.descripcion && evento.descripcion !== descripcion ? `<small>${evento.descripcion}</small>` : ''}
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// Cargar eventos al iniciar
document.addEventListener('DOMContentLoaded', cargarEventosPartido);
