// Admin - Gestión de Partidos

function mostrarFormulario(reset = true) {
    document.getElementById('formulario-partido').style.display = 'flex';
    if (reset) {
        document.getElementById('form-title').textContent = 'Crear Partido';
        document.getElementById('partido-form').reset();
        document.getElementById('partido_id').value = '';
    }
}

function cerrarFormulario() {
    document.getElementById('formulario-partido').style.display = 'none';
}

async function editarPartido(id) {
    try {
        const response = await fetch(`/partidos/${id}`);
        const partido = await response.json();
        
        mostrarFormulario(false);
        document.getElementById('form-title').textContent = 'Editar Partido';
        document.getElementById('partido_id').value = partido.partido_id;
        document.getElementById('fecha').value = partido.fecha;
        document.getElementById('hora').value = partido.hora.substring(0, 5);
        document.getElementById('jornada').value = partido.jornada;
        document.getElementById('equipo_local_id').value = partido.equipo_local_id;
        document.getElementById('equipo_visitante_id').value = partido.equipo_visitante_id;
        document.getElementById('estadio').value = partido.estadio;
        document.getElementById('temporada_id').value = partido.temporada_id;
        document.getElementById('estado').value = partido.estado;
        document.getElementById('goles_local').value = partido.goles_local || 0;
        document.getElementById('goles_visitante').value = partido.goles_visitante || 0;
    } catch (error) {
        mostrarMensaje('Error al cargar el partido', 'error');
    }
}

document.getElementById('partido-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const partidoId = document.getElementById('partido_id').value;
    const localId = parseInt(document.getElementById('equipo_local_id').value);
    const visitanteId = parseInt(document.getElementById('equipo_visitante_id').value);
    
    if (localId === visitanteId) {
        mostrarMensaje('El equipo local y visitante no pueden ser el mismo', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('fecha', document.getElementById('fecha').value);
    formData.append('hora', document.getElementById('hora').value + ':00');
    formData.append('jornada', document.getElementById('jornada').value);
    formData.append('equipo_local_id', document.getElementById('equipo_local_id').value);
    formData.append('equipo_visitante_id', document.getElementById('equipo_visitante_id').value);
    formData.append('estadio', document.getElementById('estadio').value.trim());
    formData.append('temporada_id', document.getElementById('temporada_id').value);
    formData.append('estado', document.getElementById('estado').value);
    formData.append('goles_local', document.getElementById('goles_local').value || '0');
    formData.append('goles_visitante', document.getElementById('goles_visitante').value || '0');
    
    try {
        let url, method;
        if (partidoId) {
            url = `/partidos/${partidoId}`;
            method = 'PATCH';
            formData.append('partido_id', partidoId);
        } else {
            url = '/partidos/';
            method = 'POST';
        }
        
        const response = await fetch(url, {
            method: method,
            body: formData
        });
        
        if (response.ok) {
            mostrarMensaje(`Partido ${partidoId ? 'actualizado' : 'creado'} correctamente`);
            cerrarFormulario();
            setTimeout(() => location.reload(), 1000);
        } else {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || 'Error al guardar');
        }
    } catch (error) {
        mostrarMensaje(error.message, 'error');
    }
});

// Auto-llenar estadio cuando se selecciona equipo local
document.getElementById('equipo_local_id').addEventListener('change', async (e) => {
    const equipoId = e.target.value;
    if (!equipoId) return;
    
    try {
        const response = await fetch(`/equipos/${equipoId}`);
        const equipo = await response.json();
        document.getElementById('estadio').value = equipo.estadio;
    } catch (error) {
        console.error('Error al cargar equipo');
    }
});

// Iniciar partido (cambiar estado de PROGRAMADO a EN_CURSO)
async function iniciarPartido(partidoId) {
    if (!confirm('¿Iniciar este partido? El estado cambiará a EN CURSO.')) {
        return;
    }
    
    try {
        // El valor debe coincidir con el enum: "en curso" (minúsculas con espacio)
        const response = await fetch(`/partidos/${partidoId}?estado=en%20curso`, {
            method: 'PATCH'
        });
        
        if (response.ok) {
            mostrarMensaje('Partido iniciado correctamente');
            setTimeout(() => location.reload(), 1000);
        } else {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || 'Error al iniciar partido');
        }
    } catch (error) {
        mostrarMensaje(error.message, 'error');
    }
}

// Cerrar modal al hacer clic fuera
window.onclick = function(event) {
    const modal = document.getElementById('formulario-partido');
    if (event.target === modal) {
        cerrarFormulario();
    }
}
