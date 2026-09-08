"""Personal state, kept apart from content.

The 600-odd entries are content: generated from `seed.py`, thrown away and
rebuilt whenever the vocabulary changes. What must survive that is small and
personal — which expressions you want at hand, which ones are on the table for
today's lesson, what you keep getting wrong. So it lives in its own file, and
`export_state` / `import_state` let you carry it across a redeploy by hand.

No hosted database and no accounts: a shared table with no owner would mean
anyone who opened the app's URL could read and overwrite your cheat sheet, and
solving that properly costs a login system this app has no use for.

**Rows are keyed on the Swedish text, not on `entries.id`.** Seed rows are
deleted and re-inserted whenever the content changes, and AUTOINCREMENT hands
out fresh ids each time — "Alltså" was id 387 before a reseed and 991 after.
State keyed on the id would silently reattach itself to different words. The
Swedish string is stable. Eight strings appear on two entries each (Att, Där,
Idag, Igår, Nu, När, Om, Sedan — a vocabulary entry plus a V2 anchor); they
share one state row, which is what you want: favouriting "Nu" favourites "Nu".
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

STATE_DB_PATH = Path(__file__).parent / "words" / "state.db"

# One row per expression. Deliberately small — every column here is a fact
# about you, not about Swedish.
FIELDS = ("favorite", "session_selected", "mistake_count", "uses", "last_used")

SCHEMA = """
CREATE TABLE IF NOT EXISTS entry_state (
    sv TEXT PRIMARY KEY,
    favorite INTEGER NOT NULL DEFAULT 0,
    session_selected INTEGER NOT NULL DEFAULT 0,
    mistake_count INTEGER NOT NULL DEFAULT 0,
    uses INTEGER NOT NULL DEFAULT 0,
    last_used TEXT
);
"""


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class State:
    def __init__(self, path=STATE_DB_PATH):
        self.path = Path(path)
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    # --- reading ---

    def all(self):
        """{sv: {favorite, session_selected, mistake_count, uses, last_used}}."""
        rows = self.conn.execute("SELECT * FROM entry_state").fetchall()
        return {row["sv"]: dict(row) for row in rows}

    def is_empty(self):
        return self.conn.execute("SELECT COUNT(*) FROM entry_state").fetchone()[0] == 0

    # --- writing ---

    def _update(self, sv, assignments, params=()):
        self.conn.execute("INSERT OR IGNORE INTO entry_state (sv) VALUES (?)", (sv,))
        self.conn.execute(
            f"UPDATE entry_state SET {', '.join(assignments)} WHERE sv = ?", (*params, sv)
        )
        self.conn.commit()

    def set_favorite(self, sv, favorite):
        self._update(sv, ["favorite = ?"], (int(bool(favorite)),))

    def set_session(self, sv, selected):
        self._update(sv, ["session_selected = ?"], (int(bool(selected)),))

    def clear_session(self):
        self.conn.execute("UPDATE entry_state SET session_selected = 0")
        self.conn.commit()

    def record_use(self, sv):
        """You reached for this one. This is what orders the home screen."""
        self._update(sv, ["uses = uses + 1", "last_used = ?"], (_now(),))

    def record_mistake(self, sv):
        self._update(sv, ["mistake_count = mistake_count + 1", "last_used = ?"], (_now(),))

    def record_success(self, sv):
        """Got it right: the miss counter comes back down, never below zero."""
        self._update(
            sv,
            ["mistake_count = MAX(mistake_count - 1, 0)", "uses = uses + 1", "last_used = ?"],
            (_now(),),
        )

    def prime_favorites(self, svs):
        """First run only: adopt the curated starter set as your favourites."""
        if not self.is_empty():
            return 0
        for sv in svs:
            self.set_favorite(sv, True)
        return len(svs)

    # --- carrying it across a redeploy ---

    def export_state(self):
        """Everything personal, as JSON bytes small enough to keep anywhere."""
        payload = {
            "version": 1,
            "exported_at": _now(),
            "entries": {sv: {f: row[f] for f in FIELDS} for sv, row in self.all().items()},
        }
        return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")

    def import_state(self, raw):
        """Merge an export back in. Returns how many expressions were restored.

        Merges rather than replaces: restoring an old backup should never
        silently drop what you have marked since.
        """
        payload = json.loads(raw.decode("utf-8") if isinstance(raw, bytes) else raw)
        entries = payload.get("entries")
        if not isinstance(entries, dict):
            raise ValueError("This doesn't look like a Svenska backup file.")

        restored = 0
        for sv, row in entries.items():
            if not isinstance(row, dict):
                continue
            self._update(
                sv,
                [
                    "favorite = ?",
                    "session_selected = ?",
                    "mistake_count = ?",
                    "uses = ?",
                    "last_used = COALESCE(?, last_used)",
                ],
                (
                    int(bool(row.get("favorite"))),
                    int(bool(row.get("session_selected"))),
                    int(row.get("mistake_count") or 0),
                    int(row.get("uses") or 0),
                    row.get("last_used"),
                ),
            )
            restored += 1
        return restored


def open_state(path=STATE_DB_PATH):
    return State(path)
