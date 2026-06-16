# TASK: init-s01 — перенос с GitHub и адаптация под двухагентную схему

**Дата:** 2026-06-16
**Статус:** `ожидает`
**Сложность:** средняя (git + слияние файлов + правка доков, без запуска пайплайна)

---

## Контекст

Рабочая директория: `G:\_My_Programming-2\VIDEO-CLAUDE-CHAT`

В ней **уже есть** каркас двухагентной схемы (создан архитектором):
`AGENTS.md`, `CLAUDE.md`, `CONTEXT.md`, `PROJECT_LOG.md`, `tasks/`, `MY-COMMENTS/`.

Исходный код проекта лежит на GitHub:
https://github.com/Yuri-Sverdlov/VIDEO-CLAUDE-CHAT

Там один коммит с файлами:
`champion_movie.py`, `requirements.txt`, `.env.example`, `.gitignore`,
`README_RUN.md`, `storyboard.svg`, `ARCHITECT_BRIEF.md`.

**Задача:** забрать код с GitHub в текущую папку, **не затерев** каркас, и
полностью адаптировать репозиторий под дальнейшую работу архитектор ↔ кодер.

**НЕ запускай** `champion_movie.py` и **НЕ** трать кредиты fal.ai в этом задании.

---

## Шаги

### 1. Git: инициализация и забор файлов с GitHub

```powershell
cd G:\_My_Programming-2\VIDEO-CLAUDE-CHAT
git init
git remote add origin https://github.com/Yuri-Sverdlov/VIDEO-CLAUDE-CHAT.git
git fetch origin main
```

Забери **только** файлы проекта с remote (не перезаписывая каркас целиком):

```powershell
git checkout origin/main -- champion_movie.py requirements.txt .env.example README_RUN.md storyboard.svg ARCHITECT_BRIEF.md
```

`.gitignore` — **слить вручную**: взять версию с GitHub и **добавить** строки,
если их нет (секреты, output, Python, venv — всё должно остаться).

### 2. Адаптация документации

**`CONTEXT.md`** — заполни по содержанию `ARCHITECT_BRIEF.md`:
- суть проекта (6-сценный ролик через fal.ai, 3 стадии A/B/C);
- стек (Python 3.9+, fal-client, ffmpeg, dotenv);
- стейдж-гейт и текущий фокус: «код перенесён, пайплайн ещё не запускали»;
- ссылка на `storyboard.svg` и `README_RUN.md`.

**`AGENTS.md`** — раздел «Проектные правила» заполни из `ARCHITECT_BRIEF.md`:
- `FAL_KEY` только в `.env`, никогда в код/лог/коммит;
- перед запуском проверять актуальность `IMAGE_MODEL` / `VIDEO_MODEL` на https://fal.ai/models;
- бюджет: сначала `--images-only`, видео только после приёмки архитектором;
- этика образа: stylized animated character, не фотокопия ребёнка;
- стейдж-гейт: не переходить к следующей стадии без явного задания в `TASK.md`.

**`CLAUDE.md`** — дополни «Карту проекта»:
- `champion_movie.py` — пайплайн (стадии A/B/C);
- `README_RUN.md` — инструкция запуска;
- `storyboard.svg` — визуальная раскадровка;
- `output/` — сгенерированные медиа (в git не идёт).

**`ARCHITECT_BRIEF.md`** — перенеси в `MY-COMMENTS/architect-brief-original.md`
(историческая копия). Из корня **удали** `ARCHITECT_BRIEF.md`, чтобы не дублировать
источники правды (см. `AGENTS.md` — правило против рассинхрона).

### 3. Бэклог следующего шага

Создай `tasks/backlog/2026-06-16_stage-a-images-only.md` — краткое ТЗ на будущее:
подготовка окружения + прогон стадии A (`--images-only`), без видео.

### 4. Проверки (без API)

```powershell
pip install -r requirements.txt
python -m py_compile champion_movie.py
python champion_movie.py --help
```

Если `.env` нет — **не создавай** с ключом; достаточно проверить, что `.env.example` на месте.

Проверь наличие ffmpeg: `ffmpeg -version` (если нет — зафиксируй в REPORT, не устанавливай сам).

### 5. Git commit и push

```powershell
git add -A
git status
git commit -m "chore: merge GitHub code with two-agent scaffold (init-s01)"
git push -u origin main
```

Если push отклонён (non-fast-forward) — **не делай force push**; опиши ситуацию в REPORT.

---

## Критерии приёмки

- [ ] В корне есть и код (`champion_movie.py`, `requirements.txt`, …), и каркас (`AGENTS.md`, `tasks/`, …)
- [ ] `ARCHITECT_BRIEF.md` удалён из корня; копия в `MY-COMMENTS/architect-brief-original.md`
- [ ] `CONTEXT.md` и `AGENTS.md` заполнены проектной спецификой (не заглушки)
- [ ] `python -m py_compile champion_movie.py` — OK
- [ ] `python champion_movie.py --help` — OK
- [ ] `.gitignore` покрывает `.env`, `output/`, `__pycache__/`, venv
- [ ] `git push` успешен; `git log --oneline -1` содержит `init-s01`
- [ ] Пайплайн **не запускался** (нет новых файлов в `output/` от fal.ai)

---

## Отчёт

Заполни `tasks/REPORT.md`: что сделано, вывод каждой проверки, проблемы (ffmpeg, push, конфликты).
