# Binding Sites Detection

Инструмент для поиска сайтов связывания малых молекул в белках. Сравнивает **P2Rank** (ML, surface-based) и **fpocket** (геометрический), визуализирует карманы в браузере через 3Dmol.js.

Команда проекта: Абабкова В.А., Базуев Р.Д., Пупейко. Д.Н., Янгалин И.А.

## Стек

- **Backend:** Python 3.13 + FastAPI + Pydantic v2
- **Detection:** P2Rank 2.5.1 (Java 17), fpocket 4.0
- **Frontend:** Vanilla JS + 3Dmol.js
- **Окружение:** conda env `annc` в `/home/ahamany/miniconda3/envs/annc`

## Установка

Все зависимости — **строго в conda env `annc`**. Глобально ничего не ставим.

```bash
# 1. Системные пакеты в conda env
source /home/ahamany/miniconda3/etc/profile.d/conda.sh
conda activate annc
conda install -c conda-forge -c bioconda openjdk=17 fpocket -y

# 2. Python-зависимости
pip install -r backend/requirements.txt

# 3. P2Rank в third_party/p2rank
./scripts/install_p2rank.sh
```

## Запуск

```bash
./scripts/run.sh
# → http://localhost:8000
```

## API

| Метод | Путь | Описание |
|---|---|---|
| GET  | `/api/health` | Liveness probe |
| POST | `/api/jobs` | Создать задачу (form-data: `pdb_id` или `file`) |
| GET  | `/api/jobs/{id}` | Статус + результат |
| GET  | `/api/jobs/{id}/structure` | Очищенный PDB для отрисовки |
| GET  | `/api/jobs/{id}/results` | JSON с pockets и метриками |

### Пример

```bash
curl -X POST http://localhost:8000/api/jobs -F "pdb_id=1FBL"
# → {"job_id": "abc123…"}

curl http://localhost:8000/api/jobs/abc123…
# → {"job_id": "...", "status": "done", "results": {...}}
```

## Структура

```
binding-sites/
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI app, статика, /api/health
│   │   ├── routes/jobs.py         # /api/jobs* endpoints
│   │   ├── services/binding_site.py   # оркестрация
│   │   ├── tools/
│   │   │   ├── p2rank.py          # обёртка P2Rank (Day 2)
│   │   │   ├── fpocket.py         # обёртка fpocket (Day 3)
│   │   │   └── preprocess.py      # PDB cleanup
│   │   ├── models/pocket.py       # Pydantic-схема
│   │   └── eval/dcc.py            # метрика DCC (Day 7)
│   ├── tests/                     # pytest
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── app.js                     # upload + polling + 3Dmol.js
│   └── style.css
├── benchmark/                     # COACH420 subset + run.py (Day 7)
├── docs/                          # материалы для защит
├── scripts/
│   ├── install_p2rank.sh
│   └── run.sh
├── third_party/p2rank/            # бинарь P2Rank (gitignored)
└── work/                          # job-кеши (gitignored)
```

## Roadmap

См. `/home/ahamany/.claude/plans/research-projects-pdf-splendid-wave.md` — полный план с разбивкой по дням до Pre-defense №3 (14.05) и Final Defence (16.05).

| День | Задача |
|---|---|
| 1 (07.05) | ✅ Scaffold + установка зависимостей |
| 2 (08.05) | P2Rank wrapper |
| 3 (09.05) | fpocket wrapper + unified schema |
| 4 (10.05) | REST API + curl-тест end-to-end |
| 5 (11.05) | Frontend + 3Dmol.js рендер |
| 6 (12.05) | Сравнение методов |
| 7 (13.05) | Бенчмарк + DCC eval + apo/holo |
| 8 (14.05) | **Pre-defense №3 (комбинированная)** + слайды |
| 9 (15.05) | Polish + Final-слайды |
| 16.05 | **Final Defence** |
