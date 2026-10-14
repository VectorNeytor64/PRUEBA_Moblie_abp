/**
 * PROYECTO DE AULA ABP - UNIVERSIDAD DEL SINÚ ELÍAS BECHARA ZAINÚM
 * Controlador JavaScript Interactivo para el Hub Clínico y Predictivo
 */

document.addEventListener('DOMContentLoaded', () => {
    // =========================================================================
    // ESTADO GLOBAL DE LA APLICACIÓN
    // =========================================================================
    const AppState = {
        soundEnabled: true,
        paciente: {
            nombre: 'Paciente',
            telefono: '',
            correo: '',
            direccion: '',
            edad: 35,
            peso: 72,
            estatura: 170,
            genero: 'masculino',
            imc: 24.9,
            antecedente_familiar: 'no',
            actividad: 'moderado',
            antecedentes_medicos: ''
        },
        sintomas: [],
        audioTranscription: '',
        diaActivo: 'Lunes',
        calendarioSemanal: {
            'Lunes': { desayuno: [], almuerzo: [], cena: [], snacks: [] },
            'Martes': { desayuno: [], almuerzo: [], cena: [], snacks: [] },
            'Miércoles': { desayuno: [], almuerzo: [], cena: [], snacks: [] },
            'Jueves': { desayuno: [], almuerzo: [], cena: [], snacks: [] },
            'Viernes': { desayuno: [], almuerzo: [], cena: [], snacks: [] },
            'Sábado': { desayuno: [], almuerzo: [], cena: [], snacks: [] },
            'Domingo': { desayuno: [], almuerzo: [], cena: [], snacks: [] }
        },
        diagnosticoActual: null,
        chartInstance: null
    };

    // =========================================================================
    // AUDIO FEEDBACK INTERACTIVO AL TOCAR O PONER EL CURSOR
    // =========================================================================
    let audioCtx = null;
    function playInteractiveChime(freq = 520, type = 'sine') {
        if (!AppState.soundEnabled) return;
        try {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (!AudioContext) return;
            if (!audioCtx) audioCtx = new AudioContext();
            if (audioCtx.state === 'suspended') audioCtx.resume();

            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();

            osc.type = type;
            osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
            osc.frequency.exponentialRampToValueAtTime(freq * 1.5, audioCtx.currentTime + 0.08);

            gain.gain.setValueAtTime(0.08, audioCtx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.12);

            osc.connect(gain);
            gain.connect(audioCtx.destination);

            osc.start();
            osc.stop(audioCtx.currentTime + 0.12);
        } catch (e) {
            // Audio policy fallback
        }
    }

    // Toggle de Sonido en Navbar
    const btnToggleSound = document.getElementById('btn-toggle-sound');
    if (btnToggleSound) {
        btnToggleSound.addEventListener('click', () => {
            AppState.soundEnabled = !AppState.soundEnabled;
            btnToggleSound.innerHTML = AppState.soundEnabled ? '🔊 Sonido' : '🔇 Silencio';
            if (AppState.soundEnabled) playInteractiveChime(640);
        });
    }

    // Hover y click en los 3 círculos interactivos
    document.querySelectorAll('.circle-card-item').forEach(card => {
        card.addEventListener('mouseenter', () => playInteractiveChime(440, 'triangle'));
        card.addEventListener('click', (e) => {
            e.preventDefault();
            playInteractiveChime(660, 'sine');
            const targetModule = card.getAttribute('data-target-module');
            activarModulo(targetModule);
        });
    });

    // =========================================================================
    // NAVEGACIÓN ENTRE VISTAS Y MÓDULOS
    // =========================================================================
    const heroView = document.getElementById('hero-hub-view');
    const moduleTabsBar = document.getElementById('module-navigation-tabs');
    const modules = {
        'modulo-persona': document.getElementById('modulo-persona'),
        'modulo-comida': document.getElementById('modulo-comida'),
        'modulo-diagrama': document.getElementById('modulo-diagrama')
    };

    function activarModulo(moduloId) {
        // Si es 'inicio', volver a mostrar solo los 3 círculos
        if (moduloId === 'inicio') {
            if (heroView) heroView.style.display = 'flex';
            if (moduleTabsBar) moduleTabsBar.style.display = 'none';
            Object.values(modules).forEach(m => { if (m) m.style.display = 'none'; });
            window.scrollTo({ top: 0, behavior: 'smooth' });
            return;
        }

        // Mostrar barra de tabs y ocultar el hero principal de círculos
        if (heroView) heroView.style.display = 'none';
        if (moduleTabsBar) moduleTabsBar.style.display = 'flex';

        // Ocultar todos los módulos y mostrar el seleccionado
        Object.entries(modules).forEach(([id, element]) => {
            if (element) {
                element.style.display = (id === moduloId) ? 'block' : 'none';
            }
        });

        // Actualizar estado activo en los botones de tab
        document.querySelectorAll('.tab-nav-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.getAttribute('data-module') === moduloId) {
                btn.classList.add('active');
            }
        });

        window.scrollTo({ top: 70, behavior: 'smooth' });

        // Si se abre el módulo de comida, actualizar la vista del calendario
        if (moduloId === 'modulo-comida') {
            renderizarDiaCalendario(AppState.diaActivo);
        }
    }

    document.querySelectorAll('.tab-nav-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const modId = btn.getAttribute('data-module');
            playInteractiveChime(500);
            activarModulo(modId);
        });
    });

    // =========================================================================
    // MÓDULO 1: CÁLCULO DE IMC EN VIVO
    // =========================================================================
    const inputPeso = document.getElementById('paciente-peso');
    const inputEstatura = document.getElementById('paciente-estatura');
    const bmiValDisplay = document.getElementById('bmi-val-display');
    const bmiCategoryPill = document.getElementById('bmi-category-pill');

    function actualizarCalculoIMC() {
        const peso = parseFloat(inputPeso?.value) || 70;
        const estatura = parseFloat(inputEstatura?.value) || 170;
        const estaturaM = estatura > 3.0 ? estatura / 100.0 : estatura;

        if (estaturaM > 0.5 && peso > 20) {
            const imc = (peso / (estaturaM * estaturaM)).toFixed(1);
            AppState.paciente.peso = peso;
            AppState.paciente.estatura = estatura;
            AppState.paciente.imc = parseFloat(imc);

            if (bmiValDisplay) bmiValDisplay.textContent = `${imc} kg/m²`;

            if (bmiCategoryPill) {
                if (imc < 18.5) {
                    bmiCategoryPill.textContent = 'Bajo peso';
                    bmiCategoryPill.style.background = '#e0f2fe';
                    bmiCategoryPill.style.color = '#0369a1';
                } else if (imc < 25.0) {
                    bmiCategoryPill.textContent = 'Peso saludable';
                    bmiCategoryPill.style.background = '#dcfce7';
                    bmiCategoryPill.style.color = '#15803d';
                } else if (imc < 30.0) {
                    bmiCategoryPill.textContent = 'Sobrepeso';
                    bmiCategoryPill.style.background = '#fef3c7';
                    bmiCategoryPill.style.color = '#b45309';
                } else {
                    bmiCategoryPill.textContent = 'Obesidad';
                    bmiCategoryPill.style.background = '#fee2e2';
                    bmiCategoryPill.style.color = '#b91c1c';
                }
            }
        }
    }

    if (inputPeso) inputPeso.addEventListener('input', actualizarCalculoIMC);
    if (inputEstatura) inputEstatura.addEventListener('input', actualizarCalculoIMC);
    actualizarCalculoIMC();

    // =========================================================================
    // GRABADORA DE AUDIO Y TRANSCRIPCIÓN EN VIVO DE SÍNTOMAS
    // =========================================================================
    const btnRecordMic = document.getElementById('btn-record-mic');
    const recordingTimer = document.getElementById('recording-timer');
    const waveformCanvas = document.getElementById('waveform-canvas');
    const audioPreviewPlayer = document.getElementById('audio-preview-player');
    const transcriptionText = document.getElementById('transcription-text');

    let mediaRecorder = null;
    let audioChunks = [];
    let isRecording = false;
    let timerInterval = null;
    let secondsRecorded = 0;
    let recognition = null;
    let animFrameId = null;

    // Inicializar Web Speech Recognition si está disponible
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'es-CO';

        recognition.onresult = (event) => {
            let transcript = '';
            for (let i = event.resultIndex; i < event.results.length; ++i) {
                transcript += event.results[i][0].transcript;
            }
            if (transcriptionText && transcript.trim()) {
                transcriptionText.textContent = `"${transcript.trim()}"`;
                AppState.audioTranscription = transcript.trim();
                analizarSintomasEnTexto(transcript.trim());
            }
        };

        recognition.onerror = (e) => {
            console.warn('Speech recognition warning:', e);
        };
    }

    async function toggleGrabacionAudio() {
        if (!isRecording) {
            // INICIAR GRABACIÓN
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];

                mediaRecorder.ondataavailable = (e) => {
                    if (e.data.size > 0) audioChunks.push(e.data);
                };

                mediaRecorder.onstop = () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                    const audioUrl = URL.createObjectURL(audioBlob);
                    if (audioPreviewPlayer) {
                        audioPreviewPlayer.src = audioUrl;
                        audioPreviewPlayer.style.display = 'block';
                    }
                    stream.getTracks().forEach(t => t.stop());
                };

                mediaRecorder.start();
                if (recognition) {
                    try { recognition.start(); } catch (e) {}
                }

                isRecording = true;
                btnRecordMic.classList.add('recording');
                btnRecordMic.innerHTML = `<span class="pulse-dot" style="background:#fff;"></span> Detener Grabación`;
                secondsRecorded = 0;
                actualizarTimerDisplay();
                timerInterval = setInterval(() => {
                    secondsRecorded++;
                    actualizarTimerDisplay();
                }, 1000);

                iniciarAnimacionWaveform(stream);
                playInteractiveChime(580);
            } catch (err) {
                console.error('Error accediendo al micrófono:', err);
                alert('No se pudo acceder al micrófono. Puedes escribir tus síntomas en el campo de texto o seleccionarlos en la lista inferior.');
            }
        } else {
            // DETENER GRABACIÓN
            if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                mediaRecorder.stop();
            }
            if (recognition) {
                try { recognition.stop(); } catch (e) {}
            }
            isRecording = false;
            clearInterval(timerInterval);
            if (animFrameId) cancelAnimationFrame(animFrameId);
            btnRecordMic.classList.remove('recording');
            btnRecordMic.innerHTML = `🎙️ Iniciar Nueva Grabación`;
            playInteractiveChime(420);

            // Analizar síntomas finales con el backend
            if (AppState.audioTranscription) {
                enviarTextoParaExtraccionBackend(AppState.audioTranscription);
            }
        }
    }

    function actualizarTimerDisplay() {
        if (!recordingTimer) return;
        const mins = String(Math.floor(secondsRecorded / 60)).padStart(2, '0');
        const secs = String(secondsRecorded % 60).padStart(2, '0');
        recordingTimer.textContent = `${mins}:${secs}`;
    }

    function iniciarAnimacionWaveform(stream) {
        if (!waveformCanvas) return;
        const canvasCtx = waveformCanvas.getContext('2d');
        const audioCtxWave = new (window.AudioContext || window.webkitAudioContext)();
        const source = audioCtxWave.createMediaStreamSource(stream);
        const analyser = audioCtxWave.createAnalyser();
        analyser.fftSize = 128;
        source.connect(analyser);

        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);

        function drawWave() {
            animFrameId = requestAnimationFrame(drawWave);
            analyser.getByteFrequencyData(dataArray);

            canvasCtx.fillStyle = '#f8fafc';
            canvasCtx.fillRect(0, 0, waveformCanvas.width, waveformCanvas.height);

            const barWidth = (waveformCanvas.width / bufferLength) * 2;
            let x = 0;

            for (let i = 0; i < bufferLength; i++) {
                const barHeight = (dataArray[i] / 255) * waveformCanvas.height * 0.85;
                canvasCtx.fillStyle = '#3b82f6';
                canvasCtx.fillRect(x, waveformCanvas.height - barHeight, barWidth - 1, barHeight);
                x += barWidth;
            }
        }
        drawWave();
    }

    if (btnRecordMic) {
        btnRecordMic.addEventListener('click', toggleGrabacionAudio);
    }

    // Análisis de síntomas en el cliente y mediante la API
    function analizarSintomasEnTexto(texto) {
        const t = texto.toLowerCase();
        const reglas = [
            { id: 'polidipsia', terminos: ['sed', 'agua', 'boca seca'] },
            { id: 'poliuria', terminos: ['orina', 'orinar', 'baño', 'miccion'] },
            { id: 'polifagia', terminos: ['hambre', 'comer', 'apetito'] },
            { id: 'perdida_peso', terminos: ['peso', 'rebaje', 'baje de peso', 'adelgace'] },
            { id: 'fatiga', terminos: ['cansancio', 'cansado', 'agotado', 'sueno', 'energia'] },
            { id: 'vision_borrosa', terminos: ['vision', 'borroso', 'vista', 'ojos'] },
            { id: 'hormigueo', terminos: ['hormigueo', 'dormido', 'pies', 'manos'] },
            { id: 'cicatrizacion_lenta', terminos: ['herida', 'cicatriz', 'llaga', 'no sana'] }
        ];

        reglas.forEach(r => {
            if (r.terminos.some(term => t.includes(term))) {
                if (!AppState.sintomas.includes(r.id)) {
                    AppState.sintomas.push(r.id);
                }
            }
        });
        actualizarChipsSintomas();
    }

    async function enviarTextoParaExtraccionBackend(texto) {
        try {
            const resp = await fetch('/api/extraer_sintomas_voz', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ texto })
            });
            const data = await resp.json();
            if (data.sintomas && Array.isArray(data.sintomas)) {
                data.sintomas.forEach(s => {
                    if (!AppState.sintomas.includes(s.id)) AppState.sintomas.push(s.id);
                });
                actualizarChipsSintomas();
            }
        } catch (e) {
            console.warn('Extracción por backend omitida:', e);
        }
    }

    // Chips de selección manual/automática de síntomas
    function actualizarChipsSintomas() {
        document.querySelectorAll('.symptom-chip').forEach(chip => {
            const id = chip.getAttribute('data-symptom-id');
            if (AppState.sintomas.includes(id)) {
                chip.classList.add('active');
            } else {
                chip.classList.remove('active');
            }
        });
    }

    document.querySelectorAll('.symptom-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            const id = chip.getAttribute('data-symptom-id');
            if (AppState.sintomas.includes(id)) {
                AppState.sintomas = AppState.sintomas.filter(s => s !== id);
            } else {
                AppState.sintomas.push(id);
            }
            playInteractiveChime(500);
            actualizarChipsSintomas();
        });
    });

    // =========================================================================
    // MÓDULO 2: CALENDARIO SEMANAL Y CONTADOR DE CALORÍAS
    // =========================================================================
    const daysTabs = document.querySelectorAll('.day-tab-card');
    daysTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const dia = tab.getAttribute('data-day');
            AppState.diaActivo = dia;
            daysTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            playInteractiveChime(480);
            renderizarDiaCalendario(dia);
        });
    });

    function calcularCaloriasDia(dia) {
        const registros = AppState.calendarioSemanal[dia] || {};
        let total = 0;
        let totalCarbs = 0;
        ['desayuno', 'almuerzo', 'cena', 'snacks'].forEach(slot => {
            (registros[slot] || []).forEach(item => {
                total += (item.cals || 0);
                totalCarbs += (item.carbs || 0);
            });
        });
        return { total, totalCarbs };
    }

    function renderizarDiaCalendario(dia) {
        const diaData = AppState.calendarioSemanal[dia] || {};
        const { total: calsDia, totalCarbs: carbsDia } = calcularCaloriasDia(dia);

        // Actualizar nombre del día activo en la barra de agregar alimentos
        const elActiveDay = document.getElementById('active-day-display-name');
        if (elActiveDay) elActiveDay.textContent = dia;

        // Actualizar badges en pestañas de días
        daysTabs.forEach(t => {
            const d = t.getAttribute('data-day');
            const { total: cd } = calcularCaloriasDia(d);
            const badge = t.querySelector('.day-cal-badge');
            if (badge) badge.textContent = `${cd} kcal`;
        });

        // Actualizar métricas del dashboard de calorías
        const elCalsDia = document.getElementById('metric-cals-dia');
        const elCarbsDia = document.getElementById('metric-carbs-dia');
        const elCalsSemana = document.getElementById('metric-cals-semana');
        const elPromedioDia = document.getElementById('metric-cals-promedio');

        // Total semanal acumulado
        let totalSemanal = 0;
        Object.keys(AppState.calendarioSemanal).forEach(d => {
            totalSemanal += calcularCaloriasDia(d).total;
        });
        const promedioSemanal = Math.round(totalSemanal / 7);

        if (elCalsDia) elCalsDia.textContent = `${calsDia} kcal`;
        if (elCarbsDia) elCarbsDia.textContent = `${carbsDia} g`;
        if (elCalsSemana) elCalsSemana.textContent = `${totalSemanal} kcal`;
        if (elPromedioDia) elPromedioDia.textContent = `${promedioSemanal} kcal`;

        // Renderizar slots de comida (desayuno, almuerzo, cena, snacks)
        ['desayuno', 'almuerzo', 'cena', 'snacks'].forEach(slot => {
            const listEl = document.getElementById(`list-${slot}`);
            const countEl = document.getElementById(`cals-${slot}`);
            if (!listEl) return;

            listEl.innerHTML = '';
            let slotCals = 0;
            const items = diaData[slot] || [];

            if (items.length === 0) {
                listEl.innerHTML = `<li style="font-size:0.8rem;color:#94a3b8;font-style:italic;padding:4px;">Sin alimentos registrados aún</li>`;
            } else {
                items.forEach((it, idx) => {
                    slotCals += it.cals;
                    const li = document.createElement('li');
                    li.className = 'meal-item-row';
                    li.innerHTML = `
                        <span>${it.nombre} (${it.cals} kcal)</span>
                        <button class="btn-remove-food" data-slot="${slot}" data-idx="${idx}" title="Eliminar">&times;</button>
                    `;
                    listEl.appendChild(li);
                });
            }

            if (countEl) countEl.textContent = `${slotCals} kcal`;
        });

        // Listeners para eliminar comida
        document.querySelectorAll('.btn-remove-food').forEach(btn => {
            btn.addEventListener('click', () => {
                const slot = btn.getAttribute('data-slot');
                const idx = parseInt(btn.getAttribute('data-idx'));
                AppState.calendarioSemanal[dia][slot].splice(idx, 1);
                playInteractiveChime(320);
                renderizarDiaCalendario(dia);
            });
        });
    }

    // =========================================================================
    // BARRA DIRECTA PARA AGREGAR CUALQUIER ALIMENTO (SIN PROMPTS EMERGENTES)
    // =========================================================================
    const inlineFoodName = document.getElementById('inline-food-name');
    const inlineFoodSlot = document.getElementById('inline-food-slot');
    const inlineFoodCals = document.getElementById('inline-food-cals');
    const btnSubmitInlineFood = document.getElementById('btn-submit-inline-food');
    const inlineFeedbackMsg = document.getElementById('inline-add-feedback');

    function showInlineFeedback(msg, isError = false) {
        if (!inlineFeedbackMsg) return;
        inlineFeedbackMsg.textContent = msg;
        inlineFeedbackMsg.style.display = 'block';
        if (isError) {
            inlineFeedbackMsg.style.background = '#fee2e2';
            inlineFeedbackMsg.style.color = '#b91c1c';
            inlineFeedbackMsg.style.borderColor = '#fca5a5';
        } else {
            inlineFeedbackMsg.style.background = '#dcfce7';
            inlineFeedbackMsg.style.color = '#15803d';
            inlineFeedbackMsg.style.borderColor = '#86efac';
        }
        setTimeout(() => {
            if (inlineFeedbackMsg) inlineFeedbackMsg.style.display = 'none';
        }, 4000);
    }

    async function agregarComidaDesdeBarra() {
        if (!inlineFoodName) return;
        const nombrePlato = inlineFoodName.value.trim();
        if (!nombrePlato) {
            showInlineFeedback('⚠️ Por favor escribe el nombre del alimento en la barra.', true);
            inlineFoodName.focus();
            return;
        }

        const slot = inlineFoodSlot ? inlineFoodSlot.value : 'almuerzo';
        const calsManual = inlineFoodCals && inlineFoodCals.value ? parseInt(inlineFoodCals.value) : null;

        // Si el usuario especificó sus propias calorías, las usamos de inmediato
        if (calsManual && calsManual > 0) {
            const carbs = Math.round(calsManual * 0.12);
            if (!AppState.calendarioSemanal[AppState.diaActivo][slot]) {
                AppState.calendarioSemanal[AppState.diaActivo][slot] = [];
            }
            AppState.calendarioSemanal[AppState.diaActivo][slot].push({
                nombre: nombrePlato,
                cals: calsManual,
                carbs: carbs
            });

            showInlineFeedback(`✓ "${nombrePlato}" (${calsManual} kcal) añadido al ${slot.toUpperCase()} (${AppState.diaActivo}).`);
            inlineFoodName.value = '';
            if (inlineFoodCals) inlineFoodCals.value = '';
            inlineFoodName.focus();
            playInteractiveChime(620);
            renderizarDiaCalendario(AppState.diaActivo);
            return;
        }

        // Si no puso calorías, calculamos las calorías inteligentemente según el plato escrito
        try {
            if (btnSubmitInlineFood) {
                btnSubmitInlineFood.disabled = true;
                btnSubmitInlineFood.innerHTML = 'Calculando...';
            }
            const resp = await fetch('/api/ia_detectar_comida', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ nombre_plato: nombrePlato })
            });
            const data = await resp.json();
            const cals = data.calorias || 320;
            const carbs = data.carbohidratos || Math.round(cals * 0.12);

            if (!AppState.calendarioSemanal[AppState.diaActivo][slot]) {
                AppState.calendarioSemanal[AppState.diaActivo][slot] = [];
            }
            AppState.calendarioSemanal[AppState.diaActivo][slot].push({
                nombre: data.nombre || nombrePlato,
                cals: cals,
                carbs: carbs
            });

            showInlineFeedback(`✓ "${data.nombre || nombrePlato}" (~${cals} kcal estimadas) añadido al ${slot.toUpperCase()} (${AppState.diaActivo}).`);
            inlineFoodName.value = '';
            if (inlineFoodCals) inlineFoodCals.value = '';
            inlineFoodName.focus();
            playInteractiveChime(620);
            renderizarDiaCalendario(AppState.diaActivo);
        } catch (err) {
            const calsFallback = 320;
            const carbsFallback = 38;
            if (!AppState.calendarioSemanal[AppState.diaActivo][slot]) {
                AppState.calendarioSemanal[AppState.diaActivo][slot] = [];
            }
            AppState.calendarioSemanal[AppState.diaActivo][slot].push({
                nombre: nombrePlato,
                cals: calsFallback,
                carbs: carbsFallback
            });
            showInlineFeedback(`✓ "${nombrePlato}" añadido al ${slot.toUpperCase()} (${AppState.diaActivo}).`);
            inlineFoodName.value = '';
            if (inlineFoodCals) inlineFoodCals.value = '';
            renderizarDiaCalendario(AppState.diaActivo);
        } finally {
            if (btnSubmitInlineFood) {
                btnSubmitInlineFood.disabled = false;
                btnSubmitInlineFood.innerHTML = '➕ Agregar a la Lista';
            }
        }
    }

    if (btnSubmitInlineFood) {
        btnSubmitInlineFood.addEventListener('click', agregarComidaDesdeBarra);
    }
    if (inlineFoodName) {
        inlineFoodName.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                agregarComidaDesdeBarra();
            }
        });
    }
    if (inlineFoodCals) {
        inlineFoodCals.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                agregarComidaDesdeBarra();
            }
        });
    }

    // Botones directos "+ Escribir Alimento para..." en las tarjetas de tiempos de comida
    document.querySelectorAll('.btn-add-food-slot').forEach(btn => {
        btn.addEventListener('click', () => {
            const slot = btn.getAttribute('data-slot');
            if (inlineFoodSlot) inlineFoodSlot.value = slot;

            const inlineCard = document.querySelector('.inline-add-food-card');
            if (inlineCard) {
                inlineCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
                inlineCard.classList.add('pulse-focus-card');
                setTimeout(() => inlineCard.classList.remove('pulse-focus-card'), 1200);
            }

            if (inlineFoodName) {
                inlineFoodName.focus();
                inlineFoodName.placeholder = `Escribe aquí el alimento que comiste en el ${slot.toUpperCase()}...`;
            }
            playInteractiveChime(500);
        });
    });

    renderizarDiaCalendario(AppState.diaActivo);

    // =========================================================================
    // MÓDULO 3: IA DETECTOR DE COMIDAS
    // =========================================================================
    const foodFileInput = document.getElementById('food-file-input');
    const foodDropzone = document.getElementById('food-dropzone');
    const detectedPlateCard = document.getElementById('detected-plate-card');
    const detectedPlateTitle = document.getElementById('detected-plate-title');
    const detectedPlateIngredients = document.getElementById('detected-plate-ingredients');
    const detectedPlateCals = document.getElementById('detected-plate-cals');
    const detectedPlateImpact = document.getElementById('detected-plate-impact');
    const detectedPlateAdvice = document.getElementById('detected-plate-advice');
    const btnAddDetectedToCalendar = document.getElementById('btn-add-detected-to-calendar');

    // Barra para analizar cualquier comida escrita libremente con IA en el Módulo 3
    const aiCustomFoodInput = document.getElementById('ai-custom-food-input');
    const btnAiAnalyzeCustom = document.getElementById('btn-ai-analyze-custom');

    let ultimoPlatoDetectado = null;

    if (btnAiAnalyzeCustom && aiCustomFoodInput) {
        btnAiAnalyzeCustom.addEventListener('click', () => {
            const texto = aiCustomFoodInput.value.trim();
            if (texto) {
                simularEscaneoComidaIA(texto);
            } else {
                aiCustomFoodInput.focus();
            }
        });
        aiCustomFoodInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                const texto = aiCustomFoodInput.value.trim();
                if (texto) simularEscaneoComidaIA(texto);
            }
        });
    }

    if (foodDropzone && foodFileInput) {
        foodDropzone.addEventListener('click', () => foodFileInput.click());
        foodFileInput.addEventListener('change', (e) => {
            if (e.target.files && e.target.files[0]) {
                const file = e.target.files[0];
                simularEscaneoComidaIA(file.name);
            }
        });
    }

    // Botones de muestra rápida de platos populares
    document.querySelectorAll('.btn-sample-plate').forEach(btn => {
        btn.addEventListener('click', () => {
            const plateKey = btn.getAttribute('data-plate-key');
            simularEscaneoComidaIA(plateKey);
        });
    });

    async function simularEscaneoComidaIA(claveOArchivo) {
        playInteractiveChime(700);
        if (detectedPlateTitle) detectedPlateTitle.textContent = 'Analizando alimento con Red Neuronal IA...';

        try {
            const resp = await fetch('/api/ia_detectar_comida', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ nombre_plato: claveOArchivo })
            });
            const data = await resp.json();
            ultimoPlatoDetectado = data;

            if (detectedPlateCard) detectedPlateCard.style.display = 'block';
            if (detectedPlateTitle) detectedPlateTitle.textContent = data.nombre;
            if (detectedPlateIngredients) {
                detectedPlateIngredients.textContent = `Ingredientes clave: ${(data.ingredientes || []).join(', ')}`;
            }
            if (detectedPlateCals) {
                detectedPlateCals.textContent = `Calorías: ${data.calorias} kcal | Carbohidratos: ${data.carbohidratos}g | Proteínas: ${data.proteinas}g`;
            }
            if (detectedPlateImpact) {
                detectedPlateImpact.textContent = `Impacto Glucémico: ${data.impacto_glucosa}`;
            }
            if (detectedPlateAdvice) {
                detectedPlateAdvice.textContent = data.advertencia;
            }

            // Hacer scroll suave hacia la tarjeta del plato detectado
            if (detectedPlateCard) {
                detectedPlateCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
        } catch (err) {
            console.error('Error al detectar comida:', err);
        }
    }

    // Añadir plato detectado al calendario de comidas usando los selectores directos en pantalla
    if (btnAddDetectedToCalendar) {
        btnAddDetectedToCalendar.addEventListener('click', () => {
            if (!ultimoPlatoDetectado) return;
            const selectSlot = document.getElementById('select-detected-slot');
            const selectDay = document.getElementById('select-detected-day');
            const toastFeedback = document.getElementById('toast-detected-feedback');

            const slot = (selectSlot ? selectSlot.value : 'almuerzo').toLowerCase();
            const diaDestino = selectDay ? selectDay.value : AppState.diaActivo;

            if (!AppState.calendarioSemanal[diaDestino][slot]) {
                AppState.calendarioSemanal[diaDestino][slot] = [];
            }

            AppState.calendarioSemanal[diaDestino][slot].push({
                nombre: ultimoPlatoDetectado.nombre,
                cals: ultimoPlatoDetectado.calorias,
                carbs: ultimoPlatoDetectado.carbohidratos
            });

            playInteractiveChime(650);

            if (toastFeedback) {
                toastFeedback.textContent = `✓ "${ultimoPlatoDetectado.nombre}" añadido exitosamente a ${slot.toUpperCase()} del día ${diaDestino}.`;
                toastFeedback.style.display = 'block';
                setTimeout(() => {
                    if (toastFeedback) toastFeedback.style.display = 'none';
                }, 3500);
            }

            renderizarDiaCalendario(AppState.diaActivo);
        });
    }

    // =========================================================================
    // MÓDULO 3: DIAGNÓSTICO INTEGRAL Y DIAGRAMA DEL GLUCÓMETRO
    // =========================================================================
    const btnRunDiagnosis = document.getElementById('btn-run-diagnosis');
    const diagnosisReportCard = document.getElementById('diagnosis-report-card');

    async function ejecutarDiagnosticoYCurva() {
        playInteractiveChime(750);
        if (btnRunDiagnosis) {
            btnRunDiagnosis.disabled = true;
            btnRunDiagnosis.innerHTML = `<span class="pulse-dot" style="background:#fff;"></span> Correlacionando Datos y Generando Curva...`;
        }

        // Recolectar datos acumulados de todos los módulos
        let totalCalsSemana = 0;
        let totalCarbsSemana = 0;
        Object.keys(AppState.calendarioSemanal).forEach(d => {
            const { total, totalCarbs } = calcularCaloriasDia(d);
            totalCalsSemana += total;
            totalCarbsSemana += totalCarbs;
        });
        const calsPromedio = Math.round(totalCalsSemana / 7);
        const carbsPromedio = Math.round(totalCarbsSemana / 7);

        const payload = {
            nombre: document.getElementById('paciente-nombre')?.value || AppState.paciente.nombre,
            telefono: document.getElementById('paciente-telefono')?.value || '',
            correo: document.getElementById('paciente-correo')?.value || '',
            direccion: document.getElementById('paciente-direccion')?.value || '',
            edad: parseFloat(document.getElementById('paciente-edad')?.value) || AppState.paciente.edad,
            peso: parseFloat(document.getElementById('paciente-peso')?.value) || AppState.paciente.peso,
            estatura: parseFloat(document.getElementById('paciente-estatura')?.value) || AppState.paciente.estatura,
            genero: document.getElementById('paciente-genero')?.value || 'masculino',
            antecedente_familiar: document.getElementById('paciente-antecedente-fam')?.value || 'no',
            actividad: document.getElementById('paciente-actividad')?.value || 'moderado',
            antecedentes_medicos: document.getElementById('paciente-antecedentes-medicos')?.value || '',
            sintomas: AppState.sintomas,
            audio_transcripcion: AppState.audioTranscription,
            calorias_semana_total: totalCalsSemana,
            calorias_promedio_dia: calsPromedio,
            carbohidratos_promedio: carbsPromedio
        };

        try {
            const resp = await fetch('/api/evaluar_predictivo', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await resp.json();
            AppState.diagnosticoActual = data;

            // Renderizar el informe clínico completo y el gráfico
            renderizarReporteClinico(data);

        } catch (e) {
            console.error('Error al ejecutar evaluación predictiva:', e);
            alert('Error al comunicarse con el motor diagnóstico.');
        } finally {
            if (btnRunDiagnosis) {
                btnRunDiagnosis.disabled = false;
                btnRunDiagnosis.innerHTML = `🧬 Generar Diagnóstico Clínico y Reporte de Glucometría`;
            }
        }
    }

    function renderizarReporteClinico(data) {
        if (!diagnosisReportCard) return;
        diagnosisReportCard.style.display = 'block';

        // Verdict Banner
        const verdictBanner = document.getElementById('verdict-banner');
        const verdictTitle = document.getElementById('verdict-title');
        const verdictSubtitle = document.getElementById('verdict-subtitle');
        const verdictReason = document.getElementById('verdict-reason');

        if (verdictTitle) verdictTitle.textContent = data.diagnostico;
        if (verdictSubtitle) verdictSubtitle.textContent = `Nivel de Riesgo Clínico: ${data.nivel_riesgo} (Score FINDRISC: ${data.score_findrisc} pts)`;
        if (verdictReason) verdictReason.textContent = data.motivo_clinico;

        if (verdictBanner) {
            verdictBanner.style.borderColor = data.color;
            verdictBanner.style.backgroundColor = `${data.color}15`;
            verdictTitle.style.color = data.color;
        }

        // Listas de Recomendaciones
        const listMed = document.getElementById('report-recs-medicas');
        const listNut = document.getElementById('report-recs-nutricionales');

        if (listMed) {
            listMed.innerHTML = '';
            (data.recomendaciones_medicas || []).forEach(r => {
                const li = document.createElement('li');
                li.textContent = r;
                listMed.appendChild(li);
            });
        }

        if (listNut) {
            listNut.innerHTML = '';
            (data.recomendaciones_nutricionales || []).forEach(r => {
                const li = document.createElement('li');
                li.textContent = r;
                listNut.appendChild(li);
            });
        }

        // Renderizar Diagrama del Glucómetro con Chart.js
        renderizarChartGlucometro(data.curva_diaria);

        // Scroll suave al reporte
        diagnosisReportCard.scrollIntoView({ behavior: 'smooth' });
    }

    function renderizarChartGlucometro(curvaDiaria) {
        const canvas = document.getElementById('glucometer-chart-canvas');
        if (!canvas || typeof Chart === 'undefined') return;

        const ctx = canvas.getContext('2d');
        if (AppState.chartInstance) {
            AppState.chartInstance.destroy();
        }

        const labels = curvaDiaria.map(p => p.hora);
        const dataValues = curvaDiaria.map(p => p.glucosa);
        const momentLabels = curvaDiaria.map(p => p.momento);

        // Gradiente estético
        const gradient = ctx.createLinearGradient(0, 0, 0, 300);
        gradient.addColorStop(0, 'rgba(99, 102, 241, 0.4)');
        gradient.addColorStop(1, 'rgba(99, 102, 241, 0.0)');

        AppState.chartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Glucemia Estimada (mg/dL)',
                    data: dataValues,
                    borderColor: '#4f46e5',
                    backgroundColor: gradient,
                    fill: true,
                    tension: 0.38,
                    pointBackgroundColor: dataValues.map(v => v < 100 ? '#10b981' : (v < 140 ? '#3b82f6' : (v < 200 ? '#f59e0b' : '#ef4444'))),
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    pointRadius: 6,
                    pointHoverRadius: 9
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            title: (items) => `${labels[items[0].dataIndex]} - ${momentLabels[items[0].dataIndex]}`,
                            label: (context) => {
                                const val = context.raw;
                                let estado = val < 100 ? '🟢 Normal / Ayuno' : (val < 140 ? '🟢 Normal Postprandial' : (val < 200 ? '🟡 Prediabetes' : '🔴 Límite Diabetes'));
                                return `Glucemia: ${val} mg/dL (${estado})`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        min: 50,
                        max: Math.max(220, Math.max(...dataValues) + 25),
                        grid: { color: 'rgba(226, 232, 240, 0.6)' },
                        ticks: {
                            callback: (val) => `${val} mg/dL`
                        }
                    },
                    x: {
                        grid: { display: false }
                    }
                }
            }
        });
    }

    if (btnRunDiagnosis) {
        btnRunDiagnosis.addEventListener('click', ejecutarDiagnosticoYCurva);
    }

    // =========================================================================
    // MODAL DE FICHA TÉCNICA / TÉRMICA IMPRIMIBLE EN PDF
    // =========================================================================
    const modalFichaTecnica = document.getElementById('modal-ficha-tecnica');
    const btnVerFichaPdf = document.getElementById('btn-ver-ficha-pdf');
    const btnCerrarFicha = document.getElementById('btn-cerrar-ficha');
    const btnPrintDirecto = document.getElementById('btn-print-directo');

    const toggleFormalSheet = document.getElementById('toggle-formal-sheet');
    const toggleThermalReceipt = document.getElementById('toggle-thermal-receipt');
    const viewFormalSheet = document.getElementById('view-formal-sheet');
    const viewThermalReceipt = document.getElementById('view-thermal-receipt');

    if (btnVerFichaPdf) {
        btnVerFichaPdf.addEventListener('click', () => {
            if (!AppState.diagnosticoActual) {
                alert('Primero debes generar el diagnóstico en el Módulo 3.');
                return;
            }
            playInteractiveChime(600);
            poblarFichaImprimible(AppState.diagnosticoActual);
            if (modalFichaTecnica) modalFichaTecnica.classList.remove('hidden');
        });
    }

    if (btnCerrarFicha) {
        btnCerrarFicha.addEventListener('click', () => {
            if (modalFichaTecnica) modalFichaTecnica.classList.add('hidden');
        });
    }

    if (btnPrintDirecto) {
        btnPrintDirecto.addEventListener('click', () => {
            window.print();
        });
    }

    if (toggleFormalSheet && toggleThermalReceipt) {
        toggleFormalSheet.addEventListener('click', () => {
            toggleFormalSheet.classList.add('active');
            toggleThermalReceipt.classList.remove('active');
            if (viewFormalSheet) viewFormalSheet.style.display = 'block';
            if (viewThermalReceipt) viewThermalReceipt.style.display = 'none';
        });

        toggleThermalReceipt.addEventListener('click', () => {
            toggleThermalReceipt.classList.add('active');
            toggleFormalSheet.classList.remove('active');
            if (viewFormalSheet) viewFormalSheet.style.display = 'none';
            if (viewThermalReceipt) viewThermalReceipt.style.display = 'block';
        });
    }

    function poblarFichaImprimible(diag) {
        // Llenar Ficha Formal A4
        const el = (id) => document.getElementById(id);
        if (el('sheet-folio')) el('sheet-folio').textContent = diag.folio;
        if (el('sheet-fecha')) el('sheet-fecha').textContent = diag.fecha_emision;
        if (el('sheet-nombre')) el('sheet-nombre').textContent = diag.nombre;
        if (el('sheet-edad')) el('sheet-edad').textContent = `${diag.edad} años`;
        if (el('sheet-antropometria')) el('sheet-antropometria').textContent = `${diag.peso} kg | ${diag.estatura} cm | IMC: ${diag.imc} (${diag.imc_categoria})`;
        if (el('sheet-sintomas')) el('sheet-sintomas').textContent = (diag.sintomas_reportados || []).join(', ') || 'Sin síntomas reportados';
        if (el('sheet-audio-texto')) el('sheet-audio-texto').textContent = diag.transcripcion_audio ? `"${diag.transcripcion_audio}"` : 'No grabado';
        if (el('sheet-calorias')) el('sheet-calorias').textContent = `${diag.calorias_semana_total} kcal en la semana (${diag.calorias_promedio_dia} kcal/día promedio)`;
        if (el('sheet-diagnostico')) {
            el('sheet-diagnostico').textContent = diag.diagnostico;
            el('sheet-diagnostico').style.color = diag.color;
        }
        if (el('sheet-motivo')) el('sheet-motivo').textContent = diag.motivo_clinico;

        // Tabla horaria de glucómetros estimados
        const tableBody = el('sheet-tabla-glucometro');
        if (tableBody) {
            tableBody.innerHTML = '';
            (diag.curva_diaria || []).forEach(p => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td style="padding:6px;border-bottom:1px solid #e2e8f0;">${p.hora}</td>
                    <td style="padding:6px;border-bottom:1px solid #e2e8f0;">${p.momento}</td>
                    <td style="padding:6px;border-bottom:1px solid #e2e8f0;font-weight:bold;">${p.glucosa} mg/dL</td>
                    <td style="padding:6px;border-bottom:1px solid #e2e8f0;">${p.estado.toUpperCase()}</td>
                `;
                tableBody.appendChild(tr);
            });
        }

        // Llenar Ficha Térmica (Receipt 80mm)
        if (el('thermal-folio')) el('thermal-folio').textContent = diag.folio;
        if (el('thermal-fecha')) el('thermal-fecha').textContent = diag.fecha_emision;
        if (el('thermal-nombre')) el('thermal-nombre').textContent = diag.nombre;
        if (el('thermal-imc')) el('thermal-imc').textContent = `${diag.imc} (${diag.imc_categoria})`;
        if (el('thermal-cals')) el('thermal-cals').textContent = `${diag.calorias_promedio_dia} kcal/dia`;
        if (el('thermal-basal')) el('thermal-basal').textContent = `${diag.glucosa_basal_estimada} mg/dL`;
        if (el('thermal-pico')) el('thermal-pico').textContent = `${diag.glucosa_maxima_postprandial} mg/dL`;
        if (el('thermal-diag')) el('thermal-diag').textContent = diag.diagnostico;
    }

    // =========================================================================
    // MODAL DE INTEGRANTES DEL PROYECTO ABP
    // =========================================================================
    const modalIntegrantes = document.getElementById('modal-integrantes');
    const btnVerIntegrantesNav = document.getElementById('btn-ver-integrantes-nav');
    const btnVerIntegrantesCard = document.getElementById('btn-ver-integrantes-card');
    const btnCerrarIntegrantes = document.getElementById('btn-cerrar-integrantes');

    function abrirModalIntegrantes() {
        playInteractiveChime(540);
        if (modalIntegrantes) modalIntegrantes.classList.remove('hidden');
    }

    function cerrarModalIntegrantes() {
        if (modalIntegrantes) modalIntegrantes.classList.add('hidden');
    }

    if (btnVerIntegrantesNav) btnVerIntegrantesNav.addEventListener('click', abrirModalIntegrantes);
    if (btnVerIntegrantesCard) btnVerIntegrantesCard.addEventListener('click', abrirModalIntegrantes);
    if (btnCerrarIntegrantes) btnCerrarIntegrantes.addEventListener('click', cerrarModalIntegrantes);

    // Cerrar modales con clic exterior o tecla Escape
    window.addEventListener('click', (e) => {
        if (e.target === modalIntegrantes) cerrarModalIntegrantes();
        if (e.target === modalFichaTecnica) modalFichaTecnica.classList.add('hidden');
    });

    window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            cerrarModalIntegrantes();
            if (modalFichaTecnica) modalFichaTecnica.classList.add('hidden');
        }
    });
});
