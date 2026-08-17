import random

import streamlit as st

from db import distinct_values, fetch_entries, get_connection, insert_entry, is_empty
from seed import seed_database

TABS = ["Workplace & Tech", "Social & Small Talk", "Home & Daily Life", "Grammar & V2 Anchors", "Tutor Toolkit"]

FN_LABELS = {
    "position-1": "Position-1 anchors (fronted time/place adverbials)",
    "contrast": "Contrast anchors",
    "subordinating": "Subordinating anchors",
    "modal": "Modal anchors",
}
FN_ORDER = ["position-1", "contrast", "subordinating", "modal"]

st.set_page_config(page_title="Svenska", page_icon="🇸🇪", layout="centered")


@st.cache_resource
def get_db():
    conn = get_connection()
    if is_empty(conn):
        seed_database(conn)
    return conn


conn = get_db()


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

        if entry["mistake_count"]:
            times = "time" if entry["mistake_count"] == 1 else "times"
            st.caption(f"⚠️ Missed {entry['mistake_count']} {times}")


def browse_tab():
    search = st.text_input(
        "Search",
        placeholder="Search Swedish, English, category, notes, examples…",
    )

    tab_choice = st.selectbox("Tab", ["All tabs"] + TABS, key="tab_choice")

    # Landing on the Grammar & V2 Anchors tab defaults the toggle on, since
    # that tab otherwise mixes the anchors in with plain grammar vocab. Stays
    # manually overridable until the tab is changed again.
    if st.session_state.get("_last_tab") != tab_choice:
        st.session_state["anchors_only"] = tab_choice == "Grammar & V2 Anchors"
        st.session_state["_last_tab"] = tab_choice

    col1, col2 = st.columns(2)
    with col1:
        category_choice = st.multiselect(
            "Category", distinct_values(conn, "category", tab=tab_choice)
        )
    with col2:
        pos_choice = st.multiselect(
            "Part of speech", distinct_values(conn, "pos", tab=tab_choice)
        )

    only_anchors = st.toggle("V2 Inversion anchors only", key="anchors_only")

    entries = fetch_entries(
        conn,
        tab=tab_choice,
        categories=category_choice or None,
        pos_list=pos_choice or None,
        search=search or None,
        only_anchors=only_anchors,
    )

    st.caption(f"{len(entries)} entr{'y' if len(entries) == 1 else 'ies'}")

    if not entries:
        st.info("No entries match the current filters.")
        return

    if only_anchors:
        groups = {}
        for e in entries:
            groups.setdefault(e["fn"], []).append(e)
        for fn_key in FN_ORDER:
            if fn_key in groups:
                st.subheader(FN_LABELS[fn_key])
                for e in groups[fn_key]:
                    render_entry(e)
    else:
        # Entries arrive sorted by tab, category, sv — print a heading
        # whenever either changes so categories stay visibly grouped,
        # the way the old word-list view did.
        current_tab, current_category = None, None
        for e in entries:
            if e["tab"] != current_tab or e["category"] != current_category:
                heading = e["category"] if tab_choice != "All tabs" else f"{e['tab']} · {e['category']}"
                st.subheader(heading)
                current_tab, current_category = e["tab"], e["category"]
            render_entry(e)


def improv_weave_tab():
    st.write(
        "Pull a random mini-set of entries across all tabs for a spontaneous "
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

    tab_choice = st.selectbox("Tab", ["All tabs"] + TABS, key="reverse_tab")
    category_choice = st.multiselect(
        "Category", distinct_values(conn, "category", tab=tab_choice), key="reverse_category"
    )

    pool = fetch_entries(conn, tab=tab_choice, categories=category_choice or None)
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
            if current["note"]:
                st.caption(f"Forms: {current['note']}")
            if current["ex"]:
                st.code(current["ex"], language=None)

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

    with st.form("add_entry_form", clear_on_submit=True):
        tab = st.selectbox("Tab", TABS)
        category = st.text_input("Category")
        sv = st.text_input("Swedish")
        pos = st.text_input("Part of speech")
        en = st.text_input("English")
        note = st.text_input("Note (forms, etc.)")
        ex = st.text_area("Example sentence")
        fn = st.selectbox(
            "V2 function group (only relevant for Grammar & V2 Anchors)",
            ["", "position-1", "contrast", "subordinating", "modal"],
        )
        got_wrong = st.checkbox("I got this wrong (mark for review)")
        submitted = st.form_submit_button("Add entry")

        if submitted:
            if not sv or not en or not category:
                st.error("Swedish, English, and Category are required.")
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
