// Gestión de Temporadas

function abrirModalCrear() {
    document.getElementById('modalCrearTemporada').classList.add('is-active');
    document.getElementById('formCrearTemporada').reset();
    
    // Establecer fecha de inicio como hoy
    const hoy = new Date().toISOString().split('T')[0];
    document.getElementById('fecha_inicio').value = hoy;
}

function cerrarModalCrear() {
    document.getElementById('modalCrearTemporada').classList.remove('is-active');
}

async function crearTemporada() {
    const fechaInicio = document.getElementById('fecha_inicio').value;
    const fechaFin = document.getElementById('fecha_fin').value;
    
    if (!fechaInicio || !fechaFin) {
        mostrarNotificacion('Por favor completa todos los campos', 'warning');
        return;
    }
    
    // Validar que fecha fin sea posterior a fecha inicio
    if (new Date(fechaFin) <= new Date(fechaInicio)) {
        mostrarNotificacion('La fecha de fin debe ser posterior a la fecha de inicio', 'warning');
        return;
    }
    
    const formData = new FormData();
    formData.append('fecha_inicio', fechaInicio);
    formData.append('fecha_fin', fechaFin);
    
    try {
        const response = await fetch('/temporadas/', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            mostrarNotificacion('Temporada creada exitosamente', 'success');
            cerrarModalCrear();
            setTimeout(() => window.location.reload(), 1000);
        } else {
            const error = await response.json();
            mostrarNotificacion(error.detail || 'Error al crear temporada', 'danger');
        }
    } catch (error) {
        console.error('Error:', error);
        mostrarNotificacion('Error de conexión', 'danger');
    }
}

async function finalizarTemporada(temporadaId) {
    if (!confirm('¿Estás seguro de finalizar esta temporada?\n\nEsto:\n- Marcará la temporada como FINALIZADA\n- Sumará un título al equipo ganador\n- No se podrá revertir')) {
        return;
    }
    
    try {
        const response = await fetch(`/temporadas/${temporadaId}`, {
            method: 'PATCH'
        });
        
        if (response.ok) {
            mostrarNotificacion('Temporada finalizada exitosamente', 'success');
            setTimeout(() => window.location.reload(), 1000);
        } else {
            const error = await response.json();
            mostrarNotificacion(error.detail || 'Error al finalizar temporada', 'danger');
        }
    } catch (error) {
        console.error('Error:', error);
        mostrarNotificacion('Error de conexión', 'danger');
    }
}

function mostrarNotificacion(mensaje, tipo) {
    // Crear notificación
    const notif = document.createElement('div');
    notif.className = `notification is-${tipo} is-light`;
    notif.style.position = 'fixed';
    notif.style.top = '20px';
    notif.style.right = '20px';
    notif.style.zIndex = '9999';
    notif.style.minWidth = '300px';
    notif.innerHTML = `
        <button class="delete" onclick="this.parentElement.remove()"></button>
        ${mensaje}
    `;
    
    document.body.appendChild(notif);
    
    // Auto-eliminar después de 4 segundos
    setTimeout(() => {
        if (notif.parentElement) {
            notif.remove();
        }
    }, 4000);
}

// Cerrar modal con ESC
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        cerrarModalCrear();
    }
});
