import json
import random

import streamlit as st

from db import (
    SECTIONS,
    fold,
    WORD_CLASSES,
    fetch_entries,
    fetch_entries_by_id,
    fetch_untriaged,
    get_connection,
    insert_entry,
    register_topic,
    search_entries,
    set_entry_topics,
    topic_counts,
    word_class_counts,
)
from seed import PINNED, ensure_seeded
from state import open_state

# The app is a retrieval layer, not a catalogue: the question it answers is
# "what do I need to say right now?", asked mid-conversation with seconds to
# spare. So the home is the cheat sheet and the search box; the taxonomy is
# real but it lives one click down, under Explore.
#
# Words are filed along two independent axes:
#
#   topic       what it is about  — Food & Drink, Travel & Transport, Work
#   word_class  what kind of word — Verb, Noun, Adjective, Phrase
#
# and topics are grouped by whether they are a subject you talk about or a job
# you need done (Functions), which is the distinction that matters when the
# conversation is already moving.
SECTION_BLURBS = {
    "Subjects": "Things to talk about",
    "Functions": "Things to say, and how to say them",
    "Reference": "Things to look up",
}

FN_LABELS = {
    "position-1": "Position-1 anchors (fronted time/place adverbials)",
    "contrast": "Contrast anchors",
    "subordinating": "Subordinating anchors",
    "modal": "Modal anchors",
}
FN_ORDER = ["position-1", "contrast", "subordinating", "modal"]

ANCHOR_TOPIC = "V2 Inversion Anchors"
BY_TOPIC = "By topic"
BY_WORD_CLASS = "By word class"
INDEX_COLUMNS = 3
MAX_RECENTS = 5

st.set_page_config(page_title="Svenska", page_icon="🇸🇪", layout="centered")


@st.cache_resource
def get_db():
    conn = get_connection()
    ensure_seeded(conn)
    return conn


@st.cache_resource
def get_state():
    """Personal state: favourites, today's session, what you keep missing.

    Kept in its own store because content is disposable and this is not — a
    deploy rebuilds all 604 entries but must not cost you your cheat sheet.
    """
    state = open_state()
    state.prime_favorites(sorted(PINNED))
    return state


conn = get_db()
state = get_state()


# --- navigation state -------------------------------------------------------


def all_topics():
    """{topic: (section, count)}."""
    return {row["topic"]: (row["section"], row["n"]) for row in topic_counts(conn)}


TOPIC_SECTIONS = {row["topic"]: row["section"] for row in topic_counts(conn)}


def all_word_classes():
    """[(word class, count)] in the canonical order, counts included."""
    counts = {row["word_class"]: row["n"] for row in word_class_counts(conn)}
    known = [(wc, counts.pop(wc)) for wc in WORD_CLASSES if wc in counts]
    return known + sorted(counts.items(), key=lambda kv: -kv[1])


def open_topic(topic):
    st.session_state.update(topic=topic, word_class=None)
    st.query_params.clear()
    st.query_params["topic"] = topic

    recents = [t for t in st.session_state.get("recents", []) if t != topic]
    st.session_state.recents = [topic] + recents[: MAX_RECENTS - 1]


def open_word_class(word_class):
    st.session_state.update(topic=None, word_class=word_class)
    st.query_params.clear()
    st.query_params["word_class"] = word_class


def close_all():
    st.session_state.update(topic=None, word_class=None)
    st.query_params.clear()


def restore_from_url():
    """Seed the open topic / word class from ?topic= or ?word_class= once."""
    if "topic" not in st.session_state:
        st.session_state.topic = st.query_params.get("topic")
        st.session_state.word_class = st.query_params.get("word_class")


# --- rendering --------------------------------------------------------------


def entry_state(sv):
    return st.session_state.entry_states.get(sv, {})


def is_favorite(sv):
    return bool(entry_state(sv).get("favorite"))


def in_session(sv):
    return bool(entry_state(sv).get("session_selected"))


def toggle_favorite(sv):
    state.set_favorite(sv, not is_favorite(sv))
    refresh_state()


def toggle_session(sv):
    state.set_session(sv, not in_session(sv))
    refresh_state()


def mark_used(sv):
    state.record_use(sv)
    refresh_state()


def clear_session():
    state.clear_session()
    refresh_state()


def refresh_state():
    st.session_state.entry_states = state.all()


def by_priority(entries):
    """Most recently reached for first, then most used, then alphabetical."""
    def key(entry):
        row = entry_state(entry["sv"])
        return (
            row.get("last_used") is None,
            _desc(row.get("last_used") or ""),
            -(row.get("uses") or 0),
            entry["sv"],
        )
    return sorted(entries, key=key)


def _desc(text):
    """Sort an ISO timestamp descending inside an ascending tuple sort."""
    return tuple(-ord(c) for c in text)


def render_entry(entry, hide_topic=None, key=None):
    with st.container(border=True):
        title = f"**{entry['sv']}** — {entry['en']}"
        if entry["is_custom"]:
            title += " 🆕"

        if key is None:
            st.markdown(title)
        else:
            sv = entry["sv"]
            head, star, plus = st.columns([0.76, 0.12, 0.12])
            head.markdown(title)
            star.button(
                "★" if is_favorite(sv) else "☆",
                key=f"fav_{key}_{entry['id']}",
                on_click=toggle_favorite,
                args=(sv,),
                help="Remove from favourites" if is_favorite(sv) else "Add to favourites",
            )
            plus.button(
                "●" if in_session(sv) else "○",
                key=f"ses_{key}_{entry['id']}",
                on_click=toggle_session,
                args=(sv,),
                help="Drop from this lesson" if in_session(sv) else "Add to this lesson",
            )

        meta = []
        if entry["pos"]:
            meta.append(entry["pos"])
        # The topic you arrived through is already the heading above, so only
        # the *other* topics are worth repeating here.
        others = [t for t in entry["topics"] if t != hide_topic]
        meta.extend(others)
        if entry["fn"]:
            meta.append(f"fn: {entry['fn']}")
        if meta:
            st.caption(" · ".join(meta))

        if entry["note"]:
            st.caption(f"Forms: {entry['note']}")
        if entry["antonym"]:
            st.caption(f"↔ Motsats: **{entry['antonym']}**")

        if entry["ex"]:
            st.code(entry["ex"], language=None)
        if entry["ex_en"]:
            st.caption(entry["ex_en"])

        missed = entry_state(entry["sv"]).get("mistake_count") or 0
        if missed:
            st.caption(f"⚠️ Missed {missed} time{'s' if missed != 1 else ''}")


def button_grid(labels, counts, on_click, key_prefix):
    columns = st.columns(INDEX_COLUMNS)
    for i, label in enumerate(labels):
        columns[i % INDEX_COLUMNS].button(
            f"{label}  ·  {counts[label]}",
            key=f"{key_prefix}_{label}",
            use_container_width=True,
            on_click=on_click,
            args=(label,),
        )


def render_topic_index(topics):
    counts = {name: n for name, (_s, n) in topics.items()}

    recents = [t for t in st.session_state.get("recents", []) if t in topics]
    if recents:
        st.caption("Recent")
        button_grid(recents, counts, open_topic, "recent")
        st.divider()

    for section in SECTIONS:
        names = sorted(name for name, (sec, _n) in topics.items() if sec == section)
        if not names:
            continue
        total = sum(counts[name] for name in names)
        st.subheader(section)
        st.caption(f"{SECTION_BLURBS[section]} · {len(names)} topics · {total} entries")
        button_grid(names, counts, open_topic, "index")
        st.write("")


def render_word_class_index():
    st.caption("Every word of one kind, across every topic.")
    pairs = all_word_classes()
    counts = {wc: n for wc, n in pairs}
    button_grid([wc for wc, _n in pairs], counts, open_word_class, "wc")


def render_grouped(entries, group_key, order=None, hide_topic=None, key_prefix=""):
    """Render entries under headings, in `order` where one is given."""
    groups = {}
    for e in entries:
        groups.setdefault(group_key(e), []).append(e)

    keys = [k for k in (order or []) if k in groups]
    keys += sorted(k for k in groups if k not in keys)

    single = len(keys) == 1
    for heading in keys:
        if not single:
            st.subheader(f"{heading} · {len(groups[heading])}")
        for e in groups[heading]:
            render_entry(e, hide_topic=hide_topic, key=f"{key_prefix}_{heading}")


def render_topic(topic, topics):
    section, count = topics[topic]
    st.button("← All topics", on_click=close_all)
    st.subheader(topic)
    st.caption(f"{section} · {count} entr{'y' if count == 1 else 'ies'}")

    entries = fetch_entries(conn, topics=[topic])

    classes = [wc for wc in WORD_CLASSES if any(e["word_class"] == wc for e in entries)]
    if len(classes) > 1:
        chosen = st.pills("Word class", classes, selection_mode="multi", key=f"wc_{topic}")
        if chosen:
            entries = [e for e in entries if e["word_class"] in chosen]

    if not entries:
        st.info("No entries match the current filters.")
        return

    # The V2 anchors are the one topic where the useful grouping is what
    # triggers the inversion, not the word class.
    if topic == ANCHOR_TOPIC:
        render_grouped(entries, lambda e: FN_LABELS.get(e["fn"], "Other"),
                       order=[FN_LABELS[k] for k in FN_ORDER], hide_topic=topic,
                       key_prefix="topic")
        return

    render_grouped(entries, lambda e: e["word_class"], order=WORD_CLASSES,
                   hide_topic=topic, key_prefix="topic")


def render_word_class(word_class):
    entries = fetch_entries(conn, word_classes=[word_class])
    st.button("← All topics", on_click=close_all)
    st.subheader(word_class)
    st.caption(f"{len(entries)} entr{'y' if len(entries) == 1 else 'ies'} across every topic")

    # An entry in several topics is listed under each of them.
    expanded = [(t, e) for e in entries for t in (e["topics"] or ["(no topic)"])]
    groups = {}
    for topic, entry in expanded:
        groups.setdefault(topic, []).append(entry)

    for topic in sorted(groups):
        st.subheader(f"{topic} · {len(groups[topic])}")
        for e in groups[topic]:
            render_entry(e, hide_topic=topic, key=f"wc_{topic}")


def render_search(query, topics):
    """Search runs across everything — nothing has to be chosen first."""
    counts = {name: n for name, (_s, n) in topics.items()}
    matching = sorted(name for name in topics if fold(query) in fold(name))
    if matching:
        st.caption("Jump to a topic")
        button_grid(matching, counts, open_topic, "found")
        st.divider()

    entries = search_entries(conn, query)
    st.caption(f"{len(entries)} entr{'y' if len(entries) == 1 else 'ies'}")
    if not entries:
        st.info("Nothing matches that. Accents don't matter — 'halsa' finds 'hälsa'.")
        return

    for e in entries:
        render_entry(e, key="search")


def render_compact(entry, key):
    """One tappable row. Tapping means "I used this", which is what orders the
    list next time — the only honest source of a priority signal.
    """
    st.button(
        f"{entry['sv']} — {entry['en']}",
        key=f"use_{key}_{entry['id']}",
        use_container_width=True,
        on_click=mark_used,
        args=(entry["sv"],),
        help=entry["ex"] or None,
    )


def render_quick_list(entries, key):
    for entry in by_priority(entries):
        render_compact(entry, key)


def render_session(all_entries):
    """Today's lesson: what you put on the table before or during class."""
    chosen = [e for e in all_entries if in_session(e["sv"])]
    if not chosen:
        return

    head, clear = st.columns([0.72, 0.28])
    head.subheader(f"This lesson · {len(chosen)}")
    clear.button("Clear lesson", on_click=clear_session, use_container_width=True)
    render_quick_list(chosen, "session")
    st.divider()


def render_cheat_sheet(all_entries):
    """What you actually reach for, first thing on the screen."""
    favorites = [e for e in all_entries if is_favorite(e["sv"])]
    st.subheader("My Cheat Sheet")
    if not favorites:
        st.info("Nothing here yet. Tap ☆ on any entry to keep it at hand.")
        return

    st.caption(
        f"{len(favorites)} favourites · most recently used first · "
        "tap one when you use it"
    )
    render_quick_list(favorites, "cheat")

    with st.expander("Edit cheat sheet"):
        drop = st.multiselect(
            "Remove from favourites",
            sorted(e["sv"] for e in favorites),
            key="unfav_pick",
            placeholder="Pick what you no longer need at hand",
        )
        if drop:
            st.button("Remove", key="unfav_go", on_click=unfavorite_many, args=(drop,))
        st.caption("Tap ☆ on any entry in search or Explore to add one.")


def unfavorite_many(svs):
    for sv in svs:
        state.set_favorite(sv, False)
    refresh_state()


def primary_function(entry):
    """Group the cheat sheet by the job a phrase does, not by subject."""
    for topic in entry["topics"]:
        if TOPIC_SECTIONS.get(topic) == "Functions":
            return topic
    return entry["topics"][0] if entry["topics"] else "Unfiled"


def render_inbox(topics):
    """Anything captured without a topic, so a quick save is never lost."""
    untriaged = fetch_untriaged(conn)
    if not untriaged:
        return

    st.subheader(f"Inbox · {len(untriaged)}")
    st.caption("Captured without a topic. File them when you have a moment.")
    for entry in untriaged:
        with st.container(border=True):
            st.markdown(f"**{entry['sv']}** — {entry['en']}")
            if entry["ex"]:
                st.caption(entry["ex"])
            chosen = st.multiselect(
                "File under", sorted(topics), key=f"file_{entry['id']}",
                placeholder="Pick one or more topics", label_visibility="collapsed",
            )
            if chosen:
                st.button("File it", key=f"do_file_{entry['id']}",
                          on_click=file_entry, args=(entry["id"], chosen))
    st.divider()


def file_entry(entry_id, topics):
    set_entry_topics(conn, entry_id, topics)


def render_backup():
    """State lives in a file the host will eventually delete. This is the way out."""
    with st.expander("Backup & restore — a redeploy wipes your marks"):
        st.caption(
            "Favourites, lesson picks, use counts and miss counts. A few "
            "hundred bytes; keep it anywhere."
        )
        st.download_button(
            "Download my state",
            data=state.export_state(),
            file_name="svenska-state.json",
            mime="application/json",
            use_container_width=True,
        )
        restored = st.file_uploader("Restore from a backup", type="json")
        if restored is not None:
            try:
                count = state.import_state(restored.getvalue())
            except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as error:
                st.error(str(error))
            else:
                refresh_state()
                st.success(f"Restored {count} expressions. Merged, nothing dropped.")


def render_explore(topics):
    """The taxonomy, one click down from the things you reach for."""
    with st.expander(f"Explore all {len(topics)} topics"):
        axis = st.segmented_control(
            "Browse", [BY_TOPIC, BY_WORD_CLASS], default=BY_TOPIC, key="axis"
        )
        if axis == BY_WORD_CLASS:
            render_word_class_index()
        else:
            render_topic_index(topics)


def home_view():
    topics = all_topics()
    restore_from_url()
    if "entry_states" not in st.session_state:
        refresh_state()

    query = st.text_input(
        "Search",
        placeholder="Swedish, English, a topic… accents optional",
        key="search",
        label_visibility="collapsed",
    )
    if query:
        render_search(query, topics)
        return

    topic = st.session_state.topic
    if topic in topics:
        render_topic(topic, topics)
        return

    word_class = st.session_state.get("word_class")
    if word_class:
        render_word_class(word_class)
        return

    all_entries = fetch_entries(conn)
    render_inbox(topics)
    render_session(all_entries)
    render_cheat_sheet(all_entries)
    st.divider()
    render_explore(topics)
    render_backup()


def improv_weave_view():
    st.write(
        "Pull a random mini-set of entries across all topics for a spontaneous "
        "mini-monologue drill. The set stays put until you regenerate it."
    )

    if "weave_ids" not in st.session_state:
        st.session_state.weave_ids = []

    regenerate = st.button("🎲 Generate weave")
    if regenerate or not st.session_state.weave_ids:
        all_entries = fetch_entries(conn)
        n = min(random.randint(3, 5), len(all_entries))
        st.session_state.weave_ids = [e["id"] for e in random.sample(all_entries, n)] if n else []

    if not st.session_state.weave_ids:
        st.info("No entries available yet.")
        return

    by_id = {e["id"]: e for e in fetch_entries_by_id(conn, st.session_state.weave_ids)}
    for entry_id in st.session_state.weave_ids:
        if entry_id in by_id:
            render_entry(by_id[entry_id])


def reverse_drill_view():
    st.write(
        "English shown first — say the Swedish aloud, then reveal to check "
        "yourself. Marking each card is what feeds the ⚠️ counts and the "
        "ordering on your cheat sheet."
    )
    if "entry_states" not in st.session_state:
        refresh_state()

    topics = all_topics()
    col1, col2 = st.columns(2)
    with col1:
        chosen_topics = st.multiselect(
            "Topics", sorted(topics), key="reverse_topics", placeholder="All topics"
        )
    with col2:
        chosen_classes = st.multiselect(
            "Word class",
            [wc for wc, _n in all_word_classes()],
            key="reverse_classes",
            placeholder="All word classes",
        )

    pool = fetch_entries(
        conn, topics=chosen_topics or None, word_classes=chosen_classes or None
    )
    if not pool:
        st.info("No entries match these filters.")
        return

    pool_ids = {e["id"] for e in pool}
    if st.session_state.get("reverse_entry_id") not in pool_ids:
        st.session_state.reverse_entry_id = random.choice(pool)["id"]
        st.session_state.reverse_revealed = False

    current = next(e for e in pool if e["id"] == st.session_state.reverse_entry_id)

    with st.container(border=True):
        st.markdown(f"### {current['en']}")
        st.caption(current["word_class"])

        if not st.session_state.reverse_revealed:
            if st.button("👁️ Reveal"):
                st.session_state.reverse_revealed = True
                st.rerun()
        else:
            title = f"**{current['sv']}**"
            if current["is_custom"]:
                title += " 🆕"
            st.markdown(title)
            meta = ([current["pos"]] if current["pos"] else []) + current["topics"]
            st.caption(" · ".join(meta))
            if current["note"]:
                st.caption(f"Forms: {current['note']}")
            if current["antonym"]:
                st.caption(f"↔ Motsats: **{current['antonym']}**")
            if current["ex"]:
                st.code(current["ex"], language=None)
            if current["ex_en"]:
                st.caption(current["ex_en"])

    if st.session_state.reverse_revealed:
        got, missed = st.columns(2)
        got.button("✓ Got it", key="drill_got", use_container_width=True,
                   on_click=drill_answer, args=(current["sv"], True))
        missed.button("✗ Missed it", key="drill_missed", use_container_width=True,
                      on_click=drill_answer, args=(current["sv"], False))

    if st.button("Next card ➡️"):
        next_card(pool_ids, current["id"])
        st.rerun()


def next_card(pool_ids, current_id):
    remaining = pool_ids - {current_id} or pool_ids
    st.session_state.reverse_entry_id = random.choice(list(remaining))
    st.session_state.reverse_revealed = False


def drill_answer(sv, correct):
    """The event source the states were missing: an actual answer."""
    if correct:
        state.record_success(sv)
    else:
        state.record_mistake(sv)
    refresh_state()
    st.session_state.reverse_revealed = False
    st.session_state.reverse_entry_id = None


def add_entry_view():
    flash = st.session_state.pop("add_flash", None)
    if flash:
        st.success(flash)

    st.write(
        "Catch it while it's fresh. **Swedish and English are all that's "
        "required** — leave the rest blank and it lands in the Inbox on the "
        "home screen, to be filed when you're not mid-conversation."
    )

    topics = all_topics()

    with st.form("add_entry_form", clear_on_submit=True):
        sv = st.text_input("Swedish")
        en = st.text_input("English")
        chosen = st.multiselect(
            "Topics (optional)",
            sorted(topics),
            placeholder="Leave empty to file later",
        )
        with st.expander("More detail (optional)"):
            pos = st.text_input("Part of speech", placeholder="Noun (en), Verb, Adjective…")
            note = st.text_input("Note (forms, etc.)")
            antonym = st.text_input("Opposite (Swedish)", placeholder="liten")
            ex = st.text_area("Example sentence (Swedish)")
            ex_en = st.text_area("Example sentence (English)")
            fn = st.selectbox(
                "V2 function group (only relevant for V2 Inversion Anchors)",
                ["", "position-1", "contrast", "subordinating", "modal"],
            )
        favorite = st.checkbox("Add to my cheat sheet")
        got_wrong = st.checkbox("I got this wrong (mark for review)")
        submitted = st.form_submit_button("Add entry")

        if submitted:
            if not sv or not en:
                st.error("Swedish and English are required. Everything else can wait.")
            else:
                insert_entry(
                    conn,
                    chosen,
                    sv,
                    pos or None,
                    en,
                    note or None,
                    ex or None,
                    ex_en or None,
                    fn or None,
                    antonym=antonym or None,
                    is_custom=1,
                )
                if favorite:
                    state.set_favorite(sv, True)
                if got_wrong:
                    state.record_mistake(sv)
                refresh_state()
                where = ", ".join(chosen) if chosen else "the Inbox"
                st.session_state.add_flash = f"Added “{sv}” → “{en}” to {where}."
                st.rerun()


st.title("🇸🇪 Svenska")

browse, weave, reverse, add = st.tabs(
    ["Cheat Sheet", "Improv Weave", "Reverse Drill", "Add Entry"]
)
with browse:
    home_view()
with weave:
    improv_weave_view()
with reverse:
    reverse_drill_view()
with add:
    add_entry_view()
