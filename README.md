# Svenska 🇸🇪

A personal Swedish vocabulary practice app: search and filter a growing word
set, drill sentence starters that trigger V2 word-order inversion, and
improvise mini-monologues from randomly woven vocabulary.

## Tech stack

- **[Streamlit](https://streamlit.io/)** — the entire UI (Python, no separate
  frontend build).
- **SQLite** — single-file database (`words/svenska.db`), accessed directly
  via the stdlib `sqlite3` module (no ORM).
- **Docker Compose** — optional containerized run.

## Folder structure

```
.
├── app.py               # Streamlit UI: Browse / Improv Weave / Add Entry tabs
├── db.py                # SQLite connection, schema, query helpers
├── seed.py              # One-time seed: migrates words/svenska.csv + hand-written content
├── requirements.txt     # Python dependencies (Streamlit)
├── Dockerfile            # Container image for the app
├── docker-compose.yml   # Runs the app on :8501, bind-mounts words/
├── .dockerignore
├── .gitignore
└── words/
    ├── svenska.csv       # Original seed vocabulary (source of truth for migration)
    └── svenska.db        # SQLite database (git-ignored; generated on first run)
```

## Data model

Everything lives in one `entries` table (see `db.py`):

| Column      | Meaning                                                              |
|-------------|-----------------------------------------------------------------------|
| `tab`       | One of the four top-level tabs (see Features)                        |
| `category`  | Sub-grouping within a tab, e.g. "Numbers & Counting"                  |
| `sv`        | Swedish word/phrase                                                   |
| `pos`       | Part of speech                                                        |
| `en`        | English translation                                                   |
| `note`      | Extra forms (definite/plural/tense, etc.)                             |
| `ex`        | Example sentence, shown as a copyable code block                      |
| `fn`        | V2 inversion function group (`position-1` / `contrast` / `subordinating` / `modal`), only set on V2 anchor entries |
| `is_custom` | `1` for entries you added yourself, `0` for seed data                 |

On first run, `app.py` calls `seed.seed_database()` if the `entries` table is
empty. It migrates `words/svenska.csv` into the new tab/category structure
and adds hand-written content (V2 anchors, Workplace & Tech vocab) that has
no analog in the original CSV. Subsequent runs skip seeding and use whatever
is already in `svenska.db`, so custom entries persist across restarts.

## How to run it

### Option A — Docker Compose (recommended)

```bash
docker compose up -d --build
```

Open **http://localhost:8501**. The `words/` folder is bind-mounted into the
container, so the database persists on your host across restarts.

Stop it with:

```bash
docker compose down
```

### Option B — Local Python

Requires Python 3.9+ (a recent 3.x is recommended; developed against 3.12).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open **http://localhost:8501**.

## Features

### Filtering & search
- **Multi-field live search** — matches across Swedish, English, category,
  notes, and example sentences.
- **Tab filter** — Workplace & Tech / Social & Small Talk / Home & Daily
  Life / Grammar & V2 Anchors.
- **Category filter** — scoped to whichever tab is currently selected.
- **Part-of-speech filter**.
- **V2 Inversion toggle** — isolates just the sentence-starter anchors,
  grouped by function (position-1, contrast, subordinating, modal).
  Automatically switches on when you land on the Grammar & V2 Anchors tab
  (since that tab otherwise mixes anchors with plain grammar vocab); you can
  flip it off manually to see the rest of that tab.
- Results are grouped under category headings as you browse, so it's easy to
  see where you are in the word list.

### Practice
- **Improv Weave** — pulls a random 3–5 entries from across all tabs for a
  spontaneous mini-monologue drill. The set stays in place until you hit
  "Generate weave" again.
- **Copy-to-clipboard** on example sentences (via Streamlit's built-in code
  block copy icon) — handy for pasting into chat practice or flashcards.

### Data
- SQLite backend, single `entries` table, as described above.
- **Add Entry** form writes directly into the same table, flagged
  `is_custom=1` so your own additions stay distinguishable (🆕 badge) from
  the seed set.

### Interface
- **Dark mode** via Streamlit's native theme setting (top-right menu → Settings
  → Theme) — no custom toggle needed.
- **Responsive single-column layout** (`layout="centered"`), works narrow or
  wide.

## Regenerating the seed data

To force a full reseed (e.g. after editing `seed.py`), stop the app and
delete the database file, then start again:

```bash
rm words/svenska.db
docker compose up -d --build   # or: streamlit run app.py
```

This re-migrates `words/svenska.csv` and re-inserts the hand-written content
from `seed.py`. Any custom entries you'd added are lost when you do this, since
they only ever lived in `svenska.db`.
