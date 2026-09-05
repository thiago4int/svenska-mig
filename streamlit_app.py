import random

import streamlit as st

from db import distinct_values, fetch_entries, get_connection, insert_entry, topic_counts
from seed import ensure_seeded

TABS = [
    "Workplace & Tech",
    "Social & Small Talk",
    "Home & Daily Life",
    "Grammar & V2 Anchors",
    "Questions & Prepositions",
    "Tutor Toolkit",
]

# Navigation is a flat index of topics, not a tab -> category drilldown: with
# ~45 topics everything fits on one screen, so a tree only adds a step where
# you have to know the answer (which tab a topic sits under) before you can
# ask the question. The old tabs survive only as the three headings the index
# is grouped under, which is the distinction that actually matters when you're
# choosing: something to talk about, something to look up, or something to say
# when the conversation stalls.
TOPIC_GROUPS = [
    ("Topics & situations", ["Workplace & Tech", "Social & Small Talk", "Home & Daily Life"]),
    ("Grammar & reference", ["Grammar & V2 Anchors", "Questions & Prepositions"]),
    ("Conversation toolkit", ["Tutor Toolkit"]),
]

FN_LABELS = {
    "position-1": "Position-1 anchors (fronted time/place adverbials)",
    "contrast": "Contrast anchors",
    "subordinating": "Subordinating anchors",
    "modal": "Modal anchors",
}
FN_ORDER = ["position-1", "contrast", "subordinating", "modal"]

ANCHOR_TOPIC = "V2 Inversion Anchors"
INDEX_COLUMNS = 3
MAX_RECENTS = 5

st.set_page_config(page_title="Svenska", page_icon="🇸🇪", layout="centered")


@st.cache_resource
def get_db():
    conn = get_connection()
    ensure_seeded(conn)
    return conn


conn = get_db()


# --- topic navigation -------------------------------------------------------


def all_topics():
    """{topic: (tab, count)} for every topic in the database."""
    return {row["category"]: (row["tab"], row["n"]) for row in topic_counts(conn)}


def open_topic(topic):
    st.session_state.topic = topic
    st.query_params["topic"] = topic

    recents = [t for t in st.session_state.get("recents", []) if t != topic]
    st.session_state.recents = [topic] + recents[: MAX_RECENTS - 1]


def close_topic():
    st.session_state.topic = None
    st.query_params.pop("topic", None)


def current_topic(topics):
    """The open topic, seeded from ?topic= so links and browser back work."""
    if "topic" not in st.session_state:
        st.session_state.topic = st.query_params.get("topic")

    topic = st.session_state.topic
    return topic if topic in topics else None


def topic_buttons(names, topics, key_prefix):
    """A grid of topic buttons, each labelled with its entry count."""
    columns = st.columns(INDEX_COLUMNS)
    for i, name in enumerate(names):
        _tab, count = topics[name]
        columns[i % INDEX_COLUMNS].button(
            f"{name}  ·  {count}",
            key=f"{key_prefix}_{name}",
            use_container_width=True,
            on_click=open_topic,
            args=(name,),
        )


# --- rendering --------------------------------------------------------------


def render_entry(entry):
    with st.container(border=True):
        title = f"**{entry['sv']}** — {entry['en']}"
        if entry["is_custom"]:
            title += " 🆕"
        st.markdown(title)

        meta = [entry["category"]]
        if entry["pos"]:
            meta.append(entry["pos"])
        if entry["fn"]:
            meta.append(f"fn: {entry['fn']}")
        st.caption(" · ".join(meta))

        if entry["note"]:
            st.caption(f"Forms: {entry['note']}")

        if entry["ex"]:
            st.code(entry["ex"], language=None)
        if entry["ex_en"]:
            st.caption(entry["ex_en"])

        if entry["mistake_count"]:
            times = "time" if entry["mistake_count"] == 1 else "times"
            st.caption(f"⚠️ Missed {entry['mistake_count']} {times}")


def render_index(topics):
    """The landing screen: every topic at once, one click to open."""
    recents = [t for t in st.session_state.get("recents", []) if t in topics]
    if recents:
        st.caption("Recent")
        topic_buttons(recents, topics, "recent")
        st.divider()

    for heading, tabs in TOPIC_GROUPS:
        names = sorted(name for name, (tab, _n) in topics.items() if tab in tabs)
        if not names:
            continue
        total = sum(topics[name][1] for name in names)
        st.subheader(heading)
        st.caption(f"{len(names)} topics · {total} entries")
        topic_buttons(names, topics, "index")
        st.write("")


def render_topic(topic, topics):
    tab, count = topics[topic]
    st.button("← All topics", on_click=close_topic)
    st.subheader(topic)
    st.caption(f"{tab} · {count} entr{'y' if count == 1 else 'ies'}")

    with st.expander("Refine"):
        pos_choice = st.multiselect(
            "Part of speech", distinct_values(conn, "pos", tab=tab), key="topic_pos"
        )

    entries = fetch_entries(conn, categories=[topic], pos_list=pos_choice or None)
    if not entries:
        st.info("No entries match the current filters.")
        return

    # The V2 anchors are only useful grouped by what triggers the inversion,
    # which used to need a toggle. As its own topic it can just always group.
    if topic == ANCHOR_TOPIC:
        groups = {}
        for e in entries:
            groups.setdefault(e["fn"], []).append(e)
        for fn_key in FN_ORDER:
            if fn_key in groups:
                st.subheader(FN_LABELS[fn_key])
                for e in groups[fn_key]:
                    render_entry(e)
        return

    for e in entries:
        render_entry(e)


def render_search(search, topics):
    """Search runs across everything — no topic has to be chosen first."""
    matching_topics = sorted(name for name in topics if search.lower() in name.lower())
    if matching_topics:
        st.caption("Matching topics")
        topic_buttons(matching_topics, topics, "found")
        st.divider()

    entries = fetch_entries(conn, search=search)
    st.caption(f"{len(entries)} entr{'y' if len(entries) == 1 else 'ies'}")
    if not entries:
        st.info("Nothing matches that search.")
        return

    current_category = None
    for e in entries:
        if e["category"] != current_category:
            st.subheader(e["category"])
            current_category = e["category"]
        render_entry(e)


def browse_tab():
    topics = all_topics()
    search = st.text_input(
        "Search",
        placeholder="Search Swedish, English, topic, notes, examples…",
        key="search",
    )

    if search:
        render_search(search, topics)
        return

    topic = current_topic(topics)
    if topic:
        render_topic(topic, topics)
    else:
        render_index(topics)


def improv_weave_tab():
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

    placeholders = ",".join("?" for _ in st.session_state.weave_ids)
    rows = conn.execute(
        f"SELECT * FROM entries WHERE id IN ({placeholders})", st.session_state.weave_ids
    ).fetchall()
    by_id = {r["id"]: r for r in rows}
    ordered = [by_id[i] for i in st.session_state.weave_ids if i in by_id]

    for e in ordered:
        render_entry(e)


def reverse_drill_tab():
    st.write(
        "English shown first — say the Swedish aloud, then reveal to check "
        "yourself. Active recall beats passive browsing."
    )

    topics = all_topics()
    chosen = st.multiselect(
        "Topics",
        sorted(topics),
        key="reverse_topics",
        placeholder="All topics",
    )

    pool = fetch_entries(conn, categories=chosen or None)
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
        if current["pos"]:
            st.caption(current["pos"])

        if not st.session_state.reverse_revealed:
            if st.button("👁️ Reveal"):
                st.session_state.reverse_revealed = True
                st.rerun()
        else:
            title = f"**{current['sv']}**"
            if current["is_custom"]:
                title += " 🆕"
            st.markdown(title)
            st.caption(current["category"])
            if current["note"]:
                st.caption(f"Forms: {current['note']}")
            if current["ex"]:
                st.code(current["ex"], language=None)
            if current["ex_en"]:
                st.caption(current["ex_en"])

    if st.button("Next card ➡️"):
        remaining = pool_ids - {current["id"]} or pool_ids
        st.session_state.reverse_entry_id = random.choice(list(remaining))
        st.session_state.reverse_revealed = False
        st.rerun()


def add_entry_tab():
    st.write(
        "Add your own entry — during or right after a tutor session works "
        "well, while the correction is still fresh. It's tagged 🆕 so it "
        "stays distinguishable from the seed set."
    )

    existing_topics = sorted(all_topics())

    with st.form("add_entry_form", clear_on_submit=True):
        tab = st.selectbox("Group", TABS)
        category = st.selectbox(
            "Topic",
            existing_topics,
            index=None,
            accept_new_options=True,
            placeholder="Pick a topic or type a new one",
        )
        sv = st.text_input("Swedish")
        pos = st.text_input("Part of speech")
        en = st.text_input("English")
        note = st.text_input("Note (forms, etc.)")
        ex = st.text_area("Example sentence (Swedish)")
        ex_en = st.text_area("Example sentence (English)")
        fn = st.selectbox(
            "V2 function group (only relevant for V2 Inversion Anchors)",
            ["", "position-1", "contrast", "subordinating", "modal"],
        )
        got_wrong = st.checkbox("I got this wrong (mark for review)")
        submitted = st.form_submit_button("Add entry")

        if submitted:
            if not sv or not en or not category:
                st.error("Swedish, English, and Topic are required.")
            else:
                insert_entry(
                    conn,
                    tab,
                    category,
                    sv,
                    pos or None,
                    en,
                    note or None,
                    ex or None,
                    ex_en or None,
                    fn or None,
                    is_custom=1,
                    mistake_count=1 if got_wrong else 0,
                )
                st.cache_data.clear()
                st.success(f"Added “{sv}” → “{en}”.")
                st.rerun()


st.title("🇸🇪 Svenska")

browse, weave, reverse, add = st.tabs(["Browse", "Improv Weave", "Reverse Drill", "Add Entry"])
with browse:
    browse_tab()
with weave:
    improv_weave_tab()
with reverse:
    reverse_drill_tab()
with add:
    add_entry_tab()
