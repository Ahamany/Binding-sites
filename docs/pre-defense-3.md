---
marp: true
theme: default
paginate: true
size: 16:9
backgroundColor: "#0f1419"
color: "#e6edf3"
header: "Project №4 · Binding-site detection"
footer: "Pre-defense №3 · 14.05.2026"
style: |
  section { font-size: 24px; }
  h1 { color: #58a6ff; }
  h2 { color: #58a6ff; border-bottom: 1px solid #30363d; padding-bottom: 6px; }
  code, pre { background: #161b22; }
  table { font-size: 20px; }
  th, td { border: 1px solid #30363d; padding: 6px 10px; }
  th { background: #161b22; }
  strong { color: #58a6ff; }
  .ok { color: #3fb950; }
  .fail { color: #f85149; }
  .small { font-size: 18px; color: #8b949e; }
---

<!-- _class: lead -->
# Detection of protein–small-molecule binding sites

**Веб-инструмент**, сравнивающий P2Rank (ML) и fpocket (геометрический)
на одной задаче и визуализирующий результат в браузере.

**Команда:** Абабкова В.А., Базуев Р.Д., Пупейко Д.Н., Янгалин И.А.

<span class="small">Saint Petersburg 2026 · Project №4 (K. Pavel)</span>

---

## Зачем искать binding sites

- **Drug discovery:** прежде чем подбирать молекулу, нужно знать, **куда** она сядет.
- Экспериментально (co-crystallography, NMR) — **дорого** и **долго**.
- ML/геометрические методы предсказывают сайты по 3D-структуре за **секунды**.
- Для одного белка обычно есть **несколько** карманов разной природы:
  ортостерический, аллостерический, cryptic (виден только в holo-форме).
- **Наша задача** — собрать end-to-end-инструмент, который запускает 2 разных метода
  и показывает их предсказания **рядом**, чтобы видеть зону согласия и расхождения.

---

## Goal & Objectives

**Goal:** Веб-инструмент: PDB → предсказание карманов несколькими методами → 3D-просмотрщик.

| # | Objective | Status |
|---|---|---|
| O1 | Обернуть **P2Rank** (ML, surface-based) | <span class="ok">✓</span> |
| O2 | Обернуть **fpocket** (геометрический, Voronoi) | <span class="ok">✓</span> |
| O3 | Привести вывод к единой Pydantic-схеме | <span class="ok">✓</span> |
| O4 | 3D-визуализация (3Dmol.js) + cross-method comparison | <span class="ok">✓</span> |
| O5 | Бенчмарк ~15 PDB с DCC top-N success rate | <span class="ok">✓</span> 69% |
| O6 | Apo/holo case study (HSP90) | <span class="ok">✓</span> |

**Out of scope:** обучение собственной модели, MD/ensemble, БД/auth, облачный деплой.

---

## Tool Specification

**Входы:** PDB-файл (`.pdb`, `.pdb.gz`) или PDB ID → fetch с RCSB.

**Выходы** (унифицированная JSON-схема):
```json
{
  "results": {
    "p2rank":  [{"rank": 1, "score": 9.77, "center": [70.5, 83.4, -11.5], "residues": ["A_103", ...]}, ...],
    "fpocket": [{"rank": 1, "score": 0.21, "center": [70.5, 84.2, -10.9], ...}, ...]
  },
  "comparison": [{"p2rank_rank": 1, "fpocket_rank": 1, "distance": 4.25, "jaccard": 0.74}, ...],
  "metrics":    {"p2rank": {"dcc_top1": 5.96, "success_top3": false}, "fpocket": {"dcc_top1": 3.55, "success_top3": true}}
}
```

**Дополнительные эндпойнты:** `GET /results.csv` (карманы плоской таблицей), `GET /structure` (очищенный PDB для отрисовки).

---

## System Architecture

```
┌──────────────────────────────┐
│  Browser: HTML + 3Dmol.js    │  upload / PDB-ID, viewer, comparison panel
└────────┬─────────────────────┘
         │ REST/JSON
┌────────▼─────────────────────┐
│  FastAPI + Pydantic v2       │  POST /jobs, GET /jobs/{id}[/results|/structure|/results.csv]
└──┬───────┬────────┬──────────┘
   │       │        │
┌──▼──┐ ┌──▼─────┐ ┌▼──────────┐
│Pre- │ │P2Rank  │ │ fpocket   │
│proc.│ │(Java17 │ │ (binary)  │
│Bio  │ │ subproc│ │ subproc   │
│Py   │ │)       │ │           │
└─────┘ └────┬───┘ └─────┬─────┘
             │           │
        ┌────▼───────────▼────┐
        │ Parsers → Pocket schema │
        │ + compare + DCC eval    │
        └─────────────────────────┘
```

**Стек:** Python 3.13 · FastAPI · BioPython · P2Rank 2.5.1 · fpocket 4.0 · 3Dmol.js · conda env `annc`.

---

## Live demo: 1FBL

![w:1080](screenshots/01_full_ui.png)

<span class="small">End-to-end время для 1FBL: **3.65 c** (≪ 30 с целевого). Слева: ввод. Центр: 3Dmol viewer, синие/оранжевые сферы — карманы P2Rank/fpocket. Справа: comparison-таблица + DCC-плашка.</span>

---

## Cross-method comparison panel

![w:520](screenshots/03_comparison.png)

- **P2Rank #1 ↔ fpocket #1:** карманы согласны (Δ = 4.25 Å, Jaccard = 0.74 по residues).
- **P2Rank #4 ↔ fpocket #2:** Δ = 0.74 Å — оба метода нашли один и тот же мелкий карман.
- **P2Rank #3 ↔ fpocket #10:** Δ = 10.76 Å, Jaccard = 0 — разногласие, потенциальный false-positive.
- **Live DCC** (под comparison): P2Rank top-1 = 5.96 Å <span class="fail">✗</span> · fpocket top-1 = 3.55 Å <span class="ok">✓</span> (порог 4 Å).

---

## Benchmark · COACH420 subset (15 PDB)

| Метод | Top-3 success @ 4 Å | Среднее время на PDB |
|---|---|---|
| **P2Rank** | <span class="ok">**9/13 = 69%**</span> ≥ acceptance 65% | ~7 с |
| **fpocket** | 8/13 = 62% | ~7 с |

**2 PDB пропущены** (нет co-crystallized лиганда: 1OWT, 1G3K). Бенчмарк прошёл за ~2 мин полностью.

**Метрика DCC** (Distance to Center of Cocrystal) — евклидово расстояние от центра кармана до центра co-crystallized лиганда; top-3 success = `min(DCC[1..3]) ≤ 4 Å` (порог из P2Rank-paper).

---

## Apo/holo case study · HSP90 (1YES ↔ 1YET)

| Структура | Метод | Top-1 center | DCC к holo-сайту | Verdict |
|---|---|---|---|---|
| **apo (1YES)** | p2rank | (38.9, –45.4, 63.0) | **3.66 Å** | <span class="ok">✓ cryptic site found</span> |
| apo (1YES) | fpocket | (34.3, –63.9, 62.6) | 18.88 Å | <span class="fail">✗ wrong pocket</span> |
| **holo (1YET)** | p2rank | (38.2, –46.2, 62.8) | 4.11 Å | — |
| holo (1YET) | fpocket | (40.0, –45.4, 62.2) | 3.76 Å | — |

- **P2Rank**: top-1 apo и holo разнесены **на 1.16 Å** — метод нашёл cryptic-сайт на apo-форме, где лиганда нет.
- **fpocket**: разнос **19.35 Å** — геометрия видит крупный карман в неправильном месте.

→ Этот пример показывает, ради чего ML-метод полезнее для drug discovery.

---

## Failure cases (для Q&A)

Из 13 успешно прогнанных PDB **4 fail у P2Rank**:

| PDB | DCC top-1 | Причина |
|---|---|---|
| 1IEP | 60 Å | Имeется только STI (Imatinib) — метод **реально промахнулся** |
| 2RH1 | 22 Å | Auto-detect выбрал **CLR** (холестерин, allosteric) вместо CAU (карaзолол) |
| 4COX | 23 Å top-1 / **1.7 Å top-3** ✓ | Auto-detect выбрал **HEM** вместо IMN (индометацин) |
| 3PXF | 6.4 Å | Метод нашёл соседний карман, чуть мимо |

**Вывод:** половина «провалов» — артефакт **auto-detect heuristic** (наибольшая HETATM-группа без буферов), фиксится override-колонкой `ligand_resname` в CSV.

---

## Что осталось до Final Defence

| День | Дата | Задача |
|---|---|---|
| 8 | **14.05** (сегодня) | Pre-defense №3 (комбинированная) + слайды |
| 9 | 15.05 | Polish + offline cache PDB (Risk R4) + финальные слайды + репетиция |
| Final | **16.05** | Final Defence |

**Главные риски и мера:**
- *R4:* На защите нет интернета → pre-cache 5 demo-PDB в `benchmark/work/` (план Day 9).
- *R6:* DCC-числа сходятся с P2Rank-paper (~70% top-3) → **69% получили**, в пределах нормы.
- *R7:* Поломка за день до защиты → 15.05 code-freeze, только репетиция.

---

## Сводка статуса

- **51 unit-тест** (pytest) + **18/18 smoke** проходят.
- Backend, frontend, бенчмарк, apo/holo, метрики — **all green**.
- Repo: ~3 000 строк Python + JS, ~30 файлов исходников.
- Время end-to-end (1FBL): **3.65 c** на ноутбуке без GPU.
- Реализованы **все 6 objectives** из раздела 1.

<span class="small">README + roadmap-таблица обновляются ежедневно; пайплайн воспроизводим из conda env `annc` (Python 3.13, Java 17, fpocket 4.0).</span>

---

<!-- _class: lead -->
# Q&A

**Repo:** `~/Рабочий стол/ANNC/binding-sites`
**Стек:** FastAPI + P2Rank + fpocket + 3Dmol.js · conda env `annc`
**Демо:** `./scripts/run.sh` → http://localhost:8000 → введите `1FBL`

<span class="small">Pre-defense №3 · 14.05.2026 · Команда: Абабкова, Базуев, Пупейко, Янгалин</span>
