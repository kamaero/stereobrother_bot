import { createApp, defineComponent, ref, Transition } from 'https://unpkg.com/vue@3/dist/vue.esm-browser.prod.js';
import { createRouter, createWebHashHistory, RouterView, RouterLink } from 'https://unpkg.com/vue-router@4/dist/vue-router.esm-browser.js';

import HomeView from './views/HomeView.js';
import ProcessView from './views/ProcessView.js';
import SpectrumView from './views/SpectrumView.js';
import LoudnessView from './views/LoudnessView.js';
import EQReferenceView from './views/EQReferenceView.js';

// ── Router ──────────────────────────────────────────────────────────
const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/',         component: HomeView },
    { path: '/process',  component: ProcessView },
    { path: '/spectrum', component: SpectrumView },
    { path: '/loudness', component: LoudnessView },
    { path: '/eq',       component: EQReferenceView },
  ],
  scrollBehavior: () => ({ top: 0 }),
});

// ── Nav icons (inline SVG strings) ──────────────────────────────────
const icons = {
  home: `<svg viewBox="0 0 20 20" fill="currentColor"><path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h4a1 1 0 001-1v-3h2v3a1 1 0 001 1h4a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z"/></svg>`,
  process: `<svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clip-rule="evenodd"/></svg>`,
  spectrum: `<svg viewBox="0 0 20 20" fill="currentColor"><path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zm6-4a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zm6-3a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"/></svg>`,
  loudness: `<svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.707.707L4.586 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.586l3.707-3.707a1 1 0 011.09-.217zm4.264 3.217a1 1 0 011.414 0A7.971 7.971 0 0117 10a7.971 7.971 0 01-1.939 5.207 1 1 0 01-1.414-1.414A5.976 5.976 0 0015 10a5.976 5.976 0 00-1.353-3.793 1 1 0 010-1.414zm-2.829 2.828a1 1 0 011.415 0A3.987 3.987 0 0113 10a3.987 3.987 0 01-.767 2.379 1 1 0 11-1.415-1.414A1.994 1.994 0 0011 10a1.994 1.994 0 00-.182-.965 1 1 0 010-1.414z" clip-rule="evenodd"/></svg>`,
  eq: `<svg viewBox="0 0 20 20" fill="currentColor"><path d="M5 4a1 1 0 00-2 0v7.268a2 2 0 000 3.464V16a1 1 0 102 0v-1.268a2 2 0 000-3.464V4zm6 0a1 1 0 10-2 0v1.268a2 2 0 000 3.464V16a1 1 0 102 0V8.732a2 2 0 000-3.464V4zm5 3a1 1 0 00-1 1v.268a2 2 0 000 3.464V16a1 1 0 102 0v-4.268a2 2 0 000-3.464V8a1 1 0 00-1-1z"/></svg>`,
  logo: `<svg width="28" height="28" viewBox="0 0 40 40" fill="none"><rect x="4" y="14" width="4" height="12" rx="2" fill="#7c3aed"/><rect x="10" y="8" width="4" height="24" rx="2" fill="#7c3aed"/><rect x="16" y="4" width="4" height="32" rx="2" fill="#a78bfa"/><rect x="22" y="10" width="4" height="20" rx="2" fill="#7c3aed"/><rect x="28" y="16" width="4" height="8" rx="2" fill="#7c3aed"/></svg>`,
};

// ── Root App Component ───────────────────────────────────────────────
const App = defineComponent({
  name: 'App',
  components: { RouterView, RouterLink },
  setup() {
    return { icons };
  },
  template: `
    <div class="app-shell">
      <nav class="nav">
        <router-link to="/" class="nav-logo">
          <span v-html="icons.logo"></span>
          <span>StereoBrother</span>
        </router-link>
        <div class="nav-links">
          <router-link to="/" class="nav-link" exact>
            <span v-html="icons.home"></span>
            <span>Главная</span>
          </router-link>
          <router-link to="/process" class="nav-link">
            <span v-html="icons.process"></span>
            <span>AI Обработка</span>
          </router-link>
          <router-link to="/spectrum" class="nav-link">
            <span v-html="icons.spectrum"></span>
            <span>Спектр</span>
          </router-link>
          <router-link to="/loudness" class="nav-link">
            <span v-html="icons.loudness"></span>
            <span>Громкость</span>
          </router-link>
          <router-link to="/eq" class="nav-link">
            <span v-html="icons.eq"></span>
            <span>EQ / Компрессор</span>
          </router-link>
        </div>
      </nav>
      <main class="main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  `,
});

// ── Mount ────────────────────────────────────────────────────────────
const app = createApp(App);
app.use(router);
app.mount('#app');
