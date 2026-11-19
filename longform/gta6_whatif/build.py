"""Builds the animated 9:16 Short "What if GTA 6 unlocked for everyone at the same second?" (English, about 2 minutes,
60 fps) as ch01.json.

    python longform/gta6_whatif/build.py

A what-if on launch day (Thursday 19 November 2026): the real staggered launch (preloads from 10 November, midnight local
time), the 212 GB download and the code-only box, the day-one forecasts, the arithmetic for one global switch (5.3
exabytes against the world's international bandwidth and Akamai's record peak), the scenario hour by hour (sign-in
queues, a data centre in the red, downloads at a trickle, home connections jammed), the real precedents (the Fortnite
update behind Akamai's first 100 Tbps peak in 2019, GTA Online's overwhelmed launch in 2013) and why preloads fix it.
No game artwork, logos or characters are drawn: the city, TV screen and console are generic.
Facts: Yahoo Tech, allthings.how, GTA Boss, tracker.gg (19 Nov 2026, PS5 and Xbox Series X|S, midnight local time,
preloads from 10 Nov); GamesRadar, HotHardware, tech-insider (up to 212 GB, Rockstar); GTA Intel (the box is a code);
Konvoy via Express Tribune (25 million day one), Piper Sandler via GamesRadar (about 46 million); TeleGeography, Sep 2026
(2,259 Tbps international internet bandwidth); Akamai via TV Technology (250 Tbps record peak) and ZDNet/Slashdot (106 Tbps
in October 2019, the Fortnite Chapter 2 update); The Motley Fool, GamesRadar, mp1st (GTA Online 2013 and the GTA$500,000
stimulus). Arithmetic: 25e6 x 212 GB = 5.3 EB; 5.3e18 B x 8 / 2.259e15 b/s = 5.2 h; / 2.5e14 b/s = 47 h.
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


def T(text, at_word=None, y=0.15, until=None, red=True, size=0.046, at_time=None):
    el = {"type": "text", "text": text, "x": 0.5, "y": y, "size": size, "color": "#ffffff",
          "bg": "#c62828" if red else "#14181f", "bg_alpha": 0.9, "style": "label", "stroke": False, "enter": "pop"}
    if at_word:
        el["at_word"] = at_word
    else:
        el["at"] = 0.2 if at_time is None else at_time
    if until:
        el["until"] = until
    return el


def TAG(text="WHAT IF"):
    return {"type": "text", "text": text, "x": 0.5, "y": 0.065, "size": 0.034, "color": "#ffd54a", "bg": "#14181f",
            "bg_alpha": 0.85, "style": "label", "stroke": False, "enter": "pop", "at": 0.05}


def COUNT(a, b, at_word, suffix, y=0.2, dur=2.0):
    return {"type": "counter", "from": a, "to": b, "suffix": suffix, "grouping": "western", "count_dur": dur,
            "x": 0.5, "y": y, "size": 0.05, "color": "#ffd54a", "bg": "#14181f", "bg_alpha": 0.85, "style": "label",
            "stroke": False, "enter": "pop", "at_word": at_word}


SCENES = [
    dict(S("GTA 6 is out today. But what if Rockstar had flipped one switch, and unlocked it for everyone on Earth at the same second?",
           W3, TAG(), T("GTA 6: out 19 Nov 2026", y=0.13, red=False), T("Everyone. Same second.", at_word="everyone", y=0.2)), id="s1"),
    dict(S("In reality, the launch is spread out. Preloads opened over a week early, and the game unlocks at midnight local time, one time zone after another.",
           W3, T("Preloads from 10 Nov", at_word="Preloads", y=0.13, red=False), T("Unlocks at local midnight", at_word="midnight", y=0.2, red=False)), id="s2"),
    dict(S("There's a reason. The game is a download of up to 212 gigabytes. Even the boxed copy is just a code, not a disc.",
           W3, T("Up to 212 GB", at_word="212", y=0.13), T("Boxed copy = a download code", at_word="boxed", y=0.2, red=False)), id="s3"),
    dict(S("Analysts expect around 25 million copies sold on day one. One forecast goes past 45 million.",
           W3, COUNT(0, 25000000, "25", " copies", y=0.13, dur=1.8), T("One forecast: 45M+", at_word="45", y=0.2, red=False)), id="s4"),
    dict(S("So, the maths. 25 million players, times 212 gigabytes, is 5.3 exabytes. That's 5.3 million terabytes, all asked for at once.",
           W3, T("25M × 212 GB", at_word="times", y=0.13, red=False), T("= 5.3 exabytes", at_word="exabytes.", y=0.2)), id="s5"),
    dict(S("All the international internet links on Earth combined carry about 2,259 terabits per second.",
           W3, T("World international bandwidth:", at_word="international", y=0.13, red=False, size=0.04), T("2,259 Tbps", at_word="2,259", y=0.2)), id="s6"),
    dict(S("Even if every one of them carried nothing but GTA 6, the download would take over five hours. At the biggest peak Akamai, a giant delivery network, has ever reported, almost two days.",
           W3, T("All of it, only GTA: 5+ hours", at_word="five", y=0.13), T("At Akamai's 250 Tbps record: ~2 days", at_word="almost", y=0.2, red=False, size=0.04)), id="s7"),
    dict(S("So here's how our what-if plays out. At midnight, 25 million consoles knock on the same door, in the same second.",
           W3, TAG("SCENARIO"), T("00:00:00, worldwide", at_word="midnight,", y=0.13)), id="s8"),
    dict(S("Sign-in servers built for a busy evening get a whole launch at once. Queues explode, and error codes pour out.",
           W3, TAG("SCENARIO"), T("Sign-in overload", at_word="Queues", y=0.13)), id="s9"),
    dict(S("Download servers start throttling. Speeds fall to a trickle, and progress bars sit at zero percent for hours.",
           W3, TAG("SCENARIO"), T("0% for hours", at_word="zero", y=0.13)), id="s10"),
    dict(S("Home connections max out everywhere at once. Video calls freeze, streams buffer, and even people who never play games feel it.",
           W3, TAG("SCENARIO"), T("Whole neighbourhoods slow down", at_word="freeze,", y=0.13, red=False)), id="s11"),
    dict(S("It has happened in miniature. In 2019, one Fortnite update helped push Akamai past 100 terabits per second for the first time.",
           W3, T("Oct 2019: 106 Tbps peak", at_word="2019,", y=0.13, red=False)), id="s12"),
    dict(S("And Rockstar knows what an overwhelmed launch looks like. In 2013, GTA Online's servers buckled, and players got 500,000 in-game dollars as an apology.",
           W3, T("GTA Online, Oct 2013", at_word="2013,", y=0.13, red=False), T("GTA$500,000 apology", at_word="500,000", y=0.2)), id="s13"),
    dict(S("That's why the real launch is staggered. With preloads, most copies were already downloaded before launch, so midnight only had to unlock them.",
           W3, T("Preloaded = already downloaded", at_word="preloads,", y=0.13, red=False)), id="s14"),
    dict(S("One switch for the whole planet could jam the internet for days. Midnight after midnight, it just works. Would you have stayed up for it?",
           W3, T("Follow for more what-ifs", at_word="Would", y=0.13)), id="s15"),
]
ORDER = [f"s{k}" for k in range(1, 16)]

# ---------------------------------------------------------------- environments
SPACE = {"sky_top": "#000003", "sky": "#02030a", "fog": [3000, 6000], "hemi": 0.25, "ambient": 0.18, "sun": 2.4,
         "sun_color": "#fff6e6", "sun_dir": [60, 20, 40], "cloud": "#ffffff", "ocean": "#1d3b52", "exposure": 1.0}
ROOM = {"sky_top": "#020306", "sky": "#06080e", "fog": [20, 60], "hemi": 0.45, "ambient": 0.32, "sun": 0.35,
        "sun_color": "#8fa8d8", "sun_dir": [10, 60, 20], "cloud": "#222222", "ocean": "#111111", "exposure": 1.25}
DATA = {"sky_top": "#02040a", "sky": "#081428", "fog": [120, 420], "hemi": 0.6, "ambient": 0.35, "sun": 0.8,
        "sun_color": "#bcd8ff", "sun_dir": [30, 60, 40], "cloud": "#202838", "ocean": "#101820", "exposure": 1.05}
DC = {"sky_top": "#020305", "sky": "#06080b", "fog": [6, 26], "hemi": 0.2, "ambient": 0.12, "sun": 0.25,
      "sun_color": "#9fb6d8", "sun_dir": [10, 60, 20], "cloud": "#222222", "ocean": "#111111", "exposure": 1.1}
NEON = {"sky_top": "#070414", "sky": "#3a1450", "fog": [160, 640], "hemi": 0.55, "ambient": 0.3, "sun": 0.6,
        "sun_color": "#c49cff", "sun_dir": [-40, 30, -50], "cloud": "#4a2a66", "ocean": "#0b1a2a", "exposure": 1.1}
ENV_BY_SCENE = {"s1": SPACE, "s2": SPACE, "s3": ROOM, "s4": NEON, "s5": DATA, "s6": DATA, "s7": DATA, "s8": ROOM,
                "s9": DC, "s10": ROOM, "s11": NEON, "s12": SPACE, "s13": DC, "s14": ROOM, "s15": NEON}


def env(t, d):
    return {**d, "at": t}


def cut(scene):
    return at(scene, 0, offset=-0.012), at(scene, 0)


envs = [env(0, SPACE)]
for k, sid in enumerate(ORDER[1:], 1):
    envs += [env(cut(sid)[0], ENV_BY_SCENE[ORDER[k - 1]]), env(cut(sid)[1], ENV_BY_SCENE[sid])]


def fixed(t, pos, look, fov=40, shake=0.0):
    k = {"at": t, "pos": pos, "look": look, "fov": fov}
    if shake:
        k["shake"] = shake
    return k


E = [0, 0, 0]
TVX, DX, RX, CX = 2000, 3000, 4000, 5000
END = lambda s: at(s, 1.0, offset=-0.05)  # noqa: E731
TV_WIDE, TV_MID, TV_CLOSE = [TVX, 2.3, 6.4], [TVX, 2.0, 5.4], [TVX, 1.82, 4.75]
TV_LOOK = [TVX, 1.6, -2.4]
SHOTS = {
    "s1": [fixed(cut("s1")[1], [-34, 22, 122], E, 40), fixed(at("s1", word="switch,"), [-24, 18, 112], E, 40), fixed(END("s1"), [-14, 15, 100], E, 40, 0.04)],
    "s2": [fixed(cut("s2")[1], [70, 28, 92], E, 40), fixed(END("s2"), [56, 22, 94], E, 40)],
    "s3": [fixed(cut("s3")[1], TV_WIDE, TV_LOOK, 46), fixed(END("s3"), TV_MID, TV_LOOK, 46)],
    "s4": [fixed(cut("s4")[1], [CX - 16, 9, 98], [CX, 10, 20], 50), fixed(END("s4"), [CX - 6, 13, 84], [CX, 9, 20], 50)],
    "s5": [fixed(cut("s5")[1], [DX - 34, 22, 46], [DX, 9, 0], 44), fixed(END("s5"), [DX - 40, 16, 34], [DX, 10, 0], 44)],
    "s6": [fixed(cut("s6")[1], [DX - 26, 16, 40], [DX + 20, 7, 0], 46), fixed(END("s6"), [DX - 18, 12, 44], [DX + 34, 6, 0], 46)],
    "s7": [fixed(cut("s7")[1], [DX + 20, 9, 14], [DX + 46, 6, 0], 46), fixed(at("s7", word="Akamai,"), [DX + 26, 8, 12], [DX + 56, 6, 0], 46),
           fixed(END("s7"), [DX - 30, 20, 40], [DX + 8, 8, 0], 46)],
    "s8": [fixed(cut("s8")[1], [TVX, 1.9, 5.3], TV_LOOK, 46), fixed(END("s8"), TV_CLOSE, TV_LOOK, 46)],
    "s9": [fixed(cut("s9")[1], [RX + 0.2, 1.5, 2.2], [RX, 1.3, -10], 58, 0.03), fixed(END("s9"), [RX + 0.1, 1.4, -0.8], [RX, 1.2, -10], 58, 0.05)],
    "s10": [fixed(cut("s10")[1], [TVX, 2.15, 5.9], TV_LOOK, 46), fixed(END("s10"), TV_CLOSE, TV_LOOK, 46)],
    "s11": [fixed(cut("s11")[1], [CX + 24, 30, 116], [CX - 8, 18, -40], 50), fixed(END("s11"), [CX + 14, 26, 104], [CX - 8, 20, -40], 50)],
    "s12": [fixed(cut("s12")[1], [-64, 26, 96], E, 40), fixed(END("s12"), [-50, 20, 92], E, 40)],
    "s13": [fixed(cut("s13")[1], [RX - 0.5, 0.6, -2.5], [RX + 1.4, 1.4, -6], 60, 0.03), fixed(END("s13"), [RX - 0.4, 0.7, -4.5], [RX + 1.4, 1.4, -8], 60, 0.03)],
    "s14": [fixed(cut("s14")[1], TV_CLOSE, TV_LOOK, 46), fixed(END("s14"), TV_WIDE, TV_LOOK, 46)],
    "s15": [fixed(cut("s15")[1], [CX - 60, 8, 120], [CX, 20, 0], 46), fixed(at("s15", 1.0, offset=0.6), [CX - 50, 60, 140], [CX, 10, -10], 46)],
}
CAMERA = []
for k, sid in enumerate(ORDER):
    CAMERA += SHOTS[sid]
    if k + 1 < len(ORDER):
        CAMERA.append({**SHOTS[sid][-1], "at": cut(ORDER[k + 1])[0]})
CAMERA[0] = {**CAMERA[0], "at": 0}


def tv(progress, speed, state, queue=None, clock=None):
    o = {"progress": progress, "speed": speed, "state": state}
    if queue:
        o["queue"] = queue
    if clock:
        o["clock"] = clock
    return o


# one TV room, its screen keyed scene by scene (preload in s3, midnight queue in s8, the trickle in s10, ready in s14)
TV = {"type": "tvroom", "pos": [TVX, 0, 0], "title": "OPEN-WORLD GAME", "size_label": "Download: 212 GB",
      "progress": [{"at": 0, "p": 0.31}, {"at": at("s3", 0), "p": 0.31}, {"at": at("s3", 1.0), "p": 0.47},
                   {"at": cut("s8")[1], "p": 0.0}, {"at": at("s10", 0), "p": 0.0}, {"at": at("s10", 1.0), "p": 0.002},
                   {"at": cut("s14")[0], "p": 0.002}, {"at": cut("s14")[1], "p": 0.96}, {"at": at("s14", word="unlock"), "p": 1.0}],
      "speed": [{"at": 0, "v": 186}, {"at": at("s3", 1.0), "v": 192}, {"at": at("s10", 0), "v": 40}, {"at": at("s10", word="trickle,"), "v": 0.4},
                {"at": at("s10", 1.0), "v": 0.3}, {"at": cut("s14")[1], "v": 210}],
      "state": [{"at": 0, "s": 0}, {"at": cut("s8")[1], "s": 0}, {"at": at("s8", word="midnight,", offset=0.3), "s": 1},
                {"at": cut("s10")[1], "s": 2}, {"at": at("s10", word="Speeds"), "s": 0}, {"at": at("s14", word="unlock"), "s": 3}],
      "queue": [{"at": at("s8", word="midnight,", offset=0.3), "q": 18402117}, {"at": at("s8", 1.0), "q": 18401930}],
      "clock": [{"at": cut("s3")[1], "c": 9999}, {"at": cut("s8")[1], "c": 0.12}, {"at": at("s8", word="midnight,", offset=0.3), "c": 0},
                {"at": at("s8", 1.0), "c": -0.06}, {"at": cut("s10")[0], "c": -0.06}, {"at": cut("s10")[1], "c": 9999}]}

WORLD = {
    "style": "night", "terrain": False, "far": 2000, "shadows": False,
    "env": envs,
    "objects": [
        {"type": "stars", "seed": 21, "count": 2200, "size": 1.6},
        {"type": "earth", "pos": E, "r": 20, "seed": 7, "spin": 0.04, "tilt": 22,
         "arcs": {"count": 60, "seed": 33, "color": "#7fd4ff", "power": [
             {"at": 0, "p": 0.15}, {"at": at("s1", word="switch,"), "p": 0.15}, {"at": at("s1", word="second?"), "p": 1.0},
             {"at": cut("s2")[1], "p": 0.08}, {"at": at("s2", word="midnight"), "p": 0.35}, {"at": at("s2", 1.0), "p": 0.55},
             {"at": cut("s12")[1], "p": 0.2}, {"at": at("s12", word="push"), "p": 0.9}, {"at": at("s12", 1.0), "p": 0.95}]}},
        # the living room
        TV,
        # the data: a 5.3-exabyte cube and the pipe it has to squeeze through
        {"type": "gridfloor", "pos": [DX, 0, 0], "size": 240, "div": 48, "color": "#0a1222", "line": "#1d3352"},
        {"type": "datacube", "pos": [DX, 0, 0], "n": 14, "size": 18, "seed": 8,
         "drain": [{"at": 0, "d": 0}, {"at": at("s7", 0), "d": 0}, {"at": at("s7", 1.0), "d": 0.03}]},
        {"type": "pipe", "from": [DX + 9.5, 6, 0], "to": [DX + 110, 6, 0], "r": 1.1, "count": 30, "speed": 0.02},
        # the data centre
        {"type": "racks", "pos": [RX, 0, 0], "count": 14, "seed": 41, "health": [
            {"at": 0, "h": 1}, {"at": cut("s9")[1], "h": 0.9}, {"at": at("s9", word="Queues"), "h": 0.5}, {"at": at("s9", 1.0), "h": 0.05},
            {"at": cut("s13")[1], "h": 0.4}, {"at": at("s13", word="buckled,"), "h": 0.1}, {"at": at("s13", 1.0), "h": 0.15}]},
        # the neon city by the water
        {"type": "box", "pos": [CX, -0.5, 0], "w": 900, "h": 1, "d": 900, "color": "#1c1c26"},
        {"type": "box", "pos": [CX, -0.45, 160], "w": 900, "h": 1, "d": 200, "color": "#0c1a2c"},
        {"type": "towers", "seed": 14, "count": 130, "area": [CX - 170, -170, CX + 170, 40], "lit": 0.65, "glow": 0.95,
         "neon": ["#ff3fa4", "#2de2e6", "#ff9f1c", "#b14aff"], "neon_share": 0.5,
         "flicker": [{"at": 0, "f": 0}, {"at": cut("s11")[1], "f": 0.2}, {"at": at("s11", word="freeze,"), "f": 1}, {"at": at("s11", 1.0), "f": 1},
                     {"at": cut("s15")[1], "f": 0}]},
        {"type": "palms", "seed": 6, "count": 60, "area": [CX - 200, 46, CX + 200, 60], "h": 9},
        {"type": "box", "pos": [CX, 0, 52], "w": 420, "h": 0.2, "d": 16, "color": "#3a3446"},
        {"type": "crowd", "seed": 16, "count": 1800, "area": [CX - 46, 46, CX + 46, 58], "scale": 1.0},
    ],
    "camera": CAMERA,
}

BASE = {
    "language": "en", "voice": "bm_george", "speed": 1.08, "aspect": "9:16", "fps": 60, "made_for_kids": False,
    "footage": "off", "transition": "none",
    "music": {"mood": "mystery", "volume": 0.11},
    "captions": {"style": "karaoke", "y": 0.62, "size": 0.08, "max_words": 2, "highlight": "#ffd54a",
                 "uppercase": False},
    "overlay": {"handle": "@hypercurious96", "progress_bar": False},
    "world3d": WORLD,
}

if __name__ == "__main__":
    build(HERE, [("ch01", "GTA 6, one switch", SCENES)], BASE, "What if GTA 6 unlocked for everyone at the same second?", seed=19)
