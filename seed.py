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

# Hand-written everyday-life expressions: small phrases for talking about
# routine, daily rhythm, and how things are going.
HOME_DAILY_LIFE_EXTRA = [
    # (category, sv, pos, en, note, ex)
    ("Everyday Expressions", "Hur går det?", "Phrase", "How's it going?",
     None, "Hej! Hur går det för dig idag?"),
    ("Everyday Expressions", "Som vanligt", "Phrase", "As usual",
     None, "Helgen var som vanligt, lugn och skön."),
    ("Everyday Expressions", "Ha en bra dag!", "Phrase", "Have a good day!",
     None, "Vi ses imorgon. Ha en bra dag!"),
    ("Everyday Expressions", "Jag har mycket att göra.", "Phrase", "I have a lot to do.",
     None, "Jag kan inte prata länge, jag har mycket att göra."),
    ("Everyday Expressions", "Det är lugnt.", "Phrase", "It's fine / no worries.",
     "Literally 'it's calm'; also used the way English uses 'no worries'.", "Förlåt att jag är sen! — Det är lugnt."),
    ("Everyday Expressions", "Ta det lugnt.", "Phrase", "Take it easy.",
     None, "Du behöver inte stressa, ta det lugnt."),
    ("Everyday Expressions", "Vardag", "Noun (en)", "Weekday / everyday life",
     "Definite: vardagen • Plural: vardagar • Def. plural: vardagarna", "På vardagar går jag upp klockan sex."),
    ("Everyday Expressions", "Rutin", "Noun (en)", "Routine",
     "Definite: rutinen • Plural: rutiner • Def. plural: rutinerna", "Jag har en fast morgonrutin."),
    ("Everyday Expressions", "Sköta sig själv", "Phrase", "To take care of oneself / manage on one's own",
     None, "Nu för tiden sköter han sig själv."),
]

# Hand-written weather and news small talk: extends the existing "Family &
# Weather Chat" category (the CSV only had bare nouns) and adds a new "News &
# Current Events" category — both common territory for everyday small talk.
SOCIAL_SMALL_TALK_EXTRA = [
    # (category, sv, pos, en, note, ex)
    ("Family & Weather Chat", "Vad är det för väder idag?", "Phrase", "What's the weather like today?",
     None, "Vad är det för väder idag? Ska vi ta med paraply?"),
    ("Family & Weather Chat", "Det blåser.", "Phrase", "It's windy.",
     None, "Det blåser mycket idag, håll i hatten!"),
    ("Family & Weather Chat", "Det är molnigt.", "Phrase", "It's cloudy.",
     None, "Det är molnigt idag, men det ska klarna upp senare."),
    ("Family & Weather Chat", "Klarna upp", "Verb", "To clear up (weather)",
     "Infinitive: klarna upp • Past: klarnade upp • Supine: klarnat upp", "Det regnade i morse, men det har klarnat upp nu."),
    ("Family & Weather Chat", "Prognos", "Noun (en)", "Forecast",
     "Definite: prognosen • Plural: prognoser • Def. plural: prognoserna", "Enligt prognosen blir det snö i helgen."),
    ("Family & Weather Chat", "Grad", "Noun (en)", "Degree (temperature)",
     "Definite: graden • Plural: grader • Def. plural: graderna", "Det är tjugo grader ute idag."),
    ("Family & Weather Chat", "Åska", "Noun (en)", "Thunder",
     "Definite: åskan (uncountable)", "Det åskar och blixtrar just nu."),
    ("News & Current Events", "Nyhet", "Noun (en)", "News (item)",
     "Definite: nyheten • Plural: nyheter • Def. plural: nyheterna", "Har du sett nyheterna idag?"),
    ("News & Current Events", "Tidning", "Noun (en)", "Newspaper",
     "Definite: tidningen • Plural: tidningar • Def. plural: tidningarna", "Jag läser tidningen varje morgon."),
    ("News & Current Events", "Har du hört…?", "Phrase", "Have you heard…?",
     None, "Har du hört att de bygger en ny bro?"),
    ("News & Current Events", "Vad har hänt?", "Phrase", "What happened?",
     None, "Vad har hänt? Alla pratar om det."),
    ("News & Current Events", "Enligt nyheterna…", "Phrase", "According to the news…",
     None, "Enligt nyheterna kommer det snö imorgon."),
    ("News & Current Events", "Rubrik", "Noun (en)", "Headline",
     "Definite: rubriken • Plural: rubriker • Def. plural: rubrikerna", "Rubriken var väldigt dramatisk."),
]

# Hand-written comparatives: the core "bättre/större/lättare än"-style
# vocabulary plus the two comparison sentence patterns ("lika … som" and
# "ju … desto …"), each with an example sentence the way V2_ANCHORS does.
COMPARISONS = [
    # (sv, pos, en, note, ex)
    ("Än", "Conjunction", "Than",
     "Follows a comparative adjective or adverb.", "Hon är äldre än jag."),
    ("Bättre än", "Comparative phrase", "Better than",
     "Positive: bra/god • Superlative: bäst", "Det här kaffet är bättre än det där."),
    ("Sämre än", "Comparative phrase", "Worse than",
     "Positive: dålig • Superlative: sämst", "Mitt betyg blev sämre än förra terminen."),
    ("Större än", "Comparative phrase", "Bigger than",
     "Positive: stor • Superlative: störst", "Sverige är större än Danmark."),
    ("Mindre än", "Comparative phrase", "Smaller than",
     "Positive: liten • Superlative: minst", "Min lägenhet är mindre än din."),
    ("Lättare än", "Comparative phrase", "Easier than",
     "Positive: lätt • Superlative: lättast", "Provet var lättare än jag trodde."),
    ("Svårare än", "Comparative phrase", "Harder / more difficult than",
     "Positive: svår • Superlative: svårast", "Grammatik är svårare än uttal för mig."),
    ("Snabbare än", "Comparative phrase", "Faster than",
     "Positive: snabb • Superlative: snabbast", "Tåget är snabbare än bussen."),
    ("Långsammare än", "Comparative phrase", "Slower than",
     "Positive: långsam • Superlative: långsammast", "Han pratar långsammare än jag gör."),
    ("Billigare än", "Comparative phrase", "Cheaper than",
     "Positive: billig • Superlative: billigast", "Den här tröjan är billigare än den där."),
    ("Dyrare än", "Comparative phrase", "More expensive than",
     "Positive: dyr • Superlative: dyrast", "Hyran är dyrare i år än förra året."),
    ("Fler än", "Comparative phrase", "More than (countable)",
     "Uncountable equivalent: mer än.", "Vi har fler stolar än bord."),
    ("Lika … som", "Comparative construction", "As … as",
     "The adjective stays in base form between 'lika' and 'som'.", "Hon är lika trött som jag."),
    ("Ju … desto …", "Correlative construction", "The … the …",
     "Both clauses invert: the verb follows the comparative word directly.", "Ju mer jag övar, desto bättre blir jag."),
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

    for category, sv, pos, en, note, ex in HOME_DAILY_LIFE_EXTRA:
        insert_entry(conn, "Home & Daily Life", category, sv, pos, en, note, ex, None, is_custom=0)

    for category, sv, pos, en, note, ex in SOCIAL_SMALL_TALK_EXTRA:
        insert_entry(conn, "Social & Small Talk", category, sv, pos, en, note, ex, None, is_custom=0)

    for sv, pos, en, note, ex in COMPARISONS:
        insert_entry(
            conn, "Grammar & V2 Anchors", "Comparatives & Comparisons", sv, pos, en, note, ex, None, is_custom=0
        )

    for category, sv, pos, en in TUTOR_TOOLKIT:
        insert_entry(conn, "Tutor Toolkit", category, sv, pos, en, None, None, None, is_custom=0)
