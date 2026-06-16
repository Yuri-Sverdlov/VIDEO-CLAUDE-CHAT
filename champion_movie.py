#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
champion_movie.py
=================
Пайплайн для сборки 30-секундного мультфильма-поздравления через fal.ai.

ИДЕЯ РОЛИКА (раскадровка, 6 кадров по ~5 сек):
  1. Крупный план: героиня на пьедестале "1", победный жест.
  2. Общий план: весь пьедестал, трибуны, она ликует.
  3. Крупный план: тренер по футболу надевает ей медаль.
  4. Крупный план: она благодарит тренера.
  5. Общий план: второй тренер (по бегу) вручает вторую медаль.
  6. Магический переход -> финал: она капитан футбольной команды на поле.

КАК РАБОТАЕТ ПАЙПЛАЙН (две стадии + сборка):
  Стадия A (text-to-image): для каждого кадра генерируем КЛЮЧЕВОЙ КАДР (картинку).
                            Единый CHARACTER + STYLE + фиксированный seed держат
                            образ героини стабильным во всех сценах.
  Стадия B (image-to-video): каждую картинку "оживляем" в ~5-сек клип.
  Стадия C (ffmpeg):         склеиваем 6 клипов в один ролик 30 сек.

ЗАПУСК (локально, где открыта сеть и лежит ключ):
  pip install -r requirements.txt
  # ffmpeg должен быть установлен и доступен в PATH
  # ключ кладём в файл .env (см. .env.example) ИЛИ в переменную окружения FAL_KEY
  python champion_movie.py --images-only     # только картинки (дёшево, проверить образ)
  python champion_movie.py                    # полный прогон
  python champion_movie.py --scenes 1 2       # прогнать только выбранные кадры

ВАЖНО ПРО КЛЮЧ: скрипт читает ключ ТОЛЬКО из окружения / .env.
Никогда не вписывай ключ прямо в этот файл.
"""

import argparse
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

# Необязательно: подхватить ключ из файла .env, если установлен python-dotenv.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import fal_client
except ImportError:
    sys.exit("Нет пакета fal-client. Установи: pip install -r requirements.txt")


# ---------------------------------------------------------------------------
# КОНФИГУРАЦИЯ
# ---------------------------------------------------------------------------
# Имена моделей на fal.ai периодически меняются — проверяй на https://fal.ai/models
# Это бюджетная связка: FLUX для картинок + Wan для image-to-video.
IMAGE_MODEL = "fal-ai/flux/dev"          # text-to-image (ключевые кадры)
VIDEO_MODEL = "fal-ai/wan-i2v"           # image-to-video (~$0.05/сек)

OUT_DIR = Path("output")                 # сюда складываются картинки, клипы и финал
CLIP_SECONDS = 5                         # длительность одного клипа
SEED = 7777                              # фиксированный seed -> стабильный образ
IMAGE_SIZE = "landscape_16_9"            # горизонтальный кадр

# Единый образ героини — повторяется в КАЖДОМ промпте ради постоянства.
CHARACTER = (
    "a cheerful athletic 12-year-old girl, slim, bright joyful smile, "
    "white baseball cap, bright orange sports t-shirt, grey shorts, white sneakers, "
    "a stylized animated character (not a real person)"
)

# Единый стиль — 3D Pixar/Disney.
STYLE = (
    "3D Pixar/Disney animation style, soft cinematic lighting, warm colors, "
    "expressive, high quality, sunny day"
)

NEGATIVE = "photorealistic real child, text, watermark, deformed hands, extra limbs"


# ---------------------------------------------------------------------------
# РАСКАДРОВКА: 6 кадров. Каждый — словарь с действием и планом.
# ---------------------------------------------------------------------------
STORYBOARD = [
    {
        "id": 1,
        "shot": "close-up, low angle, heroic",
        "action": "standing on the number 1 winner's podium, arms thrown up in a "
                  "victorious cheer, stadium in soft focus behind",
        "motion": "gentle camera push-in, hair and shirt move slightly in the breeze",
    },
    {
        "id": 2,
        "shot": "wide establishing shot",
        "action": "the full podium (places 2-1-3) visible, crowd stands in background, "
                  "she stands proudly in the center on top step, celebrating",
        "motion": "slow camera reveal pulling back, flags waving",
    },
    {
        "id": 3,
        "shot": "close-up",
        "action": "a friendly football coach steps in and places a shining medal "
                  "around her neck",
        "motion": "the medal swings and catches the light, both smiling",
    },
    {
        "id": 4,
        "shot": "close-up on the girl",
        "action": "she thanks the coach with a warm nod, hand over her heart, "
                  "happy grateful eyes",
        "motion": "subtle head nod, eyes sparkle, soft smile widens",
    },
    {
        "id": 5,
        "shot": "wide shot",
        "action": "a second coach, the running coach, approaches and hands her a "
                  "second medal; now two medals shine on her chest",
        "motion": "coach walks in from the side, medals glint in the sun",
    },
    {
        "id": 6,
        "shot": "wide cinematic shot, magical transition",
        "action": "a bright flash of light, then she stands on a green football pitch "
                  "wearing a team captain's kit (captain armband, slightly different "
                  "from the others), a team of 5 kids behind her (three girls, two boys), "
                  "she stands in a confident captain's pose",
        "motion": "magical sparkle transition, then a slow hero shot, banner waving",
    },
]


# ---------------------------------------------------------------------------
# ВСПОМОГАТЕЛЬНОЕ
# ---------------------------------------------------------------------------
def build_image_prompt(scene: dict) -> str:
    """Собираем промпт для картинки: образ + план + действие + стиль."""
    return f"{CHARACTER}, {scene['shot']}, {scene['action']}. {STYLE}."


def download(url: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, dest)
    return dest


def on_log(update):
    """Печать логов очереди fal во время ожидания."""
    if isinstance(update, fal_client.InProgress):
        for log in (update.logs or []):
            print("   ", log.get("message", ""))


# ---------------------------------------------------------------------------
# СТАДИЯ A: text-to-image
# ---------------------------------------------------------------------------
def generate_keyframe(scene: dict) -> Path:
    prompt = build_image_prompt(scene)
    print(f"[Кадр {scene['id']}] картинка: {prompt[:80]}...")
    result = fal_client.subscribe(
        IMAGE_MODEL,
        arguments={
            "prompt": prompt,
            "image_size": IMAGE_SIZE,
            "seed": SEED + scene["id"],   # стабильно, но не идентично между кадрами
            "num_images": 1,
        },
        with_logs=True,
        on_queue_update=on_log,
    )
    img_url = result["images"][0]["url"]
    return download(img_url, OUT_DIR / f"frame_{scene['id']:02d}.png")


# ---------------------------------------------------------------------------
# СТАДИЯ B: image-to-video
# ---------------------------------------------------------------------------
def animate_keyframe(scene: dict, image_path: Path) -> Path:
    print(f"[Кадр {scene['id']}] анимация ({CLIP_SECONDS}с)...")
    # Загружаем картинку на fal, получаем URL, который понимает видеомодель.
    image_url = fal_client.upload_file(str(image_path))
    result = fal_client.subscribe(
        VIDEO_MODEL,
        arguments={
            "image_url": image_url,
            "prompt": scene["motion"],
            "negative_prompt": NEGATIVE,
            "num_frames": CLIP_SECONDS * 16,   # ~16 fps; уточни под модель
        },
        with_logs=True,
        on_queue_update=on_log,
    )
    video_url = result["video"]["url"]
    return download(video_url, OUT_DIR / f"clip_{scene['id']:02d}.mp4")


# ---------------------------------------------------------------------------
# СТАДИЯ C: сборка ffmpeg
# ---------------------------------------------------------------------------
def assemble(clips, final: Path) -> None:
    if not clips:
        print("Нет клипов для сборки.")
        return
    listfile = OUT_DIR / "concat.txt"
    listfile.write_text("".join(f"file '{c.resolve()}'\n" for c in clips))
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(listfile), "-c:v", "libx264", "-pix_fmt", "yuv420p",
        str(final),
    ]
    print("Сборка финального ролика:", " ".join(cmd))
    subprocess.run(cmd, check=True)
    print(f"Готово: {final.resolve()}")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Champion movie pipeline (fal.ai)")
    parser.add_argument("--images-only", action="store_true",
                        help="generate keyframes only (cheap, check character look)")
    parser.add_argument("--scenes", type=int, nargs="*",
                        help="run only specified scene numbers, e.g. --scenes 1 2")
    args = parser.parse_args()

    if not os.getenv("FAL_KEY"):
        sys.exit("Не задан FAL_KEY. Создай .env из .env.example или: export FAL_KEY='...'")

    scenes = STORYBOARD
    if args.scenes:
        scenes = [s for s in STORYBOARD if s["id"] in args.scenes]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    clips = []

    for scene in scenes:
        img = generate_keyframe(scene)
        if args.images_only:
            continue
        clip = animate_keyframe(scene, img)
        clips.append(clip)
        time.sleep(1)  # лёгкая пауза между задачами

    if not args.images_only:
        assemble(clips, OUT_DIR / "champion_movie.mp4")
    else:
        print("Картинки готовы в папке output/. Проверь образ героини перед видео-стадией.")


if __name__ == "__main__":
    main()
