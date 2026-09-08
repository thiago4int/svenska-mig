import random

import streamlit as st

from db import (
    SECTIONS,
    fold,
    WORD_CLASSES,
    fetch_entries,
    fetch_entries_by_id,
    fetch_pinned,
    fetch_untriaged,
    get_connection,
    insert_entry,
    register_topic,
    search_entries,
    set_entry_topics,
    set_pinned,
    topic_counts,
    word_class_counts,
)
from seed import ensure_seeded

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


conn = get_db()


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


def toggle_pin(entry_id, pinned):
    set_pinned(conn, entry_id, pinned)


def unpin_many(entry_ids):
    for entry_id in entry_ids:
        set_pinned(conn, entry_id, False)


def render_entry(entry, hide_topic=None, key=None):
    with st.container(border=True):
        title = f"**{entry['sv']}** — {entry['en']}"
        if entry["is_custom"]:
            title += " 🆕"

        if key is None:
            st.markdown(title)
        else:
            head, star = st.columns([0.88, 0.12])
            head.markdown(title)
            star.button(
                "★" if entry["pinned"] else "☆",
                key=f"pin_{key}_{entry['id']}",
                on_click=toggle_pin,
                args=(entry["id"], not entry["pinned"]),
                help="Remove from cheat sheet" if entry["pinned"] else "Add to cheat sheet",
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

        if entry["mistake_count"]:
            times = "time" if entry["mistake_count"] == 1 else "times"
            st.caption(f"⚠️ Missed {entry['mistake_count']} {times}")


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


def render_compact(entry):
    """One scannable line. The cheat sheet is read in seconds, not studied.

    No per-row button: at phone width a column would stack under the text and
    turn every entry into three lines. Unpinning lives in one control below.
    """
    st.markdown(f"**{entry['sv']}** — {entry['en']}")
    if entry["ex"]:
        st.caption(entry["ex"])


def render_cheat_sheet():
    """What you actually reach for, first thing on the screen."""
    pinned = fetch_pinned(conn)
    st.subheader("My Cheat Sheet")
    if not pinned:
        st.info("Nothing pinned yet. Tap ☆ on any entry to keep it here.")
        return

    st.caption(f"{len(pinned)} pinned · tap ★ to drop one")
    groups = {}
    for entry in pinned:
        groups.setdefault(primary_function(entry), []).append(entry)

    for heading in sorted(groups):
        st.markdown(f"**{heading}**")
        for entry in groups[heading]:
            render_compact(entry)
        st.write("")

    with st.expander("Edit cheat sheet"):
        drop = st.multiselect(
            "Remove from the cheat sheet",
            [e["sv"] for e in pinned],
            key="unpin_pick",
            placeholder="Pick what you no longer need at hand",
        )
        if drop:
            st.button("Remove", key="unpin_go", on_click=unpin_many,
                      args=([e["id"] for e in pinned if e["sv"] in drop],))
        st.caption("Tap ☆ on any entry in search or Explore to add one.")


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

    render_inbox(topics)
    render_cheat_sheet()
    st.divider()
    render_explore(topics)


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
        "yourself. Active recall beats passive browsing."
    )

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

    if st.button("Next card ➡️"):
        remaining = pool_ids - {current["id"]} or pool_ids
        st.session_state.reverse_entry_id = random.choice(list(remaining))
        st.session_state.reverse_revealed = False
        st.rerun()


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
        pinned = st.checkbox("Pin to my cheat sheet")
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
                    pinned=1 if pinned else 0,
                    is_custom=1,
                    mistake_count=1 if got_wrong else 0,
                )
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
