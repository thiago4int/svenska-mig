import csv
from pathlib import Path

from db import insert_entry

CSV_PATH = Path(__file__).parent / "words" / "svenska.csv"

# Best-fit mapping from the old flashcard categories to the new tab/category
# structure. "Weather, family & professions" is split by word below since it
# straddles three different tabs.
CATEGORY_MAP = {
    "Greetings and pleasantries": ("Social & Small Talk", "Greetings & Pleasantries"),
    "People and pronouns": ("Grammar & V2 Anchors", "Pronouns & People"),
    "Everyday verbs": ("Home & Daily Life", "Everyday Verbs"),
    "Food and drink": ("Home & Daily Life", "Food & Drink"),
    "Time and days": ("Home & Daily Life", "Time & Days"),
    "Numbers and counting": ("Home & Daily Life", "Numbers & Counting"),
    "Places and directions": ("Home & Daily Life", "Places & Directions"),
    "Colors and adjectives": ("Home & Daily Life", "Colors & Adjectives"),
    "Question words & prepositions": ("Grammar & V2 Anchors", "Question Words & Prepositions"),
    "More adjectives": ("Home & Daily Life", "More Adjectives"),
    "Nature and seasons": ("Home & Daily Life", "Nature & Seasons"),
    "Feelings and emotions": ("Social & Small Talk", "Feelings & Emotions"),
    "More verbs": ("Home & Daily Life", "More Verbs"),
    "Conjunctions and connectors": ("Grammar & V2 Anchors", "Conjunctions & Connectors"),
    "Pronouns and articles": ("Grammar & V2 Anchors", "Pronouns & Articles"),
    "Health and body": ("Home & Daily Life", "Health & Body"),
    "Home and objects": ("Home & Daily Life", "Home & Objects"),
    "Adverbs and function words": ("Grammar & V2 Anchors", "Adverbs & Function Words"),
}

PROFESSION_WORDS = {"Lärare", "Läkare", "Student", "Kock", "Polis"}
TECH_WORDS = {"Automatiserar"}

# Hand-written V2 inversion anchors: sentence starters that push the verb
# into position 2, grouped by the grammatical role that triggers inversion.
V2_ANCHORS = [
    # position-1: fronted time/place adverbials
    ("Idag", "Adverb", "Today", "position-1", "Idag jobbar jag hemifrån.", None),
    ("Nu", "Adverb", "Now", "position-1", "Nu förstår jag.", None),
    ("Sedan", "Adverb", "Then / afterwards", "position-1", "Sedan gick vi hem.", None),
    ("Igår", "Adverb", "Yesterday", "position-1", "Igår regnade det hela dagen.", None),
    ("Där", "Adverb", "There", "position-1", "Där bor min syster.", None),
    ("Ofta", "Adverb", "Often", "position-1", "Ofta äter vi middag klockan sju.", None),
    # contrast: adverbial connectors (not coordinating conjunctions like "men")
    ("Dock", "Adverb", "However", "contrast", "Han var trött. Dock fortsatte han att jobba.", None),
    ("Ändå", "Adverb", "Still / nevertheless", "contrast", "Det regnade. Ändå gick vi ut.", None),
    ("Trots det", "Adverbial phrase", "Despite that", "contrast", "Trots det stannade hon hemma.", None),
    # subordinating: the whole subordinate clause occupies position 1
    ("Att", "Subjunction", "That", "subordinating", "Att han kommer vet jag.", "Fronted subordinate clause with 'att'."),
    ("Om", "Subjunction", "If", "subordinating", "Om det regnar stannar vi hemma.", None),
    ("När", "Subjunction", "When", "subordinating", "När jag kommer hem lagar jag mat.", None),
    ("Eftersom", "Subjunction", "Because", "subordinating", "Eftersom jag är trött går jag och lägger mig.", None),
    ("Fastän", "Subjunction", "Although", "subordinating", "Fastän det var kallt badade vi.", None),
    # modal: sentence adverbs
    ("Kanske", "Modal adverb", "Maybe", "modal", "Kanske kommer han imorgon.", "Only triggers inversion when fronted; 'Han kommer kanske imorgon' does not invert."),
    ("Nog", "Modal adverb", "Probably", "modal", "Nog blir det bra.", None),
    ("Tyvärr", "Modal adverb", "Unfortunately", "modal", "Tyvärr kan jag inte komma.", None),
]


def _split_note(forms):
    forms = (forms or "").strip()
    return None if forms in ("", "—") else forms


def seed_database(conn):
    with CSV_PATH.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            category = row["Category"]
            sv = row["Swedish"]
            pos = row["Word Type"] or None
            en = row["English"]
            note = _split_note(row["Other forms (tense / plural / etc.)"])

            if category == "Weather, family & professions":
                if sv in PROFESSION_WORDS:
                    tab, new_category = "Workplace & Tech", "Professions"
                else:
                    tab, new_category = "Social & Small Talk", "Family & Weather Chat"
            elif sv in TECH_WORDS:
                tab, new_category = "Workplace & Tech", "Tech Verbs"
            else:
                tab, new_category = CATEGORY_MAP[category]

            insert_entry(conn, tab, new_category, sv, pos, en, note, None, None, is_custom=0)

    for sv, pos, en, fn, ex, note in V2_ANCHORS:
        insert_entry(
            conn,
            "Grammar & V2 Anchors",
            "V2 Inversion Anchors",
            sv,
            pos,
            en,
            note,
            ex,
            fn,
            is_custom=0,
        )
