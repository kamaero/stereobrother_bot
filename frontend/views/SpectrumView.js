import { defineComponent, ref, onMounted, onUnmounted } from 'https://unpkg.com/vue@3/dist/vue.esm-browser.prod.js';

export default defineComponent({
  name: 'SpectrumView',

  setup() {
    const canvasRef = ref(null);
    const source = ref('file'); // 'file' | 'mic'
    const isRunning = ref(false);
    const peakFreq = ref(null);
    const peakDb = ref(null);
    const fftSize = ref(2048);
    const smoothing = ref(0.8);
    const colorMode = ref('gradient'); // 'gradient' | 'classic'
    const errorMsg = ref('');
    const fileName = ref('');

    let audioCtx = null;
    let analyser = null;
    let animId = null;
    let sourceNode = null;
    let micStream = null;

    function cleanup() {
      if (animId) { cancelAnimationFrame(animId); animId = null; }
      if (sourceNode) { try { sourceNode.disconnect(); } catch {} sourceNode = null; }
      if (micStream) { micStream.getTracks().forEach(t => t.stop()); micStream = null; }
      isRunning.value = false;
    }

    function getOrCreateCtx() {
      if (!audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      }
      if (audioCtx.state === 'suspended') audioCtx.resume();
      return audioCtx;
    }

    function createAnalyser(ctx) {
      const an = ctx.createAnalyser();
      an.fftSize = parseInt(fftSize.value);
      an.smoothingTimeConstant = parseFloat(smoothing.value);
      return an;
    }

    async function startMic() {
      cleanup();
      errorMsg.value = '';
      try {
        micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const ctx = getOrCreateCtx();
        analyser = createAnalyser(ctx);
        sourceNode = ctx.createMediaStreamSource(micStream);
        sourceNode.connect(analyser);
        isRunning.value = true;
        drawLoop();
      } catch (e) {
        errorMsg.value = 'Нет доступа к микрофону: ' + e.message;
      }
    }

    async function loadFile(file) {
      cleanup();
      errorMsg.value = '';
      fileName.value = file.name;
      try {
        const ctx = getOrCreateCtx();
        analyser = createAnalyser(ctx);
        const arrayBuf = await file.arrayBuffer();
        const audioBuf = await ctx.decodeAudioData(arrayBuf);
        sourceNode = ctx.createBufferSource();
        sourceNode.buffer = audioBuf;
        sourceNode.loop = true;
        sourceNode.connect(analyser);
        analyser.connect(ctx.destination);
        sourceNode.start();
        isRunning.value = true;
        drawLoop();
      } catch (e) {
        errorMsg.value = 'Ошибка загрузки файла: ' + e.message;
      }
    }

    function stop() {
      cleanup();
      // Clear canvas
      if (canvasRef.value) {
        const ctx = canvasRef.value.getContext('2d');
        ctx.clearRect(0, 0, canvasRef.value.width, canvasRef.value.height);
      }
    }

    function drawLoop() {
      if (!analyser || !canvasRef.value) return;
      const canvas = canvasRef.value;
      const ctx = canvas.getContext('2d');
      const W = canvas.width;
      const H = canvas.height;
      const bufLen = analyser.frequencyBinCount;
      const data = new Uint8Array(bufLen);

      function draw() {
        animId = requestAnimationFrame(draw);
        analyser.getByteFrequencyData(data);

        // Background
        ctx.fillStyle = '#0d0d16';
        ctx.fillRect(0, 0, W, H);

        // Grid lines
        ctx.strokeStyle = 'rgba(46,46,69,0.8)';
        ctx.lineWidth = 1;
        const dbLines = [0, -12, -24, -36, -48, -60];
        dbLines.forEach(db => {
          const y = H - (H * (db + 80) / 80);
          ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
          ctx.fillStyle = '#64748b';
          ctx.font = '10px JetBrains Mono, monospace';
          ctx.fillText(db + ' dB', 4, y - 3);
        });

        // Frequency labels
        const freqLabels = [100, 200, 500, 1000, 2000, 5000, 10000, 20000];
        const sampleRate = audioCtx ? audioCtx.sampleRate : 44100;
        freqLabels.forEach(f => {
          const x = Math.log10(f / 20) / Math.log10(sampleRate / 2 / 20) * W;
          ctx.strokeStyle = 'rgba(46,46,69,0.6)';
          ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke();
          const label = f >= 1000 ? (f / 1000) + 'k' : f + '';
          ctx.fillStyle = '#64748b';
          ctx.fillText(label, x + 2, H - 4);
        });

        // Bars
        const barW = W / bufLen * 2.5;
        let maxVal = 0, maxBin = 0;

        for (let i = 0; i < bufLen; i++) {
          const v = data[i];
          if (v > maxVal) { maxVal = v; maxBin = i; }

          // Log-scale x position
          const freq = (i / bufLen) * (sampleRate / 2);
          if (freq < 20) continue;
          const x = Math.log10(freq / 20) / Math.log10(sampleRate / 2 / 20) * W;
          const barH = (v / 255) * H;

          if (colorMode.value === 'gradient') {
            const hue = 260 - (v / 255) * 80; // purple → cyan
            const sat = 60 + (v / 255) * 40;
            const light = 30 + (v / 255) * 40;
            ctx.fillStyle = `hsl(${hue},${sat}%,${light}%)`;
          } else {
            ctx.fillStyle = v > 200 ? '#ef4444' : v > 150 ? '#f59e0b' : '#10b981';
          }

          ctx.fillRect(x, H - barH, Math.max(1, barW), barH);
        }

        // Peak indicator
        if (maxVal > 20) {
          const peakFreqHz = (maxBin / bufLen) * (sampleRate / 2);
          peakFreq.value = peakFreqHz < 1000
            ? Math.round(peakFreqHz) + ' Hz'
            : (peakFreqHz / 1000).toFixed(1) + ' kHz';
          peakDb.value = Math.round((maxVal / 255) * 80 - 80) + ' dB';
        }
      }

      draw();
    }

    function onFileInput(e) {
      const f = e.target.files[0];
      if (f) loadFile(f);
    }

    function onFftChange() {
      if (analyser) analyser.fftSize = parseInt(fftSize.value);
    }

    function onSmoothingChange() {
      if (analyser) analyser.smoothingTimeConstant = parseFloat(smoothing.value);
    }

    onUnmounted(cleanup);

    return {
      canvasRef, source, isRunning, peakFreq, peakDb, fftSize, smoothing,
      colorMode, errorMsg, fileName,
      startMic, stop, onFileInput, onFftChange, onSmoothingChange,
    };
  },

  template: `
    <div class="view-wide">
      <h1 class="page-title">Анализатор спектра</h1>
      <p class="page-subtitle">Визуализация частотного спектра в реальном времени — логарифмическая шкала</p>

      <div style="display:flex; gap:24px; flex-wrap:wrap; margin-bottom:20px; align-items:center;">
        <!-- Source toggle -->
        <div class="tabs" style="margin-bottom:0;">
          <button class="tab" :class="{active: source==='file'}" @click="source='file';stop()">Файл</button>
          <button class="tab" :class="{active: source==='mic'}" @click="source='mic'">Микрофон</button>
        </div>

        <!-- File input -->
        <div v-if="source==='file'" style="display:flex;gap:10px;align-items:center;">
          <label class="btn btn-secondary btn-sm" style="cursor:pointer;margin:0;">
            <svg viewBox="0 0 20 20" fill="currentColor" style="width:14px;height:14px"><path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd"/></svg>
            Загрузить
            <input type="file" accept="audio/*" style="display:none;" @change="onFileInput">
          </label>
          <span v-if="fileName" style="color:var(--muted);font-size:0.85rem;">{{ fileName }}</span>
        </div>

        <!-- Mic button -->
        <div v-if="source==='mic'" style="display:flex;gap:10px;">
          <button v-if="!isRunning" class="btn btn-primary btn-sm" @click="startMic">
            <svg viewBox="0 0 20 20" fill="currentColor" style="width:14px;height:14px"><path fill-rule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clip-rule="evenodd"/></svg>
            Включить микрофон
          </button>
          <button v-else class="btn btn-ghost btn-sm" @click="stop">Остановить</button>
        </div>

        <button v-if="isRunning && source==='file'" class="btn btn-ghost btn-sm" @click="stop">Остановить</button>

        <!-- Peak indicators -->
        <div v-if="isRunning && peakFreq" style="display:flex;gap:16px;margin-left:auto;">
          <div class="stat-block" style="padding:8px 16px;min-width:100px;">
            <div class="stat-value" style="font-size:1.1rem;color:var(--accent-lt);">{{ peakFreq }}</div>
            <div class="stat-label" style="font-size:0.7rem;">Пиковая частота</div>
          </div>
          <div class="stat-block" style="padding:8px 16px;min-width:80px;">
            <div class="stat-value" style="font-size:1.1rem;color:var(--cyan-lt);">{{ peakDb }}</div>
            <div class="stat-label" style="font-size:0.7rem;">Уровень пика</div>
          </div>
        </div>
      </div>

      <!-- Error -->
      <div v-if="errorMsg" class="alert alert-error" style="margin-bottom:16px;">{{ errorMsg }}</div>

      <!-- Canvas -->
      <div class="canvas-wrap" style="margin-bottom:20px;">
        <canvas ref="canvasRef" width="1200" height="400" style="width:100%;height:auto;min-height:280px;"></canvas>
        <div v-if="!isRunning" style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center;color:var(--subtle);">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" style="width:48px;height:48px;margin:0 auto 8px;opacity:0.4;"><path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zm0 0V5.625A1.125 1.125 0 014.125 4.5h2.25c.621 0 1.125.504 1.125 1.125V12m0 0h.008v.008H7.5V12zm5.25 0c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v3.75c0 .621-.504 1.125-1.125 1.125h-2.25A1.125 1.125 0 0112.75 15.75v-3.75zm0 0V8.625A1.125 1.125 0 0113.875 7.5h2.25c.621 0 1.125.504 1.125 1.125V12m0 0h.008v.008H12.75V12zm5.25 0c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v7.5c0 .621-.504 1.125-1.125 1.125h-2.25A1.125 1.125 0 0118 20.625v-7.5z"/></svg>
          <p>Загрузи файл или включи микрофон</p>
        </div>
      </div>

      <!-- Controls -->
      <div class="card">
        <h4 style="margin-bottom:16px; color:var(--muted);">Параметры</h4>
        <div style="display:flex; gap:32px; flex-wrap:wrap; align-items:end;">
          <div style="min-width:200px; flex:1;">
            <label>Размер FFT: <span style="color:var(--accent-lt);font-family:var(--mono);">{{ fftSize }}</span></label>
            <select class="select" v-model="fftSize" @change="onFftChange">
              <option value="512">512 (быстро)</option>
              <option value="1024">1024</option>
              <option value="2048">2048 (баланс)</option>
              <option value="4096">4096</option>
              <option value="8192">8192 (точно)</option>
            </select>
          </div>
          <div style="min-width:200px; flex:1;">
            <label>Сглаживание: <span style="color:var(--accent-lt);font-family:var(--mono);">{{ smoothing }}</span></label>
            <input type="range" v-model.number="smoothing" min="0" max="0.99" step="0.01" @input="onSmoothingChange">
          </div>
          <div style="min-width:160px; flex:1;">
            <label>Цветовая схема</label>
            <select class="select" v-model="colorMode">
              <option value="gradient">Градиент (фиолетово-голубой)</option>
              <option value="classic">Классический (зелёный/оранжевый/красный)</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  `,
});
