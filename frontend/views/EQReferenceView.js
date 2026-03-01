import { defineComponent, ref } from 'https://unpkg.com/vue@3/dist/vue.esm-browser.prod.js';

const FREQ_BANDS = [
  {
    name: 'Суббас',
    range: '20–60 Гц',
    color: '#7c3aed',
    desc: 'Физически ощутимый удар, рокот, фундамент микса. Избыток — мутность, нехватка — лёгкость звука.',
    boost: 'Добавляет вес, пробивной удар бочки и баса',
    cut: 'Убирает мутность, рокот комнаты, гул систем усиления',
    instruments: ['Бочка (kick)', 'Бас-гитара', 'Контрабас', 'Синт. бас', 'Орган'],
    tips: [
      'High-pass фильтр ниже 30–40 Гц на большинстве каналов (кроме баса/кика)',
      'При записи в плохой комнате — режь ниже 80 Гц на всём кроме ударных',
    ],
  },
  {
    name: 'Бас',
    range: '60–250 Гц',
    color: '#2563eb',
    desc: 'Теплота, тело, плотность инструментов. Фундаментальные частоты большинства инструментов.',
    boost: 'Добавляет теплоту, полноту, "мясо" в звуке',
    cut: 'Убирает "картонный" звук, улучшает разборчивость микса',
    instruments: ['Все ударные', 'Бас-гитара', 'Гитары (рит.)', 'Пианино', 'Голос (мужской)'],
    tips: [
      '200–250 Гц часто дают "картонный" призвук у гитар — попробуй срезать на 3–6 дБ',
      'Тепло голоса живёт на 100–200 Гц; слишком много — "рот" в звуке',
      'Режь бас у всего кроме низкочастотных инструментов для чистого микса',
    ],
  },
  {
    name: 'Низкие средние',
    range: '250–500 Гц',
    color: '#0891b2',
    desc: 'Зона "мутности" и полноты. Избыток — мутный, тяжёлый звук. Правильный баланс — тело без грязи.',
    boost: 'Добавляет полноту, "мясо" акустической гитары',
    cut: 'Убирает мутность, улучшает прозрачность низкочастотного пространства',
    instruments: ['Акуст. гитара', 'Бас (гармоники)', 'Том-томы', 'Голос (тело)'],
    tips: [
      'Самая проблемная зона для большинства миксов — осторожно с бустом',
      '300–400 Гц — типичная зона "картонного" призвука барабанов',
      'Попробуй узкий срез с поиском резонансов (динамическим EQ или сметя)',
    ],
  },
  {
    name: 'Средние',
    range: '500 Гц – 2 кГц',
    color: '#059669',
    desc: 'Присутствие и разборчивость. Основные обертоны. Избыток — "телефонный" звук.',
    boost: 'Добавляет присутствие, разборчивость вокала и гитары',
    cut: 'Убирает "телефонный" призвук, снижает агрессивность',
    instruments: ['Вокал', 'Гитары (гармоники)', 'Клавишные', 'Струнные', 'Флейта'],
    tips: [
      '1 кГц — добавляет "кухонный нож" атаке гитары',
      'Вокальные частицы (согласные) хорошо слышны на 800 Гц – 1.5 кГц',
      'Срез в этой области помогает при маскировке инструментов в плотном миксе',
    ],
  },
  {
    name: 'Высокие средние',
    range: '2–5 кГц',
    color: '#d97706',
    desc: 'Атака, щелчок, агрессия. Хорошее присутствие в этой зоне = инструмент слышен в миксе. Избыток — усталость слуха.',
    boost: 'Выводит инструмент вперёд, добавляет атаку и щелчок',
    cut: 'Снижает агрессивность, убирает "рез" в ушах',
    instruments: ['Вокал (атака)', 'Гитара (прис.)', 'Тарелки (нижние)', 'Клик бочки'],
    tips: [
      '3–4 кГц — зона максимальной чувствительности слуха, будь осторожен с бустом',
      '2 кГц — добавляет "рожки" и агрессию дисторшн-гитаре',
      'Boost 2–4 кГц помогает вокалу "прорезаться" сквозь плотный микс',
    ],
  },
  {
    name: 'Присутствие',
    range: '5–10 кГц',
    color: '#dc2626',
    desc: 'Чёткость, детальность, "воздух" в нижней части. Щелчок тарелок, чёткость вокала.',
    boost: 'Добавляет блеск, чёткость, "шелест"',
    cut: 'Убирает шипение, резкость, "свист"',
    instruments: ['Тарелки', 'Вокал (ч.)', 'Акуст. гитара', 'Рояль (верх)', 'Скрипки'],
    tips: [
      '5–6 кГц — де-ессер работает именно здесь для борьбы с сибилянтами',
      '8 кГц boost даёт "воздушный" звук акустическим инструментам',
      'Срез у тарелок на 6–8 кГц смягчает их в миксе',
    ],
  },
  {
    name: 'Воздух',
    range: '10–20 кГц',
    color: '#7c3aed',
    desc: 'Воздух, простор, открытость. Избыток — шипение. Правильное количество — "студийное" звучание.',
    boost: 'Добавляет "студийный воздух", открытость, блеск',
    cut: 'Убирает шипение, шум матрицы, HF-артефакты',
    instruments: ['Тарелки', 'Акуст. гитара', 'Вокал (дыхание)', 'Синтезаторы'],
    tips: [
      '12–16 кГц — High-shelf boost на мастер-шине добавляет "масштаб"',
      'Low-pass ниже 18 кГц уберёт ультразвук и снизит нагрузку при кодировании',
      'Слишком много воздуха + шум = нежелательное шипение в тихих местах',
    ],
  },
];

const COMPRESSOR_PARAMS = [
  {
    name: 'Threshold',
    desc: 'Порог срабатывания. Всё выше — компрессируется.',
    values: '-20 dB — мягкая компрессия, -6 dB — жёсткая/лимитирование',
    icon: '⬆️',
    tips: 'Начни с -15 dB для вокала, слушай когда компрессор начинает работать.',
  },
  {
    name: 'Ratio',
    desc: 'Степень сжатия. 2:1 — мягко, 10:1+ — лимитер.',
    values: '2:1–4:1 музыка, 4:1–8:1 вокал/баc, 10:1+ бочка/лимит',
    icon: '📐',
    tips: '4:1 — универсальное начало. Для прозрачного контроля динамики используй 2:1–3:1.',
  },
  {
    name: 'Attack',
    desc: 'Время до срабатывания. Медленный = транзиенты проходят насквозь.',
    values: '< 5 мс — убирает транзиенты, > 20 мс — сохраняет щелчок/атаку',
    icon: '⚡',
    tips: 'На барабанах: медленный attack (20–50 мс) сохраняет удар. На вокале: 5–15 мс.',
  },
  {
    name: 'Release',
    desc: 'Время восстановления после спада сигнала ниже порога.',
    values: '< 50 мс — может накачивать, 100–300 мс — естественно',
    icon: '🔄',
    tips: 'Auto Release часто оптимален для начала. "Накачка" (pumping) = release слишком короткий.',
  },
  {
    name: 'Knee',
    desc: 'Мягкость перехода вблизи порога.',
    values: 'Soft knee = плавно, незаметно; Hard knee = резко, чётко',
    icon: '🦵',
    tips: 'Soft knee 2–4 dB для прозрачного сжатия. Hard knee для лимитирования.',
  },
  {
    name: 'Make-up Gain',
    desc: 'Компенсация потери громкости от компрессии.',
    values: 'Обычно = GR (gain reduction). Настраивай по ощущению при A/B.',
    icon: '🔊',
    tips: 'Добавляй gain reduction / ratio примерно. Финально корректируй на слух через bypass.',
  },
];

const INSTRUMENTS_FREQ = [
  { name: 'Бочка (Kick)', ranges: ['Удар: 50–100 Гц', 'Тело: 150–250 Гц', 'Клик: 2–4 кГц', 'Атмосфера: 6–10 кГц'] },
  { name: 'Малый барабан', ranges: ['Тело: 200–400 Гц', 'Мидрейндж: 1–3 кГц', 'Снэп: 4–7 кГц', 'Шипение: 8–12 кГц'] },
  { name: 'Бас-гитара', ranges: ['Фундамент: 40–100 Гц', 'Тело: 100–250 Гц', 'Присутствие: 700 Гц–1.5 кГц', 'Щипок: 2–4 кГц'] },
  { name: 'Электрогитара', ranges: ['Тело: 100–300 Гц', 'Мутность: 300–500 Гц', 'Атака: 1–3 кГц', 'Воздух: 6–10 кГц'] },
  { name: 'Вокал (мужской)', ranges: ['Тело: 125–300 Гц', 'Тёплость: 300–800 Гц', 'Присутствие: 1–5 кГц', 'Воздух: 8–12 кГц'] },
  { name: 'Вокал (женский)', ranges: ['Тело: 200–500 Гц', 'Чёткость: 1–3 кГц', 'Присутствие: 4–8 кГц', 'Воздух: 10–16 кГц'] },
  { name: 'Акуст. гитара', ranges: ['Фундамент: 80–200 Гц', 'Тело: 200–500 Гц', 'Стрейк: 2–5 кГц', 'Воздух: 8–16 кГц'] },
  { name: 'Рояль', ranges: ['Низкий: 30–200 Гц', 'Среднее тело: 200 Гц–1 кГц', 'Присутствие: 2–5 кГц', 'Блеск: 8–16 кГц'] },
];

export default defineComponent({
  name: 'EQReferenceView',

  setup() {
    const tab = ref('bands'); // 'bands' | 'compressor' | 'instruments'
    const activeBand = ref(null);

    function selectBand(band) {
      activeBand.value = activeBand.value === band ? null : band;
    }

    return { tab, activeBand, FREQ_BANDS, COMPRESSOR_PARAMS, INSTRUMENTS_FREQ, selectBand };
  },

  template: `
    <div class="view">
      <h1 class="page-title">EQ / Компрессор</h1>
      <p class="page-subtitle">Справочник по частотным диапазонам, типичным проблемам и параметрам обработки</p>

      <div class="tabs">
        <button class="tab" :class="{active: tab==='bands'}"      @click="tab='bands'">Частотные диапазоны</button>
        <button class="tab" :class="{active: tab==='compressor'}" @click="tab='compressor'">Компрессор</button>
        <button class="tab" :class="{active: tab==='instruments'}" @click="tab='instruments'">Инструменты</button>
      </div>

      <!-- ── Frequency Bands ── -->
      <div v-if="tab==='bands'">
        <!-- Visual frequency ruler -->
        <div class="card" style="margin-bottom:24px; padding:20px;">
          <div style="display:flex; height:32px; border-radius:8px; overflow:hidden; margin-bottom:8px;">
            <div v-for="b in FREQ_BANDS" :key="b.name"
              :style="'flex:1;background:'+b.color+'99;cursor:pointer;transition:opacity 0.15s;'"
              :title="b.name + ' ' + b.range"
              @click="selectBand(b)">
            </div>
          </div>
          <div style="display:flex; justify-content:space-between; font-size:0.75rem; color:var(--muted); font-family:var(--mono);">
            <span>20 Гц</span><span>60</span><span>250</span><span>500</span><span>2k</span><span>5k</span><span>10k</span><span>20 кГц</span>
          </div>
        </div>

        <!-- Band cards -->
        <div style="display:flex;flex-direction:column;gap:10px;">
          <div v-for="b in FREQ_BANDS" :key="b.name"
            :class="['card']"
            :style="activeBand===b ? 'border-color:'+b.color+';' : ''"
            style="cursor:pointer;transition:border-color 0.15s;"
            @click="selectBand(b)"
          >
            <div style="display:flex;align-items:center;gap:16px;">
              <div :style="'width:10px;height:48px;border-radius:5px;background:'+b.color+';flex-shrink:0;'"></div>
              <div style="flex:1;">
                <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px;">
                  <h3>{{ b.name }}</h3>
                  <span class="badge" :style="'background:'+b.color+'33;color:'+b.color+';'">{{ b.range }}</span>
                </div>
                <p style="color:var(--muted);font-size:0.88rem;">{{ b.desc }}</p>
              </div>
              <svg viewBox="0 0 20 20" fill="currentColor" style="width:18px;height:18px;color:var(--subtle);flex-shrink:0;transition:transform 0.15s;"
                :style="activeBand===b ? 'transform:rotate(180deg);' : ''">
                <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd"/>
              </svg>
            </div>

            <!-- Expanded details -->
            <div v-if="activeBand===b" style="margin-top:16px;padding-top:16px;border-top:1px solid var(--border);">
              <div class="grid-2" style="gap:16px;margin-bottom:16px;">
                <div style="background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.3);border-radius:8px;padding:14px;">
                  <div style="font-size:0.78rem;color:var(--muted);margin-bottom:6px;text-transform:uppercase;letter-spacing:0.05em;">Буст (+)</div>
                  <div style="font-size:0.9rem;">{{ b.boost }}</div>
                </div>
                <div style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);border-radius:8px;padding:14px;">
                  <div style="font-size:0.78rem;color:var(--muted);margin-bottom:6px;text-transform:uppercase;letter-spacing:0.05em;">Срез (−)</div>
                  <div style="font-size:0.9rem;">{{ b.cut }}</div>
                </div>
              </div>
              <div style="margin-bottom:12px;">
                <div style="font-size:0.82rem;color:var(--muted);margin-bottom:6px;">Инструменты в этой зоне:</div>
                <div class="chip-group">
                  <span v-for="inst in b.instruments" :key="inst" class="chip" style="cursor:default;font-size:0.8rem;">{{ inst }}</span>
                </div>
              </div>
              <div>
                <div style="font-size:0.82rem;color:var(--muted);margin-bottom:6px;">Практические советы:</div>
                <ul style="list-style:none;display:flex;flex-direction:column;gap:4px;">
                  <li v-for="tip in b.tips" :key="tip" style="display:flex;gap:8px;font-size:0.88rem;color:var(--muted);">
                    <span style="color:var(--accent-lt);flex-shrink:0;">→</span>{{ tip }}
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ── Compressor ── -->
      <div v-if="tab==='compressor'">
        <div class="alert alert-info" style="margin-bottom:24px;">
          Компрессор уменьшает динамический диапазон — разницу между громкими и тихими моментами. Используй с умом: цель — контроль, а не "убить" динамику.
        </div>

        <div style="display:flex;flex-direction:column;gap:16px;">
          <div v-for="p in COMPRESSOR_PARAMS" :key="p.name" class="card">
            <div style="display:flex;align-items:flex-start;gap:16px;">
              <div style="font-size:2rem;flex-shrink:0;line-height:1;margin-top:4px;">{{ p.icon }}</div>
              <div style="flex:1;">
                <h3 style="margin-bottom:6px;">{{ p.name }}</h3>
                <p style="color:var(--muted);font-size:0.9rem;margin-bottom:10px;">{{ p.desc }}</p>
                <div style="background:var(--elevated);border-radius:6px;padding:10px;margin-bottom:10px;">
                  <div style="font-size:0.78rem;color:var(--subtle);margin-bottom:2px;">Ориентиры:</div>
                  <div style="font-size:0.88rem;font-family:var(--mono);">{{ p.values }}</div>
                </div>
                <div style="display:flex;gap:8px;align-items:flex-start;">
                  <span style="color:var(--accent-lt);flex-shrink:0;margin-top:1px;">💡</span>
                  <div style="font-size:0.88rem;color:var(--muted);">{{ p.tips }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Compressor cheat sheet -->
        <div class="card" style="margin-top:24px;background:var(--surface);">
          <h4 style="margin-bottom:16px;">Быстрый чит-лист по инструментам</h4>
          <div style="overflow-x:auto;">
            <table style="width:100%;border-collapse:collapse;font-size:0.85rem;">
              <thead>
                <tr style="color:var(--muted);border-bottom:1px solid var(--border);">
                  <th style="text-align:left;padding:8px 12px;">Инструмент</th>
                  <th style="text-align:left;padding:8px 12px;">Ratio</th>
                  <th style="text-align:left;padding:8px 12px;">Attack</th>
                  <th style="text-align:left;padding:8px 12px;">Release</th>
                  <th style="text-align:left;padding:8px 12px;">Цель</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="r in [
                  {inst:'Бочка',    ratio:'4:1–6:1',  att:'5–20 мс',  rel:'50–150 мс', goal:'Убрать пики, сохранить удар'},
                  {inst:'Малый',    ratio:'3:1–8:1',  att:'3–10 мс',  rel:'100–300 мс',goal:'Тело + снэп'},
                  {inst:'Бас',      ratio:'4:1–6:1',  att:'10–30 мс', rel:'100–200 мс',goal:'Ровный уровень'},
                  {inst:'Гитара',   ratio:'2:1–4:1',  att:'15–30 мс', rel:'100–200 мс',goal:'Прозрачный контроль'},
                  {inst:'Вокал',    ratio:'3:1–5:1',  att:'5–15 мс',  rel:'80–150 мс', goal:'Разборчивость'},
                  {inst:'Мастер',   ratio:'1.5:1–2:1',att:'20–50 мс', rel:'200 мс+',   goal:'Склейка, подъём'},
                ]" :key="r.inst" style="border-bottom:1px solid var(--border);">
                  <td style="padding:8px 12px;font-weight:600;">{{ r.inst }}</td>
                  <td style="padding:8px 12px;font-family:var(--mono);color:var(--accent-lt);">{{ r.ratio }}</td>
                  <td style="padding:8px 12px;font-family:var(--mono);color:var(--cyan-lt);">{{ r.att }}</td>
                  <td style="padding:8px 12px;font-family:var(--mono);color:var(--cyan-lt);">{{ r.rel }}</td>
                  <td style="padding:8px 12px;color:var(--muted);">{{ r.goal }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- ── Instruments ── -->
      <div v-if="tab==='instruments'">
        <div class="grid-2" style="gap:16px;">
          <div v-for="inst in INSTRUMENTS_FREQ" :key="inst.name" class="card">
            <h3 style="margin-bottom:14px;display:flex;align-items:center;gap:8px;">
              <span style="width:8px;height:8px;border-radius:50%;background:var(--accent);display:inline-block;"></span>
              {{ inst.name }}
            </h3>
            <div style="display:flex;flex-direction:column;gap:6px;">
              <div v-for="(range, i) in inst.ranges" :key="range"
                style="display:flex;align-items:center;gap:10px;background:var(--elevated);padding:8px 12px;border-radius:6px;">
                <div :style="'width:6px;height:6px;border-radius:50%;flex-shrink:0;background:'+['#7c3aed','#059669','#d97706','#dc2626'][i]"></div>
                <span style="font-size:0.85rem;">{{ range }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
});
