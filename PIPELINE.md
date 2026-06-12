# Виральный продакшн-пайплайн

Реализация продакшн-ядра системы «Виральный Рост» (boont.ai): один человек
производит короткие виральные ролики сериями, а **Claude Code выступает
оркестратором**. Это продолжение проекта `veo3maker` — Remotion-субтитры,
которые уже были в репозитории, стали финальным шагом «упаковки».

## Идея (из гайда)

- **Оркестратор — Claude Code.** Он держит контекст, пишет промпты, глазами
  проверяет кадры на артефакты и решает, что перегенерить. Работает по
  **подписке** — отдельный Anthropic API не нужен.
- **Единица работы — гипотеза** = `персонаж × формула × хук`.
- **Длинный ролик = склейка 10-секундных кусков.** Под каждый кусок свой
  first frame, который потом «оживляется».
- **Фиксированное фото персонажа** подаётся в каждый first frame → креатор
  выглядит одинаково во всех роликах и сериях. Это ключевой приём.

## Поток

```
персонаж (фикс. фото)
      │
      ▼
гипотеза = персонаж × формула × хук
      │
      ▼  на каждый 10-сек сегмент:
   first frame (Nano Banana)  ──►  QC глазами Claude  ──►  оживление (Kling/Wan)
      │
      ▼
   склейка (ffmpeg) ──► субтитры (Remotion) ──► упаковка (описание/обложка/хэштеги)
```

## Стек и стоимость

| Шаг | Сервис | Стоимость |
|---|---|---|
| Оркестрация | **Claude Code** (подписка) | $0 сверху |
| First frame | **Nano Banana** via relay (laozhang.ai) или Gemini | ~$0.04/кадр (free tier до 500/день) |
| Оживление | **fal.ai → Wan 2.5** (дефолт; Kling/Seedance флагом) | ~$0.05/с |
| Сборка | ffmpeg | $0 |
| Субтитры | Remotion (уже в репо) | $0 |
| Research-скрейпинг *(позже)* | RapidAPI social-api4 | по запросам |
| Анализ видео *(позже)* | Gemini Flash Lite | копейки |

Прикидка: ролик ~60с (6×10с) ≈ **$0.24** картинки + **$3.0** видео = **~$3.2**.

Всё **pluggable** через `.env`: провайдеры меняются одной строкой. По
умолчанию `PIPELINE_DRY_RUN=1` — весь конвейер гоняется в mock-режиме
(плейсхолдер-кадры + Ken-Burns клипы) без единого ключа и без трат.

## Структура

```
pipeline/
  pconfig.py            конфиг из .env (pluggable провайдеры)
  models.py             датаклассы (Hypothesis, Segment, Block, ...)
  character.py          хранилище персонажей (фикс. фото + описание)
  run.py                состояние рана + manifest.json
  production.py         per-segment: first frame → animate
  assembly.py           склейка ffmpeg + субтитры (Remotion)
  cli.py                CLI, который дёргает скилл
  providers/
    base.py             HTTP + mock-генераторы артефактов
    images.py           first frame: mock | relay (Nano Banana)
    video.py            оживление: mock | fal (Wan/Kling/Seedance)
.claude/skills/viral-video-production/SKILL.md   инструкция-оркестратор
workspace/              раны и персонажи (git-ignored)
```

## Быстрый старт (mock, без ключей)

```bash
pip install -r requirements.txt          # нужен также ffmpeg в системе

python -m pipeline.cli character add --name alex --photo alex.jpg \
    --description "м, 28, кэжуал, дружелюбный"

python -m pipeline.cli run init --character alex \
    --persona "уставший айтишник" --formula "до/после" \
    --hook "ты делаешь это неправильно" --segments 3
# → впиши промпты сегментов в workspace/runs/<slug>/manifest.json

python -m pipeline.cli produce  --run <slug>     # frames + animate + assemble
python -m pipeline.cli status   --run <slug>
# результат: workspace/runs/<slug>/raw.mp4
```

Обычно этим оркестрирует Claude Code через скилл `viral-video-production`
(он же делает QC кадров и упаковку). См. `SKILL.md`.

## Включить реальную генерацию

В `.env`: `PIPELINE_DRY_RUN=0`, затем
`IMAGE_PROVIDER=relay` + `IMAGE_API_KEY=...` и
`VIDEO_PROVIDER=fal` + `FAL_API_KEY=...`. Команды те же.

## Что дальше (не входит в ядро)

Этап 1 **Research** (ScrapeCreators/RapidAPI → Gemini Flash Lite анализ →
Claude ищет паттерны → «кубики»), этап 3 **Скейлинг**, этап 4 **Платный
трафик**, аналитика с алертами в Telegram. Интерфейсы заложены в `pconfig`.
