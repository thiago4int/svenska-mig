import random

import streamlit as st

from db import (
    SECTIONS,
    WORD_CLASSES,
    fetch_entries,
    fetch_entries_by_id,
    get_connection,
    insert_entry,
    register_topic,
    topic_counts,
    word_class_counts,
)
from seed import ensure_seeded

# Words are filed along two independent axes.
#
#   topic       what it is about  — Food & Drink, Travel & Transport, Work
#   word_class  what kind of word — Verb, Noun, Adjective, Phrase
#
# One used to do both jobs, which is where "More Verbs" and "Colors &
# Adjectives" came from: a word class wearing a topic's clothes. Now you can
# enter from either end, and a word can sit in several topics at once — "äter"
# is core vocabulary and food vocabulary, not one or the other.
SECTION_BLURBS = {
    "Topics & situations": "Things to talk about",
    "Grammar & reference": "Things to look up",
    "Conversation toolkit": "Things to say when you're stuck",
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


def render_entry(entry, hide_topic=None):
    with st.container(border=True):
        title = f"**{entry['sv']}** — {entry['en']}"
        if entry["is_custom"]:
            title += " 🆕"
        st.markdown(title)

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


def render_grouped(entries, group_key, order=None, hide_topic=None):
    """Render entries under headings, in `order` where one is given."""
    groups = {}
    for e in entries:
        groups.setdefault(group_key(e), []).append(e)

    keys = [k for k in (order or []) if k in groups]
    keys += sorted(k for k in groups if k not in keys)

    single = len(keys) == 1
    for key in keys:
        if not single:
            st.subheader(f"{key} · {len(groups[key])}")
        for e in groups[key]:
            render_entry(e, hide_topic=hide_topic)


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
                       order=[FN_LABELS[k] for k in FN_ORDER], hide_topic=topic)
        return

    render_grouped(entries, lambda e: e["word_class"], order=WORD_CLASSES, hide_topic=topic)


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
            render_entry(e, hide_topic=topic)


def render_search(search, topics):
    """Search runs across everything — nothing has to be chosen first."""
    counts = {name: n for name, (_s, n) in topics.items()}
    matching = sorted(name for name in topics if search.lower() in name.lower())
    if matching:
        st.caption("Matching topics")
        button_grid(matching, counts, open_topic, "found")
        st.divider()

    entries = fetch_entries(conn, search=search)
    st.caption(f"{len(entries)} entr{'y' if len(entries) == 1 else 'ies'}")
    if not entries:
        st.info("Nothing matches that search.")
        return

    render_grouped(entries, lambda e: e["word_class"], order=WORD_CLASSES)


def browse_view():
    topics = all_topics()
    restore_from_url()

    search = st.text_input(
        "Search",
        placeholder="Search Swedish, English, topic, notes, examples…",
        key="search",
    )
    if search:
        render_search(search, topics)
        return

    topic = st.session_state.topic
    if topic in topics:
        render_topic(topic, topics)
        return

    word_class = st.session_state.get("word_class")
    if word_class:
        render_word_class(word_class)
        return

    axis = st.segmented_control(
        "Browse", [BY_TOPIC, BY_WORD_CLASS], default=BY_TOPIC, key="axis"
    )
    if axis == BY_WORD_CLASS:
        render_word_class_index()
    else:
        render_topic_index(topics)


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
        "Add your own entry — during or right after a tutor session works "
        "well, while the correction is still fresh. It's tagged 🆕 so it "
        "stays distinguishable from the seed set."
    )

    topics = all_topics()

    # Outside the form, so a brand-new topic can reveal the one question that
    # can't be inferred. Existing topics ask nothing further.
    chosen = st.multiselect(
        "Topics",
        sorted(topics),
        accept_new_options=True,
        placeholder="Pick one or more topics, or type a new one",
        key="add_topics",
        help="A word can belong to several — core vocabulary that is also about food, say.",
    )

    new_topics = [t for t in chosen if t not in topics]
    section = None
    if new_topics:
        section = st.radio(
            f"{', '.join(repr(t) for t in new_topics)} — new. Where does it belong?",
            SECTIONS,
            captions=[SECTION_BLURBS[s] for s in SECTIONS],
            key="add_section",
        )

    with st.form("add_entry_form", clear_on_submit=True):
        sv = st.text_input("Swedish")
        en = st.text_input("English")
        pos = st.text_input("Part of speech", placeholder="Noun (en), Verb, Adjective…")
        note = st.text_input("Note (forms, etc.)")
        antonym = st.text_input(
            "Opposite (Swedish)", placeholder="liten",
            help="The Swedish word that means the reverse, if there is one.",
        )
        ex = st.text_area("Example sentence (Swedish)")
        ex_en = st.text_area("Example sentence (English)")
        fn = st.selectbox(
            "V2 function group (only relevant for V2 Inversion Anchors)",
            ["", "position-1", "contrast", "subordinating", "modal"],
        )
        got_wrong = st.checkbox("I got this wrong (mark for review)")
        submitted = st.form_submit_button("Add entry")

        if submitted:
            if not chosen or not sv or not en:
                st.error("At least one topic, Swedish, and English are required.")
            else:
                for topic in new_topics:
                    register_topic(conn, topic, section)
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
                    mistake_count=1 if got_wrong else 0,
                )
                st.session_state.add_flash = (
                    f"Added “{sv}” → “{en}” to {', '.join(chosen)}."
                )
                st.rerun()


st.title("🇸🇪 Svenska")

browse, weave, reverse, add = st.tabs(["Browse", "Improv Weave", "Reverse Drill", "Add Entry"])
with browse:
    browse_view()
with weave:
    improv_weave_view()
with reverse:
    reverse_drill_view()
with add:
    add_entry_view()
