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
        const response = await fetch(`/partidos/id/${id}`);
        const partido = await response.json();
        
        mostrarFormulario(false);
        document.getElementById('form-title').textContent = 'Editar Partido';
        document.getElementById('partido_id').value = partido.partido_id;
        document.getElementById('fecha').value = partido.fecha;
        if (partido.hora) document.getElementById('hora').value = partido.hora.substring(0, 5);
        document.getElementById('jornada').value = partido.jornada;
        // Preseleccionar equipos si vienen en el DTO
        if (typeof partido.equipo_local_id !== 'undefined' && document.getElementById('equipo_local_id')) {
            document.getElementById('equipo_local_id').value = String(partido.equipo_local_id);
        }
        if (typeof partido.equipo_visitante_id !== 'undefined' && document.getElementById('equipo_visitante_id')) {
            document.getElementById('equipo_visitante_id').value = String(partido.equipo_visitante_id);
        }
        // Temporada solo si está disponible en el DTO
        if (typeof partido.temporada_id !== 'undefined' && document.getElementById('temporada_id')) {
            document.getElementById('temporada_id').value = String(partido.temporada_id);
        }
        document.getElementById('estadio').value = partido.lugar || '';
        if (document.getElementById('estado')) {
            document.getElementById('estado').value = partido.estado;
        }
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
window.iniciarPartido = async function iniciarPartido(partidoId) {
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

window.acabarPartido = async function acabarPartido(partidoId) {
    if (!confirm('¿Iniciar este partido? El estado cambiará a FINALIZADO.')) {
        return;
    }
    
    try {
        // El valor debe coincidir con el enum: "finalizado" (minúsculas)
        const response = await fetch(`/partidos/${partidoId}?estado=finalizado`, {
            method: 'PATCH'
        });
        
        if (response.ok) {
            mostrarMensaje('Partido iniciado correctamente');
            setTimeout(() => location.reload(), 1000);
        } else {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || 'Error al finalizar partido');
        }
    } catch (error) {
        mostrarMensaje(error.message, 'error');
    }
}

// --------- Gestión de Formaciones del Partido ---------
window.abrirFormaciones = async function abrirFormaciones(partidoId){
    const modal = document.getElementById('modal-formaciones-partido');
    document.getElementById('modal-partido-id').value = partidoId;
    document.getElementById('formaciones-local').innerHTML = 'Cargando...';
    document.getElementById('formaciones-visitante').innerHTML = 'Cargando...';
    document.getElementById('nombre-local').textContent = '-';
    document.getElementById('nombre-visitante').textContent = '-';
    modal.style.display = 'flex';

    try {
        const resp = await fetch(`/partidos/id/${partidoId}`);
        if(!resp.ok) throw new Error('No se pudo cargar el partido');
        const p = await resp.json();

        // Nombres y enlaces de creación
        document.getElementById('nombre-local').textContent = p.equipo_local_nombre || 'Local';
        document.getElementById('nombre-visitante').textContent = p.equipo_visitante_nombre || 'Visitante';
        document.getElementById('link-formaciones-local').href = `/admin/formaciones?equipo_id=${p.equipo_local_id}`;
        document.getElementById('link-formaciones-visitante').href = `/admin/formaciones?equipo_id=${p.equipo_visitante_id}`;

        // Cargar formaciones de ambos equipos
        const [rLocal, rVis] = await Promise.all([
            fetch(`/formaciones/equipo/${p.equipo_local_id}`),
            fetch(`/formaciones/equipo/${p.equipo_visitante_id}`)
        ]);
        const [fl, fv] = await Promise.all([rLocal.json(), rVis.json()]);

        const render = (lista, contId, name) =>{
            const cont = document.getElementById(contId);
            if(!lista || lista.length === 0){
                cont.innerHTML = '<em>Sin formaciones</em>';
                return;
            }
            cont.innerHTML = '';
            lista.forEach(f=>{
                const id = `${name}-${f.formacion_id}`;
                const wrap = document.createElement('div');
                wrap.className = 'chk-item';
                const radio = document.createElement('input');
                radio.type = 'radio';
                radio.name = name;
                radio.value = f.formacion_id;
                radio.id = id;
                const lbl = document.createElement('label');
                lbl.htmlFor = id;
                lbl.style.cursor = 'pointer';
                // Pretty label with formation badge
                const badge = document.createElement('span');
                badge.className = 'badge';
                badge.style.marginRight = '8px';
                badge.textContent = `${f.defensas}-${f.mediocampistas}-${f.delanteros}`;
                const text = document.createElement('span');
                text.textContent = `Formación #${f.formacion_id}`;
                lbl.appendChild(badge);
                lbl.appendChild(text);
                // Subdetails: titulares/suplentes resumen
                const sub = document.createElement('div');
                sub.style.fontSize = '0.85rem';
                sub.style.color = '#8b949e';
                sub.style.marginTop = '4px';
                // Build real list: jugadores titulares y suplentes
                const makeList = (arr, title) => {
                    const wrap = document.createElement('div');
                    const heading = document.createElement('strong');
                    heading.textContent = `${title}:`;
                    heading.style.display = 'block';
                    heading.style.color = '#c9d1d9';
                    wrap.appendChild(heading);
                    const ul = document.createElement('ul');
                    ul.style.margin = '6px 0 8px';
                    ul.style.paddingLeft = '18px';
                    (arr || []).forEach(it => {
                        const li = document.createElement('li');
                        const nombre = it && it.nombre ? it.nombre : `#${it.jugador_id}`;
                        const pos = it && it.posicion ? ` (${it.posicion})` : '';
                        li.textContent = nombre + pos;
                        ul.appendChild(li);
                    });
                    wrap.appendChild(ul);
                    return wrap;
                };
                sub.appendChild(makeList(f.titulares, 'Titulares'));
                sub.appendChild(makeList(f.suplentes, 'Suplentes'));
                lbl.appendChild(sub);
                // highlight on select
                radio.addEventListener('change', ()=>{
                    // remove selected from siblings
                    cont.querySelectorAll('.chk-item').forEach(el=> el.classList.remove('selected'));
                    wrap.classList.add('selected');
                });
                wrap.appendChild(radio);
                wrap.appendChild(lbl);
                cont.appendChild(wrap);
            });
        };

        render(fl, 'formaciones-local', 'formacion_local');
        render(fv, 'formaciones-visitante', 'formacion_visitante');
    } catch(err){
        console.error(err);
        mostrarMensaje('Error cargando formaciones', 'error');
    }
}

function cerrarModalFormaciones(){
    document.getElementById('modal-formaciones-partido').style.display = 'none';
}

async function asignarFormacionesSeleccionadas(){
    const partidoId = document.getElementById('modal-partido-id').value;
    const localSel = document.querySelector('input[name="formacion_local"]:checked');
    const visSel = document.querySelector('input[name="formacion_visitante"]:checked');
    if(!localSel && !visSel){
        mostrarMensaje('Seleccione al menos una formación para asignar', 'error');
        return;
    }
    try{
        if(localSel){
            const r1 = await fetch(`/partidos/${partidoId}/formacion/${localSel.value}`, { method: 'POST' });
            if(!r1.ok) throw new Error('Error asignando formación local');
        }
        if(visSel){
            const r2 = await fetch(`/partidos/${partidoId}/formacion/${visSel.value}`, { method: 'POST' });
            if(!r2.ok) throw new Error('Error asignando formación visitante');
        }
        mostrarMensaje('Formaciones asignadas');
        cerrarModalFormaciones();
        setTimeout(()=> location.reload(), 800);
    }catch(err){
        mostrarMensaje(err.message || 'Error asignando formaciones', 'error');
    }
}

// Cerrar modales al hacer clic fuera
window.onclick = function(event) {
    const modalPartido = document.getElementById('formulario-partido');
    const modalFormaciones = document.getElementById('modal-formaciones-partido');
    if (event.target === modalPartido) {
        cerrarFormulario();
    }
    if (event.target === modalFormaciones) {
        cerrarModalFormaciones();
    }
}
