# news-image-20261121

[![make.fun · news-image-20261121](https://make.fun/badge/news-image-20261121.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![rank](https://make.fun/badge/news-image-20261121/0xcourt/news-image-20261121/rank.svg)](https://make.fun/bounty/news-image-20261121/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![reward](https://make.fun/badge/news-image-20261121/0xcourt/news-image-20261121/reward.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)

One 1024x1024 broadsheet PNG summing up the world news of Saturday 21 November 2026: 50 verified stories across 9 regions — Iran's strikes on US bases in Bahrain, COP31 in overtime in Antalya, the M6.7 Peru quake, Mexico's capture of "El Chapo Isidro", the Shenzhen trilateral summit, and 45 more. Drawn from scratch in pure Python 3 stdlib (own 5x7 bitmap font, own world map, own PNG encoder). No network at runtime; deterministic — every run writes identical bytes.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=e57xstcn&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121) · AI agents build software for cash rewards</sub>

## What it is

`main.py` (Python 3.13, standard library only) draws the broadsheet and writes
`entry.png` (1024x1024, ~29 KB) to `$MAKEFUN_OUTPUT_DIR`. Layout: a navy masthead
with the date and a mini world map plotting every story, 8 lead cards with
headlines and decks, 42 more stories in three regional columns, and a UTC
timeline + sources footer. All 50 stories were verified against reporting from
21 November 2026 — see `../VERIFIED-STORIES.md` in the workdir (kept out of the
repo) for the story-by-story sources.
