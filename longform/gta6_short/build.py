"""Builds the 40-second 9:16 Short "GTA 6 for everyone in the same second" in the explainer look (ch01.json).

    python longform/gta6_short/build.py

The same facts as longform/gta6_whatif (sources there), cut to about 105 words with a statement hook, a new shot
every 3 seconds, clean captions, context chips, pinned tags, PBR + HDRI light, the NASA Earth at night, and a sound
on every cut. No game artwork, logos or characters: the city, TV and console are generic.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from kit import S, build  # noqa: E402
from explainer import CAPTIONS, SOUND, LOOK, CHIP, BIG, TAG, at, shots  # noqa: E402

W3 = {"type": "world3d"}


def COUNT(a, b, at_word, suffix, y=0.2, dur=1.6):
    return {"type": "counter", "from": a, "to": b, "suffix": suffix, "grouping": "western", "count_dur": dur,
            "x": 0.5, "y": y, "size": 0.068, "color": "#ffd54a", "style": "title", "stroke": False, "shadow": True,
            "enter": "pop", "at_word": at_word}


SCENES = [
    dict(S("Unlock GTA 6 for every player on Earth in the same second, and the internet would choke.",
           W3, CHIP("What if · launch day, 19 Nov 2026")), id="s1"),
    dict(S("The download is up to 212 gigabytes.", W3, CHIP("Size: Rockstar, via GamesRadar")), id="s2"),
    dict(S("Analysts expect about 25 million players on day one.",
           W3, CHIP("Konvoy forecast"), COUNT(0, 25000000, "25", "", y=0.2)), id="s3"),
    dict(S("Together, that's 5.3 exabytes, all at once.", W3, CHIP("25 million × 212 GB")), id="s4"),
    dict(S("Every international internet link on Earth carries about 2,259 terabits a second.",
           W3, CHIP("TeleGeography, 2026")), id="s5"),
    dict(S("With nothing else on them, that's over five hours of pure GTA.",
           W3, CHIP("5.3 EB ÷ 2,259 Tbps"), BIG("5+ hours", at_word="five", y=0.2, color="#ffd54a")), id="s6"),
    dict(S("Sign-in servers drown, and downloads sit at zero.", W3, CHIP("Scenario")), id="s7"),
    dict(S("That's why Rockstar opened preloads a week early, and unlocks at midnight, one time zone at a time.",
           W3, CHIP("Preloads from 10 Nov")), id="s8"),
    dict(S("Would you have stayed up for midnight?", W3, CHIP("Follow for more what-ifs")), id="s9"),
]
ORDER = [f"s{k}" for k in range(1, 10)]

# ---------------------------------------------------------------- environments (with image-based light)
SPACE = {"sky_top": "#000003", "sky": "#02030a", "fog": [3000, 6000], "hemi": 0.2, "ambient": 0.1, "sun": 2.4,
         "sun_color": "#fff6e6", "sun_dir": [60, 20, 40], "cloud": "#ffffff", "ocean": "#1d3b52", "exposure": 1.0,
         "hdri": "none"}
ROOM = {"sky_top": "#020306", "sky": "#06080e", "fog": [20, 60], "hemi": 0.3, "ambient": 0.15, "sun": 0.35,
        "sun_color": "#8fa8d8", "sun_dir": [10, 60, 20], "cloud": "#222222", "ocean": "#111111", "exposure": 1.25,
        "hdri": "studio", "bg": "dome", "env_intensity": 0.2}
DATA = {"sky_top": "#02040a", "sky": "#081428", "fog": [120, 420], "hemi": 0.4, "ambient": 0.2, "sun": 0.8,
        "sun_color": "#bcd8ff", "sun_dir": [30, 60, 40], "cloud": "#202838", "ocean": "#101820", "exposure": 1.05,
        "hdri": "studio2", "bg": "dome", "env_intensity": 0.6}
DC = {"sky_top": "#020305", "sky": "#06080b", "fog": [6, 26], "hemi": 0.15, "ambient": 0.08, "sun": 0.25,
      "sun_color": "#9fb6d8", "sun_dir": [10, 60, 20], "cloud": "#222222", "ocean": "#111111", "exposure": 1.1,
      "hdri": "studio", "bg": "dome", "env_intensity": 0.3}
CITY = {"sky_top": "#2b3f7a", "sky": "#f4a46e", "fog": [260, 1100], "hemi": 0.3, "ambient": 0.12, "sun": 2.0,
        "sun_color": "#ffb47a", "sun_dir": [-50, 22, 70], "cloud": "#ffd9c0", "ocean": "#1d3b52", "exposure": 1.0,
        "hdri": "golden", "bg": "dome", "env_intensity": 0.7}

E = [0, 0, 0]
TVX, DX, RX, CX = 2000, 3000, 4000, 5000
TV_LOOK = [TVX, 1.6, -2.4]
TV_WIDE, TV_MID, TV_CLOSE = [TVX, 2.3, 6.4], [TVX, 2.0, 5.4], [TVX, 1.82, 4.75]

# (scene, plan) with plan = [(start, pos0, look0, pos1, look1, fov), ...]; the env of each shot follows its region
PLAN = {
    "s1": [(0, [-28, 16, 98], E, [-22, 13, 86], E, 40, SPACE),
           ("same", [-14, 10, 66], E, [-10, 8, 58], E, 40, SPACE)],
    "s2": [(0, TV_WIDE, TV_LOOK, TV_MID, TV_LOOK, 46, ROOM),
           ("212", [TVX, 1.9, 5.1], TV_LOOK, TV_CLOSE, TV_LOOK, 46, ROOM)],
    "s3": [(0, [CX - 16, 9, 98], [CX, 10, 20], [CX - 8, 12, 88], [CX, 9, 20], 50, CITY),
           ("25", [CX + 12, 4.5, 74], [CX, 2.5, 50], [CX + 8, 5, 70], [CX, 2.5, 50], 50, CITY)],
    "s4": [(0, [DX - 34, 22, 46], [DX, 9, 0], [DX - 40, 16, 34], [DX, 10, 0], 44, DATA)],
    "s5": [(0, [DX - 26, 16, 40], [DX + 20, 7, 0], [DX - 18, 12, 44], [DX + 34, 6, 0], 46, DATA),
           ("2,259", [DX + 22, 10, 16], [DX + 40, 6.5, 0], [DX + 27, 9, 13], [DX + 46, 6.5, 0], 46, DATA)],
    "s6": [(0, [DX + 30, 4, 30], [DX, 12, 0], [DX + 22, 6, 26], [DX, 12, 0], 46, DATA),
           ("five", [DX - 52, 30, 62], [DX + 8, 8, 0], [DX - 44, 26, 54], [DX + 8, 8, 0], 46, DATA)],
    "s7": [(0, [RX + 0.2, 1.5, 2.2], [RX, 1.3, -10], [RX + 0.1, 1.4, -0.8], [RX, 1.2, -10], 58, DC),
           ("downloads", [TVX, 1.9, 5.3], TV_LOOK, TV_CLOSE, TV_LOOK, 46, ROOM)],
    "s8": [(0, TV_MID, TV_LOOK, TV_WIDE, TV_LOOK, 46, ROOM),
           ("midnight,", [-54, 18, 56], E, [-46, 16, 60], E, 40, SPACE)],
    "s9": [(0, [CX + 24, 30, 116], [CX - 8, 18, -40], [CX + 14, 26, 104], [CX - 8, 20, -40], 50, CITY)],
}

CAMERA, ENVS = [], []
for k, sid in enumerate(ORDER):
    nxt = ORDER[k + 1] if k + 1 < len(ORDER) else None
    plan = PLAN[sid]
    CAMERA += shots(sid, [p[:6] for p in plan], nxt)
    for j, p in enumerate(plan):
        start = p[0]
        t1 = at(sid, 0) if j == 0 else (at(sid, word=start) if isinstance(start, str) else at(sid, start))
        t0 = {**t1, "offset": t1.get("offset", 0) - 0.012}
        if ENVS:
            ENVS.append({**ENVS[-1], "at": t0})
        ENVS.append({**p[6], "at": t1})
ENVS[0] = {**ENVS[0], "at": 0}
CAMERA[0] = {**CAMERA[0], "at": 0}

TV = {"type": "tvroom", "pos": [TVX, 0, 0], "title": "OPEN-WORLD GAME", "size_label": "Download: 212 GB",
      "progress": [{"at": 0, "p": 0.31}, {"at": at("s2", 0), "p": 0.31}, {"at": at("s2", 1.0), "p": 0.46},
                   {"at": at("s7", word="downloads", offset=-0.02), "p": 0.0}, {"at": at("s8", 0, offset=-0.02), "p": 0.0},
                   {"at": at("s8", 0), "p": 1.0}],
      "speed": [{"at": 0, "v": 188}, {"at": at("s2", 1.0), "v": 192}, {"at": at("s7", word="downloads", offset=-0.02), "v": 0.4},
                {"at": at("s7", 1.0), "v": 0.3}, {"at": at("s8", 0), "v": 210}],
      "state": [{"at": 0, "s": 0}, {"at": at("s8", 0, offset=-0.02), "s": 0}, {"at": at("s8", 0), "s": 3}],
      "clock": [{"at": 0, "c": 9999}]}

WORLD = {
    "style": "night", "terrain": False, "far": 2000, "shadows": False,
    "look": LOOK,
    "env": ENVS,
    "objects": [
        {"type": "stars", "seed": 21, "count": 2200, "size": 1.6},
        {"type": "earth", "pos": E, "r": 20, "seed": 7, "spin": 0.035, "tilt": 20, "real": True, "face_lon": -45,
         "lights": [{"at": 0, "v": 1.0}],
         "arcs": {"count": 46, "seed": 33, "color": "#7fd4ff", "power": [
             {"at": 0, "p": 0.08}, {"at": at("s1", word="same"), "p": 0.08}, {"at": at("s1", word="choke."), "p": 1.0},
             {"at": at("s8", 0), "p": 0.0}]}},
        TV,
        TAG("212 GB", pos=[TVX + 1.25, 2.72, -2.3], show=[{"from": at("s2", word="212"), "to": at("s2", 1.0)}], accent="#ffd54a"),
        {"type": "gridfloor", "pos": [DX, 0, 0], "size": 240, "div": 48, "color": "#0a1222", "line": "#1d3352"},
        {"type": "datacube", "pos": [DX, 0, 0], "n": 14, "size": 18, "seed": 8,
         "drain": [{"at": 0, "d": 0}, {"at": at("s6", 0), "d": 0}, {"at": at("s6", 1.0), "d": 0.03}]},
        TAG("5.3 exabytes", pos=[DX, 18.6, 0], dot=True, show=[{"from": at("s4", word="5.3"), "to": at("s4", 1.0)}]),
        {"type": "pipe", "from": [DX + 9.5, 6, 0], "to": [DX + 110, 6, 0], "r": 1.1, "count": 30, "speed": 0.02},
        TAG("2,259 Tbps", pos=[DX + 43, 7.3, 0], dot=True, show=[{"from": at("s5", word="2,259"), "to": at("s5", 1.0)}]),
        {"type": "racks", "pos": [RX, 0, 0], "count": 14, "seed": 41, "health": [
            {"at": 0, "h": 1}, {"at": at("s7", 0), "h": 0.6}, {"at": at("s7", word="drown,"), "h": 0.05}]},
        TAG("Sign-in servers", pos=[RX, 2.5, -7], show=[{"from": at("s7", 0.05), "to": at("s7", word="downloads", offset=-0.05)}],
            accent="#ff5252"),
        # the city by the water at sunset
        {"type": "box", "pos": [CX, -0.5, 0], "w": 900, "h": 1, "d": 900, "color": "#3a3640"},
        {"type": "box", "pos": [CX, -0.45, 160], "w": 900, "h": 1, "d": 200, "color": "#1d4a66"},
        {"type": "towers", "seed": 14, "count": 130, "area": [CX - 170, -170, CX + 170, 40], "lit": 0.45, "glow": 0.6,
         "neon": ["#ff3fa4", "#2de2e6", "#ff9f1c", "#b14aff"], "neon_share": 0.5},
        {"type": "palms", "seed": 6, "count": 60, "area": [CX - 200, 46, CX + 200, 60], "h": 9},
        {"type": "box", "pos": [CX, 0, 52], "w": 420, "h": 0.2, "d": 16, "color": "#cdb89a"},
        {"type": "crowd", "seed": 16, "count": 1800, "area": [CX - 46, 46, CX + 46, 58], "scale": 1.0},
        TAG("25 million players", pos=[CX, 3.2, 52], dot=True, show=[{"from": at("s3", word="25", offset=0.3), "to": at("s3", 1.0)}]),
    ],
    "camera": CAMERA,
}

BASE = {
    "language": "en", "voice": "bm_george", "speed": 1.1, "aspect": "9:16", "fps": 60, "made_for_kids": False,
    "footage": "off", "transition": "none",
    "music": {"mood": "mystery", "volume": 0.1},
    "captions": CAPTIONS,
    "overlay": {"handle": "@hypercurious96", "progress_bar": False},
    "sound": {**SOUND, "first": "riser", "first_gain": 0.3,
              "hits": [{"at": at("s1", word="choke."), "kind": "boom", "gain": 0.55},
                       {"at": at("s2", word="212"), "kind": "hit", "gain": 0.45},
                       {"at": at("s4", word="5.3"), "kind": "hit", "gain": 0.5},
                       {"at": at("s6", word="five"), "kind": "hit", "gain": 0.5},
                       {"at": at("s7", word="drown,"), "kind": "glitch", "gain": 0.45}]},
    "world3d": WORLD,
}

if __name__ == "__main__":
    build(HERE, [("ch01", "GTA 6, one second", SCENES)], BASE, "GTA 6 for everyone in the same second", seed=23)
