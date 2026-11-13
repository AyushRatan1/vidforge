"""Builds the animated 9:16 Short "What if Microsoft never came back?" (English, about 110 seconds) as ch01.json.

    python longform/msoutage_anim/build.py

A what-if built on the real Microsoft 365 outage of 12-13 November 2026: the planet's network going dark, a data
centre whose racks fail, recover and fail again, then the scenario hour by hour (a city at night, a city by day, a
data centre all red, grounded jets), and the reality check.
Facts: Microsoft 365 status posts (incidents EX1550543, MO1550821) as reported by Cybersecurity News and ABC7,
12-13 Nov 2026 (74 countries, 10+ hours, the secure-connection process); ABC News Australia, 13 Nov 2026 (login codes);
Microsoft FY26 Q2 results via Office 365 for IT Pros (450 million commercial paid seats); SecurityWeek, July 2024
(CrowdStrike: 8.5 million devices; Parametrix: $5.4 billion Fortune 500 loss).
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


def WHATIF():
    return {"type": "text", "text": "WHAT IF", "x": 0.5, "y": 0.065, "size": 0.034, "color": "#ffd54a", "bg": "#14181f",
            "bg_alpha": 0.85, "style": "label", "stroke": False, "enter": "pop", "at": 0.05}


def COUNT(a, b, at_word, suffix, y=0.2, dur=2.0):
    return {"type": "counter", "from": a, "to": b, "suffix": suffix, "grouping": "western", "count_dur": dur,
            "x": 0.5, "y": y, "size": 0.05, "color": "#ffd54a", "bg": "#14181f", "bg_alpha": 0.85, "style": "label",
            "stroke": False, "enter": "pop", "at_word": at_word}


SCENES = [
    dict(S("On Thursday night, Microsoft broke. Outlook, Teams and Copilot went down in 74 countries, for more than ten hours. Now imagine it never came back.",
           W3, T("Microsoft outage", y=0.13, until=99), T("12 November 2026", y=0.2, red=False, size=0.042, until=99),
           T("74 countries", at_word="74", y=0.27, red=False, size=0.042), T("10+ hours", at_word="ten", y=0.34, red=False, size=0.042)), id="s1"),
    dict(S("Inside Microsoft's data centres, servers started dropping out, and the ones left standing buckled under the extra load.",
           W3, T("Servers dropping out", at_word="dropping", y=0.13)), id="s2"),
    dict(S("Engineers brought them back. The moment traffic hit them, they fell over again. A process that sets up secure connections was overwhelmed.",
           W3, T("Fixed...", at_word="back.", y=0.13, red=False, size=0.044), T("...then down again", at_word="fell", y=0.2),
           T("Cause: secure connections overloaded", at_word="process", y=0.27, red=False, size=0.04)), id="s3"),
    dict(S("Over 450 million people pay for Microsoft 365 at work. So let's play it out. What if the fix never worked?",
           W3, COUNT(0, 450, "450", " million paid users", y=0.13), T("What if it never came back?", at_word="What", y=0.2)), id="s4"),
    dict(S("Hour one. Emails stop arriving. Teams calls freeze mid sentence. Login codes don't come through, so people get locked out of other apps too.",
           W3, WHATIF(), T("HOUR 1", y=0.13, until=99), T("Outlook: can't connect", at_word="Emails", y=0.2, red=False, size=0.042),
           T("Teams: reconnecting...", at_word="Teams", y=0.27, red=False, size=0.042), T("Login codes failing", at_word="Login", y=0.34, size=0.042)), id="s5"),
    dict(S("Day one. Offices go quiet. Invoices, contracts and payroll sit in inboxes no one can open. Schools can't reach parents.",
           W3, WHATIF(), T("DAY 1", y=0.13, until=99), T("Payroll stuck in inboxes", at_word="payroll", y=0.2, red=False, size=0.042),
           T("Schools can't reach parents", at_word="Schools", y=0.27, red=False, size=0.042)), id="s6"),
    dict(S("Day three. Now suppose it spreads to Azure, Microsoft's cloud. Bank portals, airline check-ins and hospital systems built on it start failing.",
           W3, WHATIF(), T("DAY 3", y=0.13, until=99), T("Azure down too?", at_word="Azure,", y=0.2),
           T("Banks, airlines, hospitals", at_word="Bank", y=0.27, red=False, size=0.042)), id="s7"),
    dict(S("We have seen a preview. In July 2024, one bad CrowdStrike update crashed 8.5 million Windows computers. Flights were grounded. One morning cost Fortune 500 companies 5.4 billion dollars.",
           W3, T("Real: CrowdStrike, July 2024", y=0.13, red=False, size=0.042, until=99), T("8.5 million PCs crashed", at_word="8.5", y=0.2),
           T("$5.4 billion in one morning", at_word="5.4", y=0.27)), id="s8"),
    dict(S("Day seven. A week of this would cost many times more. Companies fall back to paper, phone calls and USB drives.",
           W3, WHATIF(), T("DAY 7", y=0.13, until=99), T("Back to paper", at_word="paper,", y=0.2, red=False, size=0.044)), id="s9"),
    dict(S("In reality, that is very unlikely. Microsoft runs data centres across dozens of regions, and even big outages last hours, not weeks. By Friday morning, servers were coming back.",
           W3, T("Reality check", y=0.13, red=False, size=0.044, until=99), T("Outages last hours, not weeks", at_word="hours,", y=0.2),
           T("Servers returning, 13 Nov", at_word="coming", y=0.27, red=False, size=0.04)), id="s10"),
    dict(S("But it shows how much of the world runs through one company. Keep a backup: important files offline, and key numbers written down.",
           W3, T("So much runs through one company", at_word="world", y=0.13, red=False, size=0.04), T("Keep a backup", at_word="backup:", y=0.2)), id="s11"),
    dict(S("Follow for more true stories.", W3), id="s12"),
]

# ---------------------------------------------------------------- the world
SPACE = {"sky_top": "#000003", "sky": "#02030a", "fog": [3000, 6000], "hemi": 0.25, "ambient": 0.18, "sun": 2.4,
         "sun_color": "#fff6e6", "sun_dir": [60, 20, 40], "cloud": "#ffffff", "ocean": "#1d3b52", "exposure": 1.0}
DC = {"sky_top": "#020305", "sky": "#06080b", "fog": [6, 26], "hemi": 0.2, "ambient": 0.12, "sun": 0.25,
      "sun_color": "#9fb6d8", "sun_dir": [10, 60, 20], "cloud": "#222222", "ocean": "#111111", "exposure": 1.1}
NIGHT = {"sky_top": "#03050d", "sky": "#14203a", "fog": [140, 620], "hemi": 0.5, "ambient": 0.25, "sun": 0.6,
         "sun_color": "#9fb2e0", "sun_dir": [-30, 50, -40], "cloud": "#3a4660", "ocean": "#0b1a2a", "exposure": 1.05}
GREY = {"sky_top": "#7d8794", "sky": "#c9ced4", "fog": [120, 560], "hemi": 1.2, "ambient": 0.55, "sun": 1.0,
        "sun_color": "#eef2f6", "sun_dir": [30, 60, 20], "cloud": "#dde2e8", "ocean": "#4a5a66", "exposure": 1.0}
DUSK = {"sky_top": "#1d1f3d", "sky": "#d8683a", "fog": [160, 700], "hemi": 1.3, "ambient": 0.65, "sun": 1.8,
        "sun_color": "#ffb070", "sun_dir": [-80, 12, 20], "cloud": "#e0a080", "ocean": "#24364a", "exposure": 1.0}


def env(t, d):
    return {**d, "at": t}


def fixed(t, pos, look, fov=40, shake=0.0):
    k = {"at": t, "pos": pos, "look": look, "fov": fov}
    if shake:
        k["shake"] = shake
    return k


def cut(scene):
    return at(scene, 0, offset=-0.012), at(scene, 0)


E = [0, 0, 0]
DCX, CX, AX = 2000, 3000, 4000

ENV_BY_SCENE = [("s1", SPACE), ("s2", DC), ("s4", SPACE), ("s5", NIGHT), ("s6", GREY), ("s7", DC), ("s8", DUSK),
                ("s9", SPACE)]
envs = [env(0, SPACE)]
for k, (sid, d) in enumerate(ENV_BY_SCENE[1:], 1):
    envs += [env(cut(sid)[0], ENV_BY_SCENE[k - 1][1]), env(cut(sid)[1], d)]

PLANES = [{"type": "airliner", "scale": 3, "gear": True, "lights": False, "livery": k,
           "track": [{"at": 0, "pos": [AX - 36 + k * 26, 0.685 * 3, -6 - (k % 2) * 3], "rot": [0, 180, 0]},
                     {"at": 1, "pos": [AX - 36 + k * 26, 0.685 * 3, -6 - (k % 2) * 3], "rot": [0, 180, 0]}]} for k in range(4)]

WORLD = {
    "style": "night", "terrain": False,
    "env": envs,
    "objects": [
        {"type": "stars", "seed": 21, "count": 2200, "size": 1.6},
        {"type": "earth", "pos": E, "r": 20, "seed": 5, "spin": 0.03, "tilt": 20,
         "arcs": {"count": 46, "seed": 31, "color": "#7fd4ff", "power": [
             {"at": 0, "p": 1}, {"at": at("s1", word="broke,"), "p": 1}, {"at": at("s1", word="countries,"), "p": 0.12},
             {"at": cut("s4")[0], "p": 0.12}, {"at": cut("s4")[1], "p": 1}, {"at": at("s4", word="What"), "p": 1},
             {"at": at("s4", 1.0), "p": 0.25}, {"at": cut("s9")[1], "p": 0.08}, {"at": at("s9", 1.0), "p": 0.04},
             {"at": cut("s10")[1], "p": 0.04}, {"at": at("s10", word="coming"), "p": 1}]}},
        # the data-centre aisle
        {"type": "racks", "pos": [DCX, 0, 0], "count": 14, "seed": 41, "health": [
            {"at": 0, "h": 1}, {"at": cut("s2")[1], "h": 1}, {"at": at("s2", word="dropping"), "h": 0.95},
            {"at": at("s2", 1.0), "h": 0.22}, {"at": at("s3", word="back."), "h": 0.75}, {"at": at("s3", word="fell"), "h": 0.72},
            {"at": at("s3", word="again."), "h": 0.15}, {"at": cut("s7")[1], "h": 0.06}, {"at": at("s7", 1.0), "h": 0.0}]},
        # the city
        {"type": "box", "pos": [CX, -0.5, 0], "w": 900, "h": 1, "d": 900, "color": "#9aa0a8"},
        {"type": "towers", "seed": 12, "count": 90, "area": [CX - 160, -160, CX + 160, 160], "lit": 0.6, "glow": 0.85},
        {"type": "box", "pos": [CX, 0, 0], "w": 70, "h": 0.2, "d": 70, "color": "#d8d0c0"},
        {"type": "crowd", "seed": 16, "count": 1400, "area": [CX - 28, -28, CX + 28, 28], "scale": 1.0},
        # the airport: apron, terminal, grounded jets, stranded passengers
        {"type": "box", "pos": [AX, -0.5, 0], "w": 600, "h": 1, "d": 600, "color": "#61656b"},
        {"type": "box", "pos": [AX, 0, -38], "w": 150, "h": 12, "d": 18, "color": "#b9c0c8"},
        {"type": "box", "pos": [AX, 6, -28.9], "w": 150, "h": 7, "d": 0.3, "color": "#2f4a66"},
        *PLANES,
        {"type": "crowd", "seed": 17, "count": 500, "area": [AX - 60, -27, AX + 60, -21], "scale": 1.0},
    ],
    "camera": [
        # s1: the planet, the network lit and then going dark
        fixed(0, [-18, 16, 70], E, 40),
        fixed(at("s1", 1.0, offset=-0.05), [-8, 12, 62], E, 40),
        # s2 to s3: down the aisle of a data centre
        fixed(cut("s2")[1], [DCX + 0.2, 1.5, 2.2], [DCX, 1.3, -10], 58),
        fixed(at("s2", 1.0, offset=-0.05), [DCX + 0.1, 1.4, -0.8], [DCX, 1.2, -10], 58),
        fixed(cut("s3")[1], [DCX - 0.5, 0.6, -2.5], [DCX + 1.4, 1.4, -6], 60),
        fixed(at("s3", 1.0, offset=-0.05), [DCX - 0.4, 0.7, -4.5], [DCX + 1.4, 1.4, -8], 60),
        # s4: the planet again, the lit side
        fixed(cut("s4")[1], [44, 14, 62], E, 40),
        fixed(at("s4", 1.0, offset=-0.05), [36, 12, 58], E, 40),
        # s5: the city at night from street level
        fixed(cut("s5")[1], [CX - 32, 2.5, 44], [CX + 10, 26, -40], 54),
        fixed(at("s5", 1.0, offset=-0.05), [CX - 26, 3, 36], [CX + 10, 30, -40], 54),
        # s6: the plaza by day from above
        fixed(cut("s6")[1], [CX + 44, 22, 60], [CX, 6, -30], 50),
        fixed(at("s6", 1.0, offset=-0.05), [CX + 34, 18, 50], [CX, 6, -30], 50),
        # s7: the data centre, every rack red
        fixed(cut("s7")[1], [DCX + 0.3, 2.1, 1.8], [DCX, 1.0, -9], 56, shake=0.03),
        fixed(at("s7", 1.0, offset=-0.05), [DCX + 0.2, 1.8, -1.5], [DCX, 1.0, -9], 56, shake=0.03),
        # s8: grounded jets at dusk
        fixed(cut("s8")[1], [AX - 56, 14, 30], [AX - 8, 2, -10], 46),
        fixed(at("s8", 1.0, offset=-0.05), [AX - 44, 11, 24], [AX - 4, 2, -10], 46),
        # s9: the planet, dark
        fixed(cut("s9")[1], [-30, 10, 62], E, 40),
        fixed(at("s9", 1.0, offset=-0.05), [-24, 8, 58], E, 40),
        # s10 to s12: the lit side, the network coming back, slow pull out
        fixed(cut("s10")[1], [40, 16, 60], E, 40),
        fixed(at("s11", 1.0), [20, 22, 74], E, 40),
        fixed(at("s12", 1.0, offset=0.5), [10, 22, 80], E, 40),
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
    build(HERE, [("ch01", "Microsoft outage", SCENES)], BASE, "What if Microsoft never came back?", seed=365)
