"""Builds the animated 9:16 Short "America grounded every plane. What if the whole world did?" (English, about 115 s)
as ch01.json.

    python longform/groundstop_anim/build.py

The real event first (the FAA's nationwide ground stop of 13 November 2026: flight routes going dark, overloaded
control-centre equipment, a jet landing, grounded jets and stranded passengers, the 9/11 precedent at Gander), then a
what-if (every plane on Earth ordered down at once: minute one over the ocean, hour two with airports packed, hour six,
day two), then back to reality.
Facts: Wikipedia, "2026 FAA ground stop" (3:54 pm to 8:15 pm EST, 4 h 21 min, nearly 8,000 cancellations, 10,000+
delays, third nationwide ground stop); ABC News / AP, 13-14 Nov 2026 (3,500+ planes in the sky, 3,000+ landed safely,
11,000 flights and 1.5 million passengers due out after 4 pm, "old switches, old routers", "you will have more of
these"); CNBC (routers overloaded, cancellations into the weekend); FAA via FOX, Sep 2026 (9/11: 4,500+ planes landed
within three hours); AeroCorner (Gander: 38 aircraft; 10,000 to 24,000 aircraft airborne worldwide at any time);
Migflug (Gander population under 10,000).
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


SCENES = [
    dict(S("Yesterday, America stopped every plane from taking off. For four hours and 21 minutes, the busiest skies on Earth went quiet. It has happened only three times in history.",
           W3, T("US nationwide ground stop", y=0.13, until=99), T("13 November 2026", y=0.2, red=False, size=0.042, until=99),
           T("4 h 21 min", at_word="four", y=0.27, red=False, size=0.044), T("Only the 3rd time ever", at_word="three", y=0.34, size=0.044)), id="s1"),
    dict(S("At 3:54 in the afternoon, the links between air traffic control centres started failing. Old routers, overloaded with data, began giving inconsistent readings.",
           W3, T("3:54 pm, US Eastern time", y=0.13, red=False, size=0.042, until=99), T("Control centres losing contact", at_word="failing.", y=0.2, size=0.044),
           T("Cause: old routers overloaded", at_word="overloaded", y=0.27, red=False, size=0.042)), id="s2"),
    dict(S("More than 3,500 planes were already in the sky, and they landed safely. But 11,000 more flights, carrying one and a half million people, were due to take off.",
           W3, T("3,500+ planes in the air", at_word="3,500", y=0.13), T("11,000 flights waiting", at_word="11,000", y=0.2, red=False, size=0.044),
           T("1.5 million passengers", at_word="million", y=0.27, red=False, size=0.044)), id="s3"),
    dict(S("By the end, nearly 8,000 flights were cancelled and more than 10,000 delayed. The last time this happened was in 2023. Before that, 9/11.",
           W3, T("~8,000 flights cancelled", at_word="8,000", y=0.13), T("10,000+ delayed", at_word="10,000", y=0.2, red=False, size=0.044),
           T("Before this: 2023, and 9/11", at_word="2023.", y=0.27, red=False, size=0.042)), id="s4"),
    dict(S("On 9/11, controllers landed more than 4,500 planes in three hours. 38 jets came down in Gander, a Canadian town of under 10,000 people.",
           W3, T("Real: 11 September 2001", y=0.13, red=False, size=0.042, until=99), T("4,500+ planes landed in 3 hours", at_word="4,500", y=0.2),
           T("Gander: 38 jets, town of <10,000", at_word="38", y=0.27, red=False, size=0.04)), id="s5"),
    dict(S("So what if it happened everywhere at once? Somewhere between 10,000 and 24,000 planes are in the air at any moment. Let's land them all.",
           W3, WHATIF(), T("What if the whole world stopped?", y=0.13, until=99, size=0.044),
           T("10,000 to 24,000 planes in the air", at_word="10,000", y=0.2, red=False, size=0.04)), id="s6"),
    dict(S("Minute one. Every pilot gets the same order: land at the nearest airport. A plane halfway across the ocean has nowhere close to go.",
           W3, WHATIF(), T("MINUTE 1", y=0.13, until=99), T("“Land at the nearest airport”", at_word="land", y=0.2, red=False, size=0.042),
           T("Mid-ocean: nowhere close", at_word="halfway", y=0.27, size=0.044)), id="s7"),
    dict(S("Hour two. Small airports fill up first. Jets park on taxiways, then on runways, wingtip to wingtip, like Gander, but in thousands of towns.",
           W3, WHATIF(), T("HOUR 2", y=0.13, until=99), T("Parked wingtip to wingtip", at_word="wingtip", y=0.2, red=False, size=0.044),
           T("Thousands of Ganders", at_word="thousands", y=0.27, size=0.044)), id="s8"),
    dict(S("Hour six. Millions of passengers are stuck in places they never meant to visit. Hotels fill in minutes. Trains and buses are swamped.",
           W3, WHATIF(), T("HOUR 6", y=0.13, until=99), T("Millions stranded", at_word="Millions", y=0.2, size=0.044),
           T("Hotels full, trains swamped", at_word="Hotels", y=0.27, red=False, size=0.042)), id="s9"),
    dict(S("Day two. Air cargo stops too. Medicines, spare parts and fresh food that fly overnight don't arrive. And restarting is the hard part: every plane and crew is in the wrong city.",
           W3, WHATIF(), T("DAY 2", y=0.13, until=99), T("Air cargo stops", at_word="cargo", y=0.2, size=0.044),
           T("Planes and crews in the wrong cities", at_word="restarting", y=0.27, red=False, size=0.04)), id="s10"),
    dict(S("Back to reality. Yesterday's four hours are still cancelling flights this weekend. And the US Transport Secretary warned: you will have more of these, unless the old system is replaced.",
           W3, T("Reality check", y=0.13, red=False, size=0.044, until=99), T("Cancellations into the weekend", at_word="cancelling", y=0.2, red=False, size=0.042),
           T("“You will have more of these”", at_word="you", y=0.27, size=0.044)), id="s11"),
    dict(S("Follow for more true stories.", W3), id="s12"),
]

# ---------------------------------------------------------------- the world
SPACE = {"sky_top": "#000003", "sky": "#02030a", "fog": [3000, 6000], "hemi": 0.25, "ambient": 0.18, "sun": 2.4,
         "sun_color": "#fff6e6", "sun_dir": [60, 20, 40], "cloud": "#ffffff", "ocean": "#1d3b52", "exposure": 1.0}
DC = {"sky_top": "#020305", "sky": "#06080b", "fog": [6, 26], "hemi": 0.2, "ambient": 0.12, "sun": 0.25,
      "sun_color": "#9fb6d8", "sun_dir": [10, 60, 20], "cloud": "#222222", "ocean": "#111111", "exposure": 1.1}
DUSK = {"sky_top": "#1d1f3d", "sky": "#d8683a", "fog": [220, 900], "hemi": 1.3, "ambient": 0.65, "sun": 1.8,
        "sun_color": "#ffb070", "sun_dir": [-80, 12, 20], "cloud": "#e0a080", "ocean": "#24364a", "exposure": 1.0}
NIGHT = {"sky_top": "#03050d", "sky": "#16223c", "fog": [160, 700], "hemi": 0.75, "ambient": 0.4, "sun": 0.7,
         "sun_color": "#9fb2e0", "sun_dir": [-30, 50, -40], "cloud": "#4a5670", "ocean": "#0b1a2a", "exposure": 1.1}
DAY = {"sky_top": "#3f6ea0", "sky": "#a9c6de", "fog": [260, 1100], "hemi": 1.3, "ambient": 0.55, "sun": 1.6,
       "sun_color": "#fff3dd", "sun_dir": [30, 60, 20], "cloud": "#e4e9ee", "ocean": "#1f5572", "exposure": 1.0}
OCEAN_NIGHT = {"sky_top": "#02040b", "sky": "#132038", "fog": [180, 800], "hemi": 0.6, "ambient": 0.3, "sun": 1.2,
               "sun_color": "#a9bce8", "sun_dir": [-30, 60, -45], "cloud": "#9aa6c4", "ocean": "#0b1a2a", "exposure": 1.05}
DAWN = {"sky_top": "#22325c", "sky": "#f2b47a", "fog": [220, 1000], "hemi": 1.15, "ambient": 0.5, "sun": 2.2,
        "sun_color": "#ffc48a", "sun_dir": [80, 14, -25], "cloud": "#f7d6c8", "ocean": "#2c4a66", "exposure": 1.0}


def env(t, d):
    return {**d, "at": t}


def fixed(t, pos, look, fov=40, shake=0.0):
    k = {"at": t, "pos": pos, "look": look, "fov": fov}
    if shake:
        k["shake"] = shake
    return k


def key(t, offset, look, fov=44, follow="of"):
    return {"at": t, "follow": follow, "offset": offset, "look_offset": look, "fov": fov}


def cut(scene):
    return at(scene, 0, offset=-0.012), at(scene, 0)


def only(scene_from, scene_to=None):
    """build/hide pair: the object exists only from the start of scene_from to the end of scene_to."""
    scene_to = scene_to or scene_from
    return {"build": {"op": "slide", "offset": [0, 0, 0], "from": at(scene_from, 0), "to": at(scene_from, 0, offset=0.01)},
            "hide": {"at": at(scene_to, 1.0, offset=0.02), "dur": 0.01}}


E = [0, 0, 0]
DCX, RX, AX, GX, OX = 2000, 4000, 6000, 8000, 10000
GY = 0.685 * 3   # an airliner at scale 3 standing on its gear

ENV_BY_SCENE = [("s1", SPACE), ("s2", DC), ("s3", DUSK), ("s4", NIGHT), ("s5", DAY), ("s6", SPACE), ("s7", OCEAN_NIGHT),
                ("s8", DAY), ("s9", NIGHT), ("s10", SPACE), ("s11", DAWN), ("s12", SPACE)]
envs = [env(0, SPACE)]
for k, (sid, d) in enumerate(ENV_BY_SCENE[1:], 1):
    envs += [env(cut(sid)[0], ENV_BY_SCENE[k - 1][1]), env(cut(sid)[1], d)]


def parked(x, z, yaw=180, seed=0, extra=None):
    o = {"type": "airliner", "scale": 3, "gear": True, "lights": False, "livery": seed,
         "track": [{"at": 0, "pos": [x, GY, z], "rot": [0, yaw, 0]}, {"at": 1, "pos": [x, GY, z], "rot": [0, yaw, 0]}]}
    if extra:
        o.update(extra)
    return o


def runway(x0, length, z=0.0, width=40):
    """A runway along +x from x0 with centre-line dashes, edge lines and threshold bars."""
    objs = [{"type": "box", "pos": [x0 + length / 2, 0, z], "w": length, "h": 0.06, "d": width, "color": "#6a6f77"}]
    for k in range(int(length // 30)):
        objs.append({"type": "box", "pos": [x0 + 15 + k * 30, 0.065, z], "w": 14, "h": 0.02, "d": 0.9, "color": "#e8e8e2"})
    for sz in (-1, 1):
        objs.append({"type": "box", "pos": [x0 + length / 2, 0.065, z + sz * (width / 2 - 1.2)], "w": length, "h": 0.02, "d": 0.6, "color": "#e8e8e2"})
    for k in range(8):
        objs.append({"type": "box", "pos": [x0 + 8, 0.065, z - width / 2 + 3 + k * (width - 6) / 7], "w": 12, "h": 0.02, "d": 1.4, "color": "#e8e8e2"})
    return objs


GANDER_A = [parked(GX - 70 + k * 21, -6 - (k % 2) * 2, seed=k) for k in range(7)] + \
           [parked(GX - 60 + k * 21, -46 - (k % 2) * 2, seed=k + 3) for k in range(7)]
# hour two: more jets keep dropping in, one after another, on the runway beside the apron
GANDER_B = [parked(GX - 80 + k * 22, 44, yaw=90 + (k % 2) * 180, seed=k + 6,
                   extra={"build": {"op": "drop", "height": 40,
                                    "from": at("s8", 0.08 + k * 0.1), "to": at("s8", 0.08 + k * 0.1, offset=1.2)}}) for k in range(8)]

WORLD = {
    "style": "night", "terrain": False,
    "env": envs,
    "objects": [
        {"type": "stars", "seed": 21, "count": 2200, "size": 1.6},
        # the planet: arcs stand for flight routes; power is the share still flying
        {"type": "earth", "pos": E, "r": 20, "seed": 5, "spin": 0.03, "tilt": 20,
         "arcs": {"count": 60, "seed": 44, "color": "#ffd27a", "city": "#ffe9a8", "power": [
             {"at": 0, "p": 1}, {"at": at("s1", word="America"), "p": 1}, {"at": at("s1", word="quiet."), "p": 0.15},
             {"at": cut("s6")[0], "p": 0.15}, {"at": cut("s6")[1], "p": 1}, {"at": at("s6", word="land"), "p": 1},
             {"at": at("s6", 1.0), "p": 0.0}, {"at": cut("s10")[1], "p": 0.0}, {"at": at("s10", word="restarting"), "p": 0.0},
             {"at": at("s10", 1.0), "p": 0.12}, {"at": cut("s12")[1], "p": 0.5}, {"at": at("s12", 1.0, offset=0.5), "p": 1}]}},
        # the control-centre equipment
        {"type": "racks", "pos": [DCX, 0, 0], "count": 14, "seed": 47, "health": [
            {"at": 0, "h": 1}, {"at": cut("s2")[1], "h": 1}, {"at": at("s2", word="failing."), "h": 0.55},
            {"at": at("s2", word="inconsistent"), "h": 0.25}, {"at": at("s2", 1.0), "h": 0.12}]},
        # the runway: a landing at dusk (s3) and a take-off at dawn (s11)
        {"type": "box", "pos": [RX, -1, 0], "w": 1400, "h": 1, "d": 900, "color": "#5d6b4c"},
        *runway(RX - 300, 900),
        {"type": "airliner", "id": "lp", "scale": 3, "gear": True, "lights": True, "livery": 1, **only("s3"), "track": [
            {"at": at("s3", 0), "pos": [RX - 620, 46, 0], "rot": [3, 90, 0]},
            {"at": at("s3", word="landed"), "pos": [RX - 250, GY + 0.2, 0], "rot": [4, 90, 0], "ease": "linear"},
            {"at": at("s3", word="safely.", offset=0.3), "pos": [RX - 150, GY, 0], "rot": [0, 90, 0], "ease": "linear"},
            {"at": at("s3", 1.0), "pos": [RX + 40, GY, 0], "rot": [0, 90, 0]}]},
        {"type": "airliner", "id": "tp", "scale": 3, "gear": True, "lights": True, "livery": 2, **only("s11"), "track": [
            {"at": at("s11", 0), "pos": [RX - 240, GY, 0], "rot": [0, 90, 0]},
            {"at": at("s11", word="weekend."), "pos": [RX + 10, GY, 0], "rot": [0, 90, 0]},
            {"at": at("s11", word="warned:"), "pos": [RX + 160, GY + 1, 0], "rot": [9, 90, 0], "ease": "linear"},
            {"at": at("s11", 1.0), "pos": [RX + 420, 46, 0], "rot": [11, 90, 0], "ease": "linear"}]},
        # the airport: terminal, grounded jets at the gates, stranded passengers (s4, s9)
        {"type": "box", "pos": [AX, -1, 0], "w": 700, "h": 1, "d": 700, "color": "#61656b"},
        {"type": "box", "pos": [AX, 0, -38], "w": 170, "h": 12, "d": 18, "color": "#b9c0c8"},
        {"type": "box", "pos": [AX, 6, -28.9], "w": 170, "h": 7, "d": 0.3, "color": "#2f4a66"},
        *[parked(AX - 60 + k * 24, -6 - (k % 2) * 3, seed=k) for k in range(6)],
        {"type": "crowd", "seed": 17, "count": 700, "area": [AX - 75, -27, AX + 75, -21], "scale": 1.0,
         "n": [{"at": 0, "n": 260}, {"at": cut("s9")[1], "n": 260}, {"at": at("s9", word="Hotels"), "n": 700}]},
        # Gander: an apron of parked wide-bodies, a few low buildings, more jets arriving in hour two (s5, s8)
        {"type": "box", "pos": [GX, -1, 0], "w": 900, "h": 1, "d": 900, "color": "#56664a"},
        {"type": "box", "pos": [GX, 0, -22], "w": 200, "h": 0.06, "d": 70, "color": "#4b4f55"},
        *runway(GX - 160, 340, z=44, width=36),
        *[{"type": "box", "pos": [GX - 120 + k * 46, 0, -90 - (k % 3) * 9], "w": 22, "h": 6 + (k % 2) * 3, "d": 14,
           "color": ["#c8c2b4", "#a9b3bd", "#d6cbb5"][k % 3]} for k in range(6)],
        *GANDER_A, *GANDER_B,
        # mid-ocean at night (s7): sea, a cloud layer, one jet turning for the nearest runway
        {"type": "ocean", "y": 0, "amp": 0.5, "size": 1400, "segs": 160, **only("s7")},
        {"type": "clouds", "seed": 4, "layers": [{"y": [36, 52], "count": 26, "size": [8, 14], "from": at("s7", 0), "to": at("s7", 1.0, offset=0.05)}]},
        {"type": "airliner", "id": "of", "scale": 3, "lights": True, "livery": 3, **only("s7"), "track": [
            {"at": at("s7", 0), "pos": [OX, 70, 0], "rot": [1, 90, 0]},
            {"at": at("s7", word="order:"), "pos": [OX + 150, 70, 0], "rot": [1, 90, 0], "ease": "linear"},
            {"at": at("s7", word="airport."), "pos": [OX + 250, 69, -30], "rot": [0, 130, -28], "ease": "linear"},
            {"at": at("s7", 1.0), "pos": [OX + 300, 64, -150], "rot": [-2, 175, -12], "ease": "linear"}]},
    ],
    "camera": [
        # s1: the planet, its flight routes going dark
        fixed(0, [-18, 16, 70], E, 40),
        fixed(at("s1", 1.0, offset=-0.05), [-8, 12, 62], E, 40),
        # s2: the control-centre equipment
        fixed(cut("s2")[1], [DCX + 0.2, 1.5, 2.2], [DCX, 1.3, -10], 58),
        fixed(at("s2", 1.0, offset=-0.05), [DCX - 0.4, 0.8, -3.5], [DCX + 1.4, 1.4, -8], 60),
        # s3: beside the runway, the jet comes in and rolls out
        key(cut("s3")[1], [14, -3, 46], [0, 0, 0], 44, follow="lp"),
        key(at("s3", word="landed", offset=-1.2), [-20, 0.6, 32], [0, 0, 0], 46, follow="lp"),
        key(at("s3", word="landed"), [-24, 0.6, 22], [0, 0, 0], 46, follow="lp"),
        key(at("s3", 1.0, offset=-0.05), [-28, 2, -18], [0, 0, 4], 46, follow="lp"),
        # s4: the terminal at night, jets at the gates
        fixed(cut("s4")[1], [AX - 52, 14, 30], [AX - 8, 2, -10], 46),
        fixed(at("s4", 1.0, offset=-0.05), [AX - 40, 11, 24], [AX - 4, 2, -10], 46),
        # s5: Gander from the air
        fixed(cut("s5")[1], [GX - 96, 26, 52], [GX - 10, 0, -24], 48),
        fixed(at("s5", 1.0, offset=-0.05), [GX - 70, 20, 44], [GX - 4, 0, -24], 48),
        # s6: the planet, every route lit, then all of them go out
        fixed(cut("s6")[1], [40, 16, 62], E, 40),
        fixed(at("s6", 1.0, offset=-0.05), [32, 13, 56], E, 40),
        # s7: behind the jet over the ocean as it turns
        key(cut("s7")[1], [-12, 4, -34], [0, 0, 10], 46),
        key(at("s7", word="airport."), [-22, 6, -30], [0, 0, 6], 48),
        key(at("s7", 1.0, offset=-0.05), [-30, 9, -20], [0, 0, 0], 50),
        # s8: Gander again, jets dropping in beside the apron
        fixed(cut("s8")[1], [GX + 96, 30, 110], [GX - 4, 4, 14], 50),
        fixed(at("s8", 1.0, offset=-0.05), [GX + 76, 24, 94], [GX - 4, 4, 14], 50),
        # s9: the terminal at night, the crowd thickens
        fixed(cut("s9")[1], [AX + 30, 6, 6], [AX - 6, 3, -26], 52),
        fixed(at("s9", 1.0, offset=-0.05), [AX + 22, 5, 0], [AX - 6, 3, -26], 52),
        # s10: the planet, dark, a few routes flickering back
        fixed(cut("s10")[1], [-30, 10, 62], E, 40),
        fixed(at("s10", 1.0, offset=-0.05), [-22, 8, 58], E, 40),
        # s11: dawn, a jet takes off
        key(cut("s11")[1], [-22, 0.5, 28], [0, 1, 0], 46, follow="tp"),
        key(at("s11", word="warned:"), [-26, 0.6, 18], [0, 1, 0], 46, follow="tp"),
        key(at("s11", 1.0, offset=-0.05), [-30, -5, -34], [0, 2, 6], 48, follow="tp"),
        # s12: the planet, the routes coming back on
        fixed(cut("s12")[1], [20, 18, 72], E, 40),
        fixed(at("s12", 1.0, offset=0.5), [12, 20, 80], E, 40),
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
    build(HERE, [("ch01", "US ground stop", SCENES)], BASE, "America grounded every plane. What if the whole world did?", seed=413)
