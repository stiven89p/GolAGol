// Admin - Gestión de Formaciones

function mostrarFormulario(){
  document.getElementById('formulario-formacion').style.display='flex';
  document.getElementById('formacion-form').reset();
  document.getElementById('titulares-container').innerHTML='';
  document.getElementById('suplentes-container').innerHTML='';
    const step1 = document.getElementById('form-step-1');
    const step2 = document.getElementById('form-step-2');
    if(step1 && step2){ step1.style.display='block'; step2.style.display='none'; }
}
function cerrarFormulario(){
  document.getElementById('formulario-formacion').style.display='none';
}

function aplicarFiltroFormaciones(){
  const eq = document.getElementById('filtro-equipo').value;
  const params = new URLSearchParams();
  if(eq) params.append('equipo_id', eq);
  window.location.href = '/admin/formaciones' + (params.toString()? ('?' + params.toString()) : '');
}
function limpiarFiltroFormaciones(){
  window.location.href = '/admin/formaciones';
}


// Lista global de jugadores cargados para el equipo seleccionado
let jugadores = [];
async function cargarJugadoresEquipo(equipoId){
  if(!equipoId){
    document.getElementById('portero_id').innerHTML='';
    document.getElementById('titulares-container').innerHTML='';
    document.getElementById('suplentes-container').innerHTML='';
    return;
  }
  try {
    const resp = await fetch(`/jugadores/equipo/${equipoId}`);
    jugadores = await resp.json();
    
    // Cargar porteros en el select
    const porteroSelect = document.getElementById('portero_id');
    porteroSelect.innerHTML='<option value="">Seleccione portero</option>';
    jugadores.forEach(j=>{
      if(j.posicion === 'PORTERO' || j.posicion === 'portero'){
        porteroSelect.innerHTML += `<option value="${j.jugador_id}">${j.nombre} ${j.apellido}</option>`;
      }
    });
    
    // Ordenar jugadores por posición: Defensores, Mediocampistas, Delanteros (sin porteros)
    const ordenPosiciones = {'DEFENSOR': 1, 'defensor': 1, 'MEDIOCAMPISTA': 2, 'mediocampista': 2, 'DELANTERO': 3, 'delantero': 3};
    const jugadoresNoPorteros = jugadores.filter(j => j.posicion !== 'PORTERO' && j.posicion !== 'portero');
    jugadoresNoPorteros.sort((a, b) => (ordenPosiciones[a.posicion] || 999) - (ordenPosiciones[b.posicion] || 999));
    
    // Build selectable lists
    const titulares = document.getElementById('titulares-container');
    const suplentes = document.getElementById('suplentes-container');
    titulares.innerHTML='';
    suplentes.innerHTML='';

    // Helper to create a checkbox+label with photo
    function createOption(j, cls){
      const fotoUrl = j.foto ? `/static/img/${j.foto}` : '/static/img/default-player.png';
      const chk = document.createElement('input');
      chk.type='checkbox';
      chk.value=j.jugador_id;
      chk.name=cls === 'titular-chk' ? 'titular' : 'suplente';
      chk.className=cls;
      chk.dataset.jugadorId = j.jugador_id;
      // give an id so label can be linked
      chk.id = `${cls}-${j.jugador_id}`;

      const img = document.createElement('img');
      img.src = fotoUrl;
      img.alt = `${j.nombre} ${j.apellido}`;
      img.className = 'jugador-foto-mini';
      img.style.width = '32px';
      img.style.height = '32px';
      img.style.borderRadius = '50%';
      img.style.objectFit = 'cover';
      img.style.marginRight = '8px';
      img.onerror = function() {
        if (this.src !== '/static/img/default-player.png') {
          this.src = '/static/img/default-player.png';
        }
      };

      const lbl=document.createElement('label');
      lbl.textContent=`${j.nombre} ${j.apellido} (${j.posicion})`;
      lbl.htmlFor = chk.id;
      lbl.style.display = 'flex';
      lbl.style.alignItems = 'center';
      lbl.style.cursor = 'pointer';
      lbl.insertBefore(img, lbl.firstChild);

      const wrap=document.createElement('div'); 
      wrap.className='chk-item';
      wrap.style.cursor = 'pointer';
      wrap.appendChild(chk); 
      wrap.appendChild(lbl);
      
      // Hacer que todo el wrap sea clickeable
      wrap.addEventListener('click', (e) => {
        // Si no se hizo click directamente en el checkbox, disparar su click
        if(e.target !== chk) {
          chk.click();
        }
      });
      
      // mark selected style if checked
      chk.addEventListener('change', ()=>{
        wrap.classList.toggle('selected', chk.checked);
      });
      return wrap;
    }

    // Render titulares (all non-porteros)
    jugadoresNoPorteros.forEach(j=>{
      const fotoUrl = j.foto ? `/static/img/${j.foto}` : '/static/img/default-player.png';
      
      // Para titulares (sin porteros)
      const chkTit = document.createElement('input');
      chkTit.type='checkbox';
      chkTit.value=j.jugador_id;
      chkTit.name='titular';
      chkTit.className='titular-chk';
      chkTit.dataset.jugadorId = j.jugador_id;
      chkTit.id = `titular-${j.jugador_id}`;
      
      const imgTit = document.createElement('img');
      imgTit.src = fotoUrl;
      imgTit.alt = `${j.nombre} ${j.apellido}`;
      imgTit.className = 'jugador-foto-mini';
      imgTit.style.width = '32px';
      imgTit.style.height = '32px';
      imgTit.style.borderRadius = '50%';
      imgTit.style.objectFit = 'cover';
      imgTit.style.marginRight = '8px';
      imgTit.onerror = function() {
        if (this.src !== '/static/img/default-player.png') {
          this.src = '/static/img/default-player.png';
        }
      };
      
      const lblTit = document.createElement('label');
      lblTit.textContent=`${j.nombre} ${j.apellido} (${j.posicion})`; 
      lblTit.htmlFor = chkTit.id;
      lblTit.style.display = 'flex';
      lblTit.style.alignItems = 'center';
      lblTit.style.cursor = 'pointer';
      lblTit.insertBefore(imgTit, lblTit.firstChild);
      
      const wrapTit=document.createElement('div'); 
      wrapTit.className='chk-item';
      wrapTit.style.cursor = 'pointer';
      wrapTit.appendChild(chkTit); 
      wrapTit.appendChild(lblTit);
      
      // Hacer que todo el wrap sea clickeable
      wrapTit.addEventListener('click', (e) => {
        // Si no se hizo click directamente en el checkbox, disparar su click
        if(e.target !== chkTit) {
          chkTit.click();
        }
      });
      
      chkTit.addEventListener('change', ()=>{
        wrapTit.classList.toggle('selected', chkTit.checked);
      });
      titulares.appendChild(wrapTit);
    });

    // Function to render suplentes excluding selected titulares
    function renderSuplentes(){
      const selectedTitulares = new Set(Array.from(document.querySelectorAll('.titular-chk:checked')).map(c=> parseInt(c.value)));
      suplentes.innerHTML='';
      jugadoresNoPorteros.forEach(j=>{
        if(selectedTitulares.has(j.jugador_id)) return; // exclude already selected titulares
        const wrapSup = createOption(j, 'suplente-chk');
        suplentes.appendChild(wrapSup);
      });
      // attach change listeners after re-render
      document.querySelectorAll('.suplente-chk').forEach(chk => {
        chk.addEventListener('change', e => {
          if(e.target.checked){
            const jugadorId = e.target.dataset.jugadorId;
            const titularChk = document.querySelector(`.titular-chk[data-jugador-id="${jugadorId}"]`);
            if(titularChk) titularChk.checked = false;
            // Do NOT re-render here to preserve current suplente selections
          }
        });
      });
    }

    // Initial render of suplentes
    renderSuplentes();
    
    // Event listeners para sincronizar selección entre titulares y suplentes
    document.querySelectorAll('.titular-chk').forEach(chk => {
      chk.addEventListener('change', e => {
        if(e.target.checked){
          // Si se marca como titular, desmarcar de suplentes
          const jugadorId = e.target.dataset.jugadorId;
          const suplenteChk = document.querySelector(`.suplente-chk[data-jugador-id="${jugadorId}"]`);
          if(suplenteChk) suplenteChk.checked = false;
        }
        // Re-render suplentes to reflect inclusion/exclusion after titular changes
        renderSuplentes();
      });
    });
    
    // suplente-chk listeners are attached inside renderSuplentes
  } catch(err){
    console.error(err);
    mostrarMensaje('Error cargando jugadores','error');
  }
}

// Helpers para obtener IDs y objetos de jugadores seleccionados en el DOM
function getCheckedIds(selector){
  return Array.from(document.querySelectorAll(selector)).map(c => parseInt(c.value));
}

function getCheckedPlayers(selector){
  const ids = getCheckedIds(selector);
  return jugadores.filter(j => ids.includes(j.jugador_id));
}

document.addEventListener('DOMContentLoaded',()=>{
  const eqSelect = document.getElementById('equipo_id');
  if(eqSelect){
    eqSelect.addEventListener('change', e=> cargarJugadoresEquipo(e.target.value));
  }
    const goStep2 = document.getElementById('go-step-2');
    const backStep1 = document.getElementById('back-step-1');
    const step1 = document.getElementById('form-step-1');
    const step2 = document.getElementById('form-step-2');

    if(goStep2){
      goStep2.addEventListener('click', ()=>{
        const porteroId = document.getElementById('portero_id').value;
        const defensas = parseInt(document.getElementById('defensas').value||'0');
        const mediocampistas = parseInt(document.getElementById('mediocampistas').value||'0');
        const delanteros = parseInt(document.getElementById('delanteros').value||'0');
        const titularesSel = Array.from(document.querySelectorAll('.titular-chk:checked')).map(c=> parseInt(c.value));

        if(!porteroId){ return mostrarMensaje('Debe seleccionar un portero titular','error'); }
        if(defensas + mediocampistas + delanteros !== 10){
          return mostrarMensaje('La suma de defensas, mediocampistas y delanteros debe ser 10','error');
        }
        if(titularesSel.length !== 10){
          return mostrarMensaje('Debe seleccionar exactamente 10 jugadores de campo','error');
        }
        
        // Validar que las posiciones coincidan con las cantidades ingresadas
        const validacion = validarFormulario();
        if(!validacion){
          return; // validarFormulario ya mostró el mensaje de error
        }
        
        // Paso al Step 2
        if(step1 && step2){ step1.style.display='none'; step2.style.display='block'; }
      });
    }
    if(backStep1){
      backStep1.addEventListener('click', ()=>{
        if(step1 && step2){ step1.style.display='block'; step2.style.display='none'; }
      });
    }
  const form = document.getElementById('formacion-form');
  if(form){
    form.addEventListener('submit', async e => {
      e.preventDefault();
      const equipoId = document.getElementById('equipo_id').value;
      const porteroId = document.getElementById('portero_id').value;
      const defensas = document.getElementById('defensas').value;
      const mediocampistas = document.getElementById('mediocampistas').value;
      const delanteros = document.getElementById('delanteros').value;
      // collect selected
      const titularesSel = Array.from(document.querySelectorAll('.titular-chk:checked')).map(c=> parseInt(c.value));
      const suplentesSel = Array.from(document.querySelectorAll('.suplente-chk:checked')).map(c=> parseInt(c.value));

      // Validar que no se haya seleccionado el mismo jugador en ambas listas
      const duplicados = titularesSel.filter(id => suplentesSel.includes(id));
      if(duplicados.length > 0){
        mostrarMensaje('Un jugador no puede estar como titular y suplente al mismo tiempo','error');
        return;
      }

      if(titularesSel.length !== 10){
        mostrarMensaje('Debe seleccionar exactamente 10 jugadores titulares (sin contar el portero)','error');
        return;
      }
      if(suplentesSel.length > 9){
        mostrarMensaje('Puede seleccionar hasta 9 suplentes','error');
        return;
      }
      if(!porteroId){
        mostrarMensaje('Debe seleccionar un portero titular','error');
        return;
      }
      
      // Agregar el portero a la lista de titulares para enviar al backend (debe ser 11 en total)
      const titularesConPortero = [parseInt(porteroId), ...titularesSel];

      const payload = {
        equipo_id: parseInt(equipoId),
        portero_id: parseInt(porteroId),
        defensas: parseInt(defensas),
        mediocampistas: parseInt(mediocampistas),
        delanteros: parseInt(delanteros)
      };

      try {
        const resp = await fetch('/formaciones/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ data: payload, titulares: titularesConPortero, suplentes: suplentesSel })
        });
        if(resp.ok){
          mostrarMensaje('Formación creada correctamente');
          cerrarFormulario();
          setTimeout(()=> location.reload(), 1000);
        } else {
          const errData = await resp.json().catch(()=>({}));
          mostrarMensaje(errData.detail || 'Error creando formación','error');
        }
      } catch(err){
        console.error(err);
        mostrarMensaje('Error de red al crear formación','error');
      }
    });
  }
});

function verFormacion(id){
  alert('Ver detalles formación ' + id); // Placeholder
}

// Close modal click outside
window.onclick = function(ev){
  const modal = document.getElementById('formulario-formacion');
  if(ev.target === modal){ cerrarFormulario(); }
};

function validarFormulario(){
  // Jugadores titulares seleccionados (objetos completos)
  const titularesSeleccionados = getCheckedPlayers('.titular-chk:checked');
  
  // Filtrar por posición (usar OR en lugar de AND)
  const defensas = titularesSeleccionados.filter(j => j.posicion === 'DEFENSOR' || j.posicion === 'defensor');
  const mediocampistas = titularesSeleccionados.filter(j => j.posicion === 'MEDIOCAMPISTA' || j.posicion === 'mediocampista');
  const delanteros = titularesSeleccionados.filter(j => j.posicion === 'DELANTERO' || j.posicion === 'delantero');

  console.log('Defensas:', defensas);
  console.log('Mediocampistas:', mediocampistas);
  console.log('Delanteros:', delanteros);

  // Validar que coincidan las cantidades ingresadas
  const defensasInput = parseInt(document.getElementById('defensas').value || '0');
  const mediocampistasInput = parseInt(document.getElementById('mediocampistas').value || '0');
  const delanterosInput = parseInt(document.getElementById('delanteros').value || '0');

  if(defensas.length !== defensasInput){
    mostrarMensaje(`Debe seleccionar ${defensasInput} defensas, tiene ${defensas.length}`, 'error');
    return null;
  }
  if(mediocampistas.length !== mediocampistasInput){
    mostrarMensaje(`Debe seleccionar ${mediocampistasInput} mediocampistas, tiene ${mediocampistas.length}`, 'error');
    return null;
  }
  if(delanteros.length !== delanterosInput){
    mostrarMensaje(`Debe seleccionar ${delanterosInput} delanteros, tiene ${delanteros.length}`, 'error');
    return null;
  }

  return { titularesSeleccionados, defensas, mediocampistas, delanteros };
}