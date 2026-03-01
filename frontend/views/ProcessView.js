import { defineComponent, ref, computed } from 'https://unpkg.com/vue@3/dist/vue.esm-browser.prod.js';

const MODES = [
  {
    id: 'enhance',
    label: 'Улучшение',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z"/></svg>`,
    desc: 'Восстановление качества записи, улучшение звучания для отдельных инструментов или полного микса',
    endpoint: '/api/audio/enhance',
  },
  {
    id: 'denoise',
    label: 'Шумоподавление',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M17.25 9.75L19.5 12m0 0l2.25 2.25M19.5 12l2.25-2.25M19.5 12l-2.25 2.25m-10.5-6l4.72-4.72a.75.75 0 011.28.531V19.94a.75.75 0 01-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.506-1.938-1.354A9.01 9.01 0 012.25 12c0-.83.112-1.633.322-2.395C2.806 8.757 3.63 8.25 4.51 8.25H6.75z"/></svg>`,
    desc: 'Удаление треска, шипения (hiss), гула оборудования и фоновых шумов с сохранением полезного сигнала',
    endpoint: '/api/audio/denoise',
  },
  {
    id: 'separate',
    label: 'Стем-сепарация',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zm0 9.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zm9.75-9.75A2.25 2.25 0 0115.75 3.75H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zm0 9.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z"/></svg>`,
    desc: 'Разделение трека на отдельные инструменты: вокал, бас, ударные, мелодия — технология Demucs',
    endpoint: '/api/audio/separate',
  },
  {
    id: 'master',
    label: 'ИИ-мастеринг',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M10.5 6h9.75M10.5 6a1.5 1.5 0 11-3 0m3 0a1.5 1.5 0 10-3 0M3.75 6H7.5m3 12h9.75m-9.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-3.75 0H7.5m9-6h3.75m-3.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-9.75 0h9.75"/></svg>`,
    desc: 'Финальная обработка: выравнивание уровней, компрессия, лимитирование по пресетам',
    endpoint: '/api/audio/master',
  },
];

const ENHANCE_MODES = [
  { value: 'full_mix', label: 'Полный микс' },
  { value: 'vocals', label: 'Вокал' },
  { value: 'drums', label: 'Ударные' },
  { value: 'bass', label: 'Бас' },
  { value: 'guitars', label: 'Гитары' },
  { value: 'piano', label: 'Пианино' },
];

const MASTER_PRESETS = [
  { value: 'song', label: 'Песня (музыкальный баланс)' },
  { value: 'podcast', label: 'Подкаст (чёткость речи)' },
  { value: 'advertisement', label: 'Реклама (громкость, яркость)' },
];

const STEM_MODES = [
  { value: 'basic', label: '4 стема: Вокал / Бас / Ударные / Прочее' },
  { value: 'advanced', label: '6 стемов: + Гитара + Пианино' },
];

const NOISE_TYPES = [
  { value: 'crackle', label: 'Треск' },
  { value: 'hiss', label: 'Шипение' },
  { value: 'hum', label: 'Гул (50/60 Гц)' },
  { value: 'background', label: 'Фоновый шум' },
];

export default defineComponent({
  name: 'ProcessView',
  setup() {
    const file = ref(null);
    const dragOver = ref(false);
    const mode = ref('enhance');
    const status = ref('idle'); // idle | uploading | processing | done | error
    const progress = ref(0);
    const taskId = ref(null);
    const resultUrl = ref(null);
    const errorMsg = ref('');

    // Settings
    const enhanceMode = ref('full_mix');
    const masterPreset = ref('song');
    const stemMode = ref('basic');
    const noiseTypes = ref(['crackle', 'hiss', 'background']);
    const denoiseIntensity = ref(70);
    const outputFormat = ref('wav');

    const selectedMode = computed(() => MODES.find(m => m.id === mode.value));
    const canProcess = computed(() => file.value && status.value === 'idle');

    function onFileInput(e) {
      const f = e.target.files[0];
      if (f) setFile(f);
    }

    function onDrop(e) {
      e.preventDefault();
      dragOver.value = false;
      const f = e.dataTransfer.files[0];
      if (f) setFile(f);
    }

    function setFile(f) {
      const allowed = ['audio/mpeg', 'audio/wav', 'audio/flac', 'audio/x-flac', 'audio/ogg',
                       'audio/mp4', 'audio/x-m4a', 'audio/aac', 'audio/x-aac'];
      if (!allowed.includes(f.type) && !f.name.match(/\.(mp3|wav|flac|ogg|m4a|aac|wma)$/i)) {
        errorMsg.value = 'Неподдерживаемый формат файла';
        return;
      }
      errorMsg.value = '';
      file.value = f;
      status.value = 'idle';
      resultUrl.value = null;
    }

    function formatSize(bytes) {
      if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
      return (bytes / 1024 / 1024).toFixed(1) + ' MB';
    }

    async function processAudio() {
      if (!canProcess.value) return;

      status.value = 'uploading';
      progress.value = 10;

      try {
        const formData = new FormData();
        formData.append('file', file.value);
        formData.append('mode', mode.value);
        if (mode.value === 'enhance') formData.append('enhance_mode', enhanceMode.value);
        if (mode.value === 'master') {
          formData.append('preset', masterPreset.value);
          formData.append('format', outputFormat.value);
        }
        if (mode.value === 'separate') formData.append('stem_mode', stemMode.value);
        if (mode.value === 'denoise') {
          formData.append('noise_types', JSON.stringify(noiseTypes.value));
          formData.append('intensity', denoiseIntensity.value);
        }

        // Simulate upload progress
        const uploadInterval = setInterval(() => {
          if (progress.value < 40) progress.value += 5;
        }, 200);

        const endpoint = selectedMode.value.endpoint;
        const res = await fetch(endpoint, {
          method: 'POST',
          headers: { 'Authorization': 'Bearer demo_token' },
        });

        clearInterval(uploadInterval);
        progress.value = 50;

        if (!res.ok) throw new Error(`Ошибка сервера: ${res.status}`);

        const data = await res.json();
        taskId.value = data.task_id;
        status.value = 'processing';

        // Poll task status
        await pollTask(data.task_id);

      } catch (e) {
        status.value = 'error';
        errorMsg.value = e.message || 'Ошибка обработки';
        progress.value = 0;
      }
    }

    async function pollTask(id) {
      let attempts = 0;
      const maxAttempts = 60;

      const poll = async () => {
        if (attempts++ > maxAttempts) {
          status.value = 'error';
          errorMsg.value = 'Превышено время ожидания';
          return;
        }

        try {
          const res = await fetch(`/api/task/${id}`, {
            headers: { 'Authorization': 'Bearer demo_token' },
          });
          const data = await res.json();

          // Simulate progress
          progress.value = Math.min(90, 50 + attempts * 2);

          if (data.status === 'completed') {
            progress.value = 100;
            status.value = 'done';
            resultUrl.value = data.result_url;
          } else if (data.status === 'failed') {
            status.value = 'error';
            errorMsg.value = 'Задача завершилась с ошибкой';
          } else {
            setTimeout(poll, 2000);
          }
        } catch {
          setTimeout(poll, 3000);
        }
      };

      await poll();
    }

    function reset() {
      file.value = null;
      status.value = 'idle';
      progress.value = 0;
      taskId.value = null;
      resultUrl.value = null;
      errorMsg.value = '';
    }

    return {
      file, dragOver, mode, status, progress, taskId, resultUrl, errorMsg,
      enhanceMode, masterPreset, stemMode, noiseTypes, denoiseIntensity, outputFormat,
      MODES, ENHANCE_MODES, MASTER_PRESETS, STEM_MODES, NOISE_TYPES,
      selectedMode, canProcess,
      onFileInput, onDrop, setFile, formatSize, processAudio, reset,
    };
  },

  template: `
    <div class="view">
      <h1 class="page-title">AI Обработка аудио</h1>
      <p class="page-subtitle">Загрузи файл, выбери тип обработки и получи результат</p>

      <div class="grid-2" style="gap:32px; align-items:start;">
        <!-- LEFT: Upload + Mode -->
        <div>
          <!-- Upload zone -->
          <div
            class="upload-zone"
            :class="{ 'drag-over': dragOver }"
            style="margin-bottom:20px;"
            @dragover.prevent="dragOver=true"
            @dragleave="dragOver=false"
            @drop="onDrop"
            @click="$refs.fileInput.click()"
          >
            <svg v-if="!file" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="width:48px;height:48px;margin:0 auto 12px;color:var(--accent-lt)">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"/>
            </svg>
            <div v-if="!file">
              <h3>Перетащи файл или нажми</h3>
              <p>MP3 · WAV · FLAC · M4A · OGG · AAC</p>
              <p>Максимум 100 МБ, до 10 минут</p>
            </div>
            <div v-else style="display:flex; align-items:center; gap:12px; justify-content:center;">
              <svg viewBox="0 0 24 24" fill="currentColor" style="width:32px;height:32px;color:var(--success)"><path fill-rule="evenodd" d="M19.916 4.626a.75.75 0 01.208 1.04l-9 13.5a.75.75 0 01-1.154.114l-6-6a.75.75 0 011.06-1.06l5.353 5.353 8.493-12.739a.75.75 0 011.04-.208z" clip-rule="evenodd"/></svg>
              <div>
                <div style="font-weight:600;">{{ file.name }}</div>
                <div style="color:var(--muted);font-size:0.85rem;">{{ formatSize(file.size) }}</div>
              </div>
            </div>
            <input ref="fileInput" type="file" accept="audio/*" style="display:none" @change="onFileInput">
          </div>

          <!-- Error -->
          <div v-if="errorMsg" class="alert alert-error" style="margin-bottom:16px;">
            <svg viewBox="0 0 20 20" fill="currentColor" style="width:18px;height:18px;flex-shrink:0"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/></svg>
            {{ errorMsg }}
          </div>

          <!-- Mode selection -->
          <div class="card" style="margin-bottom:20px;">
            <h4 style="margin-bottom:16px; color:var(--muted);">Тип обработки</h4>
            <div style="display:flex; flex-direction:column; gap:8px;">
              <div
                v-for="m in MODES" :key="m.id"
                :class="['card-elevated', mode===m.id ? 'mode-active' : '']"
                :style="mode===m.id ? 'border-color:var(--accent);background:rgba(124,58,237,0.1);cursor:pointer;' : 'cursor:pointer;'"
                @click="mode=m.id"
              >
                <div style="display:flex; align-items:flex-start; gap:12px;">
                  <div style="width:36px;height:36px;border-radius:8px;background:var(--border);display:flex;align-items:center;justify-content:center;flex-shrink:0;color:var(--accent-lt);" v-html="m.icon"></div>
                  <div>
                    <div style="font-weight:600;margin-bottom:2px;">{{ m.label }}</div>
                    <div style="font-size:0.82rem;color:var(--muted);">{{ m.desc }}</div>
                  </div>
                  <div v-if="mode===m.id" style="margin-left:auto;color:var(--accent-lt);">
                    <svg viewBox="0 0 20 20" fill="currentColor" style="width:20px;height:20px"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd"/></svg>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- RIGHT: Settings + Action -->
        <div>
          <!-- Settings -->
          <div class="card" style="margin-bottom:20px;">
            <h4 style="margin-bottom:20px; color:var(--muted);">Настройки</h4>

            <!-- Enhance settings -->
            <div v-if="mode==='enhance'" class="form-group">
              <label>Режим улучшения</label>
              <select class="select" v-model="enhanceMode">
                <option v-for="o in ENHANCE_MODES" :key="o.value" :value="o.value">{{ o.label }}</option>
              </select>
            </div>

            <!-- Denoise settings -->
            <div v-if="mode==='denoise'">
              <div class="form-group">
                <label>Типы шума</label>
                <div style="display:flex; flex-wrap:wrap; gap:8px; margin-top:4px;">
                  <label v-for="n in NOISE_TYPES" :key="n.value" style="display:flex;align-items:center;gap:6px;color:var(--text);cursor:pointer;font-size:0.88rem;">
                    <input type="checkbox" :value="n.value" v-model="noiseTypes" style="accent-color:var(--accent);">
                    {{ n.label }}
                  </label>
                </div>
              </div>
              <div class="form-group">
                <label>Интенсивность: <span style="color:var(--accent-lt);font-family:var(--mono);">{{ denoiseIntensity }}%</span></label>
                <input type="range" v-model.number="denoiseIntensity" min="10" max="100" step="5">
                <div style="display:flex;justify-content:space-between;font-size:0.75rem;color:var(--subtle);margin-top:4px;">
                  <span>Мягко</span><span>Агрессивно</span>
                </div>
              </div>
            </div>

            <!-- Separate settings -->
            <div v-if="mode==='separate'" class="form-group">
              <label>Количество стемов</label>
              <select class="select" v-model="stemMode">
                <option v-for="o in STEM_MODES" :key="o.value" :value="o.value">{{ o.label }}</option>
              </select>
            </div>

            <!-- Master settings -->
            <div v-if="mode==='master'">
              <div class="form-group">
                <label>Пресет</label>
                <select class="select" v-model="masterPreset">
                  <option v-for="o in MASTER_PRESETS" :key="o.value" :value="o.value">{{ o.label }}</option>
                </select>
              </div>
            </div>

            <!-- Output format (all modes) -->
            <div class="form-group">
              <label>Формат вывода</label>
              <div style="display:flex;gap:8px;">
                <label style="display:flex;align-items:center;gap:6px;color:var(--text);cursor:pointer;font-size:0.9rem;">
                  <input type="radio" value="wav" v-model="outputFormat" style="accent-color:var(--accent);">
                  WAV (без потерь)
                </label>
                <label style="display:flex;align-items:center;gap:6px;color:var(--text);cursor:pointer;font-size:0.9rem;">
                  <input type="radio" value="mp3" v-model="outputFormat" style="accent-color:var(--accent);">
                  MP3 (сжатый)
                </label>
              </div>
            </div>
          </div>

          <!-- Progress -->
          <div v-if="status !== 'idle'" class="card" style="margin-bottom:20px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
              <span style="font-weight:600;">
                <span v-if="status==='uploading'">Загрузка файла…</span>
                <span v-else-if="status==='processing'">Обработка…</span>
                <span v-else-if="status==='done'" style="color:var(--success);">Готово!</span>
                <span v-else-if="status==='error'" style="color:var(--error);">Ошибка</span>
              </span>
              <span style="font-family:var(--mono);font-size:0.88rem;color:var(--accent-lt);">{{ progress }}%</span>
            </div>
            <div class="progress-bar" style="margin-bottom:16px;">
              <div class="progress-fill" :style="'width:'+progress+'%'"></div>
            </div>

            <!-- Result -->
            <div v-if="status==='done'" style="display:flex;gap:12px;">
              <a :href="resultUrl" class="btn btn-primary" style="flex:1;justify-content:center;">
                <svg viewBox="0 0 20 20" fill="currentColor" style="width:16px;height:16px"><path fill-rule="evenodd" d="M10 13l4.586-4.586a2 2 0 00-2.828-2.828L10 7.344l-1.758-1.758a2 2 0 00-2.828 2.828L10 13zm0 0v5M7 18h6" clip-rule="evenodd"/></svg>
                Скачать результат
              </a>
              <button class="btn btn-ghost" @click="reset">Новый файл</button>
            </div>
          </div>

          <!-- Process button -->
          <button
            class="btn btn-primary btn-lg"
            style="width:100%;justify-content:center;"
            :disabled="!canProcess"
            @click="processAudio"
          >
            <svg viewBox="0 0 20 20" fill="currentColor" style="width:18px;height:18px"><path fill-rule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clip-rule="evenodd"/></svg>
            Начать обработку
          </button>

          <p v-if="!file" style="text-align:center;color:var(--subtle);font-size:0.82rem;margin-top:8px;">
            Сначала загрузи аудиофайл
          </p>
        </div>
      </div>
    </div>
  `,
});
