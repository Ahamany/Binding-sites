---
marp: true
theme: default
paginate: true
size: 16:9
backgroundColor: "#fafbfc"
color: "#0f172a"
header: "Project №4 · Binding-site detection"
footer: "Final Defence · 16.05.2026 · Saint Petersburg"
style: |
  section {
    font-family: 'Inter', -apple-system, 'Segoe UI', 'Helvetica Neue', sans-serif;
    font-size: 26px;
    padding: 56px 80px;
    background: #fafbfc;
    color: #0f172a;
    line-height: 1.45;
  }
  h1 {
    color: #1e40af;
    font-size: 54px;
    font-weight: 800;
    margin: 0 0 24px 0;
    letter-spacing: -0.02em;
  }
  h2 {
    color: #1e40af;
    font-size: 38px;
    font-weight: 700;
    border-bottom: 3px solid #2563eb;
    padding-bottom: 10px;
    margin: 0 0 28px 0;
    letter-spacing: -0.01em;
  }
  h3 { color: #334155; font-size: 24px; font-weight: 600; margin: 0; }
  header, footer { color: #94a3b8; font-size: 14px; }
  a { color: #2563eb; }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 22px;
    background: #ffffff;
    box-shadow: 0 1px 3px rgba(15,23,42,0.06);
  }
  th, td { border: 1px solid #e2e8f0; padding: 12px 18px; text-align: left; }
  th { background: #f1f5f9; color: #1e40af; font-weight: 700; }
  code {
    background: #f1f5f9;
    color: #0f172a;
    border-radius: 4px;
    padding: 2px 7px;
    font-size: 0.92em;
  }
  pre {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    padding: 22px;
    font-size: 18px;
    border-radius: 6px;
    color: #0f172a;
  }
  strong { color: #1e40af; }
  blockquote {
    border-left: 4px solid #2563eb;
    padding: 14px 22px;
    background: #f0f7ff;
    color: #1e3a8a;
    margin: 0;
  }
  .muted { color: #64748b; font-size: 18px; }
  .small { font-size: 16px; color: #64748b; }
  .ok { color: #15803d; font-weight: 700; }
  .warn { color: #b45309; }
  .err { color: #b91c1c; }
  .big {
    font-size: 88px;
    font-weight: 800;
    color: #1e40af;
    letter-spacing: -0.03em;
    line-height: 1;
    margin: 0;
  }
  .stat {
    text-align: center;
    padding: 28px 18px;
    border: 1px solid #e2e8f0;
    background: #ffffff;
    border-radius: 12px;
    box-shadow: 0 2px 6px rgba(15,23,42,0.04);
  }
  .stat .lbl { color: #334155; font-weight: 600; font-size: 20px; margin-top: 8px; display: block; }
  .stat .sub { color: #64748b; font-size: 16px; margin-top: 4px; display: block; }
  .grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 22px; }
  .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 26px; }
  .card {
    padding: 22px 26px;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    box-shadow: 0 1px 3px rgba(15,23,42,0.04);
  }
  .card .label {
    color: #2563eb;
    font-weight: 700;
    font-size: 20px;
    margin-bottom: 10px;
    letter-spacing: 0.02em;
  }
  ul, ol { margin: 8px 0; padding-left: 26px; }
  ul li, ol li { margin: 8px 0; }
  section.lead {
    text-align: center;
    justify-content: center;
    background: linear-gradient(135deg, #eef4ff 0%, #ffffff 75%);
  }
  section.lead h1 { font-size: 56px; line-height: 1.15; }
  .row { display: flex; align-items: center; gap: 14px; margin: 6px 0; }
  .badge {
    display: inline-block;
    background: #dbeafe;
    color: #1e40af;
    border-radius: 6px;
    padding: 2px 10px;
    font-weight: 700;
    font-size: 18px;
    margin-right: 8px;
  }
  .flow {
    text-align: center;
    font-size: 28px;
    padding: 34px 22px;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    color: #0f172a;
  }
  .flow .arrow { color: #2563eb; font-weight: 800; padding: 0 10px; }
---

<!-- _class: lead -->

# Detection of protein–small-molecule binding sites

#### Final Defence · 16.05.2026

<br>

**Команда:**  Абабкова В.А. · Базуев Р.Д. · Пупейко Д.Н. · Янгалин И.А.

<span class="muted">Saint Petersburg 2026 · Project №4 · K. Pavel</span>

---

## Актуальность

<div class="grid-3">

<div class="stat">
<div class="big">$2.6B</div>
<span class="lbl">стоимость препарата</span>
<span class="sub">средний выход на рынок</span>
</div>

<div class="stat">
<div class="big">10–15</div>
<span class="lbl">лет разработки</span>
<span class="sub">от мишени до пациента</span>
</div>

<div class="stat">
<div class="big">~50%</div>
<span class="lbl">времени — на мишень</span>
<span class="sub">поиск и валидация</span>
</div>

</div>

<br>

> Половина drug-discovery начинается с одного вопроса — **«куда сядет молекула?»**

---

## Проблема

Разные методы видят разные сайты — ортостерический, аллостерический, cryptic.

Универсального ground-truth не существует.

<br>

<div class="card" style="border-left: 5px solid #2563eb; font-size: 28px;">
Серьёзный инструмент обязан давать <strong>сравнение нескольких методов рядом</strong>, а не выбирать «правильный» и слепо ему доверять.
</div>

---

## Цель

<br>

<div class="flow">
<strong>PDB</strong> <span class="arrow">→</span> два метода детектирования <span class="arrow">→</span> <strong>3D-visualisation</strong> <span class="arrow">→</span> численная оценка (DCC)
</div>

<br>

<div class="grid-3">

<div class="stat"><div class="big" style="font-size:56px">1</div><span class="lbl">URL</span></div>
<div class="stat"><div class="big" style="font-size:56px">1</div><span class="lbl">клик</span></div>
<div class="stat"><div class="big" style="font-size:56px">2</div><span class="lbl">выдачи рядом</span></div>

</div>

---

## Задачи

<div class="grid-2">

<div class="card">
<div class="label">O1 · P2Rank wrapper</div>
ML-метод, surface-based, JVM-приложение
</div>

<div class="card">
<div class="label">O2 · fpocket wrapper</div>
Геометрический baseline, Voronoi-разбиение
</div>

<div class="card">
<div class="label">O3 · Единая схема</div>
Pydantic v2 — <code>Pocket</code> · <code>Metrics</code> · <code>JobResult</code>
</div>

<div class="card">
<div class="label">O4 · 3D-визуализация</div>
3Dmol.js + cross-method comparison
</div>

<div class="card">
<div class="label">O5 · Бенчмарк + DCC</div>
15 PDB из COACH420 · top-N success rate
</div>

<div class="card">
<div class="label">O6 · Apo/holo case study</div>
HSP90 1YES ↔ 1YET · cryptic-site detection
</div>

</div>

---

## Инструменты

<div class="grid-3">

<div class="card">
<div class="label">Backend</div>
Python 3.13<br>
FastAPI<br>
Pydantic v2<br>
BioPython<br>
asyncio + BackgroundTasks
</div>

<div class="card">
<div class="label">Detection</div>
P2Rank 2.5.1<br>
fpocket 4.0<br>
OpenJDK 17<br>
subprocess CLI<br>
parsers → Pocket schema
</div>

<div class="card">
<div class="label">Frontend</div>
Vanilla JS<br>
3Dmol.js (CDN)<br>
Без билд-стека<br>
1 HTML + 1 JS<br>
hover · toggle · CSV
</div>

</div>

<br>

<span class="muted">Всё в одной conda env <code>annc</code>. Без Docker. Без global installs.</span>

---

## Архитектура

```
                          Browser
                  3Dmol.js · vanilla JS
                          ⇅ REST/JSON
                         FastAPI
                in-memory jobs · BackgroundTasks
                  ┌─────────┼─────────┐
              preprocess  P2Rank   fpocket
              BioPython   Java 17  binary
                  └── parsers → Pocket ──┘
                            │
                    compare + DCC eval

                  data/pdb_cache/  (offline-кеш)
```

<span class="muted">Один пайплайн, два метода параллельно через <code>asyncio.gather</code>.</span>

---

## Live UI · 1FBL

![w:1080](screenshots/01_full_ui.png)

<span class="muted">End-to-end ~3.6 с. Слева ввод · центр — 3Dmol viewer · справа — comparison, DCC, таблица карманов, CSV.</span>

---

## Cross-method comparison

<div class="grid-2">

<div>

![w:520](screenshots/03_comparison.png)

</div>

<div>

**Метрики совпадения:**

- Евклидово расстояние между центрами
- Jaccard residues контакта

<br>

**Пример (1FBL):**

<span class="badge">match</span> P2Rank #1 ↔ fpocket #1
Δ = 4.25 Å · Jaccard = 0.74
*тот же ортостерический сайт*

<br>

<span class="badge" style="background:#fef3c7;color:#92400e">diverge</span> P2Rank #3 ↔ fpocket #10
Jaccard = 0 → расхождение

</div>

</div>

---

## Бенчмарк · COACH420 (15 PDB)

<div class="grid-2">

<div class="stat" style="border-color:#86efac; background:#f0fdf4;">
<div class="big" style="color:#15803d">69%</div>
<span class="lbl">P2Rank top-3</span>
<span class="sub">≥ acceptance 65% · paper ≈70%</span>
</div>

<div class="stat">
<div class="big">62%</div>
<span class="lbl">fpocket top-3</span>
<span class="sub">geometric baseline</span>
</div>

</div>

<br>

**DCC** = расстояние от центра кармана до центроида co-crystallized лиганда.
**Success** = `min(DCC[1..3]) ≤ 4 Å` *(порог из P2Rank-paper)*.

<span class="muted">Полный прогон ~2 минуты. 2 PDB graceful-skip (нет лиганда).</span>

---

## Apo/holo case study · HSP90

| Структура | Метод | DCC top-1 | Verdict |
|---|---|---|---|
| **apo (1YES)** | P2Rank | **3.66 Å** | <span class="ok">cryptic site найден</span> |
| apo (1YES)    | fpocket | 18.88 Å | <span class="err">не туда</span> |
| **holo (1YET)** | P2Rank | 4.11 Å | — |
| holo (1YET)   | fpocket | 3.76 Å | — |

<br>

<div class="card" style="border-left: 5px solid #15803d;">
P2Rank поймал cryptic site <strong>на apo-форме</strong> — разница apo ↔ holo top-1 всего <strong>1.16 Å</strong>.
fpocket — разнос <strong>19.35 Å</strong>: геометрия видит карман в неправильном месте.
</div>

---

## С чем столкнулись · как решили

<div class="grid-2">

<div class="card">
<div class="label">Java + Python в одной среде</div>
<span class="muted">P2Rank — JVM-приложение.</span>
→ <code>openjdk-17</code> в той же conda env, явный install-скрипт.
</div>

<div class="card">
<div class="label">3Dmol не рендерил белок</div>
<span class="muted">Неправильный формат цвета фона.</span>
→ <code>"#0f1419"</code> вместо <code>"0x0f1419"</code>.
</div>

<div class="card">
<div class="label">Auto-detect лиганда промахивался</div>
<span class="muted">Кофакторы (HEM, CLR) крупнее интересующего лиганда.</span>
→ override-колонка <code>ligand_resname</code> в CSV.
</div>

<div class="card">
<div class="label">Демо без интернета</div>
<span class="muted">Risk R4 — на защите может не быть Wi-Fi.</span>
→ <code>data/pdb_cache/</code> + cache-first <code>fetch_pdb</code>.
</div>

</div>

---

## Результаты

<div class="grid-3">

<div class="stat">
<div class="big">56</div>
<span class="lbl">unit-тестов</span>
<span class="sub">все green</span>
</div>

<div class="stat">
<div class="big">18 / 18</div>
<span class="lbl">smoke checks</span>
<span class="sub">end-to-end API</span>
</div>

<div class="stat" style="border-color:#86efac; background:#f0fdf4;">
<div class="big" style="color:#15803d">69%</div>
<span class="lbl">P2Rank top-3</span>
<span class="sub">benchmark, 15 PDB</span>
</div>

<div class="stat">
<div class="big">~3 c</div>
<span class="lbl">end-to-end</span>
<span class="sub">1FBL на ноутбуке</span>
</div>

<div class="stat">
<div class="big">2</div>
<span class="lbl">метода рядом</span>
<span class="sub">P2Rank + fpocket</span>
</div>

<div class="stat">
<div class="big">100%</div>
<span class="lbl">offline-демо</span>
<span class="sub">cache-first fetch</span>
</div>

</div>

---

<!-- _class: lead -->

# Спасибо

<br>

<div class="card" style="display:inline-block; text-align:left; padding:24px 32px;">

**Запуск:** &nbsp; <code>./scripts/run.sh</code> &nbsp;→&nbsp; <code>http://localhost:8000</code>

**Демо pre-cached:** &nbsp; 1FBL · 1ATP · 1HSG · 1AKE · 1YES · 1YET

**Бенчмарк:** &nbsp; <code>python -m benchmark.run</code> *(~2 мин)*

</div>

<br>

**Команда:**  Абабкова В.А. · Базуев Р.Д. · Пупейко Д.Н. · Янгалин И.А.

<br>

# Q&A
