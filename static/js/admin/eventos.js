// Admin - Eventos del Partido

async function cargarPartido(partidoId){
  const r = await fetch(`/partidos/id/${partidoId}`);
  if(!r.ok) throw new Error('No se pudo cargar el partido');
  return r.json();
}

async function cargarJugadoresEquipo(equipoId){
  const r = await fetch(`/jugadores/equipo/${equipoId}`);
  if(!r.ok) return [];
  return r.json();
}

async function cargarEventos(partidoId){
  const r = await fetch(`/eventos/partido/${partidoId}`);
  if(!r.ok) return [];
  return r.json();
}

function renderPartidoHeader(p){
  const titulo = document.getElementById('partido-titulo');
  const detalle = document.getElementById('partido-detalle');
  titulo.textContent = `${p.equipo_local_nombre} vs ${p.equipo_visitante_nombre}`;
  detalle.textContent = `${p.fecha} • ${p.hora || ''} • ${p.lugar || ''} • Estado: ${p.estado}`;
}

function fillSelect(select, items, getVal, getText){
  select.innerHTML = '<option value="">Seleccione...</option>';
  items.forEach(it=>{
    const opt = document.createElement('option');
    opt.value = getVal(it);
    opt.textContent = getText(it);
    select.appendChild(opt);
  });
}

function renderEventos(lista){
  const cont = document.getElementById('eventos-lista');
  if(!lista || lista.length === 0){
    cont.innerHTML = '<div class="muted">No hay eventos</div>';
    return;
  }
  cont.innerHTML = '';
  lista.forEach(e=>{
    const row = document.createElement('div');
    row.className = 'list-item';
    const tipo = e.tipo.replace('_', ' ');
    const jug = e.jugador_nombre ? ` - ${e.jugador_nombre}` : '';
    const asoc = e.jugador_asociado_nombre ? ` → ${e.jugador_asociado_nombre}` : '';
    row.textContent = `${e.minuto}' • ${tipo}${jug}${asoc}${e.descripcion ? ' • '+e.descripcion : ''}`;
    cont.appendChild(row);
  });
}

async function init(){
  const partidoId = window.__PARTIDO_ID__ || document.getElementById('partido_id').value;
  try{
    const p = await cargarPartido(partidoId);
    renderPartidoHeader(p);

    // Autocompletar minuto según parte y tiempos del partido
    const minutoInput = document.getElementById('minuto');
    function timeToMinutes(str){
      if(!str) return null;
      const parts = str.split(':');
      const h = parseInt(parts[0]||'0',10);
      const m = parseInt(parts[1]||'0',10);
      return h*60 + m;
    }
    function nowMinutes(){
      const d = new Date();
      return d.getHours()*60 + d.getMinutes();
    }
    function calcularMinutoActual(){
      if(String(p.estado).toUpperCase() !== 'EN_CURSO') return null;
      const parte = p.parte || 'PRIMER_TIEMPO';
      const now = nowMinutes();
      let base = 0, inicio = null;
      switch(parte){
        case 'PRIMER_TIEMPO':
          base = 0;
          inicio = timeToMinutes(p.hora_inicio);
          break;
        case 'SEGUNDO_TIEMPO':
          base = 45;
          inicio = timeToMinutes(p.hora_inicio_segundo_tiempo);
          break;
        case 'PRIMER_TIEMPO_EXTRA':
          base = 90;
          inicio = timeToMinutes(p.hora_inicio_primer_tiempo_extra);
          break;
        case 'SEGUNDO_TIEMPO_EXTRA':
          base = 105;
          inicio = timeToMinutes(p.hora_inicio_segundo_tiempo_extra);
          break;
        default:
          inicio = timeToMinutes(p.hora_inicio);
          base = 0;
      }
      if(inicio == null) return null;
      const transcurrido = Math.max(0, now - inicio);
      return Math.min(120, base + transcurrido);
    }
    function actualizarMinuto(){
      const minuto = calcularMinutoActual();
      if(minuto !== null){
        minutoInput.value = minuto;
      }
    }
    actualizarMinuto();
    // Actualizar cada 30 segundos para que aparezca solo sin intervención
    setInterval(actualizarMinuto, 30000);

    // Equipos en select
    const equipoSelect = document.getElementById('equipo_id');
    fillSelect(equipoSelect, [
      { id: p.equipo_local_id, nombre: p.equipo_local_nombre },
      { id: p.equipo_visitante_id, nombre: p.equipo_visitante_nombre }
    ], x=> x.id, x=> x.nombre);

    // Jugadores dinámicos según equipo
    const jugadorSelect = document.getElementById('jugador_id');
    const asociadoSelect = document.getElementById('jugador_asociado_id');

    // Cache de eventos del partido para filtrar asociados según tipo
    let eventosCache = [];
    try { eventosCache = await cargarEventos(partidoId); } catch(_) {}

    async function updateJugadores() {
      const eqId = parseInt(equipoSelect.value);
      if (!eqId){
        jugadorSelect.innerHTML = '';
        asociadoSelect.innerHTML = '';
        return;
      }

      // === 1. Cargar jugadores del equipo actual ===
      const jugadores = await cargarJugadoresEquipo(eqId);

      // === 2. Cargar jugadores del rival ===
      // Necesitamos el objeto partido (p), asegúrate que esté disponible
      const esLocal = eqId === p.equipo_local_id;
      const eqRivalId = esLocal ? p.equipo_visitante_id : p.equipo_local_id;

      const jugadoresRival = await cargarJugadoresEquipo(eqRivalId);

      // === 3. Obtener jugadores activos desde backend ===
      let activosLocal = new Set();
      let activosVisitante = new Set();

      try {
        const activosResp = await fetch(`/partidos/${partidoId}/jugadores_en_cancha`);
        if (activosResp.ok) {
          const activosData = await activosResp.json();
          activosLocal = new Set((activosData.local || []).map(j => j.jugador_id));
          activosVisitante = new Set((activosData.visitante || []).map(j => j.jugador_id));
        }
      } catch (_) {}

      // === 4. Determinar activos de cada lado según eqId ===
      const activosSet = esLocal ? activosLocal : activosVisitante;
      const activosRivalSet = esLocal ? activosVisitante : activosLocal;

      const jugadoresActivos = jugadores.filter(j => activosSet.has(j.jugador_id));
      const jugadoresActivosRival = jugadoresRival.filter(j => activosRivalSet.has(j.jugador_id));

      // === 5. Lista principal (jugador involucrado)
      const listaPrincipal = jugadoresActivos.length > 0 ? jugadoresActivos : jugadores;

      fillSelect(
        jugadorSelect,
        listaPrincipal,
        j => j.jugador_id,
        j => `${j.nombre} ${j.apellido} (${j.posicion})`
      );

      // === 6. Construir asociados según tipo de evento ===

      function fillAsociado() {
        const tipo = document.getElementById('tipo').value;
        asociadoSelect.innerHTML = '<option value="">Ninguno</option>';

        // -- Sustitución: suplentes --
        if (tipo === 'sustitucion') {
          (async () => {
            try {
              const r = await fetch(`/partidos/${partidoId}/suplentes_en_cancha`);
              if (!r.ok) throw new Error();
              const data = await r.json();
              const lado = esLocal ? 'local' : 'visitante';
              const lista = Array.isArray(data[lado]) ? data[lado] : [];
              const idsBanca = new Set(lista.map(j => j.jugador_id));
              const candidatos = jugadores.filter(j => idsBanca.has(j.jugador_id));

              candidatos.forEach(j => {
                const opt = document.createElement('option');
                opt.value = j.jugador_id;
                opt.textContent = `${j.nombre} ${j.apellido} (${j.posicion})`;
                asociadoSelect.appendChild(opt);
              });

            } catch (_) {
              // fallback
              const candidatos = jugadores.filter(j => !activosSet.has(j.jugador_id));
              candidatos.forEach(j => {
                const opt = document.createElement('option');
                opt.value = j.jugador_id;
                opt.textContent = `${j.nombre} ${j.apellido} (${j.posicion})`;
                asociadoSelect.appendChild(opt);
              });
            }
          })();

        // -- Gol: jugadores activos del propio equipo --
        } else if (tipo === 'gol') {
          jugadoresActivos.forEach(j => {
            const opt = document.createElement('option');
            opt.value = j.jugador_id;
            opt.textContent = `${j.nombre} ${j.apellido} (${j.posicion})`;
            asociadoSelect.appendChild(opt);
          });

        // -- Entrada / Intercepción: jugadores activos del rival --
        } else if (tipo === 'entrada' || tipo === 'intercepcion') {
          jugadoresActivosRival.forEach(j => {
            const opt = document.createElement('option');
            opt.value = j.jugador_id;
            opt.textContent = `${j.nombre} ${j.apellido} (${j.posicion})`;
            asociadoSelect.appendChild(opt);
          });
        }
      }

      fillAsociado();

      // === 7. Actualizar dinámico cuando cambia el tipo ===
      document.getElementById('tipo').removeEventListener('change', fillAsociado);
      document.getElementById('tipo').addEventListener('change', fillAsociado);
    }


    equipoSelect.addEventListener('change', updateJugadores);
    await updateJugadores();

    // Cargar eventos existentes
    const eventos = await cargarEventos(partidoId).catch(()=>[]);
    renderEventos(eventos);

    // Submit
    const form = document.getElementById('evento-form');
    form.addEventListener('submit', async (e)=>{
      e.preventDefault();
      const fd = new FormData();
      fd.append('minuto', document.getElementById('minuto').value);
      // limitar a tipos esperados en UI
      const tipoVal = document.getElementById('tipo').value;
      const tiposPermitidos = new Set([  'gol','penal','penal_fallado','gol_en_contra','tarjeta_amarilla','tarjeta_roja','sustitucion','tiro','tiro_a_puerta','entrada','intercepcion']);
      fd.append('tipo', tiposPermitidos.has(tipoVal) ? tipoVal : 'gol');
      fd.append('descripcion', document.getElementById('descripcion').value);
      fd.append('partido_id', partidoId);
      fd.append('equipo_id', document.getElementById('equipo_id').value);
      fd.append('jugador_id', document.getElementById('jugador_id').value);
      const asociadoVal = document.getElementById('jugador_asociado_id').value;
      if(asociadoVal) fd.append('jugador_asociado_id', asociadoVal);
      try{
        const resp = await fetch('/eventos/', { method: 'POST', body: fd });
        if(!resp.ok){
          const err = await resp.json().catch(()=>({}));
          throw new Error(err.detail || 'Error al crear evento');
        }
        mostrarMensaje('Evento registrado');
        setTimeout(() => {window.location.reload();}, 1000);
      }catch(err){
        mostrarMensaje(err.message, 'error');
      }
    });
  }catch(err){
    mostrarMensaje('Error cargando datos del partido', 'error');
  }
}

document.addEventListener('DOMContentLoaded', init);
