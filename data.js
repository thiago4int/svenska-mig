const FLASHCARD_DATA = [
  {
    "category": "Greetings and pleasantries",
    "words": [
      {
        "sv": "Hej",
        "en": "Hello",
        "type": "Interjection",
        "forms": "—"
      },
      {
        "sv": "Hej då",
        "en": "Goodbye",
        "type": "Interjection",
        "forms": "—"
      },
      {
        "sv": "God morgon",
        "en": "Good morning",
        "type": "Phrase",
        "forms": "—"
      },
      {
        "sv": "God kväll",
        "en": "Good evening",
        "type": "Phrase",
        "forms": "—"
      },
      {
        "sv": "Tack",
        "en": "Thank you",
        "type": "Interjection",
        "forms": "—"
      },
      {
        "sv": "Varsågod",
        "en": "You're welcome/Please",
        "type": "Interjection",
        "forms": "—"
      },
      {
        "sv": "Förlåt",
        "en": "Sorry",
        "type": "Interjection",
        "forms": "—"
      },
      {
        "sv": "Ursäkta",
        "en": "Excuse me",
        "type": "Interjection",
        "forms": "—"
      },
      {
        "sv": "Ja",
        "en": "Yes",
        "type": "Particle",
        "forms": "—"
      },
      {
        "sv": "Nej",
        "en": "No",
        "type": "Particle",
        "forms": "—"
      },
      {
        "sv": "Snälla",
        "en": "Please (when making a request)",
        "type": "Adverb",
        "forms": "—"
      },
      {
        "sv": "Hur mår du?",
        "en": "How are you?",
        "type": "Phrase",
        "forms": "—"
      },
      {
        "sv": "Jag mår bra",
        "en": "I'm fine",
        "type": "Phrase",
        "forms": "—"
      }
    ]
  },
  {
    "category": "People and pronouns",
    "words": [
      {
        "sv": "Jag",
        "en": "I",
        "type": "Pronoun",
        "forms": "Object form: mig"
      },
      {
        "sv": "Du",
        "en": "You (singular)",
        "type": "Pronoun",
        "forms": "Object form: dig"
      },
      {
        "sv": "Han",
        "en": "He",
        "type": "Pronoun",
        "forms": "Object form: honom"
      },
      {
        "sv": "Hon",
        "en": "She",
        "type": "Pronoun",
        "forms": "Object form: henne"
      },
      {
        "sv": "Hen",
        "en": "They (gender-neutral singular)",
        "type": "Pronoun",
        "forms": "Object form: hen"
      },
      {
        "sv": "Vi",
        "en": "We",
        "type": "Pronoun",
        "forms": "Object form: oss"
      },
      {
        "sv": "Ni",
        "en": "You (plural)",
        "type": "Pronoun",
        "forms": "Object form: er"
      },
      {
        "sv": "De",
        "en": "They",
        "type": "Pronoun",
        "forms": "Object form: dem"
      },
      {
        "sv": "Man",
        "en": "Man",
        "type": "Noun (en)",
        "forms": "Definite: mannen • Plural: män • Def. plural: männen"
      },
      {
        "sv": "Kvinna",
        "en": "Woman",
        "type": "Noun (en)",
        "forms": "Definite: kvinnan • Plural: kvinnor • Def. plural: kvinnorna"
      },
      {
        "sv": "Barn",
        "en": "Child",
        "type": "Noun (ett)",
        "forms": "Definite: barnet • Plural: barn • Def. plural: barnen"
      },
      {
        "sv": "Familj",
        "en": "Family",
        "type": "Noun (en)",
        "forms": "Definite: familjen • Plural: familjer • Def. plural: familjerna"
      },
      {
        "sv": "Vän",
        "en": "Friend",
        "type": "Noun (en)",
        "forms": "Definite: vännen • Plural: vänner • Def. plural: vännerna"
      }
    ]
  },
  {
    "category": "Everyday verbs",
    "words": [
      {
        "sv": "Är",
        "en": "Am/is/are",
        "type": "Verb",
        "forms": "Infinitive: vara • Past: var • Supine: varit"
      },
      {
        "sv": "Har",
        "en": "Have/has",
        "type": "Verb",
        "forms": "Infinitive: ha • Past: hade • Supine: haft"
      },
      {
        "sv": "Gör",
        "en": "Do/does/doing",
        "type": "Verb",
        "forms": "Infinitive: göra • Past: gjorde • Supine: gjort"
      },
      {
        "sv": "Pratar",
        "en": "Speaking/talking",
        "type": "Verb",
        "forms": "Infinitive: prata • Past: pratade • Supine: pratat"
      },
      {
        "sv": "Äter",
        "en": "Eating",
        "type": "Verb",
        "forms": "Infinitive: äta • Past: åt • Supine: ätit"
      },
      {
        "sv": "Dricker",
        "en": "Drinking",
        "type": "Verb",
        "forms": "Infinitive: dricka • Past: drack • Supine: druckit"
      },
      {
        "sv": "Går",
        "en": "Go/walking",
        "type": "Verb",
        "forms": "Infinitive: gå • Past: gick • Supine: gått"
      },
      {
        "sv": "Kommer",
        "en": "Coming",
        "type": "Verb",
        "forms": "Infinitive: komma • Past: kom • Supine: kommit"
      },
      {
        "sv": "Sover",
        "en": "Sleeping",
        "type": "Verb",
        "forms": "Infinitive: sova • Past: sov • Supine: sovit"
      },
      {
        "sv": "Ser",
        "en": "Seeing",
        "type": "Verb",
        "forms": "Infinitive: se • Past: såg • Supine: sett"
      },
      {
        "sv": "Hör",
        "en": "Hearing",
        "type": "Verb",
        "forms": "Infinitive: höra • Past: hörde • Supine: hört"
      },
      {
        "sv": "Tycker om",
        "en": "Liking",
        "type": "Verb phrase",
        "forms": "Infinitive: tycka om • Past: tyckte om • Supine: tyckt om"
      },
      {
        "sv": "Vill",
        "en": "Want",
        "type": "Verb",
        "forms": "Infinitive: vilja • Past: ville • Supine: velat"
      }
    ]
  },
  {
    "category": "Food and drink",
    "words": [
      {
        "sv": "Mat",
        "en": "Food",
        "type": "Noun (en)",
        "forms": "Definite: maten (uncountable, no common plural)"
      },
      {
        "sv": "Dryck",
        "en": "Beverage",
        "type": "Noun (en)",
        "forms": "Definite: drycken • Plural: drycker • Def. plural: dryckerna"
      },
      {
        "sv": "Vatten",
        "en": "Water",
        "type": "Noun (ett)",
        "forms": "Definite: vattnet (uncountable)"
      },
      {
        "sv": "Kaffe",
        "en": "Coffee",
        "type": "Noun (ett)",
        "forms": "Definite: kaffet (uncountable)"
      },
      {
        "sv": "Te",
        "en": "Tea",
        "type": "Noun (ett)",
        "forms": "Definite: teet (uncountable)"
      },
      {
        "sv": "Öl",
        "en": "Beer",
        "type": "Noun (ett)",
        "forms": "Definite: ölet • Plural: öl • Def. plural: ölen"
      },
      {
        "sv": "Vin",
        "en": "Wine",
        "type": "Noun (ett)",
        "forms": "Definite: vinet • Plural: vin • Def. plural: vinen"
      },
      {
        "sv": "Bröd",
        "en": "Bread",
        "type": "Noun (ett)",
        "forms": "Definite: brödet • Plural: bröd • Def. plural: bröden"
      },
      {
        "sv": "Smör",
        "en": "Butter",
        "type": "Noun (ett)",
        "forms": "Definite: smöret (uncountable)"
      },
      {
        "sv": "Ost",
        "en": "Cheese",
        "type": "Noun (en)",
        "forms": "Definite: osten • Plural: ostar • Def. plural: ostarna"
      },
      {
        "sv": "Kött",
        "en": "Meat",
        "type": "Noun (ett)",
        "forms": "Definite: köttet (uncountable)"
      },
      {
        "sv": "Fisk",
        "en": "Fish",
        "type": "Noun (en)",
        "forms": "Definite: fisken • Plural: fiskar • Def. plural: fiskarna"
      },
      {
        "sv": "Frukt",
        "en": "Fruit",
        "type": "Noun (en)",
        "forms": "Definite: frukten • Plural: frukter • Def. plural: frukterna"
      },
      {
        "sv": "Grönsaker",
        "en": "Vegetables",
        "type": "Noun (en, pl.)",
        "forms": "Singular: grönsak • Definite: grönsaken • Def. plural: grönsakerna"
      }
    ]
  },
  {
    "category": "Time and days",
    "words": [
      {
        "sv": "Tid",
        "en": "Time",
        "type": "Noun (en)",
        "forms": "Definite: tiden • Plural: tider • Def. plural: tiderna"
      },
      {
        "sv": "Idag",
        "en": "Today",
        "type": "Adverb",
        "forms": "—"
      },
      {
        "sv": "Imorgon",
        "en": "Tomorrow",
        "type": "Adverb",
        "forms": "—"
      },
      {
        "sv": "Igår",
        "en": "Yesterday",
        "type": "Adverb",
        "forms": "—"
      },
      {
        "sv": "Nu",
        "en": "Now",
        "type": "Adverb",
        "forms": "—"
      },
      {
        "sv": "Senare",
        "en": "Later",
        "type": "Adverb",
        "forms": "—"
      },
      {
        "sv": "Måndag",
        "en": "Monday",
        "type": "Noun (en)",
        "forms": "Definite: måndagen • Plural: måndagar • Def. plural: måndagarna"
      },
      {
        "sv": "Tisdag",
        "en": "Tuesday",
        "type": "Noun (en)",
        "forms": "Definite: tisdagen • Plural: tisdagar • Def. plural: tisdagarna"
      },
      {
        "sv": "Onsdag",
        "en": "Wednesday",
        "type": "Noun (en)",
        "forms": "Definite: onsdagen • Plural: onsdagar • Def. plural: onsdagarna"
      },
      {
        "sv": "Torsdag",
        "en": "Thursday",
        "type": "Noun (en)",
        "forms": "Definite: torsdagen • Plural: torsdagar • Def. plural: torsdagarna"
      },
      {
        "sv": "Fredag",
        "en": "Friday",
        "type": "Noun (en)",
        "forms": "Definite: fredagen • Plural: fredagar • Def. plural: fredagarna"
      },
      {
        "sv": "Lördag",
        "en": "Saturday",
        "type": "Noun (en)",
        "forms": "Definite: lördagen • Plural: lördagar • Def. plural: lördagarna"
      },
      {
        "sv": "Söndag",
        "en": "Sunday",
        "type": "Noun (en)",
        "forms": "Definite: söndagen • Plural: söndagar • Def. plural: söndagarna"
      },
      {
        "sv": "Vecka",
        "en": "Week",
        "type": "Noun (en)",
        "forms": "Definite: veckan • Plural: veckor • Def. plural: veckorna"
      },
      {
        "sv": "Månad",
        "en": "Month",
        "type": "Noun (en)",
        "forms": "Definite: månaden • Plural: månader • Def. plural: månaderna"
      }
    ]
  },
  {
    "category": "Numbers and counting",
    "words": [
      {
        "sv": "Ett",
        "en": "One",
        "type": "Numeral",
        "forms": "—"
      },
      {
        "sv": "Två",
        "en": "Two",
        "type": "Numeral",
        "forms": "—"
      },
      {
        "sv": "Tre",
        "en": "Three",
        "type": "Numeral",
        "forms": "—"
      },
      {
        "sv": "Fyra",
        "en": "Four",
        "type": "Numeral",
        "forms": "—"
      },
      {
        "sv": "Fem",
        "en": "Five",
        "type": "Numeral",
        "forms": "—"
      },
      {
        "sv": "Sex",
        "en": "Six",
        "type": "Numeral",
        "forms": "—"
      },
      {
        "sv": "Sju",
        "en": "Seven",
        "type": "Numeral",
        "forms": "—"
      },
      {
        "sv": "Åtta",
        "en": "Eight",
        "type": "Numeral",
        "forms": "—"
      },
      {
        "sv": "Nio",
        "en": "Nine",
        "type": "Numeral",
        "forms": "—"
      },
      {
        "sv": "Tio",
        "en": "Ten",
        "type": "Numeral",
        "forms": "—"
      },
      {
        "sv": "Hundra",
        "en": "Hundred",
        "type": "Numeral",
        "forms": "—"
      },
      {
        "sv": "Tusen",
        "en": "Thousand",
        "type": "Numeral",
        "forms": "—"
      },
      {
        "sv": "Första",
        "en": "First",
        "type": "Adjective (ordinal)",
        "forms": "Neuter/Plural: första (invariable)"
      },
      {
        "sv": "Andra",
        "en": "Second",
        "type": "Adjective (ordinal)",
        "forms": "Neuter/Plural: andra (invariable)"
      }
    ]
  },
  {
    "category": "Places and directions",
    "words": [
      {
        "sv": "Här",
        "en": "Here",
        "type": "Adverb",
        "forms": "—"
      },
      {
        "sv": "Där",
        "en": "There",
        "type": "Adverb",
        "forms": "—"
      },
      {
        "sv": "Vänster",
        "en": "Left",
        "type": "Adjective/Noun",
        "forms": "Invariable"
      },
      {
        "sv": "Höger",
        "en": "Right",
        "type": "Adjective/Noun",
        "forms": "Invariable"
      },
      {
        "sv": "Upp",
        "en": "Up",
        "type": "Adverb",
        "forms": "—"
      },
      {
        "sv": "Ner",
        "en": "Down",
        "type": "Adverb",
        "forms": "—"
      },
      {
        "sv": "Framför",
        "en": "In front of",
        "type": "Preposition",
        "forms": "—"
      },
      {
        "sv": "Bakom",
        "en": "Behind",
        "type": "Preposition",
        "forms": "—"
      },
      {
        "sv": "Hus",
        "en": "House",
        "type": "Noun (ett)",
        "forms": "Definite: huset • Plural: hus • Def. plural: husen"
      },
      {
        "sv": "Affär",
        "en": "Store",
        "type": "Noun (en)",
        "forms": "Definite: affären • Plural: affärer • Def. plural: affärerna"
      },
      {
        "sv": "Restaurang",
        "en": "Restaurant",
        "type": "Noun (en)",
        "forms": "Definite: restaurangen • Plural: restauranger • Def. plural: restaurangerna"
      },
      {
        "sv": "Hotell",
        "en": "Hotel",
        "type": "Noun (ett)",
        "forms": "Definite: hotellet • Plural: hotell • Def. plural: hotellen"
      },
      {
        "sv": "Station",
        "en": "Station",
        "type": "Noun (en)",
        "forms": "Definite: stationen • Plural: stationer • Def. plural: stationerna"
      },
      {
        "sv": "Sjukhus",
        "en": "Hospital",
        "type": "Noun (ett)",
        "forms": "Definite: sjukhuset • Plural: sjukhus • Def. plural: sjukhusen"
      },
      {
        "sv": "Toalett",
        "en": "Toilet",
        "type": "Noun (en)",
        "forms": "Definite: toaletten • Plural: toaletter • Def. plural: toaletterna"
      }
    ]
  },
  {
    "category": "Colors and adjectives",
    "words": [
      {
        "sv": "Röd",
        "en": "Red",
        "type": "Adjective",
        "forms": "Neuter: rött • Plural: röda"
      },
      {
        "sv": "Blå",
        "en": "Blue",
        "type": "Adjective",
        "forms": "Neuter: blått • Plural: blåa"
      },
      {
        "sv": "Gul",
        "en": "Yellow",
        "type": "Adjective",
        "forms": "Neuter: gult • Plural: gula"
      },
      {
        "sv": "Grön",
        "en": "Green",
        "type": "Adjective",
        "forms": "Neuter: grönt • Plural: gröna"
      },
      {
        "sv": "Svart",
        "en": "Black",
        "type": "Adjective",
        "forms": "Neuter: svart • Plural: svarta"
      },
      {
        "sv": "Vit",
        "en": "White",
        "type": "Adjective",
        "forms": "Neuter: vitt • Plural: vita"
      },
      {
        "sv": "Stor",
        "en": "Big",
        "type": "Adjective",
        "forms": "Neuter: stort • Plural: stora"
      },
      {
        "sv": "Liten",
        "en": "Small",
        "type": "Adjective",
        "forms": "Neuter: litet • Plural: små (irregular)"
      },
      {
        "sv": "Varm",
        "en": "Hot/warm",
        "type": "Adjective",
        "forms": "Neuter: varmt • Plural: varma"
      },
      {
        "sv": "Kall",
        "en": "Cold",
        "type": "Adjective",
        "forms": "Neuter: kallt • Plural: kalla"
      },
      {
        "sv": "Bra",
        "en": "Good",
        "type": "Adjective",
        "forms": "Invariable"
      },
      {
        "sv": "Dålig",
        "en": "Bad",
        "type": "Adjective",
        "forms": "Neuter: dåligt • Plural: dåliga"
      },
      {
        "sv": "Ny",
        "en": "New",
        "type": "Adjective",
        "forms": "Neuter: nytt • Plural: nya"
      }
    ]
  },
  {
    "category": "Question words & prepositions",
    "words": [
      {
        "sv": "Vad",
        "en": "What",
        "type": "Pronoun",
        "forms": "—"
      },
      {
        "sv": "Var",
        "en": "Where",
        "type": "Adverb",
        "forms": "—"
      },
      {
        "sv": "När",
        "en": "When",
        "type": "Adverb",
        "forms": "—"
      },
      {
        "sv": "Varför",
        "en": "Why",
        "type": "Adverb",
        "forms": "—"
      },
      {
        "sv": "Hur",
        "en": "How",
        "type": "Adverb",
        "forms": "—"
      },
      {
        "sv": "Vem",
        "en": "Who",
        "type": "Pronoun",
        "forms": "Same form as subject/object"
      },
      {
        "sv": "Vilken",
        "en": "Which",
        "type": "Pronoun",
        "forms": "Neuter: vilket • Plural: vilka"
      },
      {
        "sv": "Hur mycket",
        "en": "How much",
        "type": "Phrase",
        "forms": "—"
      },
      {
        "sv": "Hur många",
        "en": "How many",
        "type": "Phrase",
        "forms": "—"
      },
      {
        "sv": "I",
        "en": "In",
        "type": "Preposition",
        "forms": "—"
      },
      {
        "sv": "På",
        "en": "On",
        "type": "Preposition",
        "forms": "—"
      },
      {
        "sv": "Under",
        "en": "Under/during",
        "type": "Preposition",
        "forms": "—"
      },
      {
        "sv": "Med",
        "en": "With",
        "type": "Preposition",
        "forms": "—"
      },
      {
        "sv": "Till",
        "en": "To",
        "type": "Preposition",
        "forms": "—"
      },
      {
        "sv": "Från",
        "en": "From",
        "type": "Preposition",
        "forms": "—"
      },
      {
        "sv": "Om",
        "en": "About/if",
        "type": "Preposition/Conjunction",
        "forms": "—"
      }
    ]
  },
  {
    "category": "Weather, family & professions",
    "words": [
      {
        "sv": "Väder",
        "en": "Weather",
        "type": "Noun (ett)",
        "forms": "Definite: vädret (uncountable)"
      },
      {
        "sv": "Sol",
        "en": "Sun",
        "type": "Noun (en)",
        "forms": "Definite: solen • Plural: solar • Def. plural: solarna"
      },
      {
        "sv": "Regn",
        "en": "Rain",
        "type": "Noun (ett)",
        "forms": "Definite: regnet (uncountable)"
      },
      {
        "sv": "Snö",
        "en": "Snow",
        "type": "Noun (en)",
        "forms": "Definite: snön (uncountable)"
      },
      {
        "sv": "Vind",
        "en": "Wind",
        "type": "Noun (en)",
        "forms": "Definite: vinden • Plural: vindar • Def. plural: vindarna"
      },
      {
        "sv": "Moln",
        "en": "Cloud",
        "type": "Noun (ett)",
        "forms": "Definite: molnet • Plural: moln • Def. plural: molnen"
      },
      {
        "sv": "Det regnar",
        "en": "It's raining",
        "type": "Phrase",
        "forms": "—"
      },
      {
        "sv": "Det är soligt",
        "en": "It's sunny",
        "type": "Phrase",
        "forms": "—"
      },
      {
        "sv": "Mamma",
        "en": "Mom",
        "type": "Noun (en)",
        "forms": "Definite: mamman • Plural: mammor • Def. plural: mammorna"
      },
      {
        "sv": "Pappa",
        "en": "Dad",
        "type": "Noun (en)",
        "forms": "Definite: pappan • Plural: pappor • Def. plural: papporna"
      },
      {
        "sv": "Syster",
        "en": "Sister",
        "type": "Noun (en)",
        "forms": "Definite: systern • Plural: systrar • Def. plural: systrarna"
      },
      {
        "sv": "Bror",
        "en": "Brother",
        "type": "Noun (en)",
        "forms": "Definite: brodern • Plural: bröder • Def. plural: bröderna (irregular)"
      },
      {
        "sv": "Dotter",
        "en": "Daughter",
        "type": "Noun (en)",
        "forms": "Definite: dottern • Plural: döttrar • Def. plural: döttrarna (irregular)"
      },
      {
        "sv": "Son",
        "en": "Son",
        "type": "Noun (en)",
        "forms": "Definite: sonen • Plural: söner • Def. plural: sönerna"
      },
      {
        "sv": "Lärare",
        "en": "Teacher",
        "type": "Noun (en)",
        "forms": "Definite: läraren • Plural: lärare • Def. plural: lärarna"
      },
      {
        "sv": "Läkare",
        "en": "Doctor",
        "type": "Noun (en)",
        "forms": "Definite: läkaren • Plural: läkare • Def. plural: läkarna"
      },
      {
        "sv": "Student",
        "en": "Student",
        "type": "Noun (en)",
        "forms": "Definite: studenten • Plural: studenter • Def. plural: studenterna"
      },
      {
        "sv": "Kock",
        "en": "Chef/cook",
        "type": "Noun (en)",
        "forms": "Definite: kocken • Plural: kockar • Def. plural: kockarna"
      },
      {
        "sv": "Polis",
        "en": "Police officer",
        "type": "Noun (en)",
        "forms": "Definite: polisen • Plural: poliser • Def. plural: poliserna"
      }
    ]
  },
  {
    "category": "More adjectives",
    "words": [
      {
        "sv": "Lätt",
        "en": "Easy/light",
        "type": "Adjective",
        "forms": "Neuter: lätt • Plural: lätta"
      },
      {
        "sv": "Svår",
        "en": "Difficult",
        "type": "Adjective",
        "forms": "Neuter: svårt • Plural: svåra"
      },
      {
        "sv": "Gammal",
        "en": "Old",
        "type": "Adjective",
        "forms": "Neuter: gammalt • Plural: gamla"
      },
      {
        "sv": "Snabb",
        "en": "Fast",
        "type": "Adjective",
        "forms": "Neuter: snabbt • Plural: snabba"
      },
      {
        "sv": "Långsam",
        "en": "Slow",
        "type": "Adjective",
        "forms": "Neuter: långsamt • Plural: långsamma"
      },
      {
        "sv": "Lång",
        "en": "Long/tall",
        "type": "Adjective",
        "forms": "Neuter: långt • Plural: långa"
      },
      {
        "sv": "Kort",
        "en": "Short",
        "type": "Adjective",
        "forms": "Neuter: kort • Plural: korta"
      },
      {
        "sv": "Stark",
        "en": "Strong",
        "type": "Adjective",
        "forms": "Neuter: starkt • Plural: starka"
      },
      {
        "sv": "Svag",
        "en": "Weak",
        "type": "Adjective",
        "forms": "Neuter: svagt • Plural: svaga"
      },
      {
        "sv": "Rolig",
        "en": "Fun",
        "type": "Adjective",
        "forms": "Neuter: roligt • Plural: roliga"
      },
      {
        "sv": "Tråkig",
        "en": "Boring",
        "type": "Adjective",
        "forms": "Neuter: tråkigt • Plural: tråkiga"
      },
      {
        "sv": "Vacker",
        "en": "Beautiful",
        "type": "Adjective",
        "forms": "Neuter: vackert • Plural: vackra"
      },
      {
        "sv": "Snäll",
        "en": "Kind",
        "type": "Adjective",
        "forms": "Neuter: snällt • Plural: snälla"
      }
    ]
  }
];
