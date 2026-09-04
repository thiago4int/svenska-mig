import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "words" / "svenska.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tab TEXT NOT NULL,
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


def _migrate(conn):
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(entries)")}
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


def insert_entry(conn, tab, category, sv, pos, en, note, ex, ex_en, fn, is_custom=0, mistake_count=0):
    conn.execute(
        """INSERT INTO entries (tab, category, sv, pos, en, note, ex, ex_en, fn, is_custom, mistake_count)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (tab, category, sv, pos, en, note, ex, ex_en, fn, int(is_custom), int(mistake_count)),
    )
    conn.commit()


def fetch_entries(conn, tab=None, categories=None, pos_list=None, search=None, only_anchors=False):
    query = "SELECT * FROM entries WHERE 1=1"
    params = []

    if tab and tab != "All tabs":
        query += " AND tab = ?"
        params.append(tab)

    if categories:
        placeholders = ",".join("?" for _ in categories)
        query += f" AND category IN ({placeholders})"
        params.extend(categories)

    if pos_list:
        placeholders = ",".join("?" for _ in pos_list)
        query += f" AND pos IN ({placeholders})"
        params.extend(pos_list)

    if only_anchors:
        query += " AND fn IS NOT NULL AND fn != ''"

    if search:
        like = f"%{search}%"
        query += (
            " AND (sv LIKE ? OR en LIKE ? OR category LIKE ? OR note LIKE ?"
            " OR ex LIKE ? OR ex_en LIKE ?)"
        )
        params.extend([like] * 6)

    query += " ORDER BY tab, category, sv"
    return conn.execute(query, params).fetchall()


def distinct_values(conn, column, tab=None):
    assert column in {"category", "pos", "fn"}
    query = f"SELECT DISTINCT {column} FROM entries WHERE {column} IS NOT NULL AND {column} != ''"
    params = []
    if tab and tab != "All tabs":
        query += " AND tab = ?"
        params.append(tab)
    query += f" ORDER BY {column}"
    return [row[0] for row in conn.execute(query, params).fetchall()]
