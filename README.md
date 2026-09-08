# Svenska 🇸🇪

A personal Swedish **retrieval layer**, not a catalogue. The question it
answers is "what do I need to say right now?", asked mid-conversation with
seconds to spare — so the home is a pinned cheat sheet and a search box that
forgives missing accents, and the taxonomy lives one click down under Explore.

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
├── streamlit_app.py     # Streamlit UI: two-axis index + Improv Weave / Reverse Drill / Add Entry
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

Words live in `entries` (see `db.py`):

| Column      | Meaning                                                              |
|-------------|-----------------------------------------------------------------------|
| `sv`        | Swedish word/phrase                                                   |
| `pos`       | Part of speech, in full: `Noun (en)`, `Verb + preposition`, …          |
| `word_class`| Coarse class derived from `pos`: Verb, Noun, Adjective, Adverb, Phrase, … The axis you browse by |
| `en`        | English translation                                                   |
| `note`      | Extra forms (definite/plural/tense, etc.)                             |
| `ex`        | Example sentence in Swedish, shown as a copyable code block           |
| `ex_en`     | English translation of the example sentence                           |
| `antonym`   | The Swedish word meaning the reverse, if there is one. Reciprocal — validation rejects a pair that points only one way |
| `pinned`    | `1` if it sits on the cheat sheet. Hand-picked starter set; you add and drop from the UI |
| `fn`        | V2 inversion function group (`position-1` / `contrast` / `subordinating` / `modal`), only set on V2 anchor entries |
| `is_custom` | `1` for entries you added yourself, `0` for seed data                 |
| `mistake_count` | Times you've flagged this entry as "got it wrong" via Add Entry (0 by default; shown as a ⚠️ badge when > 0) |

Two more tables carry the topic axis:

| Table          | Meaning                                                          |
|----------------|------------------------------------------------------------------|
| `topics`       | `topic` → `section`. The primary key makes it impossible for one topic to sit under two headings |
| `entry_topics` | `entry_id` → `topic`, many-to-many: **a word can belong to several topics.** `äter` is in Core Words *and* Food & Drink. An entry with *no* row here is in the Inbox |

**Every seed entry carries an English translation, a Swedish example sentence,
and an English translation of that example.** `seed.validate_rows()` enforces
this before anything is inserted — it also rejects a word repeated inside one
topic, a topic with no section, and any use of a retired bucket, so a seed
entry can never ship half-filled.

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

Seeding migrates `words/svenska.csv` into the section/topic structure and adds
hand-written content (V2 anchors, word-order rules and modals, the whole
questions and prepositions topics, workplace vocab, tutor-toolkit phrases)
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

### The home: cheat sheet and search

The first screen is **My Cheat Sheet** — the couple of dozen expressions you
actually reach for — grouped by the *job* each one does (Clarification,
Conversation Fillers, Sentence Patterns) rather than by subject. Entries render
compactly, one scannable line each: this surface is read in seconds, not
studied. Pin from any entry with ☆; drop from the "Edit cheat sheet" control.

Above it sits a **global search** that runs across everything with nothing
selected first. It folds accents and case, so `halsa` finds *hälsa*, `oppen`
finds *öppen* and `alltsa` finds *alltså* — you will not be typing å/ä/ö on a
phone mid-conversation. All terms must match, and results are ranked so the
word you typed beats a word that merely mentions it: Swedish prefix, then
Swedish substring, then English, then a hit in the notes or examples.

The starter cheat sheet is hand-picked because on day one there is no usage
data to rank by. `mistake_count` exists but nothing yet increments it — a
practice feedback loop, and states derived from it, are deliberately left for
a later pass rather than shipped inert.

### Capture without friction

Add Entry requires **Swedish and English only**. Everything else — topics, part
of speech, examples, opposite — is optional and folded into an expander. Save
with no topic and the entry lands in the **Inbox** on the home screen, where it
can be filed later. The point is that catching a correction mid-session should
never cost you a taxonomy decision.

### Explore: the taxonomy, one click down

Words are filed along **two independent axes**:

| Axis | Question it answers | Examples |
|------|---------------------|----------|
| **topic** | What is it *about*, or what does it *do*? | Food & Drink, Conversation Fillers, Sentence Patterns |
| **word class** | What *kind* of word is it? | Verb, Noun, Adjective, Phrase |

One field used to do both jobs, which is where `More Verbs`, `Everyday Verbs`,
`More Adjectives`, `Colors & Adjectives` and `Tech Verbs` came from — a word
class wearing a topic's clothes. All five are retired.

Explore opens an index you can enter from either end: **by topic** (open one and
its entries group by word class) or **by word class** (every verb in the app,
grouped by topic).

Topics are grouped by the distinction that matters mid-conversation:

- **Subjects** — things to talk about (Food & Drink, Travel & Transport, Work).
- **Functions** — things to say and how to say them (Conversation Fillers,
  Sentence Patterns, Clarification, Negation, Greetings, Opinions).
- **Reference** — things to look up (prepositions, question words, word order).

That split is the point: a semantic category and a communicative function are
different questions, and several topics that read as subjects — Greetings,
Invitations, Opinions, Everyday Expressions — are really functions and now sit
with the others.

**Conversation Fillers** (*alltså, typ, ju, väl, liksom, jaha, förresten*) are
the words that make speech sound like speech; exactly one of them existed
before. **Sentence Patterns** are frames with a slot (*jag skulle vilja …, det
beror på …, är det okej om jag …?*) — the productive half of speaking, since one
frame carries whatever vocabulary you drop into it. Any entry containing `…` is
tagged into Sentence Patterns automatically wherever it was written, which
recovered 22 that were scattered across nine subject topics.

A word can sit in **several topics at once**: `äter` is core vocabulary *and*
food vocabulary; `går` is core vocabulary *and* directions.

**Core Words** is where the domain-neutral backbone lives — *vara, ha, göra, gå,
komma, se, höra*, plus the general adjectives. These are not a subject and never
were.

**Negation** and **Opposites** fill what the vocabulary was thinnest on.
Negation covers *inte / aldrig / ingenting / ingenstans / varken … eller*, the
everyday negative phrases (*det är inte lätt*, *jag gillar inte det här*), the
formal `ej` on signs, the verb `slippa`, and **`jo`** — the second word for
"yes" that contradicts a negative question. Opposites holds 32 reciprocal
pairs, shown on the card as `↔ Motsats`.

- **Topics and word classes are URL-addressable** — `?topic=Core+Words`,
  `?word_class=Verb`. Streamlit rewrites the URL in place rather than pushing
  history, so browser back does not step through them; use "← All topics".
- **Recent topics** appear at the top of the index (per browser session).
- The **V2 Inversion Anchors** topic groups by what triggers the inversion
  rather than by word class.

### Practice
- **Improv Weave** — pulls a random 3–5 entries from across all topics for a
  spontaneous mini-monologue drill. The set stays in place until you hit
  "Generate weave" again.
- **Reverse Drill** — shows the English side first (optionally narrowed to
  one or more topics); say the Swedish aloud, then hit Reveal to check yourself and
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
  `GRAMMAR_EXTRA`, `V2_ANCHORS`, `COMPARISONS`, `TUTOR_TOOLKIT`), each attached
  to a section in `seed_rows()`. Each row is
  `(category, sv, pos, en, note, ex, ex_en)` — `V2_ANCHORS` also carries its
  `fn` group, and `COMPARISONS` has no category column since it's a single
  category.

Then **bump `SEED_VERSION`** in `seed.py` so running instances reseed on their
next start. Check your work without launching the app:

```bash
python3 -c "from seed import seed_rows, validate_rows; r = seed_rows(); validate_rows(r); print(len(r), 'rows OK')"
```

A missing example, a missing translation, a duplicated `(topic, sv)`, an
unknown section, or a topic split across two sections raises `ValueError` with
every offending entry listed.

## Regenerating the seed data

Bumping `SEED_VERSION` is normally enough — the app reseeds itself and keeps
your custom entries. To wipe *everything*, custom entries included, stop the
app and delete the database file:

```bash
rm words/svenska.db
docker compose up -d --build   # or: streamlit run streamlit_app.py
```
