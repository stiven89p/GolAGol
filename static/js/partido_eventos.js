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
                    fotoHTML = `<img src="${evento.jugador_foto}" alt="${evento.jugador_nombre}" class="evento-jugador-foto" onerror="if(this.src!='/static/img/default-player.png')this.src='/static/img/default-player.png'">`;
                }
                if (evento.jugador_asociado_nombre) {
                    descripcion += ` (Asistencia: ${evento.jugador_asociado_nombre})`;
                }
                break;
            case 'sustitucion':
            case 'SUSTITUCION':
                icono = '🔄';
                className += ' evento-sustitucion';
                const saleFoto = evento.jugador_foto ? `<img src="${evento.jugador_foto}" alt="${evento.jugador_nombre}" class="evento-jugador-foto jugador-sale" onerror="if(this.src!='/static/img/default-player.png')this.src='/static/img/default-player.png'">` : '';
                const entraFoto = evento.jugador_asociado_foto ? `<img src="${evento.jugador_asociado_foto}" alt="${evento.jugador_asociado_nombre}" class="evento-jugador-foto jugador-entra" onerror="if(this.src!='/static/img/default-player.png')this.src='/static/img/default-player.png'">` : '';
                
                fotoHTML = `<div class="sustitucion-fotos">${saleFoto}${entraFoto}</div>`;
                descripcion = `<span class="jugador-sale-nombre">${evento.jugador_nombre || 'Jugador'}</span> sale`;
                if (evento.jugador_asociado_nombre) {
                    descripcion += ` → <span class="jugador-entra-nombre">${evento.jugador_asociado_nombre}</span> entra`;
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
                case 'penal':
            case 'PENAL':
                icono = '✅';
                className += ' evento-penal';
                descripcion = evento.descripcion || `Penal convertido por ${evento.jugador_nombre || 'Jugador'}`;
                if (evento.jugador_foto) {
                    fotoHTML = `<img src="${evento.jugador_foto}" alt="${evento.jugador_nombre}" class="evento-jugador-foto" onerror="if(this.src!='/static/img/default-player.png')this.src='/static/img/default-player.png'">`;
                }
                break;
            case 'penal_fallado':
            case 'PENAL_FALLADO':
                icono = '❌';
                className += ' evento-penal-fallado';
                descripcion = evento.descripcion || `Penal fallado por ${evento.jugador_nombre || 'Jugador'}`;
                if (evento.jugador_foto) {
                    fotoHTML = `<img src="${evento.jugador_foto}" alt="${evento.jugador_nombre}" class="evento-jugador-foto" onerror="if(this.src!='/static/img/default-player.png')this.src='/static/img/default-player.png'">`;
                }
                break;
            case 'tiro':
            case 'TIRO':
                icono = '🎯';
                className += ' evento-tiro';
                descripcion = evento.descripcion || `Tiro de ${evento.jugador_nombre || 'Jugador'}`;
                if (evento.jugador_foto) {
                    fotoHTML = `<img src="${evento.jugador_foto}" alt="${evento.jugador_nombre}" class="evento-jugador-foto" onerror="if(this.src!='/static/img/default-player.png')this.src='/static/img/default-player.png'">`;
                }
                break;
            case 'entrada':
            case 'ENTRADA':
                icono = '➕';
                className += ' evento-entrada';
                descripcion = evento.descripcion || `Entrada de ${evento.jugador_nombre || 'Jugador'}`;
                if (evento.jugador_foto) {
                    fotoHTML = `<img src="${evento.jugador_foto}" alt="${evento.jugador_nombre}" class="evento-jugador-foto" onerror="if(this.src!='/static/img/default-player.png')this.src='/static/img/default-player.png'">`;
                }
                break;
            case 'intercepcion':
            case 'INTERCEPCION':
                icono = '🛡️';
                className += ' evento-intercepcion';
                descripcion = evento.descripcion || `Intercepción de ${evento.jugador_nombre || 'Jugador'}`;
                if (evento.jugador_foto) {
                    fotoHTML = `<img src="${evento.jugador_foto}" alt="${evento.jugador_nombre}" class="evento-jugador-foto" onerror="if(this.src!='/static/img/default-player.png')this.src='/static/img/default-player.png'">`;
                }
                break;
                            case 'gol_en_contra':
            case 'GOL_EN_CONTRA':
                icono = '⚽';
                className += ' evento-gol-en-contra';
                descripcion = evento.descripcion || `Autogol de ${evento.jugador_nombre || 'Jugador'}`;
                if (evento.jugador_foto) {
                    fotoHTML = `<img src="${evento.jugador_foto}" alt="${evento.jugador_nombre}" class="evento-jugador-foto" onerror="if(this.src!='/static/img/default-player.png')this.src='/static/img/default-player.png'">`;
                }
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

// Poller para actualizar marcador en vivo
async function pollScoreOnce(){
    try{
        const res = await fetch(`/partidos/id/${partidoId}`);
        if(!res.ok) return;
        const p = await res.json();
        const localEl = document.getElementById('goles-local');
        const visitanteEl = document.getElementById('goles-visitante');
        if(localEl) localEl.textContent = p.goles_local ?? localEl.textContent;
        if(visitanteEl) visitanteEl.textContent = p.goles_visitante ?? visitanteEl.textContent;

        // Update live badge / score styling if estado changed
        const centerScore = document.querySelector('.center-block .score');
        const liveBadge = document.querySelector('.center-block .meta.live-badge');
        if(p.estado === 'EN_CURSO'){
            if(centerScore && !centerScore.classList.contains('live')) centerScore.classList.add('live');
            if(liveBadge) liveBadge.style.display = '';
        } else {
            if(centerScore) centerScore.classList.remove('live');
            if(liveBadge) liveBadge.style.display = (p.estado === 'FINALIZADO') ? '' : 'none';
        }

        // Notify timer about potential changes (estado, hora_inicio, parte)
        try{
            const evt = new CustomEvent('partido-update', { detail: {
                estado: p.estado,
                fecha: p.fecha,
                hora_inicio: p.hora_inicio || null,
                hora_fin_primer_tiempo: p.hora_fin_primer_tiempo || null,
                hora_inicio_segundo_tiempo: p.hora_inicio_segundo_tiempo || null,
                hora_fin_segundo_tiempo: p.hora_fin_segundo_tiempo || null,
                parte: p.parte || null
            }});
            window.dispatchEvent(evt);
        }catch(_e){ /* ignore */ }
    }catch(e){
        // silently ignore polling errors
    }
}

// Start polling every 5 seconds when DOM ready
document.addEventListener('DOMContentLoaded', function(){
    // primer fetch inmediato
    pollScoreOnce();
    cargarEventosPartido();
    // actualizar marcador cada 2 segundos
    setInterval(pollScoreOnce, 2000);
    // actualizar timeline de eventos cada 2 segundos
    setInterval(cargarEventosPartido, 2000);
});
