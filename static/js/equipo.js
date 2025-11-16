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
      localLogo.src = p.equipo_local_logo
        ? `/static/${encodeURIComponent(p.equipo_local_logo)}`
        : '/static/img/default_logo.png';
      localLogo.onerror = () => { localLogo.src = '/static/img/default_logo.png'; };

      // 🟥 Escudo visitante
      const visitanteLogo = document.createElement('img');
      visitanteLogo.className = 'escudo visitante';
      visitanteLogo.alt = `Escudo ${p.equipo_visitante_nombre || 'Visitante'}`;
      visitanteLogo.src = p.equipo_visitante_logo
        ? `/static/${encodeURIComponent(p.equipo_visitante_logo)}`
        : '/static/img/default_logo.png';
      visitanteLogo.onerror = () => { visitanteLogo.src = '/static/img/default_logo.png'; };

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
      return div;
  };


  // Renderiza proximos y jugados
  const renderMatches = (matches, equipoId) => {
    const proximosSection = document.querySelector('.proximos');
    const resultadosSection = document.querySelector('.resultados');
    if (!proximosSection && !resultadosSection) return;

    // separar por estado
    const próximos = matches.filter(m => m.estado === 'PROGRAMADO');
    const jugados = matches.filter(m => m.estado === 'FINALIZADO' || m.estado === 'FINALIZADO' /* por si hay variantes */ || m.estado === 'FINALIZADO'.toString());

    // ordenar
    próximos.sort((a, b) => new Date(a.fecha) - new Date(b.fecha));
    jugados.sort((a, b) => new Date(b.fecha) - new Date(a.fecha));

    // helper para limpiar dejando <h2>
    const cleanSection = (section) => {
      if (!section) return;
      const title = section.querySelector('h2');
      section.innerHTML = '';
      if (title) section.appendChild(title);
    };

    cleanSection(proximosSection);
    cleanSection(resultadosSection);

    const equipoNombre = document.querySelector('header h1')?.textContent?.trim() ?? '';

    if (proximosSection) {
      if (próximos.length === 0) {
        const p = document.createElement('p');
        p.textContent = 'No hay próximos partidos programados.';
        proximosSection.appendChild(p);
      } else {
        próximos.forEach(p => {
          proximosSection.appendChild(createMatchCard(p, true, equipoNombre));
        });
      }
    }

    if (resultadosSection) {
      if (jugados.length === 0) {
        const p = document.createElement('p');
        p.textContent = 'No hay resultados recientes.';
        resultadosSection.appendChild(p);
      } else {
        jugados.forEach(p => {
          resultadosSection.appendChild(createMatchCard(p, false, equipoNombre));
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

  document.addEventListener('DOMContentLoaded', () => {
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

    // Manejo de partidos: solo fetch si falta contenido en alguna sección
    const proximosSection = document.querySelector('.proximos');
    const resultadosSection = document.querySelector('.resultados');
    const hasProximos = proximosSection && proximosSection.querySelectorAll('.card.next').length > 0;
    const hasResultados = resultadosSection && resultadosSection.querySelectorAll('.card').length > 0;

    if (!hasProximos || !hasResultados) {
      const equipoId = detectEquipoId();
      fetchAndRenderMatches(equipoId);
    } else {
      // si ya hay contenido, asegurar que las tarjetas sean clicables
      makeCardsClickable();
    }
  });
})();
