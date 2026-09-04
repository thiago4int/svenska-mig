# Svenska 🇸🇪

A personal Swedish vocabulary practice app: search and filter a growing word
set, drill sentence starters that trigger V2 word-order inversion, look up the
full question-word and preposition inventory, improvise mini-monologues from
randomly woven vocabulary, and run active-recall drills against yourself.

Every entry carries an English translation, a Swedish example sentence, and a
translation of that example — enforced by seed validation, not by convention.

## Tech stack

- **[Streamlit](https://streamlit.io/)** — the entire UI (Python, no separate
  frontend build).
- **SQLite** — single-file database (`words/svenska.db`), accessed directly
  via the stdlib `sqlite3` module (no ORM).
- **Docker Compose** — optional containerized run.

## Folder structure

```
.
├── streamlit_app.py     # Streamlit UI: Browse / Improv Weave / Reverse Drill / Add Entry tabs
├── db.py                # SQLite connection, schema, query helpers
├── seed.py              # One-time seed: migrates words/svenska.csv + hand-written content
├── requirements.txt     # Python dependencies (Streamlit)
├── .streamlit/
│   └── config.toml      # Shows real tracebacks instead of redacted errors
├── Dockerfile            # Container image for the app
├── docker-compose.yml   # Runs the app on :8501, bind-mounts words/
├── .dockerignore
├── .gitignore
└── words/
    ├── svenska.csv       # Base seed vocabulary incl. example sentences (source of truth for migration)
    └── svenska.db        # SQLite database (git-ignored; generated on first run)
```

`svenska.csv` columns: `#`, `Category`, `Word Type`, `Swedish`, `English`,
`Other forms (tense / plural / etc.)`, `Example`, `Example (English)`. The
last two are required — adding a row without them fails seed validation.

## Data model

Everything lives in one `entries` table (see `db.py`):

| Column      | Meaning                                                              |
|-------------|-----------------------------------------------------------------------|
| `tab`       | One of the six top-level tabs (see Features)                         |
| `category`  | Sub-grouping within a tab, e.g. "Numbers & Counting"                  |
| `sv`        | Swedish word/phrase                                                   |
| `pos`       | Part of speech                                                        |
| `en`        | English translation                                                   |
| `note`      | Extra forms (definite/plural/tense, etc.)                             |
| `ex`        | Example sentence in Swedish, shown as a copyable code block           |
| `ex_en`     | English translation of the example sentence                           |
| `fn`        | V2 inversion function group (`position-1` / `contrast` / `subordinating` / `modal`), only set on V2 anchor entries |
| `is_custom` | `1` for entries you added yourself, `0` for seed data                 |
| `mistake_count` | Times you've flagged this entry as "got it wrong" via Add Entry (0 by default; shown as a ⚠️ badge when > 0) |

**Every seed entry carries an English translation, a Swedish example sentence,
and an English translation of that example.** `seed.validate_rows()` enforces
this before anything is inserted — it also rejects duplicate
`(tab, category, sv)` rows — so a seed entry can never ship half-filled.

A second table, `meta`, holds a single `seed_version` key used for reseeding
(below).

### Seeding and reseeding

On startup `streamlit_app.py` calls `seed.ensure_seeded()`, which:

1. Seeds an empty database from scratch, or
2. **Reseeds** when `SEED_VERSION` in `seed.py` differs from the version
   recorded in the database — the case after a deploy that ships new
   vocabulary.

Reseeding deletes only the rows the seed file owns (`is_custom = 0`) and
re-inserts them, so **entries you added through Add Entry survive a deploy**.
Bump `SEED_VERSION` whenever you change seed content, and the deployed app
picks it up on its next restart with no manual database surgery.

Seeding migrates `words/svenska.csv` into the tab/category structure and adds
hand-written content (V2 anchors, word-order rules and modals, the whole
Questions & Prepositions tab, Workplace & Tech vocab, Tutor Toolkit phrases)
that has no analog in the original CSV.

`db.py` also runs a small migration on every connection (`PRAGMA table_info`
+ `ALTER TABLE` for any missing column), so pulling schema changes doesn't
require deleting an existing database.

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
streamlit run streamlit_app.py
```

Open **http://localhost:8501**.

## Features

### Filtering & search
- **Multi-field live search** — matches across Swedish, English, category,
  notes, and example sentences in both languages.
- **Tab filter** — Workplace & Tech / Social & Small Talk / Home & Daily
  Life / Grammar & V2 Anchors / Questions & Prepositions / Tutor Toolkit.
- **Category filter** — scoped to whichever tab is currently selected.
- **Part-of-speech filter**.
- **V2 Inversion toggle** — isolates just the sentence-starter anchors,
  grouped by function (position-1, contrast, subordinating, modal).
  Automatically switches on when you land on the Grammar & V2 Anchors tab
  (since that tab otherwise mixes anchors with plain grammar vocab); you can
  flip it off manually to see the rest of that tab.
- Results are grouped under category headings as you browse, so it's easy to
  see where you are in the word list.
- The **Questions & Prepositions** tab is the reference half of the app: the
  full question-word inventory (vad / vem / vems / vilken / var / vart /
  varifrån / när / varför / hur and the "hur …" family), the question
  patterns that go with them (yes/no inversion, negated questions, tag
  questions, indirect questions), and prepositions grouped by what they
  actually do — place, time, movement & direction, and everything else —
  plus the verbs that lock to a fixed preposition (`vänta på`, `bero på`,
  `längta efter`, …).
- The **Tutor Toolkit** tab is functional rather than topical: phrases for
  managing a live conversation (Clarification, Repair & Save the
  Conversation, Meta-language, Polite Feedback) rather than vocabulary about
  a subject.

### Practice
- **Improv Weave** — pulls a random 3–5 entries from across all tabs for a
  spontaneous mini-monologue drill. The set stays in place until you hit
  "Generate weave" again.
- **Reverse Drill** — shows the English side first (optionally filtered by
  tab/category); say the Swedish aloud, then hit Reveal to check yourself and
  see the example sentence with its translation. "Next card" pulls a new
  random entry from the filtered pool. Built for active recall rather than
  passive browsing.
- **Copy-to-clipboard** on example sentences (via Streamlit's built-in code
  block copy icon) — handy for pasting into chat practice or flashcards.

### Data
- SQLite backend, single `entries` table, as described above.
- **Add Entry** form writes directly into the same table, flagged
  `is_custom=1` so your own additions stay distinguishable (🆕 badge) from
  the seed set. Includes an "I got this wrong" checkbox for capturing tutor
  corrections on the spot — checking it sets `mistake_count=1` on the new
  entry, which then shows a ⚠️ "Missed N times" badge wherever it's rendered.
  The form takes the example sentence in both Swedish and English, matching
  what the seed data provides.

### Interface
- **Dark mode** via Streamlit's native theme setting (top-right menu → Settings
  → Theme) — no custom toggle needed.
- **Responsive single-column layout** (`layout="centered"`), works narrow or
  wide.

## Troubleshooting a deploy

**`ImportError` on `from seed import ensure_seeded` (or any name imported from
`db`/`seed`) after a push.** The source is fine; the running process isn't.
Streamlit Community Cloud picked up the new `streamlit_app.py` but kept a
pre-change `seed`/`db` in `sys.modules`, so the app is running a mix of old and
new modules. **Reboot the app** — Manage app (lower right) → ⋮ → Reboot app —
which restarts the Python process and re-imports everything. A push that
touches `.streamlit/config.toml` or `requirements.txt` also forces a full
restart.

To tell this apart from a real import bug, check out the deployed commit and
import it directly:

```bash
python3 -c "from seed import ensure_seeded; from db import get_connection; print('imports OK')"
```

If that passes, the repository is consistent and the problem is the running
process, not the code.

`.streamlit/config.toml` sets `showErrorDetails = "full"` so errors appear in
full instead of "the original error message is redacted to prevent data
leaks". Change it to `"stacktrace"` or `"none"` if you ever share the app more
widely.

## Adding vocabulary

Two places, depending on where the entry belongs:

- **`words/svenska.csv`** — base vocabulary. Fill in every column, including
  `Example` and `Example (English)`.
- **`seed.py`** — the themed hand-written lists (`QUESTIONS_PREPOSITIONS`,
  `WORKPLACE_TECH_EXTRA`, `HOME_DAILY_LIFE_EXTRA`, `SOCIAL_SMALL_TALK_EXTRA`,
  `GRAMMAR_EXTRA`, `V2_ANCHORS`, `COMPARISONS`, `TUTOR_TOOLKIT`). Each row is
  `(category, sv, pos, en, note, ex, ex_en)` — `V2_ANCHORS` also carries its
  `fn` group, and `COMPARISONS` has no category column since it's a single
  category.

Then **bump `SEED_VERSION`** in `seed.py` so running instances reseed on their
next start. Check your work without launching the app:

```bash
python3 -c "from seed import seed_rows, validate_rows; r = seed_rows(); validate_rows(r); print(len(r), 'rows OK')"
```

A missing example, a missing translation, or a duplicated
`(tab, category, sv)` raises `ValueError` with every offending entry listed.

## Regenerating the seed data

Bumping `SEED_VERSION` is normally enough — the app reseeds itself and keeps
your custom entries. To wipe *everything*, custom entries included, stop the
app and delete the database file:

```bash
rm words/svenska.db
docker compose up -d --build   # or: streamlit run streamlit_app.py
```
