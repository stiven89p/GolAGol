(function(){
  if (!window.estadisticas || !Array.isArray(window.estadisticas)) return;
  const pos = (window.jugadorPosicion || '').toUpperCase();

  function renderDoughnut(canvasId, labels, data, colors, title){
    const el = document.getElementById(canvasId);
    if (!el) return;
    new Chart(el, {
      type: 'doughnut',
      data: {
        labels,
        datasets: [{ data, backgroundColor: colors }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: 'bottom' },
          title: title ? { display: true, text: title, color: '#c9d1d9', font: { size: 14, weight: '600' } } : { display: false },
          tooltip: {
            callbacks: {
              label: function(context){
                const value = context.parsed;
                const total = context.chart.data.datasets[0].data.reduce((a,b)=>a+b,0) || 1;
                const pct = ((value/total)*100).toFixed(1);
                return `${context.label}: ${value} (${pct}%)`;
              }
            }
          }
        }
      }
    });
  }

  window.estadisticas.forEach(est => {
    const temporada = est.temporada;

    // Goles vs Asistencias
    renderDoughnut(
      `chart-goles-${temporada}`,
      ['Goles', 'Asistencias'],
      [est.goles || 0, est.asistencias || 0],
      ['#4caf50', '#2196f3'],
      'Goles vs Asistencias'
    );


    renderDoughnut(
      `chart-tarjetas-${temporada}`,
      ['Tarjetas Amarillas', 'Tarjetas Rojas'],
      [est.tarjetas_amarillas || 0, est.tarjetas_rojas || 0],
      ['#fbc02d', '#f44336'],
      'Distribución de Tarjetas'
    );


    // Tiros (delantero/mediocampista)
    if (pos === 'DELANTERO' || pos === 'MEDIOCAMPISTA') {
      const aPuerta = est.tiros_a_puerta || 0;
      const noPuerta = Math.max((est.tiros_totales || 0) - aPuerta, 0);
      renderDoughnut(
        `chart-tiros-${temporada}`,
        ['Tiros a Puerta', 'Tiros Fuera'],
        [aPuerta, noPuerta],
        ['#4caf50', '#f44336'],
        'Distribución de Tiros'
      );
    }

    if (pos === 'DEFENSOR' || pos === 'MEDIOCAMPISTA') {
      const aDefensa = (est.entradas || 0) + (est.intercepciones || 0);
      const noPerdidos = Math.max((est.balones_perdidos || 0), 0);
      renderDoughnut(
        `chart-defensivas-${temporada}`,
        ['Entradas + Intercepciones', 'Balones Perdidos'],
        [aDefensa, noPerdidos],
        ['#ff7043', '#90a4ae'],
        'Distribución de Defensa'
      );
    }



    // Portero
    if (pos === 'PORTERO') {
      renderDoughnut(
        `chart-portero-${temporada}`,
        ['Paradas', 'Goles Concedidos'],
        [est.paradas || 0, est.goles_concedidos || 0],
        ['#26a69a', '#ef5350'],
        'Rendimiento del Portero'
      );
    }
  });
})();
