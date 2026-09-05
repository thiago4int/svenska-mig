import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "words" / "svenska.db"

# The three sections a topic can belong to. They answer "why am I looking at
# this?" — the only grouping that ever earned its place. Each is a property of
# the *topic*, never of an individual word.
SECTIONS = ["Topics & situations", "Grammar & reference", "Conversation toolkit"]

# The six "tabs" this app used to have collapse into those three. Kept so an
# existing database can be migrated; nothing in the UI uses it.
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
    section TEXT NOT NULL,
    category TEXT NOT NULL,
    sv TEXT NOT NULL,
    pos TEXT,
    en TEXT NOT NULL,
    note TEXT,
    ex TEXT,
    ex_en TEXT,
    fn TEXT,
    is_custom INTEGER NOT NULL DEFAULT 0,
    mistake_count INTEGER NOT NULL DEFAULT 0
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


def _columns(conn):
    return {row["name"] for row in conn.execute("PRAGMA table_info(entries)")}


def _migrate_tab_to_section(conn):
    """Replace the old `tab` column with `section`, carrying values across."""
    columns = _columns(conn)
    if "section" in columns or "tab" not in columns:
        return

    conn.execute("ALTER TABLE entries ADD COLUMN section TEXT")
    for tab, section in LEGACY_TAB_TO_SECTION.items():
        conn.execute("UPDATE entries SET section = ? WHERE tab = ?", (section, tab))
    # Anything added by hand under a tab name we don't recognise still needs a
    # home; the topics section is the sane default.
    conn.execute(
        "UPDATE entries SET section = ? WHERE section IS NULL OR section = ''",
        (SECTIONS[0],),
    )
    try:
        conn.execute("ALTER TABLE entries DROP COLUMN tab")
    except sqlite3.OperationalError:
        # SQLite < 3.35 can't drop a column. Leaving it costs nothing — no
        # query reads it any more.
        pass
    conn.commit()


def _migrate(conn):
    _migrate_tab_to_section(conn)
    columns = _columns(conn)
    for column, definition in ADDED_COLUMNS.items():
        if column not in columns:
            conn.execute(f"ALTER TABLE entries ADD COLUMN {column} {definition}")
    conn.commit()


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
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
    conn.execute("DELETE FROM entries WHERE is_custom = 0")
    conn.commit()


def insert_entry(conn, section, category, sv, pos, en, note, ex, ex_en, fn, is_custom=0, mistake_count=0):
    conn.execute(
        """INSERT INTO entries (section, category, sv, pos, en, note, ex, ex_en, fn, is_custom, mistake_count)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (section, category, sv, pos, en, note, ex, ex_en, fn, int(is_custom), int(mistake_count)),
    )
    conn.commit()


def fetch_entries(conn, categories=None, pos_list=None, search=None):
    query = "SELECT * FROM entries WHERE 1=1"
    params = []

    if categories:
        placeholders = ",".join("?" for _ in categories)
        query += f" AND category IN ({placeholders})"
        params.extend(categories)

    if pos_list:
        placeholders = ",".join("?" for _ in pos_list)
        query += f" AND pos IN ({placeholders})"
        params.extend(pos_list)

    if search:
        like = f"%{search}%"
        query += (
            " AND (sv LIKE ? OR en LIKE ? OR category LIKE ? OR note LIKE ?"
            " OR ex LIKE ? OR ex_en LIKE ?)"
        )
        params.extend([like] * 6)

    query += " ORDER BY category, sv"
    return conn.execute(query, params).fetchall()


def topic_counts(conn):
    """Every topic with its section and entry count, for the topic index."""
    return conn.execute(
        "SELECT section, category, COUNT(*) AS n FROM entries "
        "GROUP BY section, category ORDER BY category"
    ).fetchall()
