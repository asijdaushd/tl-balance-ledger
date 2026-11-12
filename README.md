# tl-balance-ledger

Every weapon balance change in THRONE AND LIBERTY, extracted from the official patch notes
into per-weapon timelines. Each change is tagged buff / nerf / rework / bug fix / new.

Open `output/index.html` for the per-weapon pages, or `output/solisium-balance-ledger.html`
for one self-contained page with every weapon.

## Why

The official notes span 200+ articles over two years, in at least four different layouts.
Major expansions put their real notes on separate release pages instead of the news post.
Answering "what happened to Dagger since launch?" meant reading all of them. This tool
does that once and keeps the result current.

## Usage

```bash
pip install -r requirements.txt
python scripts/crawl_listing.py     # news listing -> data/articles.json
python scripts/fetch_articles.py    # article HTML -> cache/ (skips anything already cached)
python scripts/extract.py           # weapon changes -> data/patches/*.json
python scripts/generate.py          # per-weapon HTML -> output/
python scripts/build_single.py      # single-page ledger -> output/solisium-balance-ledger.html
```

Every stage caches, so it is safe to interrupt and cheap to re-run after a new patch.

## How extraction works

`scripts/parse.py` reads one page into an ordered list of blocks. `scripts/extract.py` finds
weapon changes in four layouts:

1. `<h2>Greatsword</h2>` style section headings
2. short `<p>` lines used as headings
3. `Wand: <change>` bullets under a generic Combat heading
4. a bare `Dagger:` bullet whose nested bullets are the changes

`scripts/classify.py` tags direction. Words like "increased" are read differently for
cooldowns and costs, where more is worse. `data/excluded.json` and `data/article-checklist.md`
list every article and why it was included or skipped.

## If a new patch extracts 0 changes

Find which of the four layouts it uses before touching the regexes. Please open an issue
with the article URL.

## Data and license

Code: MIT. Patch-note text quoted in `data/` and `output/` belongs to its publishers; it is
reproduced in short excerpts with a link back to each source article.

Unofficial fan tool. Not affiliated with or endorsed by NCSOFT or Amazon Games. THRONE AND LIBERTY is a trademark of its respective owners.
