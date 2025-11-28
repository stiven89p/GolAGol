// javascript
(() => {
  // tomar logo por defecto desde el DOM si existe; si no, usar fallback absoluto
  const defaultLogoEl = document.querySelector('img.logo');
  const defaultLogo = defaultLogoEl ? defaultLogoEl.getAttribute('src') : '/static/img/default_logo.png';

  const formatDate = (iso) => {
    const d = new Date(iso);
    if (isNaN(d)) return null;
    return new Intl.DateTimeFormat('es-ES', {
      year: 'numeric', month: 'short', day: '2-digit'
    }).format(d);
  };

  const numberSafe = (v) => (v === null || v === undefined) ? '0' : String(v);

  // Extrae equipo_id desde: a) elemento con data-equipo-id, b) meta, c) url /equipo/{id}
  const detectEquipoId = () => {
    const el = document.querySelector('[data-equipo-id]');
    if (el && el.dataset.equipoId) return el.dataset.equipoId;

    const meta = document.querySelector('meta[name="equipo-id"]');
    if (meta && meta.content) return meta.content;

    const m = location.pathname.match(/\/equipo[s]?\/(\d+)/);
    if (m) return m[1];

    return null;
  };

  // Renderiza la lista de estadísticas dentro de la sección .estadisticas
  const renderEstadisticas = (stats) => {
    const statsSection = document.querySelector('.estadisticas');
    if (!statsSection) return;

    const title = statsSection.querySelector('h2');
    statsSection.innerHTML = '';
    if (title) statsSection.appendChild(title);

    if (!Array.isArray(stats) || stats.length === 0) {
      const p = document.createElement('p');
      p.className = 'no-stats';
      p.textContent = 'No hay estadísticas disponibles';
      statsSection.appendChild(p);
      return;
    }

    stats.forEach(s => {
      const article = document.createElement('article');
      article.className = 'estadistica-item';

      const h3 = document.createElement('h3');
      h3.textContent = `Temporada: ${s.temporada ?? '—'}`;
      article.appendChild(h3);

      const table = document.createElement('table');
      table.className = 'stats-table';
      const tbody = document.createElement('tbody');

      const addRow = (label, value) => {
        const tr = document.createElement('tr');
        const th = document.createElement('th');
        th.textContent = label;
        const td = document.createElement('td');
        td.textContent = value;
        tr.appendChild(th);
        tr.appendChild(td);
        tbody.appendChild(tr);
      };

      addRow('Partidos jugados', numberSafe(s.partidos_jugados));
      addRow('Victorias', numberSafe(s.victorias));
      addRow('Empates', numberSafe(s.empates));
      addRow('Derrotas', numberSafe(s.derrotas));
      addRow('Goles a favor', numberSafe(s.goles_favor));
      addRow('Goles en contra', numberSafe(s.goles_contra));
      addRow('Puntos', numberSafe(s.puntos));
      addRow('Tarjetas amarillas', numberSafe(s.tarjetas_amarillas));
      addRow('Tarjetas rojas', numberSafe(s.tarjetas_rojas));

      table.appendChild(tbody);
      article.appendChild(table);
      statsSection.appendChild(article);
    });
  };

  // Fetch de estadísticas por equipo
  const fetchAndRenderStats = async (equipoId) => {
    if (!equipoId) return;
    try {
      const res = await fetch(`/estadisticas_equipos/equipo/${encodeURIComponent(equipoId)}`);
      if (!res.ok) {
        console.warn('No se pudieron obtener estadísticas:', res.status);
        renderEstadisticas([]);
        return;
      }
      const datos = await res.json();
      renderEstadisticas(Array.isArray(datos) ? datos : []);
    } catch (err) {
      console.error('Error al cargar estadísticas:', err);
      renderEstadisticas([]);
    }
  };

  // Renderiza jugadores por posición
  const renderJugadoresPorPosicion = (jugadores) => {
    const porterosList = document.getElementById('porteros-lista');
    const defensasList = document.getElementById('defensas-lista');
    const mediocampistasList = document.getElementById('mediocampistas-lista');
    const delanterosList = document.getElementById('delanteros-lista');

    if (!porterosList || !defensasList || !mediocampistasList || !delanterosList) return;

    const porteros = jugadores.filter(j => j.posicion === 'portero');
    const defensas = jugadores.filter(j => j.posicion === 'defensor');
    const mediocampistas = jugadores.filter(j => j.posicion === 'mediocampista');
    const delanteros = jugadores.filter(j => j.posicion === 'delantero');

    const renderGrupo = (lista, jugadoresGrupo) => {
      lista.innerHTML = '';
      if (jugadoresGrupo.length === 0) {
        const p = document.createElement('p');
        p.textContent = 'No hay jugadores en esta posición';
        p.className = 'no-jugadores';
        lista.appendChild(p);
        return;
      }

      jugadoresGrupo.forEach(j => {
        const link = document.createElement('a');
        link.href = `/jugador/${j.jugador_id}`;
        link.className = 'jugador-link jugador-card';
        link.title = `Ver perfil de ${j.nombre} ${j.apellido}`;

        const img = document.createElement('img');
        img.src = j.foto ? `/static/img/${j.foto}` : '/static/img/default-player.png';
        img.alt = `${j.nombre} ${j.apellido}`;
        img.className = 'jugador-foto';
        img.onerror = function() {
          if (this.src !== '/static/img/default-player.png') {
            this.src = '/static/img/default-player.png';
          }
        };

        const nombre = document.createElement('p');
        nombre.className = 'jugador-nombre';
        nombre.textContent = `${j.nombre} ${j.apellido}`;

        const edad = document.createElement('small');
        edad.className = 'jugador-edad';
        if (j.fecha_nacimiento) {
          const nacimiento = new Date(j.fecha_nacimiento);
          const hoy = new Date();
          let edadCalculada = hoy.getFullYear() - nacimiento.getFullYear();
          const m = hoy.getMonth() - nacimiento.getMonth();
          if (m < 0 || (m === 0 && hoy.getDate() < nacimiento.getDate())) {
            edadCalculada--;
          }
          edad.textContent = `${edadCalculada} años`;
        }

        link.append(img, nombre, edad);
        lista.appendChild(link);
      });
    };

    renderGrupo(porterosList, porteros);
    renderGrupo(defensasList, defensas);
    renderGrupo(mediocampistasList, mediocampistas);
    renderGrupo(delanterosList, delanteros);
  };

  // Fetch de jugadores del equipo
  const fetchAndRenderJugadores = async (equipoId) => {
    if (!equipoId) return;
    try {
      const res = await fetch(`/jugadores/equipo/${encodeURIComponent(equipoId)}`);
      if (!res.ok) {
        console.warn('No se pudieron obtener jugadores:', res.status);
        renderJugadoresPorPosicion([]);
        return;
      }
      const datos = await res.json();
      renderJugadoresPorPosicion(Array.isArray(datos) ? datos : []);
    } catch (err) {
      console.error('Error al cargar jugadores:', err);
      renderJugadoresPorPosicion([]);
    }
  };

  // Renderizar goleadores del equipo en el resumen
  const renderGoleadoresEquipo = (goleadores) => {
    const lista = document.getElementById('goleadores-equipo-lista');
    if (!lista) return;

    lista.innerHTML = '';

    if (!goleadores || goleadores.length === 0) {
      const p = document.createElement('p');
      p.textContent = 'No hay goleadores registrados';
      p.className = 'no-goleadores';
      lista.appendChild(p);
      return;
    }

    goleadores.forEach(g => {
      const div = document.createElement('div');
      div.className = 'jugador-card goleador-item';

      const img = document.createElement('img');
      img.src = g.jugador_foto ? `/static/img/${g.jugador_foto}` : '/static/img/default-player.png';
      img.alt = `${g.jugador_nombre} ${g.jugador_apellido}`;
      img.className = 'jugador-foto';
      img.onerror = function() {
        if (this.src !== '/static/img/default-player.png') {
          this.src = '/static/img/default-player.png';
        }
      };

      const info = document.createElement('div');
      info.className = 'jugador-info';

      const nombre = document.createElement('p');
      nombre.className = 'jugador-nombre';
      nombre.textContent = `${g.jugador_nombre} ${g.jugador_apellido}`;

      const posicion = document.createElement('small');
      posicion.className = 'jugador-posicion';
      posicion.textContent = `#${g.posicion}`;

      info.append(nombre, posicion);

      const goles = document.createElement('div');
      goles.className = 'jugador-goles';
      goles.innerHTML = `<strong>${g.goles}</strong> <small>goles</small>`;

      div.append(img, info, goles);
      lista.appendChild(div);
    });
  };

  // Fetch de goleadores del equipo
  const fetchAndRenderGoleadores = async (equipoId) => {
    if (!equipoId) return;
    try {
      // Asumiendo temporada_id = 1 (puedes hacerlo dinámico)
      const res = await fetch(`/estadisticas_jugadores/temporada/1/${encodeURIComponent(equipoId)}/goleadores?limit=5`);
      if (!res.ok) {
        console.warn('No se pudieron obtener goleadores:', res.status);
        renderGoleadoresEquipo([]);
        return;
      }
      const datos = await res.json();
      renderGoleadoresEquipo(Array.isArray(datos) ? datos : []);
    } catch (err) {
      console.error('Error al cargar goleadores:', err);
      renderGoleadoresEquipo([]);
    }
  };

  // Crea una tarjeta DOM para un partido
  const createMatchCard = (p, isNext, equipoNombre) => {
      const div = document.createElement('div');
      div.className = isNext ? 'match-card next' : 'match-card';
      div.dataset.id = p.partido_id ?? '';

      // 🛡️ contenedor principal horizontal
      const matchRow = document.createElement('div');
      matchRow.className = 'match-row';

      // 🟦 Escudo local
      const localLogo = document.createElement('img');
      localLogo.className = 'escudo local';
      localLogo.alt = `Escudo ${p.equipo_local_nombre || 'Local'}`;
      localLogo.src = p.equipo_local_logo ? `/static/img/${p.equipo_local_logo}` : '/static/img/default_logo.png';
      localLogo.onerror = function() { 
        if (this.src !== '/static/img/default_logo.png') {
          this.src = '/static/img/default_logo.png'; 
        }
      };

      // 🟥 Escudo visitante
      const visitanteLogo = document.createElement('img');
      visitanteLogo.className = 'escudo visitante';
      visitanteLogo.alt = `Escudo ${p.equipo_visitante_nombre || 'Visitante'}`;
      visitanteLogo.src = p.equipo_visitante_logo ? `/static/img/${p.equipo_visitante_logo}` : '/static/img/default_logo.png';
      visitanteLogo.onerror = function() { 
        if (this.src !== '/static/img/default_logo.png') {
          this.src = '/static/img/default_logo.png'; 
        }
      };

      // ⚽ marcador central
      const marcadorDiv = document.createElement('div');
      marcadorDiv.className = 'marcador';

      const localName = document.createElement('span');
      localName.className = 'eq-name';
      localName.textContent = p.equipo_local_nombre || '—';

      const resultado = document.createElement('strong');
      resultado.className = 'resultado';
      resultado.textContent =
        p.estado !== 'PROGRAMADO' && p.goles_local != null && p.goles_visitante != null
          ? `${p.goles_local} - ${p.goles_visitante}`
          : 'vs';

      const visitanteName = document.createElement('span');
      visitanteName.className = 'eq-name';
      visitanteName.textContent = p.equipo_visitante_nombre || '—';

      marcadorDiv.append(localName, resultado, visitanteName);

      // ensamblar fila: escudo-local | marcador | escudo-visitante
      matchRow.append(localLogo, marcadorDiv, visitanteLogo);

      // 📅 fecha y lugar debajo
      const fecha = document.createElement('small');
      fecha.className = 'fecha-hora';
      let fechaText = formatDate(p.fecha);
      if (p.hora) fechaText = fechaText ? `${fechaText} - ${p.hora}` : p.hora;
      fecha.textContent = fechaText || '';

      const lugar = document.createElement('p');
      lugar.className = 'lugar';
      if (p.lugar) lugar.textContent = `📍 ${p.lugar}`;

      div.append(matchRow, fecha, lugar);
      
      // Hacer la tarjeta clicable para ir al detalle del partido
      if (p.partido_id) {
        div.style.cursor = 'pointer';
        div.addEventListener('click', () => {
          window.location.href = `/partido/${encodeURIComponent(p.partido_id)}`;
        });
      }
      
      return div;
  };


  // Renderiza proximos y jugados
  const renderMatches = (matches, equipoId) => {
    const proximosLista = document.getElementById('proximos-lista');
    const resultadosLista = document.getElementById('resultados-lista');

    // separar por estado
    const próximos = matches.filter(m => m.estado === 'PROGRAMADO');
    const jugados = matches.filter(m => m.estado === 'FINALIZADO');

    // ordenar
    próximos.sort((a, b) => new Date(a.fecha) - new Date(b.fecha));
    jugados.sort((a, b) => new Date(b.fecha) - new Date(a.fecha));

    const equipoNombre = document.querySelector('header h1')?.textContent?.trim() ?? '';

    // Renderizar resumen (destacados)
    renderResumen(matches);

    // Renderizar lista completa de próximos
    if (proximosLista) {
      proximosLista.innerHTML = '';
      if (próximos.length === 0) {
        const p = document.createElement('p');
        p.textContent = 'No hay próximos partidos programados.';
        proximosLista.appendChild(p);
      } else {
        próximos.forEach(p => {
          proximosLista.appendChild(createMatchCard(p, true, equipoNombre));
        });
      }
    }

    // Renderizar lista completa de resultados
    if (resultadosLista) {
      resultadosLista.innerHTML = '';
      if (jugados.length === 0) {
        const p = document.createElement('p');
        p.textContent = 'No hay resultados recientes.';
        resultadosLista.appendChild(p);
      } else {
        jugados.forEach(p => {
          resultadosLista.appendChild(createMatchCard(p, false, equipoNombre));
        });
      }
    }

    makeCardsClickable();
  };

  // Fetch de partidos del equipo (todos) y render
  const fetchAndRenderMatches = async (equipoId) => {
    if (!equipoId) return;
    try {
      const res = await fetch(`/partidos/equipo/${encodeURIComponent(equipoId)}`);
      if (!res.ok) {
        console.warn('No se pudieron obtener partidos:', res.status);
        return;
      }
      const datos = await res.json();
      if (!Array.isArray(datos)) return;
      renderMatches(datos, equipoId);
    } catch (err) {
      console.error('Error al cargar partidos:', err);
    }
  };

  // Hacer tarjetas clicables; usar ruta /equipo/{id}
  const makeCardsClickable = () => {
    document.querySelectorAll('.card, .card.next').forEach(card => {
      let id = card.dataset.equipoId || card.dataset.oponenteId || card.dataset.id;
      if (!id) {
        const link = card.querySelector('a[href*="/equipo/"], a[href*="/equipos/"]');
        if (link) {
          const m = link.getAttribute('href').match(/\/equipo[s]?\/(.+)/);
          if (m) id = decodeURIComponent(m[1]);
        }
      }
      if (!id) return;
      card.style.cursor = 'pointer';
      card.setAttribute('role', 'link');
      card.tabIndex = 0;
      const target = `/equipo/${encodeURIComponent(id)}`;
      const go = () => { window.location.href = target; };
      // evitar duplicar listeners
      card.removeEventListener('click', go);
      card.addEventListener('click', go);
      card.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') go(); });
    });
  };

  // Manejo de pestañas
  const setupTabs = () => {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const targetTab = btn.dataset.tab;
        
        // Remover active de todos
        tabBtns.forEach(b => b.classList.remove('active'));
        tabContents.forEach(c => c.classList.remove('active'));
        
        // Activar el seleccionado
        btn.classList.add('active');
        const targetContent = document.getElementById(`tab-${targetTab}`);
        if (targetContent) targetContent.classList.add('active');
      });
    });
  };

  // Renderizar resumen destacado
  const renderResumen = (partidos) => {
    const proximoDestacado = document.getElementById('proximo-destacado');
    const ultimoDestacado = document.getElementById('ultimo-destacado');

    if (!proximoDestacado || !ultimoDestacado) return;

    const programados = partidos.filter(p => p.estado === 'PROGRAMADO');
    const finalizados = partidos.filter(p => p.estado === 'FINALIZADO');

    programados.sort((a, b) => new Date(a.fecha) - new Date(b.fecha));
    finalizados.sort((a, b) => new Date(b.fecha) - new Date(a.fecha));

    // Próximo partido
    if (programados.length > 0) {
      const p = programados[0];
      const card = createMatchCard(p, true, '');
      card.classList.add('partido-destacado');
      proximoDestacado.innerHTML = '';
      proximoDestacado.appendChild(card);
    } else {
      proximoDestacado.innerHTML = '<p>No hay próximos partidos</p>';
    }

    // Último resultado
    if (finalizados.length > 0) {
      const p = finalizados[0];
      const card = createMatchCard(p, false, '');
      card.classList.add('partido-destacado');
      ultimoDestacado.innerHTML = '';
      ultimoDestacado.appendChild(card);
    } else {
      ultimoDestacado.innerHTML = '<p>No hay resultados recientes</p>';
    }
  };

  document.addEventListener('DOMContentLoaded', () => {
    // Setup tabs
    setupTabs();

    // Reemplaza imágenes rotas o vacías por el logo por defecto
    document.querySelectorAll('img').forEach(img => {
      const srcAttr = img.getAttribute('src');
      if (!srcAttr || srcAttr.trim() === '') img.src = defaultLogo;
      img.addEventListener('error', () => {
        if (img.src !== defaultLogo) img.src = defaultLogo;
      });
    });

    // Formatea textos que parecen fechas a formato español
    const candidates = document.querySelectorAll('.card small, .proximos .card small, .resultados .card small, header small');
    candidates.forEach(el => {
      const txt = el.textContent.trim();
      const f = formatDate(txt);
      if (f) el.textContent = f;
    });

    // Manejo de la sección de estadísticas: si plantilla ya trae items, no hacer fetch
    const statsSection = document.querySelector('.estadisticas');
    if (statsSection) {
      const hasArticles = statsSection.querySelectorAll('.estadistica-item').length > 0;
      const hasListItems = statsSection.querySelectorAll('ul li').length > 0;
      if (!hasArticles && !hasListItems) {
        const equipoId = detectEquipoId();
        fetchAndRenderStats(equipoId);
      }
    }

    // Siempre cargar partidos desde la API para tener datos completos y tarjetas clicables
    const equipoId = detectEquipoId();
    if (equipoId) {
      fetchAndRenderMatches(equipoId);
      fetchAndRenderJugadores(equipoId);
      fetchAndRenderGoleadores(equipoId);
    }
  });
})();
