function pad(n){return n<10? '0'+n: n}

function parseTime(dateStr, timeStr){
    if(!dateStr || !timeStr) return null;
    try{
        // Both are expected as YYYY-MM-DD and HH:MM:SS or HH:MM
        const dt = new Date(dateStr + 'T' + timeStr);
        if(isNaN(dt)) return null;
        return dt;
    }catch(e){return null}
}

function formatDuration(seconds){
    if(seconds < 0) seconds = 0;
    const m = Math.floor(seconds/60);
    const s = Math.floor(seconds%60);
    return `${m}:${pad(s)}`;
}

(function(){
    // Only run if timer container exists
    const timerEl = document.getElementById('match-timer');
    const firstHalfEl = document.getElementById('first-half-timer');
    const secondHalfEl = document.getElementById('second-half-timer');
    if(!timerEl || !firstHalfEl || !secondHalfEl) return;

    // Read variables injected by template
    const estadoRaw = typeof partidoEstado !== 'undefined' ? partidoEstado : '';
    const fecha = typeof partidoFecha !== 'undefined' ? partidoFecha : '';
    const horaInicio = typeof partidoHoraInicio !== 'undefined' ? partidoHoraInicio : '';
    const horaFinPrimer = typeof partidoHoraFinPrimer !== 'undefined' ? partidoHoraFinPrimer : '';
    const horaInicioSegundo = typeof partidoHoraInicioSegundo !== 'undefined' ? partidoHoraInicioSegundo : '';
    const horaFinSegundo = typeof partidoHoraFinSegundo !== 'undefined' ? partidoHoraFinSegundo : '';
    const parteRaw = typeof partidoParte !== 'undefined' ? partidoParte : '';

    // Normalize values: backend may store enum names like 'PRIMER_TIEMPO' or readable values 'primer tiempo'
    let parte = (parteRaw || '').toString().toLowerCase().replace(/_/g, ' ').trim();
    let estado = (estadoRaw || '').toString().toUpperCase().trim();

    // Debug: log received values
    console.log('Timer initialized:', {estado, parte, parteRaw, fecha, horaInicio, horaFinPrimer, horaInicioSegundo, horaFinSegundo});

    // Parse datetimes - use today's date if match is live or finished, otherwise use scheduled date
    const actualDate = (estado === 'EN_CURSO' || estado === 'FINALIZADO') ? new Date().toISOString().split('T')[0] : fecha;
    let dtInicio = parseTime(actualDate, horaInicio);
    let dtFinPrimer = parseTime(actualDate, horaFinPrimer);
    let dtInicioSegundo = parseTime(actualDate, horaInicioSegundo);
    let dtFinSegundo = parseTime(actualDate, horaFinSegundo);
    
    console.log('Parsed dates (using actualDate:', actualDate, '):', {dtInicio, dtFinPrimer, dtInicioSegundo, dtFinSegundo});

    function update(){
        const now = new Date();
        console.log('Update called - now:', now, 'dtInicio:', dtInicio, 'estado:', estado, 'parte:', parte);

        // First half duration
        let firstSeconds = 0;
        if(dtInicio){
            console.log('dtInicio exists:', dtInicio);
            if(dtFinPrimer){
                // First half finished, calculate exact duration
                firstSeconds = (dtFinPrimer - dtInicio)/1000;
                console.log('Using dtFinPrimer:', firstSeconds);
            } else if(dtInicioSegundo){
                // Second half started => first ended at dtInicioSegundo
                firstSeconds = (dtInicioSegundo - dtInicio)/1000;
                console.log('Using dtInicioSegundo:', firstSeconds);
            } else if(estado === 'EN_CURSO' && (parte === 'primer tiempo' || !parte)){
                // First half is currently in progress (or no parte specified = assume first half)
                firstSeconds = Math.max(0, (now - dtInicio)/1000);
                console.log('Calculating EN_CURSO first half:', firstSeconds, 'now-dtInicio=', (now - dtInicio)/1000);
            } else if(estado === 'EN_CURSO' && parte === 'segundo tiempo'){
                // Second half in progress but no explicit end time for first half
                // Assume first half is about 45 minutes (this shouldn't happen normally)
                firstSeconds = 45 * 60;
                console.log('Assuming 45min for first half');
            } else {
                console.log('No condition met for firstSeconds. estado:', estado, 'parte:', parte);
            }
        } else {
            console.log('dtInicio is null!');
        }

        // Second half duration (either finished or in progress)
        let secondSeconds = 0;
        if(dtInicioSegundo){
            if(dtFinSegundo){
                // Second half finished
                secondSeconds = (dtFinSegundo - dtInicioSegundo)/1000;
            } else if(estado === 'EN_CURSO' && parte === 'segundo tiempo'){
                // Second half is currently in progress
                secondSeconds = Math.max(0, (now - dtInicioSegundo)/1000);
            }
        }

        // Live timer: show elapsed of current part
        let liveSeconds = 0;
        if(estado === 'EN_CURSO'){
            if(parte === 'segundo tiempo' || parte === 'segundo_tiempo'){
                liveSeconds = secondSeconds;
            } else {
                // First half in progress (or parte is empty, default to first half)
                liveSeconds = firstSeconds;
            }
        }

        // Update displays
        if(estado === 'EN_CURSO'){
            timerEl.textContent = formatDuration(liveSeconds);
            console.log('Updating timer display:', liveSeconds, 'formatted:', formatDuration(liveSeconds));
        } else if(estado === 'FINALIZADO'){
            // show total match time (first + second)
            timerEl.textContent = formatDuration(firstSeconds + secondSeconds);
        } else {
            timerEl.textContent = '0:00';
        }

        firstHalfEl.textContent = formatDuration(firstSeconds);
        secondHalfEl.textContent = formatDuration(secondSeconds);
    }

    // Listen for live updates from poller to refresh timer state
    window.addEventListener('partido-update', function(e){
        const p = e.detail || {};
        // p may include estado (string), fecha (YYYY-MM-DD), hora_inicio (HH:MM:SS), parte (enum name)
        if(p.estado){ estado = (p.estado || '').toString().toUpperCase(); }
        if(p.parte){ parte = (p.parte || '').toString().toLowerCase().replace(/_/g,' ').trim(); }
        const newFecha = p.fecha || fecha;
        const newHoraInicio = p.hora_inicio || horaInicio;
        const newHoraFinPrimer = p.hora_fin_primer_tiempo || horaFinPrimer;
        const newHoraInicioSegundo = p.hora_inicio_segundo_tiempo || horaInicioSegundo;
        const newHoraFinSegundo = p.hora_fin_segundo_tiempo || horaFinSegundo;

        // Re-parse times - use today's date if match is live or finished
        const updateActualDate = (estado === 'EN_CURSO' || estado === 'FINALIZADO') ? new Date().toISOString().split('T')[0] : newFecha;
        dtInicio = parseTime(updateActualDate, newHoraInicio);
        dtFinPrimer = parseTime(updateActualDate, newHoraFinPrimer);
        dtInicioSegundo = parseTime(updateActualDate, newHoraInicioSegundo);
        dtFinSegundo = parseTime(updateActualDate, newHoraFinSegundo);

        // Force immediate update on new data
        update();
    });

    // Update every 1s
    update();
    setInterval(update, 1000);
})();
