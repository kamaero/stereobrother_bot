import { defineComponent, ref, onMounted } from 'https://unpkg.com/vue@3/dist/vue.esm-browser.prod.js';

export default defineComponent({
  name: 'HomeView',
  setup() {
    const apiStatus = ref('checking'); // 'ok' | 'error' | 'checking'

    onMounted(async () => {
      try {
        const r = await fetch('/health');
        apiStatus.value = r.ok ? 'ok' : 'error';
      } catch {
        apiStatus.value = 'error';
      }
    });

    const features = [
      {
        icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z"/></svg>`,
        title: 'AI Обработка',
        desc: 'Шумоподавление, улучшение качества, разделение на стемы, ИИ-мастеринг',
        route: '/process',
        color: 'var(--accent)',
        badge: 'AI',
      },
      {
        icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zm0 0V5.625A1.125 1.125 0 014.125 4.5h2.25c.621 0 1.125.504 1.125 1.125V12m0 0h.008v.008H7.5V12zm5.25 0c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v3.75c0 .621-.504 1.125-1.125 1.125h-2.25A1.125 1.125 0 0112.75 15.75v-3.75zm0 0V8.625A1.125 1.125 0 0113.875 7.5h2.25c.621 0 1.125.504 1.125 1.125V12m0 0h.008v.008H12.75V12zm5.25 0c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v7.5c0 .621-.504 1.125-1.125 1.125h-2.25A1.125 1.125 0 0118 20.625v-7.5zm0 0V6.375A1.125 1.125 0 0119.125 5.25h2.25c.621 0 1.125.504 1.125 1.125V12"/></svg>`,
        title: 'Анализатор спектра',
        desc: 'Визуализация частотного спектра в реальном времени — файл или микрофон',
        route: '/spectrum',
        color: 'var(--cyan)',
        badge: 'Real-time',
      },
      {
        icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M19.114 5.636a9 9 0 010 12.728M16.463 8.288a5.25 5.25 0 010 7.424M6.75 8.25l4.72-4.72a.75.75 0 011.28.53v15.88a.75.75 0 01-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.01 9.01 0 012.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75z"/></svg>`,
        title: 'Анализ громкости',
        desc: 'Измерение LUFS (Integrated), RMS и True Peak с ориентирами для стриминга',
        route: '/loudness',
        color: '#f59e0b',
        badge: 'LUFS',
      },
      {
        icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M10.5 6h9.75M10.5 6a1.5 1.5 0 11-3 0m3 0a1.5 1.5 0 10-3 0M3.75 6H7.5m3 12h9.75m-9.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-3.75 0H7.5m9-6h3.75m-3.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-9.75 0h9.75"/></svg>`,
        title: 'EQ / Компрессор',
        desc: 'Справочник по частотным диапазонам, типичным проблемам и параметрам обработки',
        route: '/eq',
        color: '#10b981',
        badge: 'Справочник',
      },
    ];

    return { apiStatus, features };
  },

  template: `
    <div class="view">
      <!-- Hero -->
      <div style="text-align:center; padding: 40px 0 60px;">
        <div style="display:inline-flex; align-items:center; gap:8px; margin-bottom:20px;">
          <span class="badge badge-accent">v1.0 Beta</span>
          <span v-if="apiStatus==='ok'" class="badge badge-success">API онлайн</span>
          <span v-else-if="apiStatus==='error'" class="badge badge-error">API офлайн</span>
          <span v-else class="badge" style="background:var(--elevated); color:var(--muted)">Проверка API…</span>
        </div>

        <h1 style="font-size:2.8rem; margin-bottom:16px; background:linear-gradient(135deg,#e2e8f0,#a78bfa); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;">
          StereoBrother
        </h1>
        <p style="color:var(--muted); font-size:1.15rem; max-width:520px; margin:0 auto 36px;">
          Инструменты для звукорежиссёра — AI-обработка аудио, анализ спектра и громкости, справочник по EQ
        </p>

        <div style="display:flex; justify-content:center; gap:12px; flex-wrap:wrap;">
          <router-link to="/process" class="btn btn-primary btn-lg">
            <svg viewBox="0 0 20 20" fill="currentColor" style="width:18px;height:18px"><path fill-rule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clip-rule="evenodd"/></svg>
            Начать работу
          </router-link>
          <router-link to="/spectrum" class="btn btn-secondary btn-lg">
            Анализатор спектра
          </router-link>
        </div>
      </div>

      <!-- Feature Cards -->
      <div class="grid-2" style="margin-bottom:48px;">
        <div
          v-for="f in features"
          :key="f.route"
          class="card"
          style="cursor:pointer; transition: transform 0.2s, box-shadow 0.2s;"
          @mouseenter="e => e.currentTarget.style.transform='translateY(-3px)'"
          @mouseleave="e => e.currentTarget.style.transform=''"
          @click="$router.push(f.route)"
        >
          <div style="display:flex; align-items:flex-start; gap:16px;">
            <div :style="'width:48px;height:48px;border-radius:12px;background:'+f.color+'22;display:flex;align-items:center;justify-content:center;flex-shrink:0;color:'+f.color" v-html="f.icon"></div>
            <div style="flex:1;">
              <div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">
                <h3>{{ f.title }}</h3>
                <span class="badge badge-accent" style="font-size:0.7rem;">{{ f.badge }}</span>
              </div>
              <p style="color:var(--muted); font-size:0.9rem; line-height:1.5;">{{ f.desc }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Formats / Info row -->
      <div class="card" style="background:var(--surface);">
        <div style="display:flex; flex-wrap:wrap; gap:40px; align-items:center;">
          <div>
            <h4 style="margin-bottom:10px; color:var(--muted);">Поддерживаемые форматы</h4>
            <div class="chip-group">
              <span v-for="fmt in ['MP3','WAV','FLAC','M4A','OGG','AAC']" :key="fmt" class="chip" style="cursor:default;">{{ fmt }}</span>
            </div>
          </div>
          <div style="height:60px; width:1px; background:var(--border); flex-shrink:0;"></div>
          <div>
            <h4 style="margin-bottom:10px; color:var(--muted);">Лимиты плана</h4>
            <div style="display:flex; gap:24px; flex-wrap:wrap;">
              <div><div style="font-size:1.4rem; font-weight:700; font-family:var(--mono);">10 мин</div><div style="font-size:0.8rem; color:var(--muted);">макс. длительность</div></div>
              <div><div style="font-size:1.4rem; font-weight:700; font-family:var(--mono);">100/д</div><div style="font-size:0.8rem; color:var(--muted);">обработок в день</div></div>
              <div><div style="font-size:1.4rem; font-weight:700; font-family:var(--mono);">500 ₽</div><div style="font-size:0.8rem; color:var(--muted);">в месяц</div></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
});
