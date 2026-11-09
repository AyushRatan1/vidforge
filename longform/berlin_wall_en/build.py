"""Builds the chapter specs for "The Night the Berlin Wall Fell" (English, 16:9, about 10 minutes).

    python longform/berlin_wall_en/build.py   -> longform/berlin_wall_en/ch01.json ... ch07.json

Facts checked against berlin.de (opening of the Wall), Chronik der Mauer / ZZF Potsdam (at least 140 deaths),
and the Imperial War Museum (155 km, 302 watchtowers, reunification 3 October 1990).
Stills are Pixabay images pinned by id (PICK) after reviewing the candidate sheets for subjects.json.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from kit import S, build, card, pin, tag, vid  # noqa: E402

PICK = {  # name -> Pixabay image id, chosen from the candidate sheets for subjects.json
    "brandenburg_night": 275437, "wall_graffiti": 745066, "map": 3483539, "berlin_city": 7285666, "cold_war": 2499826,
    "ddr": 2693088, "plattenbau": 4082213, "barbed_wire": 9906199, "wall_long": 4960488,
    "concrete": 1765900, "berlin_aerial": 8429780, "wall_segment": 113173, "searchlight": 3347052, "watchtower": 7402090,
    "bernauer": 972835, "checkpoint": 4394712, "brandenburg_day": 5117579,
    "east_side": 50730, "soldier": 1822503, "tunnel": 7558887, "balloon": 736879, "memorial_candles": 5757998,
    "memorial_cross": 1772560, "watchtower_night": 1670222,
    "soviet": 1045078, "tank": 3618383, "border_fence": 2104030, "field_border": 5421517, "leipzig": 3394376,
    "candles": 1577129, "alexanderplatz": 5289802,
    "old_documents": 350376, "microphones": 6839248, "press": 2654531, "television": 2619649, "checkpoint_night": 2676144,
    "crowd_night": 6129239, "barrier": 5174667, "celebration": 3387324, "brandenburg_night2": 417890, "hammer": 5275153,
    "trabant": 4539321, "reichstag": 2463236,
    "east_side2": 643065, "memorial": 113170, "wall_piece": 745072, "wall_long2": 745071, "brandenburg_dawn": 201939,
    "fireworks": 3372188,
}


def P(name, move="in"):
    return pin(PICK[name], move)


CHAPTERS = [
    ("ch01", "A City Cut in Two", [
        S("On the night of November the ninth, 1989, a government spokesman fumbled a single sentence at a press conference. Within five hours, the most famous wall on Earth was open.",
          P("brandenburg_night", "in")),
        S("This is the story of how the Berlin Wall went up overnight, how people risked everything to cross it, and how it came down by accident.",
          P("wall_graffiti", "left")),
        S("To understand that night, we have to go back to 1945. Nazi Germany had surrendered, and the four victors, America, Britain, France and the Soviet Union, split Germany into four zones.",
          P("map", "in"), card("Chapter 1: A City Cut in Two")),
        S("Berlin sat deep inside the Soviet zone, but as the capital it was divided four ways too. Its western half became an island of the West, more than 150 kilometres inside the East.",
          P("berlin_city", "right")),
        S("In 1949 the zones hardened into two countries. In the West, the Federal Republic, a democracy allied with America. In the East, the German Democratic Republic, a one-party state backed by Moscow.",
          P("cold_war", "in")),
        S("And people voted with their feet. By 1961, around three and a half million East Germans had left for the West, many of them young, skilled and educated.",
          P("ddr", "left"), tag("3.5 million left", at_word="three")),
        S("Doctors, engineers and teachers were leaving by the thousands every week. In Berlin, escaping was as easy as taking a train across town.",
          P("plattenbau", "right")),
        S("Then, on the night of August the twelfth, 1961, soldiers and workers rolled out barbed wire along the border through the city. Berliners woke up on Sunday morning to find their city cut in two.",
          P("barbed_wire", "in"), tag("13 August 1961", at_word="Sunday")),
        S("East Germany called it the Anti-Fascist Protection Rampart, a shield against the West. Everyone else simply called it the Wall.",
          P("wall_long", "left")),
    ]),
    ("ch02", "Anatomy of a Wall", [
        S("Within days, the wire turned into concrete. Over the years the Wall was rebuilt again and again, and by the 1980s it was not just a wall. It was a system.",
          P("concrete", "in"), card("Chapter 2: Anatomy of a Wall")),
        S("It ran for about 155 kilometres, completely encircling West Berlin. Around 43 kilometres of it cut straight through the middle of the city.",
          P("berlin_aerial", "out"), tag("155 km around West Berlin", at_word="155")),
        S("The final version was made of prefabricated concrete slabs about three and a half metres high, topped with a smooth round pipe so that nobody could get a grip.",
          P("wall_segment", "up")),
        S("Behind it lay the death strip: raked sand that showed every footprint, trip wires, anti-vehicle trenches, guard dogs, and floodlights that turned night into day.",
          P("searchlight", "in"), tag("The death strip", at_word="death")),
        S("Watching it all were around 300 watchtowers, staffed by guards whose orders were to stop escapes by any means, including firearms.",
          P("watchtower", "up"), tag("302 watchtowers", at_word="300")),
        S("Families were split overnight. On Bernauer Strasse, the pavement belonged to the West while the houses belonged to the East, and people jumped from their windows to reach freedom.",
          P("bernauer", "left")),
        S("Checkpoint Charlie, the most famous crossing, became a stage for the Cold War. In October 1961, American and Soviet tanks faced each other there for about sixteen hours.",
          P("checkpoint", "in"), tag("Checkpoint Charlie", at_word="Checkpoint")),
        S("Two American presidents came to speak in its shadow. In 1963, John F. Kennedy declared: Ich bin ein Berliner. In 1987, Ronald Reagan stood near the Brandenburg Gate and said: Mr. Gorbachev, tear down this wall.",
          P("brandenburg_day", "out")),
    ]),
    ("ch03", "Over, Under, Through", [
        S("Despite all of this, people kept trying. Around five thousand people escaped across the Berlin Wall in its twenty eight years.",
          P("east_side", "left"), card("Chapter 3: Over, Under, Through")),
        S("Two days after the wire went up, a nineteen year old border guard named Conrad Schumann leapt over the barbed wire into the West. A photographer caught the moment, and the picture went around the world.",
          P("soldier", "in"), tag("Conrad Schumann, 15 Aug 1961", at_word="Schumann")),
        S("Others went underground. In October 1964, fifty seven people crawled to freedom through a tunnel about 145 metres long, dug from an old bakery in West Berlin, beneath the death strip.",
          P("tunnel", "in"), tag("Tunnel 57", at_word="tunnel")),
        S("People hid in car boots, used forged passports, and once even slid across on a homemade zip line. In 1979, two families escaped East Germany in a hot air balloon sewn together from scraps of fabric.",
          P("balloon", "up")),
        S("Many did not make it. Researchers have documented at least 140 people who were killed at the Berlin Wall, or died because of it.",
          P("memorial_candles", "in"), tag("At least 140 deaths", at_word="140")),
        S("In August 1962, eighteen year old Peter Fechter was shot while climbing the Wall and fell back into the death strip. He bled for nearly an hour in full view of the West, and no one came to help.",
          P("memorial_cross", "in")),
        S("The last person shot dead trying to cross was Chris Gueffroy, aged twenty, in February 1989. Nine months later, the Wall would be open.",
          P("watchtower_night", "out")),
    ]),
    ("ch04", "Cracks Appear", [
        S("By the late 1980s, the Soviet bloc was in trouble. Its economies were stagnating, and in Moscow, Mikhail Gorbachev was preaching openness and reform.",
          P("soviet", "in"), card("Chapter 4: Cracks Appear")),
        S("Crucially, Moscow signalled that it would no longer send tanks to keep its allies in line.",
          P("tank", "left")),
        S("The first crack came from Hungary. In May 1989, Hungary began tearing down its fence on the Austrian border. That summer, thousands of East Germans went there on holiday and simply never came back.",
          P("border_fence", "right"), tag("Hungary, 1989", at_word="Hungary.")),
        S("In August, at a so-called Pan-European Picnic on the border, hundreds slipped through a gate into Austria. On September the eleventh, Hungary opened its border completely, and tens of thousands left.",
          P("field_border", "left")),
        S("Inside East Germany, people found their voice. Every Monday in Leipzig, crowds gathered after prayers at the Nikolai Church and marched through the city, chanting: we are the people.",
          P("leipzig", "in"), tag("Wir sind das Volk", at_word="chanting:")),
        S("On October the ninth, about seventy thousand people marched in Leipzig. Many feared a massacre. But the security forces did not shoot.",
          P("candles", "in")),
        S("Nine days later, the long-time leader Erich Honecker was pushed out. On November the fourth, a crowd often put at half a million people filled Alexanderplatz in East Berlin, demanding free speech and free travel.",
          P("alexanderplatz", "up")),
    ]),
    ("ch05", "One Sentence", [
        S("The new leadership decided to relieve the pressure with new travel rules. People would be able to apply for exit visas, and the rules would start the next day, with the border still under control.",
          P("old_documents", "in"), card("Chapter 5: One Sentence")),
        S("On the evening of November the ninth, Politburo spokesman Günter Schabowski was handed a note about the new rules shortly before a live press conference. Nobody had briefed him on the details.",
          P("microphones", "in")),
        S("Near the end, almost as an afterthought, he read it out. A journalist asked: when does this take effect? Schabowski shuffled his papers and said: as far as I know, immediately, without delay.",
          P("press", "in"), tag("“Immediately, without delay.”", at_word="immediately,")),
        S("It was just before seven in the evening. By eight, West German television was reporting that East Germany had opened its border, and East Berliners, who watched Western TV, heard it too.",
          P("television", "in"), tag("7 pm, 9 November 1989", at_word="seven")),
        S("Thousands headed for the checkpoints. The border guards had received no orders at all. Nobody had told them anything.",
          P("checkpoint_night", "left")),
    ]),
    ("ch06", "The Night", [
        S("The pressure was worst at the Bornholmer Strasse crossing. As the crowd grew into the thousands, chanting open the gate, the officer in charge, Harald Jäger, kept calling his superiors. Nobody would decide.",
          P("crowd_night", "in"), card("Chapter 6: The Night")),
        S("At about half past eleven, with no official order, he gave in. The barrier went up. In the next hour, around twenty thousand people walked across the bridge without being checked.",
          P("barrier", "up"), tag("11:30 pm: the gate opens", at_word="eleven,")),
        S("One by one, the other crossings opened. Strangers hugged, cried and shared drinks. West Berliners greeted the East with flowers and applause.",
          P("celebration", "in")),
        S("Before long, people were dancing on top of the Wall at the Brandenburg Gate, the very place where, a year earlier, guards would have shot them.",
          P("brandenburg_night2", "out")),
        S("In the days that followed, Berliners attacked the Wall with hammers and chisels. They were nicknamed Mauerspechte, the wall woodpeckers.",
          P("hammer", "in"), tag("Mauerspechte", at_word="Mauerspechte,")),
        S("That first weekend, millions of East Germans visited the West. Each was offered one hundred Deutschmarks of welcome money to spend.",
          P("trabant", "left")),
        S("Less than a year later, on October the third, 1990, the two German states were reunited. Within two more years, the Soviet Union itself was gone.",
          P("reichstag", "in"), tag("3 October 1990", at_word="third,")),
    ]),
    ("ch07", "What Remains", [
        S("Today, only fragments of the Wall still stand. The longest, the East Side Gallery, runs for about one point three kilometres along the River Spree, covered in murals.",
          P("east_side2", "left"), card("Chapter 7: What Remains")),
        S("A double row of cobblestones traces where the Wall once ran through the city, and on Bernauer Strasse a memorial preserves a stretch of the death strip as it was.",
          P("memorial", "in")),
        S("Pieces of the Wall are now scattered around the world, standing in museums, parks and embassies on almost every continent.",
          P("wall_piece", "in")),
        S("And here is the strangest fact of all. The Berlin Wall has now been gone for longer than it ever stood. It stood for twenty eight years. It fell thirty seven years ago today.",
          P("wall_long2", "right"), tag("Stood 28 years. Gone 37.", at_word="strangest")),
        S("It went up in one night, and it opened in one night, because of one fumbled sentence. History, it turns out, can turn on very small things.",
          P("brandenburg_dawn", "out")),
        S("Which part of this story surprised you most? Tell us in the comments, and subscribe to Hypercurious for more stories from history.",
          P("fireworks", "in"), tag("Subscribe: Hypercurious", at_word="subscribe")),
    ]),
]

BASE = {
    "language": "en", "voice": "bm_george", "speed": 1.0, "aspect": "16:9", "made_for_kids": False,
    "category": "education", "footage": "auto", "transition": "fade",
    "music": {"mood": "mystery", "volume": 0.08},
    "captions": {"style": "karaoke", "y": 0.9, "size": 0.026, "max_words": 7, "highlight": "#ffd54a",
                 "box": "#000000", "box_alpha": 0.45, "uppercase": False},
    "overlay": {"handle": "@hypercurious96", "progress_bar": False},
}

if __name__ == "__main__":
    build(HERE, CHAPTERS, BASE, "The Night the Berlin Wall Fell, part {k}: {title}", seed=300)
