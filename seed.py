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

# Hand-written Workplace & Tech content: the old CSV barely touched this
# domain (just five professions + one stray verb), so these are fresh.
WORKPLACE_TECH_EXTRA = [
    # (category, sv, pos, en, note, ex)
    ("Workplace Basics", "Jobb", "Noun (ett)", "Job / work",
     "Definite: jobbet • Plural: jobb • Def. plural: jobben", "Jag har ett nytt jobb."),
    ("Workplace Basics", "Möte", "Noun (ett)", "Meeting",
     "Definite: mötet • Plural: möten • Def. plural: mötena", "Vi har ett möte klockan tio."),
    ("Workplace Basics", "Kollega", "Noun (en)", "Colleague",
     "Definite: kollegan • Plural: kollegor • Def. plural: kollegorna", "Min kollega heter Anna."),
    ("Workplace Basics", "Chef", "Noun (en)", "Boss / manager",
     "Definite: chefen • Plural: chefer • Def. plural: cheferna", "Chefen är på semester."),
    ("Workplace Basics", "Tidsfrist", "Noun (en)", "Deadline",
     "Definite: tidsfristen • Plural: tidsfrister • Def. plural: tidsfristerna", "Vi har en tidsfrist imorgon."),
    ("Workplace Basics", "Distansarbete", "Noun (ett)", "Remote work",
     "Definite: distansarbetet (uncountable)", "Jag jobbar med distansarbete idag."),
    ("Tech & Devices", "Dator", "Noun (en)", "Computer",
     "Definite: datorn • Plural: datorer • Def. plural: datorerna", "Min dator är trasig."),
    ("Tech & Devices", "Skärm", "Noun (en)", "Screen / monitor",
     "Definite: skärmen • Plural: skärmar • Def. plural: skärmarna", "Skärmen är för liten."),
    ("Tech & Devices", "Fil", "Noun (en)", "File",
     "Definite: filen • Plural: filer • Def. plural: filerna", "Kan du skicka filen?"),
    ("Tech & Devices", "Lösenord", "Noun (ett)", "Password",
     "Definite: lösenordet • Plural: lösenord • Def. plural: lösenorden", "Jag glömde mitt lösenord."),
    ("Tech & Devices", "Uppdatera", "Verb", "To update",
     "Infinitive: uppdatera • Past: uppdaterade • Supine: uppdaterat", "Jag måste uppdatera programmet."),
    ("Tech & Devices", "Programmera", "Verb", "To program",
     "Infinitive: programmera • Past: programmerade • Supine: programmerat", "Han programmerar varje dag."),
]

# Hand-written Tutor Toolkit: conversation-management phrases for keeping a
# tutoring session in Swedish even when you need help. New tab, no analog in
# the original CSV.
TUTOR_TOOLKIT = [
    # (category, sv, pos, en)
    ("Clarification", "Kan du upprepa?", "Phrase", "Can you repeat?"),
    ("Clarification", "Vad betyder det?", "Phrase", "What does that mean?"),
    ("Clarification", "Kan du säga det långsammare?", "Phrase", "Can you say it slower?"),
    ("Clarification", "Jag hängde inte med.", "Phrase", "I didn't catch that."),
    ("Repair & Save the Conversation", "Jag menar …", "Phrase", "I mean … (self-correcting)"),
    ("Repair & Save the Conversation", "Jag har glömt ordet.", "Phrase", "I've forgotten the word."),
    ("Repair & Save the Conversation", "Får jag tänka lite?", "Phrase", "Can I think a bit?"),
    ("Repair & Save the Conversation", "Jag försöker igen.", "Phrase", "I'll try again."),
    ("Meta-language", "Hur säger man det på svenska?", "Phrase", "How do you say that in Swedish?"),
    ("Meta-language", "Hur stavas det?", "Phrase", "How is it spelled?"),
    ("Meta-language", "Kan du ge ett exempel?", "Phrase", "Can you give an example?"),
    ("Polite Feedback", "Det här är svårt för mig.", "Phrase", "This is difficult for me."),
    ("Polite Feedback", "Jag förstår inte riktigt.", "Phrase", "I don't quite understand."),
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

    for category, sv, pos, en, note, ex in WORKPLACE_TECH_EXTRA:
        insert_entry(conn, "Workplace & Tech", category, sv, pos, en, note, ex, None, is_custom=0)

    for category, sv, pos, en in TUTOR_TOOLKIT:
        insert_entry(conn, "Tutor Toolkit", category, sv, pos, en, None, None, None, is_custom=0)
