let jugadoresData = [];
let jugadorSeleccionado = null;
let estadisticasData = null;

// Cargar jugadores del equipo
async function cargarJugadores() {
    try {
        const response = await fetch(`/jugadores/equipo/${equipoId}`);
        if (!response.ok) throw new Error('Error al cargar jugadores');
        
        jugadoresData = await response.json();
        renderizarJugadores(jugadoresData);
        
        // Seleccionar el primer jugador automáticamente
        if (jugadoresData.length > 0) {
            seleccionarJugador(jugadoresData[0].jugador_id);
        }
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('jugadores-lista').innerHTML = '<p class="error">Error al cargar jugadores</p>';
    }
}

// Renderizar lista de jugadores
function renderizarJugadores(jugadores) {
    const lista = document.getElementById('jugadores-lista');
    
    if (!jugadores || jugadores.length === 0) {
        lista.innerHTML = '<p class="no-data">No hay jugadores en este equipo</p>';
        return;
    }
    
    // Agrupar por posición
    const grupos = {
        'PORTERO': [],
        'DEFENSOR': [],
        'MEDIOCAMPISTA': [],
        'DELANTERO': []
    };
    
    jugadores.forEach(j => {
        if (grupos[j.posicion]) {
            grupos[j.posicion].push(j);
        }
    });
    
    let html = '';
    const posicionLabels = {
        'PORTERO': '🧤 Porteros',
        'DEFENSOR': '🛡️ Defensas',
        'MEDIOCAMPISTA': '⚙️ Mediocampistas',
        'DELANTERO': '⚔️ Delanteros'
    };
    
    for (const [posicion, jugadores] of Object.entries(grupos)) {
        if (jugadores.length > 0) {
            html += `<div class="posicion-grupo-jugadores">`;
            html += `<h3 class="posicion-titulo">${posicionLabels[posicion]}</h3>`;
            
            jugadores.forEach(j => {
                const fotoUrl = j.foto || '/static/img/default-player.png';
                const edad = calcularEdad(j.fecha_nacimiento);
                
                html += `
                    <div class="jugador-item" data-jugador-id="${j.jugador_id}" data-posicion="${j.posicion}">
                        <img src="${fotoUrl}" alt="${j.nombre}" class="jugador-foto-small">
                        <div class="jugador-item-info">
                            <strong class="jugador-nombre-item">${j.nombre} ${j.apellido}</strong>
                            <div class="jugador-meta">
                                <span class="jugador-numero">#${j.numero_camiseta || '-'}</span>
                                <span class="jugador-edad-item">${edad} años</span>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            html += `</div>`;
        }
    }
    
    lista.innerHTML = html;
    
    // Añadir eventos de clic para redirigir a la página del jugador
    document.querySelectorAll('.jugador-item').forEach(item => {
        item.addEventListener('click', () => {
            const jugadorId = parseInt(item.dataset.jugadorId);
            window.location.href = `/jugador/${jugadorId}`;
        });
    });
}

// Seleccionar un jugador
async function seleccionarJugador(jugadorId) {
    jugadorSeleccionado = jugadoresData.find(j => j.jugador_id === jugadorId);
    
    if (!jugadorSeleccionado) return;
    
    // Marcar como activo
    document.querySelectorAll('.jugador-item').forEach(item => {
        item.classList.remove('active');
        if (parseInt(item.dataset.jugadorId) === jugadorId) {
            item.classList.add('active');
        }
    });
    
    // Cargar estadísticas
    await cargarEstadisticas(jugadorId);
    
    // Renderizar información
    renderizarInfoJugador();
}

// Cargar estadísticas del jugador
async function cargarEstadisticas(jugadorId) {
    try {
        const response = await fetch(`/estadisticas-jugadores/jugador/${jugadorId}`);
        if (response.ok) {
            estadisticasData = await response.json();
        } else {
            estadisticasData = null;
        }
    } catch (error) {
        console.error('Error al cargar estadísticas:', error);
        estadisticasData = null;
    }
}

// Renderizar información del jugador
function renderizarInfoJugador() {
    if (!jugadorSeleccionado) return;
    
    const container = document.getElementById('jugador-info');
    const j = jugadorSeleccionado;
    const fotoUrl = j.foto || '/static/img/default-player.png';
    const edad = calcularEdad(j.fecha_nacimiento);
    
    let html = `
        <div class="jugador-perfil panel">
            <div class="jugador-header-perfil">
                <img src="${fotoUrl}" alt="${j.nombre} ${j.apellido}" class="jugador-foto-grande">
                <div class="jugador-datos-principales">
                    <h1 class="jugador-nombre-grande">${j.nombre} ${j.apellido}</h1>
                    <div class="jugador-numero-grande">#${j.numero_camiseta || '-'}</div>
                    <div class="jugador-info-basica">
                        <div class="info-item">
                            <span class="info-label">Posición</span>
                            <span class="info-value">${formatearPosicion(j.posicion)}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Edad</span>
                            <span class="info-value">${edad} años</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Fecha de Nacimiento</span>
                            <span class="info-value">${formatearFecha(j.fecha_nacimiento)}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Nacionalidad</span>
                            <span class="info-value">${j.nacionalidad}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="jugador-estadisticas panel">
            <h2>📊 Estadísticas</h2>
    `;
    
    if (estadisticasData && estadisticasData.length > 0) {
        // Mostrar estadísticas por temporada
        estadisticasData.forEach(est => {
            html += `
                <div class="estadistica-temporada">
                    <h3>Temporada ${est.temporada_nombre || est.temporada}</h3>
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-valor">${est.partidos_jugados || 0}</div>
                            <div class="stat-label">Partidos</div>
                        </div>
                        <div class="stat-card destacado">
                            <div class="stat-valor">${est.goles || 0}</div>
                            <div class="stat-label">⚽ Goles</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-valor">${est.asistencias || 0}</div>
                            <div class="stat-label">🎯 Asistencias</div>
                        </div>
                        <div class="stat-card amarilla">
                            <div class="stat-valor">${est.tarjetas_amarillas || 0}</div>
                            <div class="stat-label">🟨 T. Amarillas</div>
                        </div>
                        <div class="stat-card roja">
                            <div class="stat-valor">${est.tarjetas_rojas || 0}</div>
                            <div class="stat-label">🟥 T. Rojas</div>
                        </div>
                    </div>
                </div>
            `;
        });
    } else {
        html += '<p class="no-data">No hay estadísticas disponibles para este jugador</p>';
    }
    
    html += `</div>`;
    
    container.innerHTML = html;
}

// Filtrar jugadores por posición
function filtrarJugadores(posicion) {
    const jugadoresFiltrados = posicion === 'todos' 
        ? jugadoresData 
        : jugadoresData.filter(j => j.posicion === posicion);
    
    renderizarJugadores(jugadoresFiltrados);
    
    // Actualizar botones activos
    document.querySelectorAll('.filtro-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.filter === posicion) {
            btn.classList.add('active');
        }
    });
}

// Utilidades
function calcularEdad(fechaNacimiento) {
    const hoy = new Date();
    const nacimiento = new Date(fechaNacimiento);
    let edad = hoy.getFullYear() - nacimiento.getFullYear();
    const mes = hoy.getMonth() - nacimiento.getMonth();
    if (mes < 0 || (mes === 0 && hoy.getDate() < nacimiento.getDate())) {
        edad--;
    }
    return edad;
}

function formatearFecha(fecha) {
    const d = new Date(fecha);
    const opciones = { year: 'numeric', month: 'long', day: 'numeric' };
    return d.toLocaleDateString('es-ES', opciones);
}

function formatearPosicion(posicion) {
    const posiciones = {
        'PORTERO': 'Portero',
        'DEFENSOR': 'Defensa',
        'MEDIOCAMPISTA': 'Mediocampista',
        'DELANTERO': 'Delantero'
    };
    return posiciones[posicion] || posicion;
}

// Inicializar
document.addEventListener('DOMContentLoaded', () => {
    cargarJugadores();
    
    // Eventos de filtro
    document.querySelectorAll('.filtro-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            filtrarJugadores(btn.dataset.filter);
        });
    });
});
