"""Builds the 'Space Is Weird' English series specs (what the writer agent produces, hand-checked).

Facts and sources:
- Voyager 1 reaches 1 light-day (25.9 billion km, 173 AU) on 18 Nov 2026; launched 5 Sep 1977; most instruments off.
  https://earthsky.org/space/voyager-1-1-light-day-from-earth-november-17-18-2026/
- HD 189733b: ~64 light-years, blue from silicate (glass) particles, ~930 C day side, ~5,400 mph winds.
  https://www.space.com/22614-blue-alien-planet-glass-rain.html  https://science.nasa.gov/resource/blue-and-bizarre/
- Neutron stars: ~20 km wide, 1-2 solar masses, sugar cube ~1 billion tons, fastest spin 716/s.
  https://www.space.com/22180-neutron-stars.html
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
BOLT = {"type": "character", "id": "bolt", "species": "robot", "color": "#8fa3b8", "talking": True}
YEL = "#ffd400"


def badge(n):
    return {"type": "text", "text": f"SPACE IS WEIRD · #{n}", "y": 0.085, "size": 0.038, "style": "label",
            "bg": "#7c3aed", "bg_alpha": 0.92, "stroke": False, "enter": "fade", "at": 0}


def pill(text, y, color="#1d2b53", **kw):
    return {"type": "text", "text": text, "y": y, "size": kw.pop("size", 0.055), "bg": color, "bg_alpha": 0.92,
            "stroke": False, "enter": kw.pop("enter", "pop"), **kw}


def base(n, title, desc, tags, mood, seed):
    return {"title": title, "description": desc + "\n\nPart of the Space Is Weird series. Visuals and voice are AI-assisted.",
            "tags": tags + ["space", "space facts", "astronomy", "shorts"], "language": "en", "voice": "af_heart",
            "speed": 1.05, "aspect": "9:16", "made_for_kids": False, "category": "science",
            "music": {"mood": mood, "volume": 0.16, "seed": seed},
            "captions": {"style": "karaoke", "y": 0.745, "size": 0.07, "max_words": 3, "highlight": YEL, "uppercase": True},
            "overlay": {"handle": "@vidforge.cosmos", "progress_bar": True, "bar_color": "#a78bfa"},
            "thumbnail": {"scene": 0, "t": 1.6}, "transition": "fade", "scenes": []}


SPACE = {"type": "space", "stars": 280, "shooting": False}

# ------------------------------------------------------------------ EP1 Voyager
ep1 = base(1, "This Spacecraft Is Now One Light-Day From Earth 🤯 #Shorts",
           "On 18 November 2026, Voyager 1 becomes the first human-made object one light-day (25.9 billion km) from Earth. "
           "Launched in 1977, it still phones home.\nSource: NASA via EarthSky.",
           ["Voyager 1", "light day", "NASA", "deep space"], "cosmic", 21)
ep1["scenes"] = [
    {"id": "hook", "narration": "On November eighteenth, a spacecraft launched in nineteen seventy-seven will be one full light-day from Earth.",
     "caption": "On November 18th, a spacecraft launched in 1977 will be one full light-day from Earth.",
     "background": SPACE, "camera": {"zoom": [1.0, 1.08]}, "sfx": [{"kind": "whoosh", "at": 0}],
     "elements": [badge(1),
                  {"type": "text", "text": "NOV 18, 2026", "y": 0.16, "size": 0.12, "color": YEL, "enter": "pop", "at": 0.1},
                  {"type": "text", "text": "1 LIGHT-DAY FROM EARTH", "y": 0.24, "size": 0.06, "enter": "slide_up", "at": 0.5},
                  {"type": "prop", "name": "voyager", "x": 0.55, "y": 0.47, "size": 0.16, "enter": "fade", "at": 0,
                   "keys": [{"t": 0, "scale": 1.15}, {"t": 7, "scale": 0.85}], "behaviors": [{"kind": "float", "amp": 0.01, "period": 3.5}]},
                  {**BOLT, "x": 0.15, "y": 0.62, "r": 0.06, "look": [0.6, -0.4], "enter": "pop", "at": 0.3}]},
    {"id": "signal", "narration": "That's Voyager one. It's so far away that a radio message, moving at the speed of light, takes a whole day to reach it.",
     "caption": "That's Voyager 1. It's so far away that a radio message, moving at the speed of light, takes a whole day to reach it.",
     "background": SPACE,
     "elements": [{"type": "planet", "style": "earth", "x": 0.13, "y": 0.42, "r": 0.075},
                  {"type": "prop", "name": "voyager", "x": 0.87, "y": 0.42, "size": 0.06},
                  {"type": "shape", "shape": "line", "x": 0.5, "y": 0.42, "from": [-0.3, 0], "to": [0.3, 0], "dashed": True,
                   "color": "#7dd3fc", "stroke_w": 0.005, "enter": "draw", "at": 0.3, "enter_dur": 1.0},
                  {"type": "shape", "shape": "circle", "w": 0.035, "color": "#7dff9a", "y": 0.42,
                   "keys": [{"t": 1.2, "x": 0.2}, {"t": 6.5, "x": 0.8, "ease": "linear"}], "at": 1.2, "enter": "pop",
                   "behaviors": [{"kind": "pulse", "amp": 0.25, "period": 0.5}]},
                  {"type": "text", "text": "AT LIGHT SPEED ⚡", "y": 0.3, "size": 0.05, "enter": "fade", "at_word": "speed"},
                  {"type": "counter", "from": 0, "to": 24, "suffix": " HOURS", "grouping": "none", "y": 0.58, "size": 0.12,
                   "color": YEL, "enter": "pop", "at_word": "whole", "count_dur": 1.6}]},
    {"id": "distance", "narration": "One light-day is about twenty-six billion kilometers. That's a hundred and seventy-three times farther than the Sun.",
     "caption": "One light-day is about 26 billion km. That's 173 times farther than the Sun.",
     "background": SPACE,
     "elements": [{"type": "counter", "from": 0, "to": 25.9, "decimals": 1, "suffix": " BILLION KM", "grouping": "none",
                   "y": 0.16, "size": 0.085, "color": YEL, "enter": "pop", "at": 0.3, "count_dur": 1.8},
                  {"type": "text", "text": "(16.1 billion miles)", "y": 0.225, "size": 0.042, "color": "#9fb3d1", "stroke": False, "enter": "fade", "at": 1.6},
                  {"type": "planet", "style": "sun", "x": 0.1, "y": 0.43, "r": 0.04},
                  {"type": "planet", "style": "earth", "x": 0.18, "y": 0.43, "r": 0.015, "glow": False},
                  {"type": "text", "text": "SUN TO EARTH = 1×", "x": 0.3, "y": 0.36, "size": 0.04, "width": 0.5, "enter": "fade", "at": 0.8},
                  {"type": "shape", "shape": "arrow", "x": 0.5, "y": 0.5, "from": [-0.4, 0], "to": [0.38, 0], "color": YEL,
                   "stroke_w": 0.008, "enter": "draw", "at_word": "hundred", "enter_dur": 1.4},
                  {"type": "prop", "name": "voyager", "x": 0.92, "y": 0.5, "size": 0.035, "enter": "fade", "at_word": "hundred"},
                  {"type": "text", "text": "VOYAGER = 173×", "y": 0.59, "size": 0.07, "color": YEL, "enter": "pop", "at_word": "times"}]},
    {"id": "speed", "narration": "It's flying at about seventeen kilometers every second. That's London to New York in under six minutes.",
     "caption": "It's flying at about 17 km every second. That's London to New York in under 6 minutes.",
     "background": SPACE,
     "elements": [{"type": "particles", "kind": "stream", "y": 0.42, "angle": 0, "thickness": 0.5, "speed": -0.9, "streak": 0.05,
                   "color": "#ffffff", "count": 60},
                  {"type": "counter", "from": 0, "to": 17, "suffix": " KM/S", "grouping": "none", "y": 0.17, "size": 0.14,
                   "color": YEL, "enter": "pop", "at": 0.2, "count_dur": 1.4},
                  {"type": "prop", "name": "voyager", "y": 0.42, "size": 0.09, "rot": -8,
                   "keys": [{"t": 0, "x": 0.25}, {"t": 6, "x": 0.75, "ease": "in_out"}]},
                  pill("LONDON ✈️ NEW YORK: < 6 MIN", 0.6, at_word="London")]},
    {"id": "power", "narration": "After forty-nine years in space, most of its instruments are switched off to save power. But it still phones home.",
     "caption": "After 49 years in space, most of its instruments are switched off to save power. But it still phones home.",
     "background": SPACE,
     "elements": [{"type": "text", "text": "49 YEARS", "y": 0.15, "size": 0.12, "color": YEL, "enter": "pop", "at": 0.2},
                  {"type": "prop", "name": "voyager", "x": 0.5, "y": 0.4, "size": 0.14, "behaviors": [{"kind": "float", "amp": 0.01, "period": 3}]},
                  {"type": "emoji", "text": "🔋", "x": 0.22, "y": 0.6, "size": 0.1, "enter": "pop", "at_word": "power"},
                  {"type": "emoji", "text": "📡", "x": 0.78, "y": 0.6, "size": 0.1, "enter": "pop", "at_word": "phones"}]},
    {"id": "record", "narration": "And on board is a golden record, with sounds and pictures of Earth, for anyone who might find it.",
     "background": SPACE,
     "elements": [{"type": "text", "text": "THE GOLDEN RECORD", "y": 0.14, "size": 0.075, "color": "#ffcf4a", "enter": "pop", "at_word": "golden"},
                  {"type": "prop", "name": "record", "x": 0.5, "y": 0.4, "size": 0.19, "enter": "spin_in", "at_word": "golden"},
                  {"type": "particles", "kind": "sparkles", "count": 22, "at_word": "golden"},
                  {"type": "text", "text": "🎵 SOUNDS  •  🖼️ PICTURES", "y": 0.6, "size": 0.05, "enter": "slide_up", "at_word": "sounds"}]},
    {"id": "next", "narration": "Next up: a blue planet where it rains glass. Sideways. Follow so you don't miss it.",
     "background": SPACE, "hold": 0.5,
     "elements": [pill("NEXT ▶", 0.12, "#7c3aed", size=0.05),
                  {"type": "text", "text": "IT RAINS GLASS 🌧️", "y": 0.2, "size": 0.085, "color": YEL, "enter": "pop", "at": 0.3},
                  {"type": "planet", "style": "exoplanet", "color": "#2f6bff", "x": 0.5, "y": 0.42, "r": 0.15},
                  {"type": "particles", "kind": "stream", "y": 0.42, "angle": 8, "thickness": 0.35, "speed": 1.1, "streak": 0.045,
                   "color": "#d9f3ff", "count": 70, "at_word": "Sideways"},
                  {**BOLT, "x": 0.15, "y": 0.6, "r": 0.06, "wave": True, "enter": "pop", "at": 0.2},
                  pill("FOLLOW FOR PART 2", 0.62, "#ff3b5c", at_word="Follow", behaviors=[{"kind": "pulse", "amp": 0.04, "period": 1.2}])]},
]

# ------------------------------------------------------------------ EP2 Glass rain
GLASS = {"type": "particles", "kind": "stream", "y": 0.43, "angle": 8, "thickness": 0.6, "speed": 1.2, "streak": 0.05,
         "color": "#d9f3ff", "count": 120}
ep2 = base(2, "The Planet Where It Rains Glass… Sideways 🌧️ #Shorts",
           "HD 189733b is a blue gas giant about 64 light-years away. Its sky is full of glass (silicate) particles, it's around 930 °C, "
           "and winds of about 5,400 mph blow the glass sideways.\nSources: NASA, Space.com.",
           ["HD 189733b", "exoplanet", "glass rain", "hot Jupiter"], "mystery", 5)
BLUE = {"type": "planet", "style": "exoplanet", "color": "#2f6bff"}
ep2["scenes"] = [
    {"id": "hook", "narration": "There's a planet where it rains glass. Sideways.", "background": SPACE,
     "camera": {"zoom": [1.0, 1.1]}, "sfx": [{"kind": "whoosh", "at": 0}],
     "elements": [badge(2), {**BLUE, "x": 0.5, "y": 0.43, "r": 0.22},
                  {**GLASS},
                  {"type": "text", "text": "IT RAINS GLASS", "y": 0.16, "size": 0.11, "color": YEL, "enter": "pop", "at": 0.1},
                  {"type": "text", "text": "SIDEWAYS 💨", "y": 0.245, "size": 0.07, "enter": "slide_left", "at_word": "Sideways"},
                  {**BOLT, "x": 0.15, "y": 0.63, "r": 0.06, "expression": "surprised", "enter": "pop", "at": 0.3}]},
    {"id": "name", "narration": "Meet H D one eight nine seven three three b. A giant gas planet, about sixty-four light-years away.",
     "caption": "Meet HD 189733b. A giant gas planet, about 64 light-years away.", "background": SPACE,
     "elements": [{"type": "planet", "style": "sun", "x": -0.05, "y": 0.4, "r": 0.22},
                  pill("HD 189733 b", 0.14, size=0.07),
                  {**BLUE, "x": 0.6, "y": 0.4, "r": 0.15, "enter": "pop", "at": 0.2},
                  {"type": "counter", "from": 0, "to": 64, "suffix": " LIGHT-YEARS", "grouping": "none", "y": 0.6, "size": 0.075,
                   "color": YEL, "enter": "pop", "at_word": "sixty", "count_dur": 1.2}]},
    {"id": "looks", "narration": "From far away, it looks calm and blue. A lot like Earth.", "background": SPACE,
     "elements": [{"type": "text", "text": "LOOKS FAMILIAR?", "y": 0.15, "size": 0.085, "enter": "pop", "at": 0.2},
                  {"type": "planet", "style": "earth", "x": 0.28, "y": 0.4, "r": 0.1, "enter": "pop", "at": 0.8},
                  {**BLUE, "x": 0.7, "y": 0.4, "r": 0.17},
                  {"type": "text", "text": "EARTH", "x": 0.28, "y": 0.55, "size": 0.045, "width": 0.4, "enter": "fade", "at": 1.0},
                  {"type": "text", "text": "HD 189733b", "x": 0.7, "y": 0.58, "size": 0.045, "width": 0.5, "enter": "fade", "at": 0.4}]},
    {"id": "heat", "narration": "But it's nearly a thousand degrees Celsius there. Hot enough to melt aluminum.",
     "caption": "But it's nearly 1,000 °C there. Hot enough to melt aluminum.",
     "background": {"type": "space", "stars": 200, "shooting": False, "nebula": ["#7a1d0b", "#5a1226", "#2a0b3a"]},
     "elements": [{"type": "counter", "from": 0, "to": 930, "suffix": " °C", "grouping": "none", "y": 0.18, "size": 0.15,
                   "color": "#ff7a3d", "enter": "pop", "at": 0.3, "count_dur": 1.6},
                  {**BLUE, "x": 0.5, "y": 0.42, "r": 0.14, "glow": True},
                  {"type": "emoji", "text": "🔥", "x": 0.8, "y": 0.33, "size": 0.1, "enter": "pop", "at": 1.0,
                   "behaviors": [{"kind": "wiggle", "amp": 4, "period": 2}]},
                  pill("MELTS ALUMINUM", 0.6, "#b4321a", at_word="melt")]},
    {"id": "blue", "narration": "Its deep blue color likely comes from tiny particles of glass, called silicates, floating in its sky.",
     "background": SPACE,
     "elements": [{**BLUE, "x": 0.5, "y": 0.4, "r": 0.26},
                  {"type": "text", "text": "WHY SO BLUE?", "y": 0.14, "size": 0.085, "color": "#7fb2ff", "enter": "pop", "at": 0.2},
                  {"type": "shape", "shape": "ring", "x": 0.5, "y": 0.4, "w": 0.6, "color": "#9fd3ff", "stroke_w": 0.012, "enter": "grow", "at": 0.5},
                  {"type": "particles", "kind": "stream", "y": 0.4, "angle": 8, "thickness": 0.12, "speed": 0.15, "color": "#d9f3ff", "count": 45},
                  {"type": "particles", "kind": "sparkles", "count": 20, "color": "#cfe8ff", "at_word": "glass"},
                  pill("GLASS = SILICATES", 0.6, at_word="silicates")]},
    {"id": "wind", "narration": "And winds of about fifty-four hundred miles per hour hurl that glass sideways. That's around seven times the speed of sound.",
     "caption": "And winds of about 5,400 mph hurl that glass sideways. That's around 7× the speed of sound.",
     "background": SPACE, "camera": {"zoom": [1.0, 1.06], "shake": True},
     "elements": [{**BLUE, "x": 0.5, "y": 0.45, "r": 0.15},
                  {**GLASS, "y": 0.45, "count": 160, "speed": 1.6},
                  {"type": "counter", "from": 0, "to": 5400, "suffix": " MPH", "grouping": "none", "y": 0.16, "size": 0.13,
                   "color": YEL, "enter": "pop", "at_word": "fifty", "count_dur": 1.4},
                  {"type": "text", "text": "(about 8,700 km/h)", "y": 0.23, "size": 0.042, "color": "#9fb3d1", "stroke": False, "enter": "fade", "at_word": "miles"},
                  pill("7× THE SPEED OF SOUND", 0.62, "#ff3b5c", at_word="seven")]},
    {"id": "next", "narration": "Next: a star so dense, a single sugar cube of it weighs a billion tons. Follow for part three.",
     "background": SPACE, "hold": 0.5,
     "elements": [pill("NEXT ▶", 0.12, "#7c3aed", size=0.05),
                  {"type": "text", "text": "A BILLION-TON SUGAR CUBE", "y": 0.2, "size": 0.07, "color": YEL, "enter": "pop", "at": 0.3},
                  {"type": "planet", "style": "neutron_star", "x": 0.5, "y": 0.42, "r": 0.035, "beam_speed": 80},
                  {"type": "shape", "shape": "rect", "x": 0.78, "y": 0.3, "w": 0.08, "h": 0.08, "radius": 0.01,
                   "gradient": ["#ffffff", "#d9dee6"], "stroke": "#aab4c0", "stroke_w": 0.003, "enter": "drop", "at_word": "sugar"},
                  {**BOLT, "x": 0.15, "y": 0.6, "r": 0.06, "wave": True, "enter": "pop", "at": 0.2},
                  pill("FOLLOW FOR PART 3", 0.62, "#ff3b5c", at_word="Follow", behaviors=[{"kind": "pulse", "amp": 0.04, "period": 1.2}])]},
]

# ------------------------------------------------------------------ EP3 Neutron star
NS = {"type": "planet", "style": "neutron_star"}
ep3 = base(3, "A Sugar Cube of This Star Weighs a Billion Tons 😳 #Shorts",
           "Neutron stars pack the mass of the Sun (or more) into a ball about 20 km wide. A sugar cube of neutron-star matter "
           "would weigh around a billion tons, and the fastest known one spins 716 times a second.\nSource: Space.com.",
           ["neutron star", "pulsar", "dense", "supernova"], "epic", 9)
ep3["thumbnail"] = {"scene": 0, "t": 2.8}
ep3["scenes"] = [
    {"id": "hook", "narration": "A sugar cube made of this star would weigh about a billion tons.",
     "caption": "A sugar cube made of this star would weigh about 1 billion tons.", "background": SPACE,
     "camera": {"zoom": [1.0, 1.08]}, "sfx": [{"kind": "whoosh", "at": 0}],
     "elements": [badge(3), {**NS, "x": 0.5, "y": 0.4, "r": 0.05, "beam_speed": 70},
                  {"type": "counter", "from": 0, "to": 1000000000, "suffix": " TONS", "grouping": "none", "y": 0.17, "size": 0.085,
                   "color": YEL, "enter": "pop", "at": 0.2, "count_dur": 2.2},
                  {"type": "shape", "shape": "rect", "x": 0.5, "y": 0.6, "w": 0.1, "h": 0.1, "radius": 0.012,
                   "gradient": ["#ffffff", "#d9dee6"], "stroke": "#aab4c0", "stroke_w": 0.003, "enter": "drop", "at_word": "sugar"},
                  {"type": "text", "text": "1 SUGAR CUBE", "x": 0.77, "y": 0.6, "size": 0.04, "width": 0.4, "enter": "fade", "at_word": "sugar"},
                  {**BOLT, "x": 0.15, "y": 0.63, "r": 0.06, "expression": "surprised", "enter": "pop", "at": 0.3}]},
    {"id": "collapse", "narration": "It's a neutron star, the crushed core left behind when a giant star explodes.", "background": SPACE,
     "elements": [{"type": "planet", "style": "sun", "color": "#ff6b3d", "x": 0.5, "y": 0.4, "r": 0.2, "until": 2.9, "exit": "pop",
                   "keys": [{"t": 0, "scale": 1.0}, {"t": 1.6, "scale": 1.08}, {"t": 2.9, "scale": 0.12, "ease": "in"}]},
                  {"type": "particles", "kind": "confetti", "count": 60, "colors": ["#ffd166", "#ff7a3d", "#ffffff"], "at": 2.9, "until": 4.2},
                  {**NS, "x": 0.5, "y": 0.4, "r": 0.04, "enter": "pop", "at": 2.9, "beam_speed": 90},
                  {"type": "text", "text": "SUPERNOVA 💥", "y": 0.15, "size": 0.09, "color": "#ff9a3d", "enter": "pop", "at": 2.8},
                  {"type": "text", "text": "NEUTRON STAR", "y": 0.6, "size": 0.07, "color": YEL, "enter": "pop", "at": 3.2}]},
    {"id": "size", "narration": "It packs the mass of our Sun, or more, into a ball about twenty kilometers wide. Roughly the size of a city.",
     "caption": "It packs the mass of our Sun, or more, into a ball about 20 km wide. Roughly the size of a city.", "background": SPACE,
     "elements": [{"type": "text", "text": "SAME MASS ⚖️", "y": 0.13, "size": 0.085, "enter": "pop", "at": 0.2},
                  {"type": "planet", "style": "sun", "x": 0.27, "y": 0.38, "r": 0.19},
                  {"type": "text", "text": "=", "x": 0.6, "y": 0.38, "size": 0.12, "enter": "pop", "at": 1.0},
                  {**NS, "x": 0.8, "y": 0.38, "r": 0.02, "beams": False, "enter": "pop", "at": 1.2},
                  {"type": "text", "text": "THE SUN", "x": 0.27, "y": 0.56, "size": 0.045, "width": 0.4, "enter": "fade", "at": 0.6},
                  {"type": "text", "text": "~20 KM 🏙️", "x": 0.8, "y": 0.47, "size": 0.05, "width": 0.4, "color": YEL, "enter": "pop", "at_word": "twenty"}]},
    {"id": "spin", "narration": "And some of them spin over seven hundred times every second.",
     "caption": "And some of them spin over 700 times every second.", "background": SPACE,
     "elements": [{**NS, "x": 0.5, "y": 0.42, "r": 0.05, "beam_speed": 540, "beam_length": 12},
                  {"type": "counter", "from": 0, "to": 716, "suffix": " SPINS / SEC", "grouping": "none", "y": 0.16, "size": 0.09,
                   "color": YEL, "enter": "pop", "at_word": "seven", "count_dur": 1.4},
                  pill("FASTEST KNOWN: 716 PER SECOND", 0.63, size=0.045, at_word="second")]},
    {"id": "pulsar", "narration": "Their beams sweep across space like a lighthouse, so we see them blink. We call them pulsars.",
     "background": SPACE,
     "elements": [{**NS, "x": 0.5, "y": 0.4, "r": 0.04, "beam_speed": 110, "beam_length": 14},
                  {"type": "planet", "style": "earth", "x": 0.85, "y": 0.6, "r": 0.03},
                  {"type": "text", "text": "LIKE A LIGHTHOUSE 🔦", "y": 0.14, "size": 0.065, "enter": "pop", "at_word": "lighthouse"},
                  {"type": "text", "text": "PULSAR", "y": 0.62, "size": 0.1, "color": YEL, "enter": "pop", "at_word": "pulsars"}]},
    {"id": "next", "narration": "Next time: what really happens if you fall into a black hole. Follow so you don't miss it.",
     "background": SPACE, "hold": 0.5,
     "elements": [pill("NEXT ▶", 0.12, "#7c3aed", size=0.05),
                  {"type": "text", "text": "FALLING INTO A BLACK HOLE", "y": 0.2, "size": 0.065, "color": YEL, "enter": "pop", "at": 0.3},
                  {"type": "planet", "style": "black_hole", "x": 0.5, "y": 0.42, "r": 0.09},
                  {**BOLT, "x": 0.15, "y": 0.6, "r": 0.06, "wave": True, "enter": "pop", "at": 0.2},
                  pill("FOLLOW FOR PART 4", 0.62, "#ff3b5c", at_word="Follow", behaviors=[{"kind": "pulse", "amp": 0.04, "period": 1.2}])]},
]

for name, spec in (("space_is_weird_01_voyager", ep1), ("space_is_weird_02_glass_rain", ep2), ("space_is_weird_03_neutron_star", ep3)):
    with open(os.path.join(HERE, name + ".json"), "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=1)
    print("wrote", name)
