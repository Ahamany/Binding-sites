# Binding Sites Detection

Веб-инструмент для поиска сайтов связывания малых молекул в белках: загружаем PDB → запускаем **P2Rank** (ML, surface-based) и **fpocket** (геометрия) параллельно → видим карманы в 3D-просмотрщике в браузере → получаем численную оценку (DCC) и сравнение методов между собой.

**Метрики качества:** 56 unit-тестов · 18/18 smoke · бенчмарк P2Rank top-3 = **69%** @ 4 Å на 15-PDB подмножестве COACH420.

---

## О проекте

### Что делает

На входе — 3D-структура белка: PDB ID с RCSB или локальный `.pdb` файл. На выходе:

- **2 набора карманов** — P2Rank и fpocket рядом (single pass, параллельно).
- **3D-визуализация** в браузере: оба метода поверх белка, hover → подсветка, чекбоксы → toggle.
- **Cross-method comparison** — distance + Jaccard residues между лучшими карманами обоих методов.
- **DCC-метрика** (Distance to Center of Cocrystal) — численная оценка качества относительно реального co-crystallized лиганда. Порог success = 4 Å (P2Rank-paper).
- **CSV-выгрузка** карманов с координатами центров, score и остатками контакта.

### Зачем

Drug discovery: прежде чем подбирать молекулу, нужно знать **куда** она сядет. Со-кристаллография и NMR — дорого и медленно; геометрические и ML-методы предсказывают сайт за секунды по 3D-структуре. Сложность в том, что разные методы видят разные сайты (ортостерический vs аллостерический vs cryptic), и нет универсального ground-truth — поэтому нужна сравнительная оценка двух подходов, а не «один правильный ответ».

### Ключевые фичи

- **Два метода рядом** — P2Rank (ML) + fpocket (геометрия) в одном пайплайне, общая Pydantic-схема результата.
- **3Dmol.js viewer** — синие сферы P2Rank, оранжевые fpocket, hover-подсветка, toggle одного из методов.
- **Cross-method comparison** — для каждого top-N P2Rank находит ближайший fpocket-карман (distance + Jaccard).
- **DCC top-1 / top-3** — реальные числа метода относительно co-crystallized лиганда, success-флаг.
- **Бенчмарк** на 15 PDB из COACH420 — aggregate top-3 success rate за ~2 минуты.
- **Apo/holo case study** на HSP90 (1YES apo / 1YET holo) — демонстрация cryptic-site detection.
- **Offline-кеш PDB** (`data/pdb_cache/`) — демо работает без интернета (Risk R4).

### Команда

Абабкова В.А., Базуев Р.Д., Пупейко Д.Н., Янгалин И.А.

Saint Petersburg 2026 · Project №4 «Detection of protein–small-molecule binding sites» (K. Pavel).

---

## Стек

- **Backend:** Python 3.13 + FastAPI + Pydantic v2 + BioPython, async через `asyncio` + `BackgroundTasks`.
- **Detection:** P2Rank 2.5.1 (Java 17 CLI), fpocket 4.0 (бинарь).
- **Frontend:** Vanilla JS + 3Dmol.js (CDN), без билд-стека.
- **Тесты:** pytest (unit) + bash smoke-скрипт против поднятого API.
- **Окружение:** conda env `annc` (Python 3.13). Все зависимости — **строго туда**, глобально ничего не ставим.

---

## Установка

### 1. Создать (или активировать) conda env

```bash
source "$(conda info --base)/etc/profile.d/conda.sh"
conda create -n annc python=3.13 -y    # если env ещё нет
conda activate annc
```

### 2. Системные пакеты — Java 17 и fpocket

```bash
conda install -c conda-forge -c bioconda openjdk=17 fpocket -y
```

Проверка:

```bash
java -version    # → openjdk 17.x.x
fpocket -h       # → справка fpocket 4.0
```

### 3. Python-зависимости

```bash
pip install -r backend/requirements.txt
```

### 4. P2Rank в third_party/

```bash
./scripts/install_p2rank.sh
```

Скрипт скачает P2Rank 2.5.1 и распакует в `third_party/p2rank/`. Проверка:

```bash
./third_party/p2rank/prank -version    # → 2.5.1
```

### 5. (Опционально) прогрев offline-кеша

```bash
./scripts/precache_demo.sh
```

Скачает 6 демо-PDB в `data/pdb_cache/` — после этого демо работает без интернета (см. ниже).

### Sanity-check

```bash
pytest backend/tests/ -v       # → 56 unit-тестов pass
./scripts/run.sh &             # поднять backend в фоне
sleep 2 && ./scripts/smoke.sh  # → 18/18 pass
pkill -f uvicorn               # остановить backend
```

---

## Запуск

```bash
./scripts/run.sh
```

Бэк поднимается на `http://localhost:8000`, фронт раздаётся им же как статикой. Останов — `Ctrl+C` или `pkill -f uvicorn`.

---

## Использование (UI walkthrough)

1. **Открыть** `http://localhost:8000` в браузере.
2. **Ввести PDB ID** (например, `1FBL`) или **загрузить локальный `.pdb`** через форму. Нажать **Predict**.
3. **Дождаться** статуса `done` — обычно 3–10 секунд для среднего белка (≤500 residues).
4. **3D-viewer** покажет:
   - Белок cartoon-style серым.
   - **Синие сферы** — карманы P2Rank, размер пропорционален score.
   - **Оранжевые сферы** — карманы fpocket.
   - **Hover** по строке таблицы → подсветка соответствующего кармана.
   - **Чекбоксы P2Rank / fpocket** — toggle видимости одного из методов.
5. **Comparison-плашка** под viewer'ом покажет лучшее совпадение, например: «P2Rank #1 ↔ fpocket #1 · Δ=4.25 Å · Jaccard=0.74» — оба метода нашли один и тот же сайт.
6. **Metrics-плашка** (только если PDB содержит co-crystallized лиганд): «P2Rank DCC: 5.96 Å · fpocket DCC: 3.55 Å» с success-флагами относительно порога 4 Å.
7. **Download CSV** — кнопка ниже таблицы карманов. CSV содержит rank, score, координаты центра, остатки контакта для каждого метода.

Apo-структура (без HETATM) — comparison остаётся, но metrics-плашка скрыта.

---

## API

| Метод | Путь | Описание |
|---|---|---|
| `GET`  | `/api/health` | Liveness probe |
| `GET`  | `/api/jobs` | Список всех задач |
| `POST` | `/api/jobs` | Создать задачу (form-data: `pdb_id` или `file`) |
| `GET`  | `/api/jobs/{id}` | Статус + полный результат (pockets + comparison + metrics) |
| `GET`  | `/api/jobs/{id}/structure` | Очищенный PDB (для 3Dmol.js) |
| `GET`  | `/api/jobs/{id}/results` | Только pockets + comparison + metrics |
| `GET`  | `/api/jobs/{id}/results.csv` | Карманы плоской таблицей CSV |

### Примеры

Создать задачу по PDB ID:

```bash
curl -X POST http://localhost:8000/api/jobs -F "pdb_id=1FBL"
# → {"job_id": "695ac1d152d0"}
```

Загрузить локальный файл:

```bash
curl -X POST http://localhost:8000/api/jobs -F "file=@./my_protein.pdb"
```

Получить результат (poll до `status=done`):

```bash
curl http://localhost:8000/api/jobs/695ac1d152d0
# → {"job_id": "695ac1d152d0", "status": "done", "pdb_id": "1FBL",
#    "results":    {"p2rank": {...}, "fpocket": {...}},
#    "comparison": [{"p2rank_rank":1, "fpocket_rank":1, "distance":4.25, "jaccard":0.74}],
#    "metrics":    {"p2rank":  {"dcc_top1":5.96, "success_top3":false},
#                   "fpocket": {"dcc_top1":3.55, "success_top3":true}}}
```

Скачать CSV:

```bash
curl -O http://localhost:8000/api/jobs/695ac1d152d0/results.csv
```

---

## Бенчмарк (COACH420 subset)

```bash
python -m benchmark.run --out benchmark/report.md
```

Прогон по 15 PDB из `benchmark/coach420_subset.csv` (well-known protein-ligand complexes). Время — около 2 минут на ноутбуке. Результат в `benchmark/report.md`:

- Per-PDB таблица: DCC top-1 / top-3 для каждого метода + success-флаг.
- Aggregate строка: «P2Rank top-3 success: 9/13 = 69%, fpocket: 8/13 = 62%».
- 2 PDB graceful-skip (нет co-crystallized лиганда).

Метрика **DCC** (Distance to Center of Cocrystal): евклидово расстояние от центра кармана до центроида co-crystallized лиганда. **Top-3 success** = `min(DCC[1..3]) ≤ 4 Å` (порог из P2Rank-paper).

Custom subset:

```bash
python -m benchmark.run --subset my_subset.csv --out my_report.md --work my_work_dir
```

Формат CSV — `pdb_id,ligand_resname`. Пустой `ligand_resname` → auto-detect (самая большая HETATM-группа, исключая буферы).

---

## Apo/holo case study

```bash
python -m benchmark.apo_holo --apo 1YES --holo 1YET --out benchmark/apo_holo_report.md
```

Тот же пайплайн на паре апо-/холо-структур одной мишени (HSP90 — каноничный пример из литературы). Reference-сайт берётся из holo-структуры (1YET, где лиганд кристаллизован).

В отчёте:

- Top-1 карман каждого метода для apo и holo (координаты центра).
- DCC каждого top-1 относительно holo-binding-site.
- Distance между apo top-1 и holo top-1 одного метода.

Интерпретация (числа из реального прогона):

- **P2Rank top-1 apo (DCC 3.66 Å) и holo (DCC 4.11 Å) разнесены на 1.16 Å** — метод нашёл **cryptic site на apo-форме**, где лиганда нет. Это «зачем ML, а не только геометрия» для drug discovery.
- **fpocket разнос между apo и holo — 19.35 Å** — геометрия видит крупный карман в неправильном месте на apo.

---

## Offline-демо (Risk R4)

На защите или демо может не быть интернета. Решение — локальный кеш PDB.

```bash
./scripts/precache_demo.sh                 # warm-up data/pdb_cache/ (дефолтный набор)
./scripts/precache_demo.sh 1FBL 2RH1       # custom subset
```

Дефолтный набор: **1FBL, 1ATP, 1HSG, 1AKE, 1YES, 1YET** (6 PDB · ~1.4 МБ).

Как работает `fetch_pdb`:

1. **Cache hit** (`data/pdb_cache/{PDB}.pdb` существует) → копия в `work/{job_id}/input.pdb`, **без сети**.
2. **Cache miss** → fetch с RCSB (`https://files.rcsb.org/download/...`); при успехе **автозалив** в кеш для будущих оффлайн-запусков.
3. **404** → `PDBNotFoundError`, в кеш ничего не пишется.

После прогрева кеша демо `1FBL` отрабатывает за ~3 секунды полностью локально.

---

## Тесты

```bash
pytest backend/tests/ -v       # 56 unit-тестов
./scripts/smoke.sh             # 18 end-to-end проверок (требует running backend)
```

Покрытие критичных модулей: P2Rank/fpocket парсеры, preprocess, comparison (distance + Jaccard), DCC, fetch-cache, REST API, валидация PDB ID.

---

## Структура

```
binding-sites/
├── backend/
│   ├── app/
│   │   ├── main.py                   # FastAPI app, статика, /api/health
│   │   ├── routes/jobs.py            # /api/jobs* endpoints
│   │   ├── services/binding_site.py  # оркестрация + fetch_pdb с offline-кешем
│   │   ├── tools/
│   │   │   ├── p2rank.py             # обёртка P2Rank
│   │   │   ├── fpocket.py            # обёртка fpocket
│   │   │   └── preprocess.py         # PDB cleanup (BioPython)
│   │   ├── models/pocket.py          # Pydantic-схема (Pocket, MethodResult, Metrics, JobResult)
│   │   └── eval/
│   │       ├── compare.py            # cross-method сравнение (distance + Jaccard)
│   │       └── dcc.py                # DCC + ligand-center extraction
│   ├── tests/                        # 56 pytest-тестов
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── app.js                        # upload + polling + 3Dmol.js + comparison + metrics
│   └── style.css
├── benchmark/
│   ├── coach420_subset.csv           # 15 PDB ID для бенчмарка
│   ├── run.py                        # batch runner + markdown report
│   ├── apo_holo.py                   # apo/holo case study
│   ├── report.md                     # generated
│   └── apo_holo_report.md            # generated
├── docs/
│   ├── pre-defense-3.{md,pdf,pptx}   # Pre-defense №3 слайды (13)
│   ├── final-defence.{md,pdf,pptx}   # Final Defence слайды (15)
│   └── screenshots/                  # PNG-скриншоты UI для слайдов
├── data/
│   └── pdb_cache/                    # offline-кеш PDB (Risk R4)
├── scripts/
│   ├── install_p2rank.sh
│   ├── run.sh                        # запуск uvicorn
│   ├── smoke.sh                      # 18 end-to-end проверок
│   ├── precache_demo.sh              # warm-up offline-кеша
│   └── screenshots.py                # playwright headless-скриншоты
├── third_party/p2rank/               # бинарь P2Rank (gitignored)
└── work/                             # job-кеши (gitignored)
```
