# Ролик «Юная чемпионка» — запуск локально

Генерацию запускаем там, где открыта сеть и лежит ключ fal.ai.

## Что понадобится
- Python 3.9+
- ffmpeg в PATH (Windows: `winget install Gyan.FFmpeg`)
- Ключ fal.ai: https://fal.ai/dashboard/keys

## Установка (один раз)
```bash
pip install -r requirements.txt
```
Переименуй `.env.example` → `.env` и впиши свой ключ:
```
FAL_KEY=твой_настоящий_ключ
```

## Запуск
```bash
python champion_movie.py --images-only   # сначала только картинки (дёшево)
python champion_movie.py                  # полный ролик -> output/champion_movie.mp4
python champion_movie.py --scenes 1       # одна сцена для теста
```

## Если ошибка
- `Не задан FAL_KEY` → не создан `.env`.
- Ошибка имени модели → актуальные имена на https://fal.ai/models, впиши в
  константы `IMAGE_MODEL` / `VIDEO_MODEL` в начале `champion_movie.py`.
- `ffmpeg not found` → установи ffmpeg.
