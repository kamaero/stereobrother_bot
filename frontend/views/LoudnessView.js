import { defineComponent, ref } from 'https://unpkg.com/vue@3/dist/vue.esm-browser.prod.js';

// Streaming platform loudness targets (LUFS Integrated)
const TARGETS = [
  { name: 'Spotify',      lufs: -14, icon: '🟢' },
  { name: 'Apple Music',  lufs: -16, icon: '🍎' },
  { name: 'YouTube',      lufs: -14, icon: '▶️' },
  { name: 'Tidal',        lufs: -14, icon: '🌊' },
  { name: 'SoundCloud',   lufs: -14, icon: '☁️' },
  { name: 'Broadcast',    lufs: -23, icon: '📺' },
];

/**
 * K-weighting ITU-R BS.1770 approximation using Web Audio API BiquadFilters.
 * Returns { lufs, rms, truePeak } — all in dBFS.
 */
async function analyzeLoudness(audioBuffer) {
  const sampleRate = audioBuffer.sampleRate;
  const numCh = audioBuffer.numberOfChannels;
  const len = audioBuffer.length;

  // Stage 1: K-weighting via OfflineAudioContext
  const offCtx = new OfflineAudioContext(numCh, len, sampleRate);
  const src = offCtx.createBufferSource();
  src.buffer = audioBuffer;

  // High-shelf pre-filter (stage 1): +4 dB shelf at ~1500 Hz
  const shelf = offCtx.createBiquadFilter();
  shelf.type = 'highshelf';
  shelf.frequency.value = 1500;
  shelf.gain.value = 4.0;

  // High-pass filter (stage 2): 100 Hz, Q=0.5
  const hp = offCtx.createBiquadFilter();
  hp.type = 'highpass';
  hp.frequency.value = 100;
  hp.Q.value = 0.5;

  src.connect(shelf);
  shelf.connect(hp);
  hp.connect(offCtx.destination);
  src.start();

  const filtered = await offCtx.startRendering();

  // Block-based loudness (400ms blocks, 75% overlap = 100ms hop)
  const blockSamples = Math.round(0.4 * sampleRate);
  const hopSamples = Math.round(0.1 * sampleRate);
  const blocks = [];

  for (let start = 0; start + blockSamples <= len; start += hopSamples) {
    let sumSq = 0;
    for (let ch = 0; ch < filtered.numberOfChannels; ch++) {
      const d = filtered.getChannelData(ch);
      for (let i = start; i < start + blockSamples; i++) {
        sumSq += d[i] * d[i];
      }
    }
    const ms = sumSq / (blockSamples * filtered.numberOfChannels);
    blocks.push(ms);
  }

  if (blocks.length === 0) return null;

  // Absolute gating: discard blocks below -70 LUFS (≈ 1e-7 mean square)
  const abs = blocks.filter(ms => ms > 1e-7);
  if (abs.length === 0) return null;

  // Relative gating: -10 LU from preliminary loudness
  const prelim = abs.reduce((a, b) => a + b, 0) / abs.length;
  const prelimLufs = -0.691 + 10 * Math.log10(prelim);
  const relThresh = Math.pow(10, (prelimLufs - 10 + 0.691) / 10);

  const gated = abs.filter(ms => ms >= relThresh);
  const finalMs = gated.length > 0
    ? gated.reduce((a, b) => a + b, 0) / gated.length
    : prelim;

  const integratedLufs = -0.691 + 10 * Math.log10(finalMs);

  // RMS (overall, unweighted)
  let totalSq = 0, totalSamples = 0;
  for (let ch = 0; ch < numCh; ch++) {
    const d = audioBuffer.getChannelData(ch);
    for (let i = 0; i < len; i++) totalSq += d[i] * d[i];
    totalSamples += len;
  }
  const rmsDb = 20 * Math.log10(Math.sqrt(totalSq / totalSamples));

  // True Peak (max absolute sample)
  let tpLinear = 0;
  for (let ch = 0; ch < numCh; ch++) {
    const d = audioBuffer.getChannelData(ch);
    for (let i = 0; i < len; i++) {
      const abs = Math.abs(d[i]);
      if (abs > tpLinear) tpLinear = abs;
    }
  }
  const truePeakDb = 20 * Math.log10(tpLinear);

  // Dynamic range: difference between loudest and softest 10% of blocks
  const sorted = [...blocks].sort((a, b) => b - a);
  const top = sorted.slice(0, Math.max(1, Math.floor(sorted.length * 0.1)));
  const bottom = sorted.slice(Math.floor(sorted.length * 0.9));
  const topLufs = -0.691 + 10 * Math.log10(top.reduce((a, b) => a + b, 0) / top.length);
  const bottomLufs = -0.691 + 10 * Math.log10(Math.max(1e-10, bottom.reduce((a, b) => a + b, 0) / bottom.length));
  const dynamicRange = topLufs - bottomLufs;

  return {
    lufs: integratedLufs,
    rms: rmsDb,
    truePeak: truePeakDb,
    dynamicRange,
    duration: len / sampleRate,
    sampleRate,
    channels: numCh,
  };
}

export default defineComponent({
  name: 'LoudnessView',

  setup() {
    const isDragging = ref(false);
    const isAnalyzing = ref(false);
    const errorMsg = ref('');
    const result = ref(null);
    const fileName = ref('');

    function fmt1(n) { return isFinite(n) ? n.toFixed(1) : '—'; }
    function fmtDur(s) {
      const m = Math.floor(s / 60);
      const sec = Math.floor(s % 60);
      return `${m}:${sec.toString().padStart(2, '0')}`;
    }

    function lufsColor(val) {
      if (!isFinite(val)) return 'var(--muted)';
      if (val > -8) return 'var(--error)';
      if (val > -11) return 'var(--warning)';
      if (val >= -16) return 'var(--success)';
      return 'var(--cyan)';
    }

    function targetStatus(target, lufs) {
      if (!isFinite(lufs)) return '';
      const diff = lufs - target.lufs;
      if (Math.abs(diff) <= 1) return 'ok';
      if (diff > 0) return 'loud';
      return 'quiet';
    }

    function targetStatusLabel(target, lufs) {
      const s = targetStatus(target, lufs);
      if (s === 'ok') return '✓ В норме';
      if (s === 'loud') return `+${fmt1(lufs - target.lufs)} LU громче`;
      if (s === 'quiet') return `${fmt1(lufs - target.lufs)} LU тише`;
      return '—';
    }

    function targetStatusColor(target, lufs) {
      const s = targetStatus(target, lufs);
      if (s === 'ok') return 'var(--success)';
      if (s === 'loud') return 'var(--error)';
      if (s === 'quiet') return 'var(--cyan)';
      return 'var(--muted)';
    }

    function targetBarWidth(lufs) {
      // Map -40..0 LUFS to 0..100%
      return Math.max(0, Math.min(100, ((lufs + 40) / 40) * 100));
    }

    async function analyzeFile(file) {
      result.value = null;
      errorMsg.value = '';
      fileName.value = file.name;
      isAnalyzing.value = true;

      try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const buf = await file.arrayBuffer();
        const audioBuf = await ctx.decodeAudioData(buf);
        result.value = await analyzeLoudness(audioBuf);
        ctx.close();
      } catch (e) {
        errorMsg.value = 'Ошибка анализа: ' + e.message;
      } finally {
        isAnalyzing.value = false;
      }
    }

    function onFileInput(e) {
      const f = e.target.files[0];
      if (f) analyzeFile(f);
    }

    function onDrop(e) {
      e.preventDefault();
      isDragging.value = false;
      const f = e.dataTransfer.files[0];
      if (f) analyzeFile(f);
    }

    return {
      isDragging, isAnalyzing, errorMsg, result, fileName,
      TARGETS, fmt1, fmtDur, lufsColor,
      targetStatus, targetStatusLabel, targetStatusColor, targetBarWidth,
      onFileInput, onDrop,
    };
  },

  template: `
    <div class="view">
      <h1 class="page-title">Анализ громкости</h1>
      <p class="page-subtitle">LUFS, RMS и True Peak — с ориентирами для стриминговых платформ</p>

      <!-- Upload zone -->
      <div
        class="upload-zone"
        :class="{ 'drag-over': isDragging }"
        style="margin-bottom:24px;"
        @dragover.prevent="isDragging=true"
        @dragleave="isDragging=false"
        @drop="onDrop"
        @click="$refs.fileIn.click()"
      >
        <div v-if="!isAnalyzing">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="width:44px;height:44px;margin:0 auto 12px;color:var(--accent-lt)">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"/>
          </svg>
          <h3>{{ fileName || 'Загрузи аудиофайл для анализа' }}</h3>
          <p>Перетащи или нажми · MP3, WAV, FLAC, M4A и др.</p>
        </div>
        <div v-else style="text-align:center;">
          <div class="loading-spinner" style="margin:0 auto 12px;"></div>
          <p>Анализирую {{ fileName }}…</p>
          <p style="font-size:0.8rem;color:var(--subtle);">Для длинных файлов это может занять несколько секунд</p>
        </div>
        <input ref="fileIn" type="file" accept="audio/*" style="display:none;" @change="onFileInput">
      </div>

      <!-- Error -->
      <div v-if="errorMsg" class="alert alert-error" style="margin-bottom:20px;">{{ errorMsg }}</div>

      <!-- Results -->
      <div v-if="result">
        <!-- Main stats -->
        <div class="grid-4" style="margin-bottom:24px;">
          <div class="stat-block">
            <div class="stat-value" :style="'color:'+lufsColor(result.lufs)">{{ fmt1(result.lufs) }}</div>
            <div class="stat-label">LUFS Integrated</div>
          </div>
          <div class="stat-block">
            <div class="stat-value" style="color:var(--cyan-lt)">{{ fmt1(result.rms) }}</div>
            <div class="stat-label">RMS dBFS</div>
          </div>
          <div class="stat-block">
            <div class="stat-value" :style="result.truePeak > -1 ? 'color:var(--error)' : 'color:var(--success)'">
              {{ fmt1(result.truePeak) }}
            </div>
            <div class="stat-label">True Peak dBTP</div>
          </div>
          <div class="stat-block">
            <div class="stat-value" style="color:var(--accent-lt)">{{ fmt1(result.dynamicRange) }}</div>
            <div class="stat-label">Dynamic Range LU</div>
          </div>
        </div>

        <!-- Metadata -->
        <div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:24px;">
          <span class="badge badge-accent">{{ fmtDur(result.duration) }}</span>
          <span class="badge badge-cyan">{{ result.sampleRate / 1000 }} kHz</span>
          <span class="badge" style="background:var(--elevated);color:var(--muted);">{{ result.channels === 1 ? 'Mono' : 'Stereo' }}</span>
          <span v-if="result.truePeak > -1" class="badge badge-error">⚠ True Peak clipping!</span>
        </div>

        <!-- LUFS meter -->
        <div class="card" style="margin-bottom:24px;">
          <h4 style="margin-bottom:16px;">Уровень громкости</h4>
          <div style="position:relative; height:40px; background:var(--elevated); border-radius:8px; overflow:hidden; margin-bottom:8px;">
            <!-- Color zones -->
            <div style="position:absolute;left:0;top:0;bottom:0;width:25%;background:rgba(6,182,212,0.2);border-right:1px solid var(--border2);"></div>
            <div style="position:absolute;left:25%;top:0;bottom:0;width:37.5%;background:rgba(16,185,129,0.15);"></div>
            <div style="position:absolute;left:62.5%;top:0;bottom:0;right:0;background:rgba(239,68,68,0.1);border-left:1px solid var(--border2);"></div>
            <!-- Fill -->
            <div :style="'position:absolute;left:0;top:0;bottom:0;width:'+targetBarWidth(result.lufs)+'%;background:linear-gradient(90deg,var(--cyan),var(--accent),'+lufsColor(result.lufs)+');border-radius:8px;transition:width 0.5s;'"></div>
            <!-- Value label -->
            <div style="position:absolute;top:50%;right:12px;transform:translateY(-50%);font-family:var(--mono);font-size:0.9rem;font-weight:700;z-index:1;">
              {{ fmt1(result.lufs) }} LUFS
            </div>
          </div>
          <div style="display:flex;justify-content:space-between;font-size:0.75rem;color:var(--subtle);padding:0 2px;">
            <span>−40</span><span>Тихо</span><span>Норма</span><span>Громко</span><span>0</span>
          </div>
        </div>

        <!-- Platform targets -->
        <div class="card">
          <h4 style="margin-bottom:20px;">Сравнение со стриминговыми платформами</h4>
          <div style="display:flex;flex-direction:column;gap:10px;">
            <div v-for="t in TARGETS" :key="t.name"
              style="display:flex;align-items:center;gap:12px;padding:10px 14px;background:var(--elevated);border-radius:8px;">
              <span style="font-size:1.1rem;">{{ t.icon }}</span>
              <div style="min-width:110px;">
                <div style="font-weight:600;font-size:0.9rem;">{{ t.name }}</div>
                <div style="font-size:0.78rem;color:var(--muted);">{{ t.lufs }} LUFS цель</div>
              </div>
              <div style="flex:1; height:6px; background:var(--border); border-radius:3px; overflow:hidden; position:relative;">
                <!-- Target marker -->
                <div :style="'position:absolute;top:-3px;bottom:-3px;width:2px;background:var(--border2);left:'+targetBarWidth(t.lufs)+'%;'"></div>
                <!-- File level -->
                <div :style="'height:100%;width:'+targetBarWidth(result.lufs)+'%;background:'+lufsColor(result.lufs)+';border-radius:3px;'"></div>
              </div>
              <div style="min-width:140px;text-align:right;font-size:0.85rem;font-weight:600;"
                :style="'color:'+targetStatusColor(t, result.lufs)">
                {{ targetStatusLabel(t, result.lufs) }}
              </div>
            </div>
          </div>

          <div style="margin-top:16px; padding-top:16px; border-top:1px solid var(--border);">
            <div v-if="result.truePeak > -1" class="alert alert-error" style="margin-bottom:8px;">
              True Peak превышает 0 dBTP — возможна цифровая перегрузка при кодировании. Рекомендуется лимитер с потолком −1 dBTP.
            </div>
            <div v-if="result.dynamicRange < 6" class="alert alert-warning">
              Низкий динамический диапазон ({{ fmt1(result.dynamicRange) }} LU) — возможна чрезмерная компрессия.
            </div>
            <div v-if="result.lufs > -9" class="alert alert-error">
              Уровень слишком высокий. Стриминговые платформы автоматически понизят громкость.
            </div>
          </div>
        </div>
      </div>

      <!-- Info when no result -->
      <div v-else-if="!isAnalyzing" class="card" style="background:var(--surface);">
        <h4 style="margin-bottom:16px;">О метриках громкости</h4>
        <div class="grid-2" style="gap:20px;">
          <div>
            <h4 style="color:var(--accent-lt);margin-bottom:6px;">LUFS (Integrated)</h4>
            <p style="color:var(--muted);font-size:0.88rem;">Средняя громкость всего трека с K-взвешиванием по ITU-R BS.1770. Основная метрика для стриминга.</p>
          </div>
          <div>
            <h4 style="color:var(--cyan-lt);margin-bottom:6px;">RMS dBFS</h4>
            <p style="color:var(--muted);font-size:0.88rem;">Среднеквадратичное значение амплитуды без взвешивания. Традиционный показатель мощности сигнала.</p>
          </div>
          <div>
            <h4 style="color:var(--success);margin-bottom:6px;">True Peak</h4>
            <p style="color:var(--muted);font-size:0.88rem;">Максимальный пик после интерполяции. Рекомендуется держать ниже −1 dBTP чтобы избежать клиппинга при кодировании.</p>
          </div>
          <div>
            <h4 style="color:var(--warning);margin-bottom:6px;">Dynamic Range</h4>
            <p style="color:var(--muted);font-size:0.88rem;">Разница между громкими и тихими частями. Чем выше — тем больше «дыхания» в треке.</p>
          </div>
        </div>
      </div>
    </div>
  `,
});
