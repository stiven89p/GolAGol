// Admin - Gestión de Equipos (robusto)

function mostrarFormulario(reset = true) {
    const modal = document.getElementById('formulario-equipo');
    if (!modal) return;
    modal.style.display = 'flex';
    const title = document.getElementById('form-title');
    const form = document.getElementById('equipo-form');
    const idInput = document.getElementById('equipo_id');
    if (reset) {
        if (title) title.textContent = 'Crear Equipo';
        if (form) form.reset();
        if (idInput) idInput.value = '';
    }
}

function cerrarFormulario() {
    const modal = document.getElementById('formulario-equipo');
    if (modal) modal.style.display = 'none';
}

async function editarEquipo(id) {
    try {
        const response = await fetch(`/equipos/${id}`);
        if (!response.ok) throw new Error('No se pudo obtener el equipo');
        const equipo = await response.json();
        mostrarFormulario(false); // abrir sin resetear
        document.getElementById('form-title').textContent = 'Editar Equipo';
        document.getElementById('equipo_id').value = equipo.equipo_id;
        document.getElementById('nombre').value = equipo.nombre;
        document.getElementById('ciudad').value = equipo.ciudad;
        document.getElementById('estadio').value = equipo.estadio;
        document.getElementById('anio_fundacion').value = equipo.anio_fundacion;
        document.getElementById('titulos').value = equipo.titulos || 0;
        const fileInput = document.getElementById('logo_file');
        if (fileInput) fileInput.value = '';
    } catch (error) {
        console.error(error);
        mostrarMensaje('Error al cargar el equipo', 'error');
    }
}

async function eliminarEquipo(id) {
    if (!confirm('¿Estás seguro de eliminar este equipo?')) return;
    try {
        const response = await fetch(`/equipos/${id}`, { method: 'DELETE' });
        if (response.ok) {
            mostrarMensaje('Equipo eliminado correctamente');
            setTimeout(() => location.reload(), 800);
        } else {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.detail || 'Error al eliminar');
        }
    } catch (error) {
        console.error(error);
        mostrarMensaje(error.message || 'Error al eliminar el equipo', 'error');
    }
}

async function activarEquipo(id) {
    if (!confirm('¿Activar este equipo?')) return;
    try {
        const formData = new FormData();
        formData.append('activo', 'true');
        const response = await fetch(`/equipos/${id}`, { method: 'PATCH', body: formData });
        if (response.ok) {
            mostrarMensaje('Equipo activado correctamente');
            setTimeout(() => location.reload(), 800);
        } else {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.detail || 'Error al activar');
        }
    } catch (error) {
        console.error(error);
        mostrarMensaje(error.message || 'Error al activar el equipo', 'error');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('equipo-form');
    if (!form) return; // seguridad
    const submitBtn = form.querySelector('button[type="submit"]');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const equipoId = document.getElementById('equipo_id').value;
        const formData = new FormData();
        formData.append('nombre', document.getElementById('nombre').value.trim());
        formData.append('ciudad', document.getElementById('ciudad').value.trim());
        formData.append('estadio', document.getElementById('estadio').value.trim());
        formData.append('anio_fundacion', document.getElementById('anio_fundacion').value);
        formData.append('titulos', document.getElementById('titulos').value || '0');
        const fileInput = document.getElementById('logo_file');
        if (fileInput && fileInput.files.length > 0) {
            formData.append('file', fileInput.files[0]);
        }
        const url = equipoId ? `/equipos/${equipoId}` : '/equipos/';
        const method = equipoId ? 'PATCH' : 'POST';
        console.log('Enviando', method, url);
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.classList.add('is-loading');
        }
        try {
            const response = await fetch(url, { method, body: formData });
            console.log('Respuesta', response.status);
            if (response.ok) {
                mostrarMensaje(`Equipo ${equipoId ? 'actualizado' : 'creado'} correctamente`);
                cerrarFormulario();
                setTimeout(() => location.reload(), 800);
            } else {
                let errorText = 'Error al guardar';
                const contentType = response.headers.get('content-type') || '';
                if (contentType.includes('application/json')) {
                    const errData = await response.json().catch(() => ({}));
                    errorText = errData.detail || JSON.stringify(errData) || errorText;
                } else {
                    errorText = await response.text();
                }
                throw new Error(errorText);
            }
        } catch (error) {
            console.error(error);
            mostrarMensaje(error.message || 'Error al guardar el equipo', 'error');
        } finally {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.classList.remove('is-loading');
            }
        }
    });
});

// Cerrar modal al hacer clic fuera
window.addEventListener('click', (event) => {
    const modal = document.getElementById('formulario-equipo');
    if (event.target === modal) cerrarFormulario();
});
