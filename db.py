import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "words" / "svenska.db"

# The three groupings a topic can belong to. The split that matters mid-
# conversation is semantic vs communicative: "Food & Drink" is a subject you
# talk *about*, "Clarification" is a job you need done *now*. Reference is the
# grammar you look up rather than reach for.
SECTIONS = ["Subjects", "Functions", "Reference"]

LEGACY_SECTIONS = {
    "Topics & situations": "Subjects",
    "Conversation toolkit": "Functions",
    "Grammar & reference": "Reference",
}

# The second axis. `pos` keeps the detail that matters when you use a word
# (en/ett gender, which preposition a verb takes); `word_class` is the coarse
# grouping you browse by, so "show me every verb" is one click.
WORD_CLASSES = [
    "Verb",
    "Noun",
    "Adjective",
    "Adverb",
    "Phrase",
    "Preposition",
    "Pronoun",
    "Conjunction",
    "Numeral",
    "Interjection",
    "Article",
    "Pattern",
]

POS_TO_WORD_CLASS = {
    "Noun (en)": "Noun",
    "Noun (ett)": "Noun",
    "Noun (plural)": "Noun",
    "Noun (en, pl.)": "Noun",
    "Noun (en) / Verb": "Noun",
    "Proper noun": "Noun",
    "Adjective/Noun": "Noun",
    "Verb": "Verb",
    "Verb phrase": "Verb",
    "Verb (modal)": "Verb",
    "Verb + preposition": "Verb",
    "Adjective": "Adjective",
    "Adjective (ordinal)": "Adjective",
    "Adjective/Adverb": "Adjective",
    "Adverb": "Adverb",
    "Modal adverb": "Adverb",
    "Adverbial phrase": "Adverb",
    "Adverb pair": "Adverb",
    "Phrase": "Phrase",
    "Comparative phrase": "Phrase",
    "Comparative construction": "Phrase",
    "Correlative construction": "Phrase",
    "Time expression": "Phrase",
    "Tag question": "Phrase",
    "Preposition": "Preposition",
    "Preposition/Conjunction": "Preposition",
    "Pronoun": "Pronoun",
    "Conjunction": "Conjunction",
    "Subjunction": "Conjunction",
    "Numeral": "Numeral",
    "Interjection": "Interjection",
    "Particle": "Interjection",
    "Article": "Article",
    "Word-order rule": "Pattern",
    "Pattern": "Pattern",
}

# Legacy value maps, kept only so an existing database can be migrated.
LEGACY_TAB_TO_SECTION = {
    "Workplace & Tech": "Topics & situations",
    "Social & Small Talk": "Topics & situations",
    "Home & Daily Life": "Topics & situations",
    "Grammar & V2 Anchors": "Grammar & reference",
    "Questions & Prepositions": "Grammar & reference",
    "Tutor Toolkit": "Conversation toolkit",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sv TEXT NOT NULL,
    pos TEXT,
    word_class TEXT NOT NULL,
    en TEXT NOT NULL,
    note TEXT,
    ex TEXT,
    ex_en TEXT,
    antonym TEXT,
    pinned INTEGER NOT NULL DEFAULT 0,   -- seed's curated starter set only
    fn TEXT,
    is_custom INTEGER NOT NULL DEFAULT 0
);

-- A topic belongs to exactly one section: the primary key makes it impossible
-- for one topic to appear under two headings on the index.
CREATE TABLE IF NOT EXISTS topics (
    topic TEXT PRIMARY KEY,
    section TEXT NOT NULL
);

-- A word can sit in several topics at once: "äter" is core vocabulary and it
-- is also food vocabulary.
CREATE TABLE IF NOT EXISTS entry_topics (
    entry_id INTEGER NOT NULL REFERENCES entries(id) ON DELETE CASCADE,
    topic TEXT NOT NULL,
    PRIMARY KEY (entry_id, topic)
);

CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

# How often you miss a word is a fact about you, so it lives in state.py, not
# here. Older databases keep a `mistake_count` column; nothing reads it.
ADDED_COLUMNS = {
    "ex_en": "TEXT",
    "antonym": "TEXT",
    "pinned": "INTEGER NOT NULL DEFAULT 0",
}


def word_class_for(pos):
    """Coarse word class for a part-of-speech string; 'Other' when unrecognised."""
    return POS_TO_WORD_CLASS.get((pos or "").strip(), "Other")


def _columns(conn):
    return {row["name"] for row in conn.execute("PRAGMA table_info(entries)")}


def _drop_column(conn, column):
    try:
        conn.execute(f"ALTER TABLE entries DROP COLUMN {column}")
    except sqlite3.OperationalError:
        # SQLite < 3.35 can't drop a column. Leaving it costs nothing — no
        # query reads it any more.
        pass


def _migrate_tab_to_section(conn):
    """Oldest shape: a `tab` column instead of `section`."""
    columns = _columns(conn)
    if "section" in columns or "tab" not in columns:
        return

    conn.execute("ALTER TABLE entries ADD COLUMN section TEXT")
    for tab, section in LEGACY_TAB_TO_SECTION.items():
        conn.execute("UPDATE entries SET section = ? WHERE tab = ?", (section, tab))
    conn.execute(
        "UPDATE entries SET section = ? WHERE section IS NULL OR section = ''",
        (SECTIONS[0],),
    )
    _drop_column(conn, "tab")
    conn.commit()


def _migrate_category_to_topics(conn):
    """Move the single `category`/`section` pair onto the topics tables."""
    columns = _columns(conn)
    if "category" not in columns:
        return

    conn.execute(
        "INSERT OR IGNORE INTO topics (topic, section) "
        "SELECT DISTINCT category, section FROM entries "
        "WHERE category IS NOT NULL AND category != ''"
    )
    conn.execute(
        "INSERT OR IGNORE INTO entry_topics (entry_id, topic) "
        "SELECT id, category FROM entries WHERE category IS NOT NULL AND category != ''"
    )

    if "word_class" not in columns:
        conn.execute("ALTER TABLE entries ADD COLUMN word_class TEXT")
    for pos in [row["pos"] for row in conn.execute("SELECT DISTINCT pos FROM entries")]:
        conn.execute(
            "UPDATE entries SET word_class = ? WHERE pos IS ?", (word_class_for(pos), pos)
        )

    _drop_column(conn, "category")
    _drop_column(conn, "section")
    conn.commit()


def _migrate_section_values(conn):
    """Rename the old section values onto Subjects / Functions / Reference."""
    for old, new in LEGACY_SECTIONS.items():
        conn.execute("UPDATE topics SET section = ? WHERE section = ?", (new, old))
    conn.commit()


def _migrate(conn):
    _migrate_tab_to_section(conn)
    _migrate_category_to_topics(conn)
    _migrate_section_values(conn)
    columns = _columns(conn)
    for column, definition in ADDED_COLUMNS.items():
        if column not in columns:
            conn.execute(f"ALTER TABLE entries ADD COLUMN {column} {definition}")
    conn.commit()


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    conn.commit()
    _migrate(conn)
    return conn


def is_empty(conn):
    return conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0] == 0


def get_meta(conn, key):
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None


def set_meta(conn, key, value):
    conn.execute(
        "INSERT INTO meta (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, str(value)),
    )
    conn.commit()


def delete_seed_entries(conn):
    """Drop seed-provided rows, keeping anything added through Add Entry."""
    conn.execute("DELETE FROM entry_topics WHERE entry_id IN (SELECT id FROM entries WHERE is_custom = 0)")
    conn.execute("DELETE FROM entries WHERE is_custom = 0")
    # Topics nothing points at any more (a retired bucket, say) go too.
    conn.execute(
        "DELETE FROM topics WHERE topic NOT IN (SELECT DISTINCT topic FROM entry_topics)"
    )
    conn.commit()


def register_topic(conn, topic, section):
    conn.execute(
        "INSERT INTO topics (topic, section) VALUES (?, ?) "
        "ON CONFLICT(topic) DO UPDATE SET section = excluded.section",
        (topic, section),
    )
    conn.commit()


def insert_entry(conn, topics, sv, pos, en, note, ex, ex_en, fn, antonym=None,
                 pinned=0, is_custom=0):
    """Insert one entry and link it to every topic it belongs to.

    `topics` may be empty: an entry captured mid-conversation lands untriaged
    and is filed later.
    """
    cursor = conn.execute(
        """INSERT INTO entries
             (sv, pos, word_class, en, note, ex, ex_en, antonym, fn, pinned, is_custom)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (sv, pos, word_class_for(pos), en, note, ex, ex_en, antonym, fn, int(pinned),
         int(is_custom)),
    )
    conn.executemany(
        "INSERT OR IGNORE INTO entry_topics (entry_id, topic) VALUES (?, ?)",
        [(cursor.lastrowid, t) for t in topics],
    )
    conn.commit()
    return cursor.lastrowid


def _attach_topics(conn, rows):
    """Turn entry rows into dicts carrying every topic they belong to."""
    entries = [dict(row) for row in rows]
    if not entries:
        return entries

    placeholders = ",".join("?" for _ in entries)
    links = conn.execute(
        f"SELECT entry_id, topic FROM entry_topics WHERE entry_id IN ({placeholders}) "
        "ORDER BY topic",
        [e["id"] for e in entries],
    ).fetchall()

    by_entry = {}
    for link in links:
        by_entry.setdefault(link["entry_id"], []).append(link["topic"])
    for entry in entries:
        entry["topics"] = by_entry.get(entry["id"], [])
    return entries


def fetch_entries(conn, topics=None, word_classes=None):
    query = "SELECT DISTINCT e.* FROM entries e"
    params = []

    if topics:
        query += " JOIN entry_topics et ON et.entry_id = e.id"

    query += " WHERE 1=1"

    if topics:
        placeholders = ",".join("?" for _ in topics)
        query += f" AND et.topic IN ({placeholders})"
        params.extend(topics)

    if word_classes:
        placeholders = ",".join("?" for _ in word_classes)
        query += f" AND e.word_class IN ({placeholders})"
        params.extend(word_classes)

    query += " ORDER BY e.sv"
    return _attach_topics(conn, conn.execute(query, params).fetchall())


def fetch_entries_by_id(conn, ids):
    if not ids:
        return []
    placeholders = ",".join("?" for _ in ids)
    rows = conn.execute(f"SELECT * FROM entries WHERE id IN ({placeholders})", list(ids)).fetchall()
    return _attach_topics(conn, rows)


def topic_counts(conn):
    """Every topic with its section and entry count, for the topic index."""
    return conn.execute(
        "SELECT t.topic, t.section, COUNT(et.entry_id) AS n "
        "FROM topics t LEFT JOIN entry_topics et ON et.topic = t.topic "
        "GROUP BY t.topic, t.section HAVING n > 0 ORDER BY t.topic"
    ).fetchall()


def word_class_counts(conn):
    """Every word class with its entry count, for the other way into the index."""
    return conn.execute(
        "SELECT word_class, COUNT(*) AS n FROM entries GROUP BY word_class ORDER BY n DESC"
    ).fetchall()


# --- search -----------------------------------------------------------------

# Swedish folds so a keyboard-lazy query still finds the word: "halsa" should
# reach "hälsa", "oppen" should reach "öppen".
_FOLD = str.maketrans({
    "å": "a", "ä": "a", "ö": "o", "é": "e", "è": "e", "ü": "u", "á": "a", "à": "a",
    "Å": "a", "Ä": "a", "Ö": "o", "É": "e", "È": "e", "Ü": "u", "Á": "a", "À": "a",
})


def fold(text):
    """Lowercase and strip the accents that make a query miss."""
    return (text or "").lower().translate(_FOLD)


def _haystack(entry):
    parts = [entry["sv"], entry["en"], entry["note"], entry["ex"], entry["ex_en"],
             entry["antonym"], entry["pos"], entry["word_class"]]
    parts.extend(entry["topics"])
    return fold(" ".join(p for p in parts if p))


def search_entries(conn, query):
    """Every entry matching all terms, best match first.

    Ranked so the word you typed comes before a word that merely mentions it:
    a Swedish prefix beats a Swedish substring beats an English match beats a
    hit somewhere in the notes or examples.
    """
    terms = [t for t in fold(query).split() if t]
    if not terms:
        return []

    results = []
    for entry in fetch_entries(conn):
        haystack = _haystack(entry)
        if not all(term in haystack for term in terms):
            continue

        sv, en = fold(entry["sv"]), fold(entry["en"])
        first = terms[0]
        if sv.startswith(first):
            rank = 0
        elif first in sv:
            rank = 1
        elif en.startswith(first):
            rank = 2
        elif first in en:
            rank = 3
        else:
            rank = 4
        results.append((rank, len(entry["sv"]), entry["sv"], entry))

    results.sort(key=lambda r: r[:3])
    return [entry for *_rest, entry in results]


def fetch_untriaged(conn):
    """Entries captured without a topic — the Inbox."""
    rows = conn.execute(
        "SELECT * FROM entries WHERE id NOT IN (SELECT entry_id FROM entry_topics) "
        "ORDER BY id DESC"
    ).fetchall()
    return _attach_topics(conn, rows)


def set_entry_topics(conn, entry_id, topics):
    """Replace an entry's topics — used to file something out of the Inbox."""
    conn.execute("DELETE FROM entry_topics WHERE entry_id = ?", (entry_id,))
    conn.executemany(
        "INSERT OR IGNORE INTO entry_topics (entry_id, topic) VALUES (?, ?)",
        [(entry_id, t) for t in topics],
    )
    conn.commit()
