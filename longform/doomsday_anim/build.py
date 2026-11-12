"""Builds the animated 9:16 Short "Doomsday: Friday 13 November 2026" (English, about 100 seconds) as ch01.json.

    python longform/doomsday_anim/build.py

A what-if: the 1960 Science paper by von Foerster, Mora and Amiot ("Doomsday: Friday, 13 November, AD 2026") extrapolated
population growth to infinity on that date. We play the scenario out (3D: a planet from space, a city whose crowds fill
every square metre), then the facts: growth peaked in 1963 at about 2.2% a year, is about 0.8% now, and we are about
8.2 billion. Facts: Science (von Foerster et al., 1960); US Census Bureau growth estimates as quoted by WION, Nov 2026;
Science.org, Oct 2026 ("Will the world end next month? Science said so, in 1960").
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from kit import S, build  # noqa: E402

W3 = {"type": "world3d"}


def at(scene, t=None, word=None, offset=0.0):
    ref = {"scene": scene}
    if word:
        ref["word"] = word
    elif t is not None:
        ref["t"] = t
    if offset:
        ref["offset"] = offset
    return ref


def T(text, at_word=None, y=0.15, until=None, red=True, size=0.05, at_time=None):
    el = {"type": "text", "text": text, "x": 0.5, "y": y, "size": size, "color": "#ffffff",
          "bg": "#c62828" if red else "#14181f", "bg_alpha": 0.9, "style": "label", "stroke": False, "enter": "pop"}
    if at_word:
        el["at_word"] = at_word
    else:
        el["at"] = 0.2 if at_time is None else at_time
    if until:
        el["until"] = until
    return el


def POP(a, b, at_word=None, dur=2.0, until=None, y=0.22, suffix=" billion people", dec=1, prefix=""):
    el = {"type": "counter", "from": a, "to": b, "prefix": prefix, "suffix": suffix, "grouping": "western", "decimals": dec,
          "count_dur": dur, "x": 0.5, "y": y, "size": 0.05, "color": "#ffd54a", "bg": "#14181f", "bg_alpha": 0.85,
          "style": "label", "stroke": False, "enter": "pop"}
    if at_word:
        el["at_word"] = at_word
    else:
        el["at"] = 0.2
    if until:
        el["until"] = until
    return el


SCENES = [
    dict(S("In 1960, three scientists published an equation in Science magazine. Its title: Doomsday, Friday, 13 November, 2026. That is tomorrow.",
           W3, T("Science, 1960", y=0.13, red=False, size=0.042, until=99), T("DOOMSDAY: FRIDAY 13 NOV 2026", at_word="Doomsday,", y=0.2)), id="s1"),
    dict(S("Not an asteroid. Not a war. Us. The maths said the human population was growing faster and faster, and on that Friday the number of people on Earth would reach infinity.",
           W3, POP(0.3, 3.0, at_word="growing", dur=3.0, until=99, y=0.13, suffix=" billion in 1960"), T("Population: infinity", at_word="infinity.", y=0.2)), id="s2"),
    dict(S("So let's play it out. Suppose the equation was right.",
           W3, T("What if it were true?", y=0.13, red=False, size=0.044)), id="s3"),
    dict(S("By the 1990s there are 12 billion of us. Cities swallow the farms, the forests, the rivers. There is nowhere left to grow food.",
           W3, T("1990s", y=0.13, red=False, size=0.042, until=99), POP(6, 12, at_word="12", dur=2.5, until=99)), id="s4"),
    dict(S("By 2010, 60 billion. The oceans are fished empty. Water is rationed by the cup. Every roof, every road, every field is covered in people.",
           W3, T("2010", y=0.13, red=False, size=0.042, until=99), POP(12, 60, at_word="60", dur=2.5, until=99, dec=0)), id="s5"),
    dict(S("By 2020, a trillion. One person per square metre of land. Then ten. Then a hundred. The crowd becomes a single mass, moving as one.",
           W3, T("2020", y=0.13, red=False, size=0.042, until=99), POP(60, 1000, at_word="trillion.", dur=2.5, until=99, dec=0),
           T("1 person per m²", at_word="One", y=0.29, red=False, size=0.04, until=99)), id="s6"),
    dict(S("The last week. The weight of humanity outweighs the oceans. The heat of our bodies alone warms the planet like a furnace.",
           W3, T("November 2026", y=0.13, red=False, size=0.042, until=99), T("Humans outweigh the oceans", at_word="outweighs", y=0.2)), id="s7"),
    dict(S("Friday, 13 November, 2026. Infinity. In the paper's own words, humanity is squeezed to death.",
           W3, T("FRIDAY 13 NOV 2026", y=0.13), T("∞ people", at_word="Infinity.", y=0.21, size=0.07),
           T("“squeezed to death”", at_word="squeezed", y=0.3, red=False, size=0.044)), id="s8"),
    dict(S("Here is what really happened. World population growth peaked in 1963, at 2.2 percent a year. Today it is 0.8. We are 8.2 billion, not infinite.",
           W3, T("Growth peaked in 1963: 2.2% a year", at_word="peaked", y=0.13, red=False, size=0.04),
           T("2026: 0.8% a year", at_word="0.8.", y=0.2, red=False, size=0.04), POP(3.0, 8.2, at_word="8.2", dur=2.0, y=0.27)), id="s9"),
    dict(S("Run the equation backwards and the first human is born 200 billion years ago, before the universe existed. The authors admitted it was partly a joke.",
           W3, T("First human: 200 billion years ago?", at_word="200", y=0.13, red=False, size=0.04),
           T("Universe: 13.8 billion years old", at_word="universe", y=0.2, red=False, size=0.04)), id="s10"),
    dict(S("So tomorrow, the world does not end. But the question the paper asked still stands: how many of us can one planet hold?",
           W3, T("Not the end of the world", at_word="not", y=0.13, red=False, size=0.044),
           T("How many can one planet hold?", at_word="how", y=0.2)), id="s11"),
    dict(S("Follow for more true stories.", W3), id="s12"),
]

# ---------------------------------------------------------------- the world
SPACE = {"sky_top": "#000003", "sky": "#02030a", "fog": [3000, 6000], "hemi": 0.25, "ambient": 0.18, "sun": 2.4,
         "sun_color": "#fff6e6", "sun_dir": [60, 20, 40], "cloud": "#ffffff", "ocean": "#1d3b52", "exposure": 1.0}
CITY_DUSK = {"sky_top": "#1b2238", "sky": "#e0834e", "fog": [120, 520], "hemi": 0.9, "ambient": 0.4, "sun": 1.5,
             "sun_color": "#ffb27a", "sun_dir": [-70, 12, 30], "cloud": "#e8b090", "ocean": "#24364a", "exposure": 1.0}
CITY_HAZE = {"sky_top": "#6a5a4a", "sky": "#c9a07a", "fog": [60, 320], "hemi": 0.95, "ambient": 0.5, "sun": 1.2,
             "sun_color": "#f0c8a0", "sun_dir": [30, 40, 20], "cloud": "#c9a890", "ocean": "#2c3a44", "exposure": 1.0}
CITY_HOT = {"sky_top": "#3a1208", "sky": "#c8441c", "fog": [40, 240], "hemi": 0.9, "ambient": 0.5, "sun": 1.6,
            "sun_color": "#ff8a4a", "sun_dir": [0, 70, 0], "cloud": "#c86a40", "ocean": "#3a2a2a", "exposure": 1.1}
WHITE = {"sky_top": "#ffffff", "sky": "#ffffff", "fog": [1, 2], "hemi": 3.0, "ambient": 3.0, "sun": 0.0,
         "sun_color": "#ffffff", "sun_dir": [0, 70, 0], "cloud": "#ffffff", "ocean": "#ffffff", "exposure": 2.5}


def env(t, d):
    return {**d, "at": t}


def fixed(t, pos, look, fov=40, shake=0.0, roll=0):
    k = {"at": t, "pos": pos, "look": look, "fov": fov}
    if shake:
        k["shake"] = shake
    if roll:
        k["roll"] = roll
    return k


def cut(scene):
    return at(scene, 0, offset=-0.012), at(scene, 0)


CX = 3000  # the city sits far from the planet
E = [0, 0, 0]

WORLD = {
    "style": "night", "terrain": False,
    "env": [
        env(0, SPACE), env(cut("s3")[0], SPACE), env(cut("s3")[1], CITY_DUSK), env(cut("s5")[0], CITY_DUSK), env(cut("s5")[1], CITY_HAZE),
        env(cut("s6")[0], CITY_HAZE), env(cut("s6")[1], CITY_HOT), env(cut("s7")[0], CITY_HOT), env(cut("s7")[1], SPACE),
        env(cut("s8")[0], SPACE), env(cut("s8")[1], CITY_HOT), env(at("s8", word="squeezed", offset=-0.1), CITY_HOT),
        env(at("s8", word="squeezed", offset=0.5), WHITE), env(at("s8", 1.0), WHITE),
        env(cut("s9")[0], WHITE), env(cut("s9")[1], SPACE),
    ],
    "objects": [
        {"type": "stars", "seed": 21, "count": 2200, "size": 1.6},
        {"type": "earth", "pos": E, "r": 20, "seed": 3, "spin": 0.03, "tilt": 23,
         "tint": [{"at": 0, "warm": 0}, {"at": cut("s7")[1], "warm": 0.55}, {"at": at("s7", 1.0), "warm": 0.85}, {"at": cut("s8")[1], "warm": 0.95},
                  {"at": cut("s9")[0], "warm": 0.95}, {"at": cut("s9")[1], "warm": 0}]},
        # the city: a ground slab, a skyline that grows, a square that fills with people
        {"type": "box", "pos": [CX, -0.5, 0], "w": 900, "h": 1, "d": 900, "color": "#2a2d32"},
        {"type": "towers", "seed": 12, "count": 90, "area": [CX - 160, -160, CX + 160, 160], "lit": 0.55, "glow": 0.8,
         "rise": [{"at": 0, "s": 0.55}, {"at": cut("s4")[1], "s": 0.55}, {"at": at("s4", 1.0), "s": 1.0}, {"at": at("s6", 1.0), "s": 1.35}]},
        {"type": "crowd", "seed": 15, "count": 9000, "area": [CX - 36, -36, CX + 36, 36], "y": 0, "scale": 1.0,
         "n": [{"at": 0, "n": 180}, {"at": cut("s4")[1], "n": 180}, {"at": at("s4", 1.0), "n": 900}, {"at": at("s5", 1.0), "n": 2600},
               {"at": at("s6", word="hundred."), "n": 9000}]},
        {"type": "box", "pos": [CX, 0, 0], "w": 76, "h": 0.2, "d": 76, "color": "#6e6c66"},
    ],
    "camera": [
        # s1: the planet from space, slow drift in
        fixed(0, [-70, 22, 60], E, 40),
        fixed(at("s1", 1.0, offset=-0.05), [-52, 14, 48], E, 40),
        # s2: closer, half-lit limb
        fixed(cut("s2")[1], [40, 14, 66], [2, 2, 0], 38),
        fixed(at("s2", 1.0, offset=-0.05), [46, 8, 56], [2, 2, 0], 38),
        # s3: the city at dusk from the air
        fixed(cut("s3")[1], [CX - 150, 60, 170], [CX, 8, 0], 46),
        fixed(at("s3", 1.0, offset=-0.05), [CX - 120, 50, 140], [CX, 8, 0], 46),
        # s4: street level, the square filling, towers rising behind
        fixed(cut("s4")[1], [CX - 40, 3, 70], [CX, 6, 0], 50),
        fixed(at("s4", 1.0, offset=-0.05), [CX - 30, 4, 62], [CX, 10, 0], 50),
        # s5: over the crowd, haze
        fixed(cut("s5")[1], [CX + 30, 12, 60], [CX, 1, 0], 48),
        fixed(at("s5", 1.0, offset=-0.05), [CX + 20, 9, 50], [CX, 1, 0], 48),
        # s6: top-down, packed solid
        fixed(cut("s6")[1], [CX + 2, 44, 2], [CX, 0, 0], 50),
        fixed(at("s6", word="hundred."), [CX + 1, 24, 1], [CX, 0, 0], 50),
        fixed(at("s6", 1.0, offset=-0.05), [CX + 1, 18, 1], [CX, 0, 0], 50),
        # s7: the planet glowing warm
        fixed(cut("s7")[1], [40, 12, 50], [2, 0, 0], 40),
        fixed(at("s7", 1.0, offset=-0.05), [34, 8, 44], [2, 0, 0], 40),
        # s8: into the crowd, then the white-out
        fixed(cut("s8")[1], [CX - 6, 1.6, 10], [CX, 1.2, 0], 56, shake=0.12),
        fixed(at("s8", word="squeezed", offset=-0.1), [CX - 3, 1.5, 5], [CX, 1.2, 0], 60, shake=0.25),
        fixed(at("s8", 1.0, offset=-0.05), [CX - 1, 1.4, 2.5], [CX, 1.2, 0], 64, shake=0.3),
        # s9 to s12: the planet, calm, slow orbit
        fixed(cut("s9")[1], [58, 16, 60], E, 40),
        fixed(at("s10", 1.0), [34, 22, 76], E, 40),
        fixed(at("s12", 1.0, offset=0.5), [14, 20, 82], E, 40),
    ],
}

BASE = {
    "language": "en", "voice": "bm_george", "speed": 1.08, "aspect": "9:16", "made_for_kids": False,
    "footage": "off", "transition": "none",
    "music": {"mood": "mystery", "volume": 0.11},
    "captions": {"style": "karaoke", "y": 0.62, "size": 0.08, "max_words": 2, "highlight": "#ffd54a",
                 "uppercase": False},
    "overlay": {"handle": "@hypercurious96", "progress_bar": False},
    "world3d": WORLD,
}

if __name__ == "__main__":
    build(HERE, [("ch01", "Doomsday 2026", SCENES)], BASE, "Doomsday: Friday 13 November 2026", seed=13)
