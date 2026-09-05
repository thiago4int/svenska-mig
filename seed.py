import csv
from pathlib import Path

from db import (
    SECTIONS,
    delete_seed_entries,
    get_meta,
    insert_entry,
    is_empty,
    register_topic,
    set_meta,
)

CSV_PATH = Path(__file__).parent / "words" / "svenska.csv"

# Bumped whenever the seed content below changes. A deployed app compares this
# against the value stored in the database and reseeds when they differ, so new
# vocabulary shows up on deploy without anyone deleting svenska.db by hand.
SEED_VERSION = "4"

# Best-fit mapping from the old flashcard categories onto (section, topic).
# A section is one of the three headings on the index — the only grouping above
# the topic that the app has. "Weather, family & professions" is split by word
# below since it straddles three different topics.
CATEGORY_MAP = {
    "Greetings and pleasantries": ("Topics & situations", "Greetings & Pleasantries"),
    "People and pronouns": ("Grammar & reference", "Pronouns & People"),
    "Everyday verbs": ("Topics & situations", "Everyday Verbs"),
    "Food and drink": ("Topics & situations", "Food & Drink"),
    "Time and days": ("Topics & situations", "Time & Days"),
    "Numbers and counting": ("Topics & situations", "Numbers & Counting"),
    "Places and directions": ("Topics & situations", "Places & Directions"),
    "Colors and adjectives": ("Topics & situations", "Colors & Adjectives"),
    "Question words & prepositions": ("Grammar & reference", "Question Words"),
    "More adjectives": ("Topics & situations", "More Adjectives"),
    "Nature and seasons": ("Topics & situations", "Nature & Seasons"),
    "Feelings and emotions": ("Topics & situations", "Feelings & Emotions"),
    "More verbs": ("Topics & situations", "More Verbs"),
    "Conjunctions and connectors": ("Grammar & reference", "Conjunctions & Connectors"),
    "Pronouns and articles": ("Grammar & reference", "Pronouns & Articles"),
    "Health and body": ("Topics & situations", "Health & Body"),
    "Home and objects": ("Topics & situations", "Home & Objects"),
    "Adverbs and function words": ("Grammar & reference", "Adverbs & Function Words"),
}


# The five topics that were really word classes in disguise — "More Verbs",
# "Everyday Verbs", "More Adjectives", "Colors & Adjectives", "Tech Verbs" —
# are retired here. Grouping by word class is now the `word_class` axis, which
# every entry already has, so what these words needed was the thing they never
# had: the subject they belong to.
#
# Most of them turn out to belong to no subject at all. "Everyday Verbs" and
# "More Verbs" together are vara, ha, göra, gå, komma, se, höra — the core of
# the language, which is why no domain ever fitted them. They go to Core Words,
# and pick up a subject only where one genuinely applies.
BUCKET_RETAG = {
    # Everyday verbs — the backbone
    "Är": ("Core Words",),
    "Har": ("Core Words",),
    "Gör": ("Core Words",),
    "Vill": ("Core Words",),
    "Ser": ("Core Words",),
    "Hör": ("Core Words",),
    "Går": ("Core Words", "Places & Directions"),
    "Kommer": ("Core Words", "Places & Directions"),
    "Pratar": ("Core Words", "Greetings & Pleasantries"),
    "Äter": ("Core Words", "Food & Drink"),
    "Dricker": ("Core Words", "Food & Drink"),
    "Sover": ("Core Words", "Everyday Expressions"),
    "Tycker om": ("Core Words", "Opinions & Reactions"),
    # More verbs — also backbone
    "Blir": ("Core Words",),
    "Säger": ("Core Words",),
    "Tar": ("Core Words",),
    "Frågar": ("Core Words",),
    "Försvinner": ("Core Words",),
    "Förstår": ("Core Words", "Clarification"),
    "Köper": ("Core Words", "Shopping & Money"),
    "Lider": ("Core Words", "Health & Body"),
    "Ska": ("Core Words", "Modal Verbs"),
    # Colors are a set worth browsing on their own
    "Röd": ("Colors",),
    "Blå": ("Colors",),
    "Gul": ("Colors",),
    "Grön": ("Colors",),
    "Svart": ("Colors",),
    "Vit": ("Colors",),
    # …the rest of that topic was never about colour
    "Stor": ("Core Words",),
    "Liten": ("Core Words",),
    "Ny": ("Core Words",),
    "Varm": ("Core Words", "Family & Weather Chat"),
    "Kall": ("Core Words", "Family & Weather Chat"),
    "Bra": ("Core Words", "Opinions & Reactions"),
    "Dålig": ("Core Words", "Opinions & Reactions"),
    # More adjectives — general-purpose descriptors
    "Gammal": ("Core Words",),
    "Lång": ("Core Words",),
    "Kort": ("Core Words",),
    "Lätt": ("Core Words",),
    "Stark": ("Core Words",),
    "Svag": ("Core Words",),
    "Vacker": ("Core Words",),
    "Riktig": ("Core Words",),
    "Förra": ("Core Words", "Time & Days"),
    "Snabb": ("Core Words", "Travel & Transport"),
    "Långsam": ("Core Words", "Travel & Transport"),
    "Snäll": ("Core Words", "Family & Weather Chat"),
    "Rolig": ("Core Words", "Opinions & Reactions"),
    "Tråkig": ("Core Words", "Opinions & Reactions"),
    "Svår": ("Core Words", "Opinions & Reactions"),
    "Väldefinierad": ("Tech & Devices",),
    # the single "Tech Verbs" entry belongs with the rest of the tech words
    "Automatiserar": ("Tech & Devices",),
}

# The topics those words used to live in. Nothing may be left in them.
RETIRED_BUCKETS = {
    "Everyday Verbs",
    "More Verbs",
    "More Adjectives",
    "Colors & Adjectives",
    "Tech Verbs",
}

PROFESSION_WORDS = {"Lärare", "Läkare", "Student", "Kock", "Polis"}
TECH_WORDS = {"Automatiserar"}

# Prepositions get function-based topics of their own, so the CSV rows that
# carry them — both the ones filed under "Question words & prepositions" and the
# handful scattered through other categories — are re-homed by (csv category,
# Swedish word) into those topics.
PREPOSITION_REHOME = {
    ("Question words & prepositions", "I"): "Prepositions of Place",
    ("Question words & prepositions", "På"): "Prepositions of Place",
    ("Question words & prepositions", "Under"): "Prepositions of Place",
    ("Question words & prepositions", "Med"): "Other Common Prepositions",
    ("Question words & prepositions", "Till"): "Prepositions of Movement & Direction",
    ("Question words & prepositions", "Från"): "Prepositions of Movement & Direction",
    ("Question words & prepositions", "Om"): "Other Common Prepositions",
    ("Places and directions", "Framför"): "Prepositions of Place",
    ("Places and directions", "Bakom"): "Prepositions of Place",
    ("Adverbs and function words", "Av"): "Other Common Prepositions",
}

# Hand-written V2 inversion anchors: sentence starters that push the verb
# into position 2, grouped by the grammatical role that triggers inversion.
# (sv, pos, en, fn, note, ex, ex_en)
V2_ANCHORS = [
    # position-1: fronted time/place adverbials
    ("Idag", "Adverb", "Today", "position-1", None,
     "Idag jobbar jag hemifrån.", "Today I'm working from home."),
    ("Nu", "Adverb", "Now", "position-1", None,
     "Nu förstår jag.", "Now I understand."),
    ("Sedan", "Adverb", "Then / afterwards", "position-1", None,
     "Sedan gick vi hem.", "Then we went home."),
    ("Igår", "Adverb", "Yesterday", "position-1", None,
     "Igår regnade det hela dagen.", "Yesterday it rained all day."),
    ("Där", "Adverb", "There", "position-1", None,
     "Där bor min syster.", "That's where my sister lives."),
    ("Ofta", "Adverb", "Often", "position-1", None,
     "Ofta äter vi middag klockan sju.", "We often eat dinner at seven."),
    ("Först", "Adverb", "First", "position-1", None,
     "Först läser jag mejlen, sedan börjar jag jobba.",
     "First I read my email, then I start working."),
    ("Varje dag", "Adverbial phrase", "Every day", "position-1", None,
     "Varje dag tar jag bussen till jobbet.", "Every day I take the bus to work."),
    ("På helgen", "Adverbial phrase", "On the weekend", "position-1", None,
     "På helgen sover vi längre.", "On the weekend we sleep in."),
    ("Plötsligt", "Adverb", "Suddenly", "position-1", None,
     "Plötsligt slocknade lampan.", "Suddenly the lamp went out."),
    # contrast: adverbial connectors (not coordinating conjunctions like "men")
    ("Dock", "Adverb", "However", "contrast", None,
     "Han var trött. Dock fortsatte han att jobba.",
     "He was tired. He kept working, however."),
    ("Ändå", "Adverb", "Still / nevertheless", "contrast", None,
     "Det regnade. Ändå gick vi ut.", "It was raining. We went out anyway."),
    ("Trots det", "Adverbial phrase", "Despite that", "contrast", None,
     "Trots det stannade hon hemma.", "Despite that, she stayed home."),
    ("Däremot", "Adverb", "On the other hand / by contrast", "contrast", None,
     "Jag gillar te. Däremot dricker jag aldrig kaffe.",
     "I like tea. Coffee, on the other hand, I never drink."),
    ("Annars", "Adverb", "Otherwise", "contrast", None,
     "Skynda dig, annars missar vi tåget.", "Hurry up, otherwise we'll miss the train."),
    ("Därför", "Adverb", "Therefore / that's why", "contrast",
     "Not the same as 'därför att' (because), which introduces a subordinate clause.",
     "Det var sent. Därför tog vi en taxi.", "It was late. That's why we took a taxi."),
    # subordinating: the whole subordinate clause occupies position 1
    ("Att", "Subjunction", "That", "subordinating", "Fronted subordinate clause with 'att'.",
     "Att han kommer vet jag.", "That he's coming, I know."),
    ("Om", "Subjunction", "If", "subordinating", None,
     "Om det regnar stannar vi hemma.", "If it rains we'll stay home."),
    ("När", "Subjunction", "When", "subordinating", None,
     "När jag kommer hem lagar jag mat.", "When I get home I cook."),
    ("Eftersom", "Subjunction", "Because", "subordinating", None,
     "Eftersom jag är trött går jag och lägger mig.",
     "Because I'm tired I'm going to bed."),
    ("Fastän", "Subjunction", "Although", "subordinating", None,
     "Fastän det var kallt badade vi.", "Although it was cold, we went swimming."),
    ("Innan", "Subjunction", "Before", "subordinating",
     "'Innan' introduces a clause; the preposition 'före' takes a noun.",
     "Innan jag åker ringer jag dig.", "Before I leave I'll call you."),
    ("Medan", "Subjunction", "While", "subordinating", None,
     "Medan du lagar mat dukar jag.", "While you cook I'll set the table."),
    ("Även om", "Subjunction", "Even if / even though", "subordinating", None,
     "Även om det snöar åker vi.", "Even if it snows, we're going."),
    ("Så fort", "Subjunction", "As soon as", "subordinating", None,
     "Så fort mötet är slut ringer jag.", "As soon as the meeting is over I'll call."),
    ("Trots att", "Subjunction", "Despite the fact that", "subordinating", None,
     "Trots att han var sjuk kom han till jobbet.",
     "Even though he was ill, he came to work."),
    # modal: sentence adverbs
    ("Kanske", "Modal adverb", "Maybe", "modal",
     "Only triggers inversion when fronted; 'Han kommer kanske imorgon' does not invert.",
     "Kanske kommer han imorgon.", "Maybe he'll come tomorrow."),
    ("Nog", "Modal adverb", "Probably", "modal", None,
     "Nog blir det bra.", "It'll probably turn out fine."),
    ("Tyvärr", "Modal adverb", "Unfortunately", "modal", None,
     "Tyvärr kan jag inte komma.", "Unfortunately I can't come."),
    ("Säkert", "Modal adverb", "Surely / no doubt", "modal", None,
     "Säkert har hon glömt mötet.", "She's surely forgotten the meeting."),
    ("Naturligtvis", "Modal adverb", "Of course", "modal", None,
     "Naturligtvis hjälper jag dig.", "Of course I'll help you."),
    ("Förhoppningsvis", "Modal adverb", "Hopefully", "modal", None,
     "Förhoppningsvis blir vi klara i tid.", "Hopefully we'll finish in time."),
    ("Faktiskt", "Modal adverb", "Actually", "modal", None,
     "Faktiskt tyckte jag om filmen.", "I actually liked the film."),
]

# Word-order rules and modal verbs: the scaffolding around the V2 anchors.
# (category, sv, pos, en, note, ex, ex_en)
GRAMMAR_EXTRA = [
    ("Word Order Rules", "Rak ordföljd", "Word-order rule", "Straight word order (subject first)",
     "The default main-clause pattern: subject, then the finite verb.",
     "Jag dricker kaffe på morgonen.", "I drink coffee in the morning."),
    ("Word Order Rules", "Omvänd ordföljd", "Word-order rule", "Inverted word order (verb before subject)",
     "Triggered whenever something other than the subject takes position 1.",
     "På morgonen dricker jag kaffe.", "In the morning I drink coffee."),
    ("Word Order Rules", "Verbet på plats 2", "Word-order rule", "The finite verb stays in position 2",
     "Position 1 holds exactly one element — a subject, an adverbial, or a whole subordinate clause.",
     "Imorgon börjar kursen.", "Tomorrow the course starts."),
    ("Word Order Rules", "BIFF-regeln", "Word-order rule", "The BIFF rule: 'inte' goes before the verb in subordinate clauses",
     "Bisats = Inte Före Finita verbet.",
     "Han säger att han inte kommer idag.", "He says that he isn't coming today."),
    ("Word Order Rules", "Inte i huvudsats", "Word-order rule", "'Inte' goes after the finite verb in main clauses",
     "The mirror image of the BIFF rule.",
     "Vi åker inte till stranden idag.", "We're not going to the beach today."),
    ("Word Order Rules", "Bisats utan inversion", "Word-order rule", "Subordinate clauses never invert",
     "After 'att', 'om', 'när' and friends the subject comes first, even after a question word.",
     "Vet du när tåget går?", "Do you know when the train leaves?"),
    ("Modal Verbs", "Kan", "Verb (modal)", "Can / to be able to",
     "Infinitive: kunna • Past: kunde • Supine: kunnat. Modals take a bare infinitive — 'kan simma', never 'kan att simma'.",
     "Jag kan simma.", "I can swim."),
    ("Modal Verbs", "Måste", "Verb (modal)", "Must / to have to",
     "Same form in present and past: måste • Supine: måst",
     "Jag måste gå nu.", "I have to go now."),
    ("Modal Verbs", "Får", "Verb (modal)", "May / to be allowed to",
     "Infinitive: få • Past: fick • Supine: fått",
     "Får jag sitta här?", "May I sit here?"),
    ("Modal Verbs", "Bör", "Verb (modal)", "Ought to / should",
     "Infinitive: böra • Past: borde • Supine: bort",
     "Du bör vila lite.", "You ought to rest a bit."),
    ("Modal Verbs", "Skulle", "Verb (modal)", "Would",
     "Past tense of 'ska'; used for politeness and hypotheticals.",
     "Jag skulle gärna vilja komma.", "I would really like to come."),
    ("Modal Verbs", "Brukar", "Verb", "To usually do something",
     "Infinitive: bruka • Past: brukade • Supine: brukat. No English one-word equivalent.",
     "Jag brukar springa på morgonen.", "I usually run in the morning."),
    ("Modal Verbs", "Behöver", "Verb", "To need to",
     "Infinitive: behöva • Past: behövde • Supine: behövt",
     "Du behöver inte vänta på mig.", "You don't need to wait for me."),
]

# ---------------------------------------------------------------------------
# Questions & prepositions topics
# ---------------------------------------------------------------------------

# The CSV covers vad/var/när/varför/hur/vem/vilken/hur mycket/hur många; these
# are the rest of the question inventory.
# (category, sv, pos, en, note, ex, ex_en)
QUESTIONS_PREPOSITIONS = [
    ("Question Words", "Vems", "Pronoun", "Whose",
     "Genitive of 'vem'; the noun after it takes no article.",
     "Vems jacka är det här?", "Whose jacket is this?"),
    ("Question Words", "Vart", "Adverb", "Where to",
     "'Var' asks about location, 'vart' about destination.",
     "Vart ska du imorgon?", "Where are you going tomorrow?"),
    ("Question Words", "Varifrån", "Adverb", "Where from", None,
     "Varifrån kommer du?", "Where do you come from?"),
    ("Question Words", "Hur dags", "Phrase", "At what time",
     "Asks for a clock time; 'när' asks more generally.",
     "Hur dags börjar mötet?", "What time does the meeting start?"),
    ("Question Words", "Hur länge", "Phrase", "How long (duration)", None,
     "Hur länge har du bott i Sverige?", "How long have you lived in Sweden?"),
    ("Question Words", "Hur långt", "Phrase", "How far (distance)",
     "'Hur långt' is distance, 'hur länge' is time.",
     "Hur långt är det kvar?", "How much further is it?"),
    ("Question Words", "Hur ofta", "Phrase", "How often", None,
     "Hur ofta tränar du?", "How often do you work out?"),
    ("Question Words", "Hur gammal", "Phrase", "How old",
     "Neuter: hur gammalt • Plural: hur gamla",
     "Hur gammal är din bror?", "How old is your brother?"),
    ("Question Words", "Vad för slags", "Phrase", "What kind of", None,
     "Vad för slags musik gillar du?", "What kind of music do you like?"),
    ("Question Words", "Var någonstans", "Phrase", "Whereabouts",
     "Softer and more conversational than a bare 'var'.",
     "Var någonstans bor du?", "Whereabouts do you live?"),
    ("Question Patterns", "Ja/nej-fråga: verbet först", "Pattern", "Yes/no question: verb first",
     "Statement 'Du bor i Lund' becomes the question 'Bor du i Lund?'.",
     "Bor du i Lund?", "Do you live in Lund?"),
    ("Question Patterns", "Frågeord + verb + subjekt", "Pattern", "Question word + verb + subject",
     "The question word fills position 1, so the verb still lands second.",
     "När slutar du jobbet?", "When do you finish work?"),
    ("Question Patterns", "Negerad fråga", "Pattern", "Negated question",
     "'Inte' comes after the subject in a question.",
     "Kommer du inte imorgon?", "Aren't you coming tomorrow?"),
    ("Question Patterns", "…, eller hur?", "Tag question", "…, right? / isn't it?", None,
     "Du är från Brasilien, eller hur?", "You're from Brazil, right?"),
    ("Question Patterns", "…, va?", "Tag question", "…, huh? (informal)", None,
     "Det var kallt idag, va?", "It was cold today, wasn't it?"),
    ("Question Patterns", "Indirekt fråga med 'om'", "Pattern", "Indirect yes/no question with 'om'",
     "The subordinate clause keeps subject-first order: 'om du kommer', not 'om kommer du'.",
     "Jag undrar om du kommer imorgon.", "I wonder whether you're coming tomorrow."),
    ("Question Patterns", "Vet du var …?", "Pattern", "Do you know where …?",
     "Indirect question: no inversion after the question word — 'var tåget går', not 'var går tåget'.",
     "Vet du var tåget går?", "Do you know where the train leaves from?"),
    ("Question Patterns", "Kan du …?", "Phrase", "Can you …? (request)", None,
     "Kan du hjälpa mig med det här?", "Can you help me with this?"),
    ("Question Patterns", "Skulle du kunna …?", "Phrase", "Could you …? (extra polite)", None,
     "Skulle du kunna öppna fönstret?", "Could you open the window?"),
    ("Question Patterns", "Får jag …?", "Phrase", "May I …?", None,
     "Får jag ställa en fråga?", "May I ask a question?"),
    ("Question Patterns", "Vad tycker du om …?", "Phrase", "What do you think of …?", None,
     "Vad tycker du om den nya chefen?", "What do you think of the new boss?"),
    ("Question Patterns", "Hur kommer det sig att …?", "Phrase", "How come …?",
     "Followed by subordinate word order.",
     "Hur kommer det sig att du flyttade hit?", "How come you moved here?"),
    ("Question Patterns", "Är det någon som …?", "Phrase", "Is there anyone who …?", None,
     "Är det någon som vet svaret?", "Is there anyone who knows the answer?"),
    ("Question Patterns", "Vad menar du med det?", "Phrase", "What do you mean by that?", None,
     "Förlåt, vad menar du med det?", "Sorry, what do you mean by that?"),
    ("Prepositions of Place", "Över", "Preposition", "Over / above",
     "Can also mean 'across': 'över gatan'.",
     "Lampan hänger över bordet.", "The lamp hangs above the table."),
    ("Prepositions of Place", "Bredvid", "Preposition", "Next to / beside", None,
     "Han sitter bredvid mig.", "He is sitting next to me."),
    ("Prepositions of Place", "Mellan", "Preposition", "Between", None,
     "Affären ligger mellan banken och kyrkan.", "The shop is between the bank and the church."),
    ("Prepositions of Place", "Hos", "Preposition", "At (someone's place)",
     "Used with people, not places: 'hos Anna', 'hos läkaren'.",
     "Vi sover hos mina föräldrar.", "We're sleeping at my parents' place."),
    ("Prepositions of Place", "Vid", "Preposition", "By / at (right next to)", None,
     "Vi möts vid ingången.", "We'll meet by the entrance."),
    ("Prepositions of Place", "Inne i", "Preposition", "Inside", None,
     "Nycklarna ligger inne i väskan.", "The keys are inside the bag."),
    ("Prepositions of Place", "Utanför", "Preposition", "Outside of", None,
     "Bilen står utanför huset.", "The car is parked outside the house."),
    ("Prepositions of Place", "Ovanför", "Preposition", "Above",
     "'Ovanför' is strictly higher up; 'över' can also mean across.",
     "Hyllan sitter ovanför skrivbordet.", "The shelf is above the desk."),
    ("Prepositions of Place", "Nedanför", "Preposition", "Below", None,
     "Sjön ligger nedanför berget.", "The lake is below the mountain."),
    ("Prepositions of Place", "Bland", "Preposition", "Among", None,
     "Han stod bland publiken.", "He stood among the audience."),
    ("Prepositions of Place", "Mitt emot", "Preposition", "Opposite / across from", None,
     "Apoteket ligger mitt emot stationen.", "The pharmacy is opposite the station."),
    ("Prepositions of Place", "Omkring", "Preposition", "Around", None,
     "Vi satt omkring bordet.", "We sat around the table."),
    ("Prepositions of Time", "På måndag", "Time expression", "On Monday",
     "Days and dates take 'på'.",
     "På måndag börjar kursen.", "On Monday the course starts."),
    ("Prepositions of Time", "I januari", "Time expression", "In January",
     "Months, years and seasons take 'i'.",
     "I januari åker vi till fjällen.", "In January we're going to the mountains."),
    ("Prepositions of Time", "På morgonen", "Time expression", "In the morning",
     "Parts of the day take 'på': på morgonen, på kvällen, på natten.",
     "På morgonen dricker jag kaffe.", "In the morning I drink coffee."),
    ("Prepositions of Time", "Om tre dagar", "Time expression", "In three days (from now)",
     "'Om' measures time until something happens.",
     "Vi ses om tre dagar.", "We'll see each other in three days."),
    ("Prepositions of Time", "På två timmar", "Time expression", "In two hours (time it took)",
     "'På' measures how long something took to complete.",
     "Jag gjorde klart det på två timmar.", "I finished it in two hours."),
    ("Prepositions of Time", "I två timmar", "Time expression", "For two hours (duration)",
     "'I' measures how long something went on.",
     "Vi väntade i två timmar.", "We waited for two hours."),
    ("Prepositions of Time", "För tre år sedan", "Time expression", "Three years ago",
     "Fixed frame: för + time + sedan.",
     "Jag flyttade hit för tre år sedan.", "I moved here three years ago."),
    ("Prepositions of Time", "Sedan", "Preposition", "Since", None,
     "Jag har bott här sedan 2019.", "I have lived here since 2019."),
    ("Prepositions of Time", "Före", "Preposition", "Before",
     "'Före' takes a noun; the subjunction 'innan' introduces a clause.",
     "Vi äter före filmen.", "We eat before the film."),
    ("Prepositions of Time", "Efter", "Preposition", "After", None,
     "Vi tar en promenad efter middagen.", "We take a walk after dinner."),
    ("Prepositions of Time", "Under sommaren", "Time expression", "During the summer",
     "'Under' covers a stretch of time as well as a position underneath something.",
     "Under sommaren jobbar jag mindre.", "During the summer I work less."),
    ("Prepositions of Time", "Mellan tre och fyra", "Time expression", "Between three and four", None,
     "Jag är ledig mellan tre och fyra.", "I'm free between three and four."),
    ("Prepositions of Time", "Från … till …", "Time expression", "From … to …", None,
     "Butiken är öppen från nio till sex.", "The shop is open from nine to six."),
    ("Prepositions of Time", "Inom", "Preposition", "Within", None,
     "Vi svarar inom 24 timmar.", "We reply within 24 hours."),
    ("Prepositions of Time", "I helgen", "Time expression", "This weekend / last weekend",
     "Context decides whether it points forward or back.",
     "I helgen ska vi måla köket.", "This weekend we're going to paint the kitchen."),
    ("Prepositions of Movement & Direction", "Mot", "Preposition", "Towards",
     "Also means 'against': 'spela mot ett annat lag'.",
     "Vi gick mot stationen.", "We walked towards the station."),
    ("Prepositions of Movement & Direction", "Genom", "Preposition", "Through", None,
     "Vi cyklade genom parken.", "We cycled through the park."),
    ("Prepositions of Movement & Direction", "Förbi", "Preposition", "Past", None,
     "Bussen körde förbi hållplatsen.", "The bus drove past the stop."),
    ("Prepositions of Movement & Direction", "In i", "Preposition", "Into", None,
     "Katten sprang in i köket.", "The cat ran into the kitchen."),
    ("Prepositions of Movement & Direction", "Ut ur", "Preposition", "Out of", None,
     "Han gick ut ur rummet.", "He walked out of the room."),
    ("Prepositions of Movement & Direction", "Upp på", "Preposition", "Up onto", None,
     "Barnet klättrade upp på stolen.", "The child climbed up onto the chair."),
    ("Prepositions of Movement & Direction", "Ner i", "Preposition", "Down into", None,
     "Hon lade nycklarna ner i väskan.", "She put the keys down into the bag."),
    ("Prepositions of Movement & Direction", "Tvärs över", "Preposition", "Straight across", None,
     "Vi gick tvärs över torget.", "We walked straight across the square."),
    ("Prepositions of Movement & Direction", "Längs", "Preposition", "Along", None,
     "Vi promenerade längs stranden.", "We walked along the beach."),
    ("Prepositions of Movement & Direction", "Runt", "Preposition", "Around", None,
     "Vi åkte runt sjön.", "We drove around the lake."),
    ("Prepositions of Movement & Direction", "Hem / hemma", "Adverb pair", "(To) home / at home",
     "Direction takes 'hem', location takes 'hemma' — the same split as vart/var.",
     "Jag åker hem nu, sedan är jag hemma hela kvällen.",
     "I'm going home now, then I'll be at home all evening."),
    ("Other Common Prepositions", "Utan", "Preposition", "Without", None,
     "Jag dricker kaffe utan mjölk.", "I drink coffee without milk."),
    ("Other Common Prepositions", "För", "Preposition", "For",
     "Also means 'too' in front of an adjective: 'för dyr'.",
     "Den här boken är för dig.", "This book is for you."),
    ("Other Common Prepositions", "Som", "Preposition", "As / like", None,
     "Han jobbar som lärare.", "He works as a teacher."),
    ("Other Common Prepositions", "Enligt", "Preposition", "According to", None,
     "Enligt kartan är vi nästan framme.", "According to the map we're almost there."),
    ("Other Common Prepositions", "Trots", "Preposition", "Despite",
     "With a clause, use 'trots att'.",
     "Vi gick ut trots regnet.", "We went out despite the rain."),
    ("Other Common Prepositions", "Tack vare", "Preposition", "Thanks to",
     "Positive cause; use 'på grund av' for a neutral or negative one.",
     "Tack vare din hjälp blev jag klar i tid.", "Thanks to your help I finished on time."),
    ("Other Common Prepositions", "På grund av", "Preposition", "Because of",
     "Abbreviated 'p.g.a.' in writing.",
     "Tåget är försenat på grund av vädret.", "The train is delayed because of the weather."),
    ("Other Common Prepositions", "Istället för", "Preposition", "Instead of", None,
     "Jag tog tåget istället för bilen.", "I took the train instead of the car."),
    ("Other Common Prepositions", "Förutom", "Preposition", "Except / besides", None,
     "Alla kom förutom Erik.", "Everyone came except Erik."),
    ("Other Common Prepositions", "Åt", "Preposition", "For (on someone's behalf)",
     "'Åt' is for someone's benefit; 'till' marks a recipient.",
     "Kan du göra det åt mig?", "Can you do it for me?"),
    ("Other Common Prepositions", "Angående", "Preposition", "Regarding", None,
     "Jag mejlar angående mötet.", "I'm emailing regarding the meeting."),
    ("Verbs with Fixed Prepositions", "Titta på", "Verb + preposition", "To look at / to watch", None,
     "Vi tittar på en film ikväll.", "We're watching a film tonight."),
    ("Verbs with Fixed Prepositions", "Lyssna på", "Verb + preposition", "To listen to", None,
     "Jag lyssnar på poddar när jag springer.", "I listen to podcasts when I run."),
    ("Verbs with Fixed Prepositions", "Vänta på", "Verb + preposition", "To wait for", None,
     "Vi väntar på bussen.", "We're waiting for the bus."),
    ("Verbs with Fixed Prepositions", "Tänka på", "Verb + preposition", "To think about",
     "'Tänka på' is to have in mind; 'tänka om' is to reconsider.",
     "Jag tänker på min familj.", "I'm thinking about my family."),
    ("Verbs with Fixed Prepositions", "Prata om", "Verb + preposition", "To talk about", None,
     "Vi pratade om semestern.", "We talked about the holiday."),
    ("Verbs with Fixed Prepositions", "Bero på", "Verb + preposition", "To depend on", None,
     "Det beror på vädret.", "It depends on the weather."),
    ("Verbs with Fixed Prepositions", "Längta efter", "Verb + preposition", "To long for", None,
     "Jag längtar efter sommaren.", "I'm longing for summer."),
    ("Verbs with Fixed Prepositions", "Fråga efter", "Verb + preposition", "To ask after / for", None,
     "Hon frågade efter dig.", "She asked after you."),
    ("Verbs with Fixed Prepositions", "Vara intresserad av", "Verb + preposition", "To be interested in", None,
     "Jag är intresserad av historia.", "I'm interested in history."),
    ("Verbs with Fixed Prepositions", "Vara rädd för", "Verb + preposition", "To be afraid of", None,
     "Han är rädd för hundar.", "He is afraid of dogs."),
    ("Verbs with Fixed Prepositions", "Vara bra på", "Verb + preposition", "To be good at", None,
     "Hon är bra på matte.", "She is good at maths."),
    ("Verbs with Fixed Prepositions", "Tacka för", "Verb + preposition", "To thank for", None,
     "Jag vill tacka för hjälpen.", "I want to thank you for the help."),
    ("Verbs with Fixed Prepositions", "Börja med", "Verb + preposition", "To start with", None,
     "Vi börjar med en kort presentation.", "We'll start with a short presentation."),
    ("Verbs with Fixed Prepositions", "Hjälpa till med", "Verb + preposition", "To help out with", None,
     "Kan du hjälpa till med disken?", "Can you help out with the dishes?"),
    ("Verbs with Fixed Prepositions", "Åka till", "Verb + preposition", "To travel to", None,
     "Vi åker till Norge i sommar.", "We're going to Norway this summer."),
    ("Verbs with Fixed Prepositions", "Bjuda på", "Verb + preposition", "To treat someone to", None,
     "Jag bjuder på fika.", "The coffee's on me."),
    ("Verbs with Fixed Prepositions", "Skratta åt", "Verb + preposition", "To laugh at", None,
     "Alla skrattade åt skämtet.", "Everyone laughed at the joke."),
    ("Verbs with Fixed Prepositions", "Passa på", "Verb + preposition", "To seize the chance", None,
     "Passa på att fråga medan hon är här.", "Take the chance to ask while she's here."),
]

# Hand-written Workplace & Tech content: the old CSV barely touched this
# domain (just five professions + one stray verb), so these are fresh.
# (category, sv, pos, en, note, ex, ex_en)
WORKPLACE_TECH_EXTRA = [
    ("Workplace Basics", "Jobb", "Noun (ett)", "Job / work",
     "Definite: jobbet • Plural: jobb • Def. plural: jobben",
     "Jag har ett nytt jobb.", "I have a new job."),
    ("Workplace Basics", "Möte", "Noun (ett)", "Meeting",
     "Definite: mötet • Plural: möten • Def. plural: mötena",
     "Vi har ett möte klockan tio.", "We have a meeting at ten."),
    ("Workplace Basics", "Kollega", "Noun (en)", "Colleague",
     "Definite: kollegan • Plural: kollegor • Def. plural: kollegorna",
     "Min kollega heter Anna.", "My colleague is called Anna."),
    ("Workplace Basics", "Chef", "Noun (en)", "Boss / manager",
     "Definite: chefen • Plural: chefer • Def. plural: cheferna",
     "Chefen är på semester.", "The boss is on holiday."),
    ("Workplace Basics", "Tidsfrist", "Noun (en)", "Deadline",
     "Definite: tidsfristen • Plural: tidsfrister • Def. plural: tidsfristerna",
     "Vi har en tidsfrist imorgon.", "We have a deadline tomorrow."),
    ("Workplace Basics", "Distansarbete", "Noun (ett)", "Remote work",
     "Definite: distansarbetet (uncountable)",
     "Jag jobbar med distansarbete idag.", "I'm working remotely today."),
    ("Workplace Basics", "Lön", "Noun (en)", "Salary / pay",
     "Definite: lönen • Plural: löner • Def. plural: lönerna",
     "Lönen betalas ut den 25:e.", "The salary is paid out on the 25th."),
    ("Workplace Basics", "Semester", "Noun (en)", "Holiday / vacation",
     "Definite: semestern • Plural: semestrar • Def. plural: semestrarna",
     "Jag har semester i juli.", "I'm on holiday in July."),
    ("Workplace Basics", "Anställning", "Noun (en)", "Employment / position",
     "Definite: anställningen • Plural: anställningar • Def. plural: anställningarna",
     "Hon fick en fast anställning.", "She got a permanent position."),
    ("Workplace Basics", "Ansöka", "Verb", "To apply",
     "Infinitive: ansöka • Past: ansökte • Supine: ansökt. Takes 'om': ansöka om ett jobb.",
     "Jag ska ansöka om tjänsten.", "I'm going to apply for the position."),
    ("Workplace Basics", "Övertid", "Noun (en)", "Overtime",
     "Definite: övertiden (uncountable)",
     "Vi jobbade övertid hela veckan.", "We worked overtime all week."),
    ("Workplace Basics", "Sjukanmäla sig", "Verb phrase", "To call in sick",
     "Infinitive: sjukanmäla sig • Past: sjukanmälde sig • Supine: sjukanmält sig",
     "Han sjukanmälde sig på måndagen.", "He called in sick on Monday."),
    ("Workplace Basics", "Avdelning", "Noun (en)", "Department",
     "Definite: avdelningen • Plural: avdelningar • Def. plural: avdelningarna",
     "Jag jobbar på ekonomiavdelningen.", "I work in the finance department."),
    ("Workplace Basics", "Projekt", "Noun (ett)", "Project",
     "Definite: projektet • Plural: projekt • Def. plural: projekten",
     "Projektet är försenat.", "The project is delayed."),
    ("Workplace Basics", "Fika", "Noun (en) / Verb", "Coffee break (and to take one)",
     "Both a noun and a verb: 'ta en fika' or 'att fika'.",
     "Vi fikar klockan tre varje dag.", "We take a coffee break at three every day."),
    ("Meetings & Communication", "Dagordning", "Noun (en)", "Agenda",
     "Definite: dagordningen • Plural: dagordningar • Def. plural: dagordningarna",
     "Vad står på dagordningen?", "What's on the agenda?"),
    ("Meetings & Communication", "Boka in", "Verb", "To book / to schedule",
     "Infinitive: boka in • Past: bokade in • Supine: bokat in",
     "Kan vi boka in ett möte på torsdag?", "Can we schedule a meeting on Thursday?"),
    ("Meetings & Communication", "Skjuta upp", "Verb", "To postpone",
     "Infinitive: skjuta upp • Past: sköt upp • Supine: skjutit upp",
     "Vi måste skjuta upp mötet.", "We have to postpone the meeting."),
    ("Meetings & Communication", "Stämma av", "Verb", "To check in / to sync up",
     "Infinitive: stämma av • Past: stämde av • Supine: stämt av",
     "Vi stämmer av på fredag.", "We'll sync up on Friday."),
    ("Meetings & Communication", "Återkoppla", "Verb", "To get back to someone / to follow up",
     "Infinitive: återkoppla • Past: återkopplade • Supine: återkopplat",
     "Jag återkopplar imorgon.", "I'll get back to you tomorrow."),
    ("Meetings & Communication", "Mejl", "Noun (ett)", "Email",
     "Definite: mejlet • Plural: mejl • Def. plural: mejlen",
     "Jag skickade ett mejl igår.", "I sent an email yesterday."),
    ("Meetings & Communication", "Sammanfattning", "Noun (en)", "Summary",
     "Definite: sammanfattningen • Plural: sammanfattningar • Def. plural: sammanfattningarna",
     "Kan du skicka en sammanfattning av mötet?", "Can you send a summary of the meeting?"),
    ("Meetings & Communication", "Vi är kort om tid.", "Phrase", "We're short on time.", None,
     "Vi är kort om tid, så vi tar det snabbt.", "We're short on time, so let's be quick."),
    ("Meetings & Communication", "Hur ligger vi till?", "Phrase", "Where do we stand?", None,
     "Hur ligger vi till med projektet?", "Where do we stand on the project?"),
    ("Tech & Devices", "Dator", "Noun (en)", "Computer",
     "Definite: datorn • Plural: datorer • Def. plural: datorerna",
     "Min dator är trasig.", "My computer is broken."),
    ("Tech & Devices", "Skärm", "Noun (en)", "Screen / monitor",
     "Definite: skärmen • Plural: skärmar • Def. plural: skärmarna",
     "Skärmen är för liten.", "The screen is too small."),
    ("Tech & Devices", "Fil", "Noun (en)", "File",
     "Definite: filen • Plural: filer • Def. plural: filerna",
     "Kan du skicka filen?", "Can you send the file?"),
    ("Tech & Devices", "Lösenord", "Noun (ett)", "Password",
     "Definite: lösenordet • Plural: lösenord • Def. plural: lösenorden",
     "Jag glömde mitt lösenord.", "I forgot my password."),
    ("Tech & Devices", "Uppdatera", "Verb", "To update",
     "Infinitive: uppdatera • Past: uppdaterade • Supine: uppdaterat",
     "Jag måste uppdatera programmet.", "I have to update the program."),
    ("Tech & Devices", "Programmera", "Verb", "To program",
     "Infinitive: programmera • Past: programmerade • Supine: programmerat",
     "Han programmerar varje dag.", "He programs every day."),
    ("Tech & Devices", "Kod", "Noun (en)", "Code",
     "Definite: koden • Plural: koder • Def. plural: koderna",
     "Koden är svår att läsa.", "The code is hard to read."),
    ("Tech & Devices", "Server", "Noun (en)", "Server",
     "Definite: servern • Plural: servrar • Def. plural: servrarna",
     "Servern är nere just nu.", "The server is down right now."),
    ("Tech & Devices", "Molnet", "Noun (ett)", "The cloud",
     "Almost always used in the definite: 'i molnet'.",
     "Vi sparar allt i molnet.", "We save everything in the cloud."),
    ("Tech & Devices", "Databas", "Noun (en)", "Database",
     "Definite: databasen • Plural: databaser • Def. plural: databaserna",
     "Databasen behöver en säkerhetskopia.", "The database needs a backup."),
    ("Tech & Devices", "Säkerhetskopia", "Noun (en)", "Backup",
     "Definite: säkerhetskopian • Plural: säkerhetskopior • Def. plural: säkerhetskopiorna",
     "Vi tar en säkerhetskopia varje natt.", "We take a backup every night."),
    ("Tech & Devices", "Fel", "Noun (ett)", "Error / fault",
     "Definite: felet • Plural: fel • Def. plural: felen",
     "Det blev ett fel i programmet.", "There was an error in the program."),
    ("Tech & Devices", "Felsöka", "Verb", "To troubleshoot / to debug",
     "Infinitive: felsöka • Past: felsökte • Supine: felsökt",
     "Jag felsöker nätverket.", "I'm troubleshooting the network."),
    ("Tech & Devices", "Installera", "Verb", "To install",
     "Infinitive: installera • Past: installerade • Supine: installerat",
     "Jag måste installera om systemet.", "I have to reinstall the system."),
    ("Tech & Devices", "Ladda ner", "Verb", "To download",
     "Infinitive: ladda ner • Past: laddade ner • Supine: laddat ner",
     "Ladda ner filen först.", "Download the file first."),
    ("Tech & Devices", "Starta om", "Verb", "To restart",
     "Infinitive: starta om • Past: startade om • Supine: startat om",
     "Prova att starta om datorn.", "Try restarting the computer."),
    ("Tech & Devices", "Nätverk", "Noun (ett)", "Network",
     "Definite: nätverket • Plural: nätverk • Def. plural: nätverken",
     "Nätverket är långsamt idag.", "The network is slow today."),
    ("Tech & Devices", "Tangentbord", "Noun (ett)", "Keyboard",
     "Definite: tangentbordet • Plural: tangentbord • Def. plural: tangentborden",
     "Mitt tangentbord är smutsigt.", "My keyboard is dirty."),
    ("Professions", "Ingenjör", "Noun (en)", "Engineer",
     "Definite: ingenjören • Plural: ingenjörer • Def. plural: ingenjörerna. "
     "Professions take no article after 'vara': 'Han är ingenjör'.",
     "Han är ingenjör på ett stort företag.", "He is an engineer at a big company."),
    ("Professions", "Utvecklare", "Noun (en)", "Developer",
     "Definite: utvecklaren • Plural: utvecklare • Def. plural: utvecklarna",
     "Vi söker en utvecklare till teamet.", "We're looking for a developer for the team."),
    ("Professions", "Sjuksköterska", "Noun (en)", "Nurse",
     "Definite: sjuksköterskan • Plural: sjuksköterskor • Def. plural: sjuksköterskorna",
     "Min syster är sjuksköterska.", "My sister is a nurse."),
    ("Professions", "Snickare", "Noun (en)", "Carpenter",
     "Definite: snickaren • Plural: snickare • Def. plural: snickarna",
     "Vi anlitade en snickare.", "We hired a carpenter."),
    ("Professions", "Säljare", "Noun (en)", "Salesperson",
     "Definite: säljaren • Plural: säljare • Def. plural: säljarna",
     "Säljaren ringde igår.", "The salesperson called yesterday."),
]

# Hand-written everyday-life expressions: small phrases for talking about
# routine, daily rhythm, and how things are going.
# (category, sv, pos, en, note, ex, ex_en)
HOME_DAILY_LIFE_EXTRA = [
    ("Everyday Expressions", "Hur går det?", "Phrase", "How's it going?", None,
     "Hej! Hur går det för dig idag?", "Hi! How's it going for you today?"),
    ("Everyday Expressions", "Som vanligt", "Phrase", "As usual", None,
     "Helgen var som vanligt, lugn och skön.", "The weekend was as usual, calm and nice."),
    ("Everyday Expressions", "Ha en bra dag!", "Phrase", "Have a good day!", None,
     "Vi ses imorgon. Ha en bra dag!", "See you tomorrow. Have a good day!"),
    ("Everyday Expressions", "Jag har mycket att göra.", "Phrase", "I have a lot to do.", None,
     "Jag kan inte prata länge, jag har mycket att göra.",
     "I can't talk long, I have a lot to do."),
    ("Everyday Expressions", "Det är lugnt.", "Phrase", "It's fine / no worries.",
     "Literally 'it's calm'; used the way English uses 'no worries'.",
     "Förlåt att jag är sen! — Det är lugnt.", "Sorry I'm late! — No worries."),
    ("Everyday Expressions", "Ta det lugnt.", "Phrase", "Take it easy.", None,
     "Du behöver inte stressa, ta det lugnt.", "You don't need to rush, take it easy."),
    ("Everyday Expressions", "Vardag", "Noun (en)", "Weekday / everyday life",
     "Definite: vardagen • Plural: vardagar • Def. plural: vardagarna",
     "På vardagar går jag upp klockan sex.", "On weekdays I get up at six."),
    ("Everyday Expressions", "Rutin", "Noun (en)", "Routine",
     "Definite: rutinen • Plural: rutiner • Def. plural: rutinerna",
     "Jag har en fast morgonrutin.", "I have a fixed morning routine."),
    ("Everyday Expressions", "Sköta sig själv", "Phrase", "To manage on one's own", None,
     "Nu för tiden sköter han sig själv.", "These days he manages on his own."),
    ("Shopping & Money", "Handla", "Verb", "To shop / to buy groceries",
     "Infinitive: handla • Past: handlade • Supine: handlat",
     "Jag handlar mat på vägen hem.", "I buy groceries on the way home."),
    ("Shopping & Money", "Kassa", "Noun (en)", "Checkout / till",
     "Definite: kassan • Plural: kassor • Def. plural: kassorna",
     "Det är kö vid kassan.", "There's a queue at the checkout."),
    ("Shopping & Money", "Kvitto", "Noun (ett)", "Receipt",
     "Definite: kvittot • Plural: kvitton • Def. plural: kvittona",
     "Kan jag få ett kvitto, tack?", "Could I have a receipt, please?"),
    ("Shopping & Money", "Rea", "Noun (en)", "Sale",
     "Definite: rean • Plural: reor • Def. plural: reorna",
     "Jackan var på rea.", "The jacket was on sale."),
    ("Shopping & Money", "Betala", "Verb", "To pay",
     "Infinitive: betala • Past: betalade • Supine: betalat",
     "Kan jag betala med kort?", "Can I pay by card?"),
    ("Shopping & Money", "Kosta", "Verb", "To cost",
     "Infinitive: kosta • Past: kostade • Supine: kostat",
     "Hur mycket kostar biljetten?", "How much does the ticket cost?"),
    ("Shopping & Money", "Pengar", "Noun (plural)", "Money",
     "Plural only • Definite: pengarna",
     "Jag har inte tillräckligt med pengar.", "I don't have enough money."),
    ("Shopping & Money", "Dyr", "Adjective", "Expensive",
     "Neuter: dyrt • Plural: dyra",
     "Den här restaurangen är dyr.", "This restaurant is expensive."),
    ("Shopping & Money", "Billig", "Adjective", "Cheap",
     "Neuter: billigt • Plural: billiga",
     "Vi hittade ett billigt hotell.", "We found a cheap hotel."),
    ("Shopping & Money", "Påse", "Noun (en)", "Bag",
     "Definite: påsen • Plural: påsar • Def. plural: påsarna",
     "Vill du ha en påse?", "Would you like a bag?"),
    ("Travel & Transport", "Buss", "Noun (en)", "Bus",
     "Definite: bussen • Plural: bussar • Def. plural: bussarna",
     "Bussen går var tionde minut.", "The bus runs every ten minutes."),
    ("Travel & Transport", "Tåg", "Noun (ett)", "Train",
     "Definite: tåget • Plural: tåg • Def. plural: tågen",
     "Tåget är försenat.", "The train is delayed."),
    ("Travel & Transport", "Biljett", "Noun (en)", "Ticket",
     "Definite: biljetten • Plural: biljetter • Def. plural: biljetterna",
     "Jag köpte biljetten i appen.", "I bought the ticket in the app."),
    ("Travel & Transport", "Hållplats", "Noun (en)", "Stop (bus or tram)",
     "Definite: hållplatsen • Plural: hållplatser • Def. plural: hållplatserna",
     "Vi går av vid nästa hållplats.", "We get off at the next stop."),
    ("Travel & Transport", "Byta", "Verb", "To change (trains) / to swap",
     "Infinitive: byta • Past: bytte • Supine: bytt",
     "Du måste byta tåg i Hässleholm.", "You have to change trains in Hässleholm."),
    ("Travel & Transport", "Försenad", "Adjective", "Delayed",
     "Neuter: försenat • Plural: försenade",
     "Flyget är försenat två timmar.", "The flight is delayed by two hours."),
    ("Travel & Transport", "Cykel", "Noun (en)", "Bicycle",
     "Definite: cykeln • Plural: cyklar • Def. plural: cyklarna",
     "Jag tar cykeln till jobbet.", "I take the bike to work."),
    ("Travel & Transport", "Åka", "Verb", "To go / to travel (by vehicle)",
     "Infinitive: åka • Past: åkte • Supine: åkt. 'Åka' uses a vehicle; 'gå' means to walk.",
     "Vi åker tåg till Malmö.", "We're taking the train to Malmö."),
    ("Travel & Transport", "Resa", "Noun (en)", "Trip / journey",
     "Definite: resan • Plural: resor • Def. plural: resorna",
     "Resan tog fyra timmar.", "The journey took four hours."),
    ("Travel & Transport", "Stiga av", "Verb", "To get off",
     "Infinitive: stiga av • Past: steg av • Supine: stigit av",
     "Stig av vid centralstationen.", "Get off at the central station."),
    ("Cooking & Kitchen", "Laga mat", "Verb phrase", "To cook",
     "Infinitive: laga mat • Past: lagade mat • Supine: lagat mat",
     "Jag lagar mat nästan varje kväll.", "I cook almost every evening."),
    ("Cooking & Kitchen", "Recept", "Noun (ett)", "Recipe",
     "Definite: receptet • Plural: recept • Def. plural: recepten",
     "Receptet finns på nätet.", "The recipe is online."),
    ("Cooking & Kitchen", "Koka", "Verb", "To boil",
     "Infinitive: koka • Past: kokade • Supine: kokat",
     "Koka vattnet först.", "Boil the water first."),
    ("Cooking & Kitchen", "Steka", "Verb", "To fry",
     "Infinitive: steka • Past: stekte • Supine: stekt",
     "Jag steker fisken i smör.", "I fry the fish in butter."),
    ("Cooking & Kitchen", "Ugn", "Noun (en)", "Oven",
     "Definite: ugnen • Plural: ugnar • Def. plural: ugnarna",
     "Sätt in formen i ugnen.", "Put the dish in the oven."),
    ("Cooking & Kitchen", "Kylskåp", "Noun (ett)", "Fridge",
     "Definite: kylskåpet • Plural: kylskåp • Def. plural: kylskåpen",
     "Mjölken står i kylskåpet.", "The milk is in the fridge."),
    ("Cooking & Kitchen", "Tallrik", "Noun (en)", "Plate",
     "Definite: tallriken • Plural: tallrikar • Def. plural: tallrikarna",
     "Kan du duka fram tallrikarna?", "Can you set out the plates?"),
    ("Cooking & Kitchen", "Salt", "Noun (ett)", "Salt",
     "Definite: saltet (uncountable)",
     "Kan du skicka saltet?", "Can you pass the salt?"),
    ("Cooking & Kitchen", "Det smakar gott.", "Phrase", "It tastes good.", None,
     "Det smakar riktigt gott!", "That tastes really good!"),
    ("Cooking & Kitchen", "Diska", "Verb", "To do the dishes",
     "Infinitive: diska • Past: diskade • Supine: diskat",
     "Jag diskar efter middagen.", "I do the dishes after dinner."),
    ("Health & Body", "Huvud", "Noun (ett)", "Head",
     "Definite: huvudet • Plural: huvuden • Def. plural: huvudena",
     "Jag har ont i huvudet.", "I have a headache."),
    ("Health & Body", "Ont", "Noun (ett)", "Pain / ache",
     "Fixed frame: 'ha ont i' + body part.",
     "Jag har ont i ryggen.", "My back hurts."),
    ("Health & Body", "Feber", "Noun (en)", "Fever",
     "Definite: febern (uncountable)",
     "Han har feber och stannar hemma.", "He has a fever and is staying home."),
    ("Health & Body", "Förkyld", "Adjective", "Having a cold",
     "Neuter: förkylt • Plural: förkylda",
     "Jag är förkyld den här veckan.", "I have a cold this week."),
    ("Health & Body", "Vårdcentral", "Noun (en)", "Health centre / clinic",
     "Definite: vårdcentralen • Plural: vårdcentraler • Def. plural: vårdcentralerna",
     "Ring vårdcentralen och boka tid.", "Call the health centre and book an appointment."),
    ("Health & Body", "Medicin", "Noun (en)", "Medicine",
     "Definite: medicinen • Plural: mediciner • Def. plural: medicinerna",
     "Ta medicinen två gånger om dagen.", "Take the medicine twice a day."),
    ("Health & Body", "Mage", "Noun (en)", "Stomach",
     "Definite: magen • Plural: magar • Def. plural: magarna",
     "Magen kurrar, jag är hungrig.", "My stomach is rumbling, I'm hungry."),
    ("Health & Body", "Må bättre", "Verb phrase", "To feel better",
     "Infinitive: må bättre • Past: mådde bättre • Supine: mått bättre",
     "Jag mår bättre idag, tack.", "I feel better today, thanks."),
    ("Health & Body", "Krya på dig!", "Phrase", "Get well soon!", None,
     "Krya på dig, vi ses nästa vecka!", "Get well soon, see you next week!"),
    ("Home & Objects", "Lägenhet", "Noun (en)", "Apartment",
     "Definite: lägenheten • Plural: lägenheter • Def. plural: lägenheterna",
     "Vår lägenhet har två rum.", "Our apartment has two rooms."),
    ("Home & Objects", "Rum", "Noun (ett)", "Room",
     "Definite: rummet • Plural: rum • Def. plural: rummen",
     "Det finns ett extra rum för gäster.", "There's a spare room for guests."),
    ("Home & Objects", "Kök", "Noun (ett)", "Kitchen",
     "Definite: köket • Plural: kök • Def. plural: köken",
     "Vi renoverade köket förra året.", "We renovated the kitchen last year."),
    ("Home & Objects", "Säng", "Noun (en)", "Bed",
     "Definite: sängen • Plural: sängar • Def. plural: sängarna",
     "Sängen är för mjuk.", "The bed is too soft."),
    ("Home & Objects", "Fönster", "Noun (ett)", "Window",
     "Definite: fönstret • Plural: fönster • Def. plural: fönstren",
     "Kan du stänga fönstret?", "Can you close the window?"),
    ("Home & Objects", "Nyckel", "Noun (en)", "Key",
     "Definite: nyckeln • Plural: nycklar • Def. plural: nycklarna",
     "Jag glömde nyckeln hemma.", "I forgot the key at home."),
    ("Home & Objects", "Städa", "Verb", "To clean",
     "Infinitive: städa • Past: städade • Supine: städat",
     "Vi städar på lördagsförmiddagen.", "We clean on Saturday mornings."),
    ("Home & Objects", "Tvätta", "Verb", "To wash / to do laundry",
     "Infinitive: tvätta • Past: tvättade • Supine: tvättat",
     "Jag tvättar kläder ikväll.", "I'm doing laundry tonight."),
    ("Home & Objects", "Sopor", "Noun (plural)", "Rubbish / trash",
     "Plural only • Definite: soporna",
     "Kan du ta ut soporna?", "Can you take out the rubbish?"),
    ("Home & Objects", "Trasig", "Adjective", "Broken",
     "Neuter: trasigt • Plural: trasiga",
     "Kranen är trasig.", "The tap is broken."),
]

# Hand-written distance and directions vocabulary: extends the existing
# "Places & Directions" category with near/far, the "det finns" existential
# construction, and church/city/street words for describing where things are.
# (category, sv, pos, en, note, ex, ex_en)
PLACES_DIRECTIONS_EXTRA = [
    ("Places & Directions", "Nära", "Adjective/Adverb", "Near / close", None,
     "Affären ligger nära mitt hus.", "The shop is close to my house."),
    ("Places & Directions", "Långt", "Adverb", "Far",
     "Comparative: längre • Superlative: längst",
     "Det är långt till stationen.", "It's far to the station."),
    ("Places & Directions", "Det finns", "Phrase", "There is / there are",
     "Existential construction with 'finnas'; the form stays the same regardless of number.",
     "Det finns en kyrka i stan.", "There is a church in town."),
    ("Places & Directions", "Kyrka", "Noun (en)", "Church",
     "Definite: kyrkan • Plural: kyrkor • Def. plural: kyrkorna",
     "Kyrkan ligger mitt i stan.", "The church is right in the middle of town."),
    ("Places & Directions", "Stad", "Noun (en)", "City / town",
     "Definite: staden • Plural: städer • Def. plural: städerna (irregular)",
     "Jag bor i en liten stad.", "I live in a small town."),
    ("Places & Directions", "By", "Noun (en)", "Village",
     "Definite: byn • Plural: byar • Def. plural: byarna",
     "Mina morföräldrar bor i en by.", "My grandparents live in a village."),
    ("Places & Directions", "Gata", "Noun (en)", "Street",
     "Definite: gatan • Plural: gator • Def. plural: gatorna",
     "Vi bor på samma gata.", "We live on the same street."),
    ("Places & Directions", "Korsning", "Noun (en)", "Intersection / crossing",
     "Definite: korsningen • Plural: korsningar • Def. plural: korsningarna",
     "Vänta vid korsningen.", "Wait at the intersection."),
    ("Places & Directions", "Centrum", "Noun (ett)", "City centre / downtown",
     "Indeclinable: the same in singular, plural, and definite forms.",
     "Vi ska till centrum ikväll.", "We're going downtown tonight."),
    ("Places & Directions", "Svänga", "Verb", "To turn",
     "Infinitive: svänga • Past: svängde • Supine: svängt",
     "Sväng vänster vid korsningen.", "Turn left at the intersection."),
    ("Places & Directions", "Hur långt är det till…?", "Phrase", "How far is it to…?", None,
     "Hur långt är det till centrum?", "How far is it to the city centre?"),
    ("Places & Directions", "Rakt fram", "Phrase", "Straight ahead", None,
     "Gå rakt fram och sväng sedan vänster.", "Go straight ahead and then turn left."),
    ("Places & Directions", "Till vänster / till höger", "Phrase", "To the left / to the right", None,
     "Sväng till höger vid kyrkan.", "Turn right at the church."),
    ("Places & Directions", "I närheten", "Phrase", "Nearby / in the vicinity", None,
     "Finns det en bank i närheten?", "Is there a bank nearby?"),
    ("Places & Directions", "På andra sidan", "Phrase", "On the other side", None,
     "Biblioteket ligger på andra sidan gatan.", "The library is on the other side of the street."),
]

# Hand-written weather and news small talk: extends the existing "Family &
# Weather Chat" category (the CSV only had bare nouns) and adds "News &
# Current Events", "Invitations & Plans" and "Opinions & Reactions" — the rest
# of what everyday small talk actually runs on.
# (category, sv, pos, en, note, ex, ex_en)
SOCIAL_SMALL_TALK_EXTRA = [
    ("Family & Weather Chat", "Vad är det för väder idag?", "Phrase", "What's the weather like today?", None,
     "Vad är det för väder idag? Ska vi ta med paraply?",
     "What's the weather like today? Should we bring an umbrella?"),
    ("Family & Weather Chat", "Det blåser.", "Phrase", "It's windy.", None,
     "Det blåser mycket idag, håll i hatten!", "It's very windy today, hold on to your hat!"),
    ("Family & Weather Chat", "Det är molnigt.", "Phrase", "It's cloudy.", None,
     "Det är molnigt idag, men det ska klarna upp senare.",
     "It's cloudy today, but it's supposed to clear up later."),
    ("Family & Weather Chat", "Klarna upp", "Verb", "To clear up (weather)",
     "Infinitive: klarna upp • Past: klarnade upp • Supine: klarnat upp",
     "Det regnade i morse, men det har klarnat upp nu.",
     "It rained this morning, but it has cleared up now."),
    ("Family & Weather Chat", "Prognos", "Noun (en)", "Forecast",
     "Definite: prognosen • Plural: prognoser • Def. plural: prognoserna",
     "Enligt prognosen blir det snö i helgen.",
     "According to the forecast there'll be snow this weekend."),
    ("Family & Weather Chat", "Grad", "Noun (en)", "Degree (temperature)",
     "Definite: graden • Plural: grader • Def. plural: graderna",
     "Det är tjugo grader ute idag.", "It's twenty degrees outside today."),
    ("Family & Weather Chat", "Åska", "Noun (en)", "Thunder",
     "Definite: åskan (uncountable)",
     "Det åskar och blixtrar just nu.", "It's thundering and lightning right now."),
    ("Family & Weather Chat", "Släkt", "Noun (en)", "Relatives / extended family",
     "Definite: släkten • Plural: släkter • Def. plural: släkterna",
     "Hela släkten kom på kalaset.", "The whole extended family came to the party."),
    ("Family & Weather Chat", "Sambo", "Noun (en)", "Live-in partner",
     "Definite: sambon • Plural: sambor • Def. plural: samborna",
     "Min sambo lagar maten ikväll.", "My partner is cooking tonight."),
    ("Family & Weather Chat", "Mormor", "Noun (en)", "Grandmother (mother's side)",
     "Swedish names grandparents by side: mormor, morfar, farmor, farfar.",
     "Min mormor bor kvar i huset.", "My grandmother still lives in the house."),
    ("News & Current Events", "Nyhet", "Noun (en)", "News (item)",
     "Definite: nyheten • Plural: nyheter • Def. plural: nyheterna",
     "Har du sett nyheterna idag?", "Have you seen the news today?"),
    ("News & Current Events", "Tidning", "Noun (en)", "Newspaper",
     "Definite: tidningen • Plural: tidningar • Def. plural: tidningarna",
     "Jag läser tidningen varje morgon.", "I read the newspaper every morning."),
    ("News & Current Events", "Har du hört…?", "Phrase", "Have you heard…?", None,
     "Har du hört att de bygger en ny bro?", "Have you heard that they're building a new bridge?"),
    ("News & Current Events", "Vad har hänt?", "Phrase", "What happened?", None,
     "Vad har hänt? Alla pratar om det.", "What happened? Everyone is talking about it."),
    ("News & Current Events", "Enligt nyheterna…", "Phrase", "According to the news…", None,
     "Enligt nyheterna kommer det snö imorgon.",
     "According to the news it's going to snow tomorrow."),
    ("News & Current Events", "Rubrik", "Noun (en)", "Headline",
     "Definite: rubriken • Plural: rubriker • Def. plural: rubrikerna",
     "Rubriken var väldigt dramatisk.", "The headline was very dramatic."),
    ("Invitations & Plans", "Vad gör du i helgen?", "Phrase", "What are you doing this weekend?", None,
     "Vad gör du i helgen? Vi tänkte grilla.",
     "What are you doing this weekend? We were thinking of having a barbecue."),
    ("Invitations & Plans", "Ska vi ta en fika?", "Phrase", "Shall we grab a coffee?", None,
     "Ska vi ta en fika efter jobbet?", "Shall we grab a coffee after work?"),
    ("Invitations & Plans", "Vill du följa med?", "Phrase", "Do you want to come along?", None,
     "Vi ska på bio. Vill du följa med?", "We're going to the cinema. Do you want to come along?"),
    ("Invitations & Plans", "Det låter kul!", "Phrase", "That sounds fun!", None,
     "Det låter kul, jag är med.", "That sounds fun, I'm in."),
    ("Invitations & Plans", "Jag kan tyvärr inte.", "Phrase", "Unfortunately I can't.", None,
     "Jag kan tyvärr inte, jag har redan planer.",
     "Unfortunately I can't, I already have plans."),
    ("Invitations & Plans", "Passar det på fredag?", "Phrase", "Does Friday work for you?", None,
     "Passar det på fredag klockan sju?", "Does Friday at seven work for you?"),
    ("Invitations & Plans", "Vi hörs!", "Phrase", "We'll be in touch!", None,
     "Vi hörs i veckan!", "We'll talk during the week!"),
    ("Invitations & Plans", "Vi ses!", "Phrase", "See you!", None,
     "Vi ses på lördag!", "See you on Saturday!"),
    ("Invitations & Plans", "Hälsa så gott!", "Phrase", "Say hi from me!", None,
     "Hälsa så gott till din familj!", "Say hello to your family from me!"),
    ("Opinions & Reactions", "Jag tycker att …", "Phrase", "I think that … (opinion)",
     "'Tycka' is an opinion, 'tro' is a belief, 'tänka' is having something in mind.",
     "Jag tycker att filmen var för lång.", "I think the film was too long."),
    ("Opinions & Reactions", "Jag tror att …", "Phrase", "I believe that …", None,
     "Jag tror att det blir regn imorgon.", "I think it's going to rain tomorrow."),
    ("Opinions & Reactions", "Jag håller med.", "Phrase", "I agree.", None,
     "Jag håller med dig helt.", "I completely agree with you."),
    ("Opinions & Reactions", "Jag håller inte med.", "Phrase", "I disagree.", None,
     "Jag håller inte med, jag tror tvärtom.", "I disagree, I think the opposite."),
    ("Opinions & Reactions", "Vad synd!", "Phrase", "What a shame!", None,
     "Vad synd att du inte kunde komma!", "What a shame you couldn't come!"),
    ("Opinions & Reactions", "Vad kul!", "Phrase", "How nice! / How fun!", None,
     "Vad kul att du är här!", "How nice that you're here!"),
    ("Opinions & Reactions", "Precis!", "Interjection", "Exactly!", None,
     "Precis, det var det jag menade.", "Exactly, that's what I meant."),
    ("Opinions & Reactions", "Jaså?", "Interjection", "Oh really?", None,
     "Jaså, har de flyttat?", "Oh really, have they moved?"),
    ("Opinions & Reactions", "Så klart!", "Phrase", "Of course!", None,
     "Så klart att du får låna den.", "Of course you can borrow it."),
    ("Opinions & Reactions", "Det spelar ingen roll.", "Phrase", "It doesn't matter.", None,
     "Det spelar ingen roll, välj du.", "It doesn't matter, you choose."),
    ("Opinions & Reactions", "Tvärtom", "Adverb", "On the contrary", None,
     "Det var inte tråkigt, tvärtom!", "It wasn't boring, quite the opposite!"),
]

# Hand-written comparatives: the core "bättre/större/lättare än"-style
# vocabulary plus the two comparison sentence patterns ("lika … som" and
# "ju … desto …").
# (sv, pos, en, note, ex, ex_en)
COMPARISONS = [
    ("Än", "Conjunction", "Than",
     "Follows a comparative adjective or adverb.",
     "Hon är äldre än jag.", "She is older than me."),
    ("Bättre än", "Comparative phrase", "Better than",
     "Positive: bra/god • Superlative: bäst",
     "Det här kaffet är bättre än det där.", "This coffee is better than that one."),
    ("Sämre än", "Comparative phrase", "Worse than",
     "Positive: dålig • Superlative: sämst",
     "Mitt betyg blev sämre än förra terminen.", "My grade was worse than last term."),
    ("Större än", "Comparative phrase", "Bigger than",
     "Positive: stor • Superlative: störst",
     "Sverige är större än Danmark.", "Sweden is bigger than Denmark."),
    ("Mindre än", "Comparative phrase", "Smaller than",
     "Positive: liten • Superlative: minst",
     "Min lägenhet är mindre än din.", "My apartment is smaller than yours."),
    ("Lättare än", "Comparative phrase", "Easier than",
     "Positive: lätt • Superlative: lättast",
     "Provet var lättare än jag trodde.", "The test was easier than I thought."),
    ("Svårare än", "Comparative phrase", "Harder / more difficult than",
     "Positive: svår • Superlative: svårast",
     "Grammatik är svårare än uttal för mig.", "Grammar is harder than pronunciation for me."),
    ("Snabbare än", "Comparative phrase", "Faster than",
     "Positive: snabb • Superlative: snabbast",
     "Tåget är snabbare än bussen.", "The train is faster than the bus."),
    ("Långsammare än", "Comparative phrase", "Slower than",
     "Positive: långsam • Superlative: långsammast",
     "Han pratar långsammare än jag gör.", "He speaks more slowly than I do."),
    ("Billigare än", "Comparative phrase", "Cheaper than",
     "Positive: billig • Superlative: billigast",
     "Den här tröjan är billigare än den där.", "This jumper is cheaper than that one."),
    ("Dyrare än", "Comparative phrase", "More expensive than",
     "Positive: dyr • Superlative: dyrast",
     "Hyran är dyrare i år än förra året.", "The rent is more expensive this year than last year."),
    ("Fler än", "Comparative phrase", "More than (countable)",
     "Uncountable equivalent: mer än.",
     "Vi har fler stolar än bord.", "We have more chairs than tables."),
    ("Lika … som", "Comparative construction", "As … as",
     "The adjective stays in its base form between 'lika' and 'som'.",
     "Hon är lika trött som jag.", "She is as tired as I am."),
    ("Ju … desto …", "Correlative construction", "The … the …",
     "Both halves invert: the verb follows the comparative word directly.",
     "Ju mer jag övar, desto bättre blir jag.", "The more I practise, the better I get."),
]

# Hand-written Tutor Toolkit: conversation-management phrases for keeping a
# tutoring session in Swedish even when you need help. No analog in
# the original CSV.
# (category, sv, pos, en, note, ex, ex_en)
TUTOR_TOOLKIT = [
    ("Clarification", "Kan du upprepa?", "Phrase", "Can you repeat that?", None,
     "Förlåt, kan du upprepa? Jag hörde inte.", "Sorry, can you repeat that? I didn't hear."),
    ("Clarification", "Vad betyder det?", "Phrase", "What does that mean?", None,
     "Vad betyder det ordet?", "What does that word mean?"),
    ("Clarification", "Kan du säga det långsammare?", "Phrase", "Can you say it more slowly?", None,
     "Kan du säga det långsammare, tack?", "Can you say it more slowly, please?"),
    ("Clarification", "Jag hängde inte med.", "Phrase", "I didn't catch that.", None,
     "Förlåt, jag hängde inte med på slutet.", "Sorry, I didn't follow at the end."),
    ("Clarification", "Menar du …?", "Phrase", "Do you mean …?", None,
     "Menar du att jag ska använda 'på' här?", "Do you mean I should use 'på' here?"),
    ("Clarification", "Kan du skriva det?", "Phrase", "Can you write it down?", None,
     "Kan du skriva det i chatten?", "Can you write it in the chat?"),
    ("Clarification", "En gång till, tack.", "Phrase", "One more time, please.", None,
     "En gång till, tack — jag vill höra uttalet.",
     "One more time, please — I want to hear the pronunciation."),
    ("Repair & Save the Conversation", "Jag menar …", "Phrase", "I mean … (self-correcting)", None,
     "Jag menar, jag åkte igår — inte idag.", "I mean, I went yesterday — not today."),
    ("Repair & Save the Conversation", "Jag har glömt ordet.", "Phrase", "I've forgotten the word.", None,
     "Jag har glömt ordet … det där för 'bridge'.",
     "I've forgotten the word … the one for 'bridge'."),
    ("Repair & Save the Conversation", "Får jag tänka lite?", "Phrase", "Can I think for a moment?", None,
     "Får jag tänka lite innan jag svarar?", "May I think for a moment before I answer?"),
    ("Repair & Save the Conversation", "Jag försöker igen.", "Phrase", "I'll try again.", None,
     "Det blev fel. Jag försöker igen.", "That came out wrong. I'll try again."),
    ("Repair & Save the Conversation", "Hur var det nu igen?", "Phrase", "How was it again?", None,
     "Hur var det nu igen — 'ligger' eller 'lägger'?",
     "How was it again — 'ligger' or 'lägger'?"),
    ("Repair & Save the Conversation", "Vänta lite.", "Phrase", "Hold on a second.", None,
     "Vänta lite, jag tänker efter.", "Hold on a second, I'm thinking."),
    ("Repair & Save the Conversation", "Jag vet inte hur man säger det.", "Phrase",
     "I don't know how to say it.", None,
     "Jag vet inte hur man säger det på svenska.", "I don't know how to say it in Swedish."),
    ("Meta-language", "Hur säger man det på svenska?", "Phrase", "How do you say that in Swedish?", None,
     "Hur säger man 'deadline' på svenska?", "How do you say 'deadline' in Swedish?"),
    ("Meta-language", "Hur stavas det?", "Phrase", "How is it spelled?", None,
     "Hur stavas det? Kan du skriva det?", "How is it spelled? Can you write it down?"),
    ("Meta-language", "Kan du ge ett exempel?", "Phrase", "Can you give an example?", None,
     "Jag förstår regeln, men kan du ge ett exempel?",
     "I understand the rule, but can you give an example?"),
    ("Meta-language", "Är det rätt?", "Phrase", "Is that right?", None,
     "Jag sa 'jag har åkt'. Är det rätt?", "I said 'jag har åkt'. Is that right?"),
    ("Meta-language", "Vad är skillnaden mellan … och …?", "Phrase",
     "What's the difference between … and …?", None,
     "Vad är skillnaden mellan 'tycker' och 'tänker'?",
     "What's the difference between 'tycker' and 'tänker'?"),
    ("Meta-language", "Kan du rätta mig?", "Phrase", "Can you correct me?", None,
     "Kan du rätta mig när jag säger fel?", "Can you correct me when I say something wrong?"),
    ("Meta-language", "Säger man så?", "Phrase", "Do people actually say that?", None,
     "Säger man så, eller låter det konstigt?", "Do people say that, or does it sound odd?"),
    ("Polite Feedback", "Det här är svårt för mig.", "Phrase", "This is difficult for me.", None,
     "Det här är svårt för mig, men jag övar.", "This is difficult for me, but I'm practising."),
    ("Polite Feedback", "Jag förstår inte riktigt.", "Phrase", "I don't quite understand.", None,
     "Jag förstår inte riktigt skillnaden.", "I don't quite understand the difference."),
    ("Polite Feedback", "Nu förstår jag!", "Phrase", "Now I understand!", None,
     "Nu förstår jag, tack för förklaringen!", "Now I understand, thanks for the explanation!"),
    ("Polite Feedback", "Kan vi öva på det här?", "Phrase", "Can we practise this?", None,
     "Kan vi öva på det här lite mer?", "Can we practise this a bit more?"),
    ("Polite Feedback", "Det gick bättre nu.", "Phrase", "That went better.", None,
     "Det gick bättre nu, eller hur?", "That went better, didn't it?"),
]


def _split_note(forms):
    forms = (forms or "").strip()
    return None if forms in ("", "—") else forms


# Each themed list is written for one section; a row's first field is its topic.
GROUPED = [
    ("Grammar & reference", GRAMMAR_EXTRA),
    ("Grammar & reference", QUESTIONS_PREPOSITIONS),
    ("Topics & situations", WORKPLACE_TECH_EXTRA),
    ("Topics & situations", HOME_DAILY_LIFE_EXTRA),
    ("Topics & situations", PLACES_DIRECTIONS_EXTRA),
    ("Topics & situations", SOCIAL_SMALL_TALK_EXTRA),
    ("Conversation toolkit", TUTOR_TOOLKIT),
]

# Topics the retag introduces, which no list declares on its own.
NEW_TOPICS = {
    "Core Words": "Topics & situations",
    "Colors": "Topics & situations",
}


def topic_sections():
    """{topic: section} for every topic the seed uses.

    Derived from the same structures that produce the rows, so a topic can
    never drift out of sync with the section it is filed under.
    """
    sections = dict(NEW_TOPICS)

    for section, topic in CATEGORY_MAP.values():
        if topic not in RETIRED_BUCKETS:
            sections[topic] = section
    for topic in PREPOSITION_REHOME.values():
        sections[topic] = "Grammar & reference"

    # CSV rows that branch by word rather than by category.
    sections["Professions"] = "Topics & situations"
    sections["Family & Weather Chat"] = "Topics & situations"

    sections["V2 Inversion Anchors"] = "Grammar & reference"
    sections["Comparatives & Comparisons"] = "Grammar & reference"

    for section, group in GROUPED:
        for row in group:
            sections[row[0]] = section

    return sections


def _csv_rows():
    """Migrate words/svenska.csv into (topics, sv, pos, en, note, ex, ex_en, fn) rows."""
    rows = []
    with CSV_PATH.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = row["Category"]
            sv = row["Swedish"]
            pos = row["Word Type"] or None
            en = row["English"]
            note = _split_note(row["Other forms (tense / plural / etc.)"])
            ex = row["Example"]
            ex_en = row["Example (English)"]

            rehomed = PREPOSITION_REHOME.get((category, sv))
            if rehomed:
                topic = rehomed
            elif category == "Weather, family & professions":
                topic = "Professions" if sv in PROFESSION_WORDS else "Family & Weather Chat"
            elif sv in TECH_WORDS:
                topic = "Tech Verbs"
            else:
                topic = CATEGORY_MAP[category][1]

            if topic in RETIRED_BUCKETS:
                topics = BUCKET_RETAG.get(sv)
                if not topics:
                    raise ValueError(
                        f"{sv!r} sits in the retired bucket {topic!r} with no retag"
                    )
            else:
                topics = (topic,)

            rows.append((topics, sv, pos, en, note, ex, ex_en, None))
    return rows


def seed_rows():
    """Every row the seed inserts, as (topics, sv, pos, en, note, ex, ex_en, fn)."""
    rows = _csv_rows()

    for sv, pos, en, fn, note, ex, ex_en in V2_ANCHORS:
        rows.append((("V2 Inversion Anchors",), sv, pos, en, note, ex, ex_en, fn))

    for sv, pos, en, note, ex, ex_en in COMPARISONS:
        rows.append((("Comparatives & Comparisons",), sv, pos, en, note, ex, ex_en, None))

    for _section, group in GROUPED:
        for topic, sv, pos, en, note, ex, ex_en in group:
            rows.append(((topic,), sv, pos, en, note, ex, ex_en, None))

    return rows


def validate_rows(rows):
    """Everything a seeded entry must satisfy before any of it is inserted."""
    problems = []
    sections = topic_sections()
    seen_per_topic = {}

    for section in sections.values():
        if section not in SECTIONS:
            problems.append(f"unknown section {section!r}")

    for topics, sv, _pos, en, _note, ex, ex_en, _fn in rows:
        where = f"{'/'.join(topics)} / {sv}"

        for label, value in (("translation", en), ("example", ex), ("example translation", ex_en)):
            if not (value or "").strip():
                problems.append(f"{where}: missing {label}")

        if not topics:
            problems.append(f"{where}: no topic")

        for topic in topics:
            if topic in RETIRED_BUCKETS:
                problems.append(f"{where}: uses retired bucket {topic!r}")
            elif topic not in sections:
                problems.append(f"{where}: topic {topic!r} has no section")

            # The same word must not appear twice inside one topic.
            if sv in seen_per_topic.setdefault(topic, set()):
                problems.append(f"{where}: duplicated inside {topic!r}")
            seen_per_topic[topic].add(sv)

    if problems:
        raise ValueError("Seed data problems:\n  " + "\n  ".join(problems))


def seed_database(conn):
    rows = seed_rows()
    validate_rows(rows)

    for topic, section in topic_sections().items():
        register_topic(conn, topic, section)

    for topics, sv, pos, en, note, ex, ex_en, fn in rows:
        insert_entry(conn, topics, sv, pos, en, note, ex, ex_en, fn, is_custom=0)


def ensure_seeded(conn):
    """Seed on an empty database, and reseed when the seed content has changed.

    Reseeding replaces only the rows this file owns (is_custom = 0), so entries
    added through the Add Entry form survive a deploy that ships new vocabulary.
    """
    if is_empty(conn):
        seed_database(conn)
    elif get_meta(conn, "seed_version") != SEED_VERSION:
        delete_seed_entries(conn)
        seed_database(conn)
    set_meta(conn, "seed_version", SEED_VERSION)
