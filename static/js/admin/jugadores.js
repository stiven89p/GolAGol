// Admin - Gestión de Jugadores

function mostrarFormulario() {
    document.getElementById('formulario-jugador').style.display = 'flex';
    document.getElementById('form-title').textContent = 'Crear Jugador';
    document.getElementById('jugador-form').reset();
    document.getElementById('jugador_id').value = '';
}

function cerrarFormulario() {
    document.getElementById('formulario-jugador').style.display = 'none';
}

async function editarJugador(id) {
    try {
        const response = await fetch(`/jugadores/${id}`);
        const jugador = await response.json();
        
        mostrarFormulario();
        document.getElementById('form-title').textContent = 'Editar Jugador';
        document.getElementById('jugador_id').value = jugador.jugador_id;
        document.getElementById('nombre').value = jugador.nombre;
        document.getElementById('apellido').value = jugador.apellido;
        document.getElementById('equipo_id').value = jugador.equipo_id;
        document.getElementById('posicion').value = jugador.posicion;
        document.getElementById('numero_camiseta').value = jugador.numero_camiseta || '';
        document.getElementById('fecha_nacimiento').value = jugador.fecha_nacimiento;
        document.getElementById('nacionalidad').value = jugador.nacionalidad;
        const fileInput = document.getElementById('foto_file');
        if (fileInput) fileInput.value = '';
    } catch (error) {
        mostrarMensaje('Error al cargar el jugador', 'error');
    }
}

async function eliminarJugador(id) {
    if (!confirm('¿Estás seguro de eliminar este jugador?')) return;
    
    try {
        const response = await fetch(`/jugadores/${id}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            mostrarMensaje('Jugador eliminado correctamente');
            setTimeout(() => location.reload(), 1000);
        } else {
            throw new Error('Error al eliminar');
        }
    } catch (error) {
        mostrarMensaje('Error al eliminar el jugador', 'error');
    }
}

function aplicarFiltros() {
    const equipoId = document.getElementById('filtro-equipo').value;
    const posicion = document.getElementById('filtro-posicion').value;
    
    const params = new URLSearchParams();
    if (equipoId) params.append('equipo_id', equipoId);
    if (posicion) params.append('posicion', posicion);
    
    const queryString = params.toString();
    window.location.href = `/admin/jugadores${queryString ? '?' + queryString : ''}`;
}

function limpiarFiltros() {
    window.location.href = '/admin/jugadores';
}

document.getElementById('jugador-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const jugadorId = document.getElementById('jugador_id').value;
    const formData = new FormData();
    
    formData.append('nombre', document.getElementById('nombre').value.trim());
    formData.append('apellido', document.getElementById('apellido').value.trim());
    formData.append('equipo_id', document.getElementById('equipo_id').value);
    formData.append('posicion', document.getElementById('posicion').value);
    formData.append('numero_camiseta', document.getElementById('numero_camiseta').value);
    formData.append('fecha_nacimiento', document.getElementById('fecha_nacimiento').value);
    formData.append('nacionalidad', document.getElementById('nacionalidad').value.trim());
    
    const fileInput = document.getElementById('foto_file');
    if (fileInput && fileInput.files.length > 0) {
        formData.append('foto', fileInput.files[0]);
    }
    
    try {
        const url = jugadorId ? `/jugadores/${jugadorId}` : '/jugadores/';
        const method = jugadorId ? 'PATCH' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            body: formData
        });
        
        if (response.ok) {
            mostrarMensaje(`Jugador ${jugadorId ? 'actualizado' : 'creado'} correctamente`);
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

// Cerrar modal al hacer clic fuera
window.onclick = function(event) {
    const modal = document.getElementById('formulario-jugador');
    if (event.target === modal) {
        cerrarFormulario();
    }
}
