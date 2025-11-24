// Admin - Gestión de Formaciones

function mostrarFormulario(){
  document.getElementById('formulario-formacion').style.display='flex';
  document.getElementById('formacion-form').reset();
  document.getElementById('titulares-container').innerHTML='';
  document.getElementById('suplentes-container').innerHTML='';
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

async function cargarJugadoresEquipo(equipoId){
  if(!equipoId){
    document.getElementById('portero_id').innerHTML='';
    document.getElementById('titulares-container').innerHTML='';
    document.getElementById('suplentes-container').innerHTML='';
    return;
  }
  try {
    const resp = await fetch(`/jugadores/equipo/${equipoId}`);
    const jugadores = await resp.json();
    const porteroSelect = document.getElementById('portero_id');
    porteroSelect.innerHTML='<option value="">Seleccione portero</option>';
    jugadores.forEach(j=>{
      if(j.posicion === 'portero'){
        porteroSelect.innerHTML += `<option value="${j.jugador_id}">${j.nombre} ${j.apellido}</option>`;
      }
    });
    // build selectable lists
    const titulares = document.getElementById('titulares-container');
    const suplentes = document.getElementById('suplentes-container');
    titulares.innerHTML='';
    suplentes.innerHTML='';
    jugadores.forEach(j=>{
      const chkTit = document.createElement('input');
      chkTit.type='checkbox';
      chkTit.value=j.jugador_id;
      chkTit.name='titular';
      chkTit.className='titular-chk';
      const lblTit = document.createElement('label');
      lblTit.textContent=`${j.nombre} ${j.apellido} (${j.posicion})`; 
      const wrapTit=document.createElement('div'); wrapTit.className='chk-item';
      wrapTit.appendChild(chkTit); wrapTit.appendChild(lblTit);
      titulares.appendChild(wrapTit);

      const chkSup = document.createElement('input');
      chkSup.type='checkbox';
      chkSup.value=j.jugador_id;
      chkSup.name='suplente';
      chkSup.className='suplente-chk';
      const lblSup=document.createElement('label');
      lblSup.textContent=`${j.nombre} ${j.apellido} (${j.posicion})`;
      const wrapSup=document.createElement('div'); wrapSup.className='chk-item';
      wrapSup.appendChild(chkSup); wrapSup.appendChild(lblSup);
      suplentes.appendChild(wrapSup);
    });
  } catch(err){
    console.error(err);
    mostrarMensaje('Error cargando jugadores','error');
  }
}

document.addEventListener('DOMContentLoaded',()=>{
  const eqSelect = document.getElementById('equipo_id');
  if(eqSelect){
    eqSelect.addEventListener('change', e=> cargarJugadoresEquipo(e.target.value));
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

      if(titularesSel.length !== 11){
        mostrarMensaje('Debe seleccionar exactamente 11 titulares','error');
        return;
      }
      if(suplentesSel.length > 9){
        mostrarMensaje('Puede seleccionar hasta 9 suplentes','error');
        return;
      }
      if(!titularesSel.includes(parseInt(porteroId))){
        mostrarMensaje('El portero debe estar entre los titulares','error');
        return;
      }

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
          body: JSON.stringify({ data: payload, titulares: titularesSel, suplentes: suplentesSel })
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
