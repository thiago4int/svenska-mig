import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "words" / "svenska.db"

# The three sections a topic can belong to. They answer "why am I looking at
# this?" — a property of the topic, never of a word.
SECTIONS = ["Topics & situations", "Grammar & reference", "Conversation toolkit"]

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
    fn TEXT,
    is_custom INTEGER NOT NULL DEFAULT 0,
    mistake_count INTEGER NOT NULL DEFAULT 0
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

ADDED_COLUMNS = {
    "mistake_count": "INTEGER NOT NULL DEFAULT 0",
    "ex_en": "TEXT",
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


def _migrate(conn):
    _migrate_tab_to_section(conn)
    _migrate_category_to_topics(conn)
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


def insert_entry(conn, topics, sv, pos, en, note, ex, ex_en, fn, is_custom=0, mistake_count=0):
    """Insert one entry and link it to every topic it belongs to."""
    cursor = conn.execute(
        """INSERT INTO entries (sv, pos, word_class, en, note, ex, ex_en, fn, is_custom, mistake_count)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (sv, pos, word_class_for(pos), en, note, ex, ex_en, fn, int(is_custom), int(mistake_count)),
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


def fetch_entries(conn, topics=None, word_classes=None, search=None):
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

    if search:
        like = f"%{search}%"
        query += (
            " AND (e.sv LIKE ? OR e.en LIKE ? OR e.note LIKE ?"
            " OR e.ex LIKE ? OR e.ex_en LIKE ?"
            " OR e.id IN (SELECT entry_id FROM entry_topics WHERE topic LIKE ?))"
        )
        params.extend([like] * 6)

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
