// Cargar eventos del jugador
async function cargarEventosJugador() {
    const container = document.getElementById('eventos-jugador');
    if (!container) return;
    
    try {
        // Cargar eventos donde el jugador participó
        const response = await fetch(`/eventos/jugador/${jugadorId}`);
        
        if (!response.ok) {
            container.innerHTML = '<p class="no-data">No hay eventos registrados para este jugador</p>';
            return;
        }
        
        const eventos = await response.json();
        
        if (!eventos || eventos.length === 0) {
            container.innerHTML = '<p class="no-data">No hay eventos registrados</p>';
            return;
        }
        
        // Ordenar por fecha más reciente
        eventos.sort((a, b) => {
            if (a.partido_fecha !== b.partido_fecha) {
                return new Date(b.partido_fecha) - new Date(a.partido_fecha);
            }
            return b.minuto - a.minuto;
        });
        
        let html = '<div class="eventos-lista">';
        
        eventos.forEach(evento => {
            let icono = '';
            let className = 'evento-jugador-item';
            
            switch(evento.tipo) {
                case 'gol':
                case 'GOL':
                    icono = '⚽';
                    className += ' evento-gol';
                    break;
                case 'sustitucion':
                case 'SUSTITUCION':
                    icono = '🔄';
                    className += ' evento-sustitucion';
                    break;
                case 'tarjeta_amarilla':
                case 'TARJETA_AMARILLA':
                    icono = '🟨';
                    className += ' evento-tarjeta-amarilla';
                    break;
                case 'tarjeta_roja':
                case 'TARJETA_ROJA':
                    icono = '🟥';
                    className += ' evento-tarjeta-roja';
                    break;
                default:
                    icono = '•';
            }
            
            html += `
                <a href="/partido/${evento.partido_id}" class="evento-jugador-link">
                    <div class="${className}">
                    <span class="evento-icono-grande">${icono}</span>
                    <div class="evento-info">
                        <div class="evento-partido">
                            <strong>${evento.partido_local || 'Local'} vs ${evento.partido_visitante || 'Visitante'}</strong>
                        </div>
                        <div class="evento-detalles-jugador">
                            <span class="evento-minuto-small">${evento.minuto}'</span>
                            <span class="evento-descripcion-small">${evento.descripcion || evento.tipo}</span>
                        </div>
                        <small class="evento-fecha">${formatearFecha(evento.partido_fecha)}</small>
                    </div>
                    </div>
                </a>
            `;
        });
        
        html += '</div>';
        container.innerHTML = html;
        
    } catch (error) {
        console.error('Error cargando eventos:', error);
        container.innerHTML = '<p class="error">Error al cargar eventos del jugador</p>';
    }
}

function formatearFecha(fecha) {
    if (!fecha) return '';
    const d = new Date(fecha);
    const opciones = { year: 'numeric', month: 'long', day: 'numeric' };
    return d.toLocaleDateString('es-ES', opciones);
}

// Inicializar
document.addEventListener('DOMContentLoaded', () => {
    cargarEventosJugador();
});
