"""Builds the animated 9:16 Short "Air France 447: what really happened" (English, about 94 seconds) as ch01.json.

    python longform/af447_anim/build.py

A 3D recreation (engine/world3d_runtime flight kit): a generic airliner (no airline livery) cruising over a night
cloud deck, flying into storms, the iced pitot probes, the climb, the stall and the fall to the ocean; then the search,
the wreck on the seabed with the flight recorders, and the aftermath at sunrise.
Facts: BEA final report (5 July 2012) as summarised by Wikipedia; Paris Court of Appeal verdict of 21 May 2026 (Al Jazeera).
Times are scene references ({"scene": "s6", "word": "hits"}), so the action stays locked to the narration.
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


def ALT(a, b, at_word=None, dur=2.0, until=None, at_time=None):
    el = {"type": "counter", "from": a, "to": b, "suffix": " ft", "grouping": "western", "count_dur": dur,
          "x": 0.5, "y": 0.23, "size": 0.05, "color": "#ffd54a", "bg": "#14181f", "bg_alpha": 0.85, "style": "label",
          "stroke": False, "enter": "pop"}
    if at_word:
        el["at_word"] = at_word
    else:
        el["at"] = 0.2 if at_time is None else at_time
    if until:
        el["until"] = until
    return el


SCENES = [
    dict(S("In 2009, a jet carrying 228 people vanished over the Atlantic. The answer was hiding four kilometres under the sea.",
           W3, T("Air France 447", y=0.13, red=True), T("1 June 2009", y=0.2, red=False, size=0.042)), id="s1"),
    dict(S("Air France 447, Rio to Paris. After midnight it flies into a wall of storms, and the captain goes for his rest break.",
           W3, T("Rio de Janeiro to Paris", y=0.13, red=False, size=0.042, until=4.0)), id="s2"),
    dict(S("Ice crystals block the pitot tubes, the probes that measure speed. The readings go haywire, and the autopilot switches off.",
           W3, T("Pitot tubes icing up", at_word="pitot", until=5.0), T("AUTOPILOT OFF", at_word="autopilot")), id="s3"),
    dict(S("The co-pilot takes manual control and pulls the nose up. The jet climbs, loses speed, and stalls.",
           W3, ALT(35000, 38000, at_word="climbs,", dur=1.8), T("STALL", at_word="stalls.", y=0.13)), id="s4"),
    dict(S("The stall alarm blares. But when the plane got too slow, the computer ignored its own data and went quiet. Pushing the nose down, the right move, made the alarm come back.",
           W3, T("STALL!  STALL!", at_word="blares.", y=0.13, until=5.6),
           T("Too slow: the alarm goes silent", at_word="quiet.", y=0.13, red=False, size=0.04, until=8.0),
           T("Nose down: the alarm returns", at_word="down,", y=0.13, size=0.04)), id="s5"),
    dict(S("The captain rushes back, but it is too late. For three and a half minutes the jet falls, nose up, and hits the ocean. No one survives.",
           W3, T("3 min 30 s", at_word="three", y=0.13, until=6.4), ALT(38000, 0, at_time=0.2, dur=6.3, until=6.6),
           T("228 lives lost", at_word="survives.", y=0.13, red=False, size=0.042)), id="s6"),
    dict(S("Wreckage is found within days. The black boxes are not.",
           W3, T("June 2009: the search", y=0.13, red=False, size=0.042)), id="s7"),
    dict(S("Then in April 2011, a sonar search finds the wreck almost four kilometres down. Both recorders still work.",
           W3, T("April 2011", y=0.13, red=False, size=0.042, until=4.0), T("3,980 m deep", at_word="four", y=0.13),
           T("Flight recorders recovered", at_word="recorders", y=0.2, red=False, size=0.04)), id="s8"),
    dict(S("The verdict: frozen sensors, a confusing alarm, and pilots never trained to fly by hand up there.",
           W3, T("1. Frozen sensors", at_word="frozen", y=0.12, size=0.042),
           T("2. A confusing alarm", at_word="confusing", y=0.18, size=0.042),
           T("3. No training for this", at_word="pilots", y=0.24, size=0.042)), id="s9"),
    dict(S("The sensors were replaced, and pilots now train for exactly this kind of stall.",
           W3, T("New pitot tubes", at_word="sensors", y=0.13, red=False, size=0.042, until=2.6),
           T("New stall training", at_word="train", y=0.13, red=False, size=0.042)), id="s10"),
    dict(S("And in May 2026, a Paris court found Airbus and Air France guilty of manslaughter. Airbus plans to appeal.",
           W3, T("Guilty, 21 May 2026", at_word="guilty", y=0.13),
           T("Airbus to appeal", at_word="appeal.", y=0.2, red=False, size=0.04)), id="s11"),
    dict(S("Follow for more true stories.", W3), id="s12"),
]

# ---------------------------------------------------------------- the world
NIGHT = {"sky_top": "#02050c", "sky": "#1a2642", "fog": [70, 330], "hemi": 0.6, "ambient": 0.25, "sun": 1.4,
         "sun_color": "#a9bce8", "sun_dir": [-30, 60, -45], "cloud": "#5a6684", "ocean": "#0c1b2b", "exposure": 1.05}
STORM = {**NIGHT, "sky": "#151d30", "fog": [30, 170], "cloud": "#4a546e", "hemi": 0.55}
FALL = {**STORM, "fog": [45, 230]}
DAY = {"sky_top": "#66778a", "sky": "#b7c1cb", "fog": [70, 330], "hemi": 1.25, "ambient": 0.5, "sun": 1.3,
       "sun_color": "#f2f0ea", "sun_dir": [20, 50, 30], "cloud": "#d4d9df", "ocean": "#3a586a", "exposure": 1.0}
DEEP = {"sky_top": "#010a14", "sky": "#072a42", "fog": [4, 55], "hemi": 0.9, "ambient": 0.35, "sun": 0.5,
        "sun_color": "#3f6f9a", "sun_dir": [0, 60, 0], "cloud": "#04121f", "ocean": "#04121f", "exposure": 1.1}
DAWN = {"sky_top": "#22325c", "sky": "#f2a66a", "fog": [90, 360], "hemi": 1.0, "ambient": 0.42, "sun": 2.3,
        "sun_color": "#ffc48a", "sun_dir": [80, 14, -25], "cloud": "#f7d6c8", "ocean": "#2c4a66", "exposure": 1.0}

IMPACT = [973, 0, 0]
SEA = [973, -80, 0]


def env(t, d):
    return {**d, "at": t}


def key(t, offset, look, fov=40, shake=0.0, follow="jet", ease=None, roll=0):
    k = {"at": t, "follow": follow, "offset": offset, "look_offset": look, "fov": fov}
    if shake:
        k["shake"] = shake
    if ease:
        k["ease"] = ease
    if roll:
        k["roll"] = roll
    return k


def fixed(t, pos, look, fov=40, shake=0.0):
    k = {"at": t, "pos": pos, "look": look, "fov": fov}
    if shake:
        k["shake"] = shake
    return k


def cut(scene):
    """(the end of the previous shot, the start of this one): two times 0.01 s apart make a hard cut."""
    return at(scene, 0, offset=-0.012), at(scene, 0)


WORLD = {
    "style": "night", "terrain": False,
    "env": [
        env(0, NIGHT), env(at("s2", 0.45), NIGHT), env(at("s3", 0), STORM), env(at("s6", 0), STORM), env(at("s6", 0.5), FALL),
        env(cut("s7")[0], FALL), env(cut("s7")[1], DAY), env(cut("s8")[0], DAY), env(cut("s8")[1], DEEP),
        env(cut("s9")[0], DEEP), env(cut("s9")[1], STORM), env(cut("s10")[0], STORM), env(cut("s10")[1], DAWN),
    ],
    "lightning": [{"from": at("s2", 0.35), "to": at("s6", 0.75), "rate": 0.9, "seed": 3, "strength": 1.0},
                  {"from": at("s9", 0), "to": at("s10", 0), "rate": 1.2, "seed": 9, "strength": 1.0}],
    "objects": [
        {"type": "ocean", "y": 0, "amp": 0.85},
        {"type": "clouds", "seed": 4, "layers": [
            {"y": [35, 66], "count": 120, "size": [12, 24]},
            {"y": [88, 150], "count": 22, "size": [6, 13]},
            {"y": [84, 128], "count": 70, "size": [7, 15], "from": at("s2", 0.8), "to": at("s6", 0.15)},
        ]},
        {"type": "clouds", "seed": 12, "layers": [{"y": [84, 126], "count": 70, "size": [7, 15], "from": at("s9", 0),
                                                   "to": at("s10", 0, offset=-0.01), "fade": 0.01}]},
        # the storm wall seen ahead in s2 (gone once the jet is inside it)
        *[{"type": "cumulus", "pos": p, "h": h, "r": r, "seed": sd, "hide": {"at": at("s3", 0), "dur": 0.01}}
          for p, h, r, sd in (([640, 18, 26], 200, 42, 2), ([700, 12, -34], 180, 38, 5), ([780, 20, 6], 220, 46, 8))],
        # the jet: cruise, the storm, the climb, the stall, the fall
        {"type": "airliner", "id": "jet", "ice": {"from": at("s3", word="block"), "to": at("s3", word="block", offset=2.6)},
         "track": [
             {"at": 0, "pos": [0, 100, 0], "rot": [2, 90, 0]},
             {"at": at("s4", word="pulls"), "pos": [756, 100, 0], "rot": [2, 90, 0]},
             {"at": at("s4", word="climbs,"), "pos": [793, 106, 0], "rot": [12, 90, 0]},
             {"at": at("s5", 0), "pos": [828, 116, 0], "rot": [15, 90, 0]},
             {"at": at("s5", word="quiet."), "pos": [870, 112, 0], "rot": [16, 90, 0]},
             {"at": at("s5", word="Pushing"), "pos": [874, 111, 0], "rot": [15, 90, 0]},
             {"at": at("s5", word="down,"), "pos": [883, 109, 0], "rot": [4, 90, 0]},
             {"at": at("s5", word="move,"), "pos": [892, 107, 0], "rot": [6, 90, 0]},
             {"at": at("s5", word="back."), "pos": [914, 103, 0], "rot": [15, 90, 0]},
             {"at": at("s6", 0), "pos": [921, 100, 0], "rot": [15, 90, 0]},
             {"at": at("s6", word="falls,"), "pos": [963, 18, 0], "rot": [14, 90, 0], "ease": "linear"},
             {"at": at("s6", word="hits"), "pos": IMPACT, "rot": [14, 90, 0], "ease": "linear"},
         ],
         "wobble": [{"from": at("s2", 0.6), "to": at("s4", 0.3), "roll": 3, "pitch": 0.6, "freq": 0.7},
                    {"from": at("s4", 0.9), "to": at("s6", word="hits"), "roll": 13, "pitch": 2.5, "freq": 0.28}],
         "hide": {"at": at("s6", word="hits", offset=0.05), "op": "sink", "dur": 0.5, "depth": 6}},
        {"type": "streaks", "follow": "jet", "from": at("s2", 0.8), "to": at("s6", 0.4), "count": 340, "box": [14, 9, 14],
         "dir": [-1, -0.22, 0.05], "speed": 70, "len": 1.7, "opacity": 0.5},
        {"type": "splash", "pos": IMPACT, "at": at("s6", word="hits"), "size": 1.5},
        # the search, on a grey morning
        {"type": "debris", "pos": IMPACT, "count": 30, "spread": 16, "seed": 21,
         "build": {"op": "slide", "offset": [0, 0, 0], "from": at("s7", 0), "to": at("s7", 0, offset=0.01)}},
        {"type": "ship", "pos": [994, 0, 20], "length": 16, "heading": 75,
         "build": {"op": "slide", "offset": [0, 0, 0], "from": at("s7", 0), "to": at("s7", 0, offset=0.01)}},
        # the deep: seabed, wreckage, the recorders and an AUV with a searchlight
        {"type": "seabed", "pos": SEA, "size": 170, "seed": 4, "clear": 9},
        {"type": "wreck", "pos": [973, -79.85, 0], "seed": 8},
        {"type": "recorder", "pos": [975.6, -79.82, 1.6], "rot": 35, "scale": 1.3},
        {"type": "auv", "id": "auv", "light": 55, "track": [
            {"at": at("s8", 0.1), "pos": [957, -76.3, -7], "rot": [-6, 55, 0]},
            {"at": at("s8", word="four"), "pos": [968, -77.0, -2.6], "rot": [-8, 52, 0]},
            {"at": at("s9", 0, offset=-0.05), "pos": [972.6, -77.6, -0.4], "rot": [-12, 50, 0]}]},
        {"type": "streaks", "from": at("s8", 0), "to": at("s9", 0, offset=-0.6), "count": 420, "box": [6, 4, 6],
         "dir": [0.15, 1, 0.08], "speed": 0.5, "len": 0.06, "opacity": 0.75, "color": "#b9cfdc"},
        # the replay: the same jet in the storm, frosting over again
        {"type": "airliner", "id": "jet2", "ice": {"from": at("s9", 0.05), "to": at("s9", word="frozen")},
         "build": {"op": "slide", "offset": [0, 0, 0], "from": at("s9", 0), "to": at("s9", 0, offset=0.01)},
         "hide": {"at": at("s10", 0, offset=-0.01), "dur": 0.01},
         "track": [{"at": at("s9", 0), "pos": [3000, 100, 0], "rot": [2, 90, 0]},
                   {"at": at("s10", 0), "pos": [3174, 100, 0], "rot": [3, 90, 0]}],
         "wobble": [{"from": at("s9", 0), "to": at("s10", 0), "roll": 4, "pitch": 1, "freq": 0.7}]},
        {"type": "streaks", "follow": "jet2", "from": at("s9", 0), "to": at("s10", 0, offset=-0.6), "count": 340,
         "box": [14, 9, 14], "dir": [-1, -0.22, 0.05], "speed": 70, "len": 1.7, "opacity": 0.5},
        # sunrise: new probes, new training
        {"type": "airliner", "id": "jet3",
         "build": {"op": "slide", "offset": [0, 0, 0], "from": at("s10", 0), "to": at("s10", 0, offset=0.01)},
         "track": [{"at": at("s10", 0), "pos": [6000, 100, 0], "rot": [2, 90, 0]},
                   {"at": at("s12", 1.0, offset=0.5), "pos": [6410, 101, 0], "rot": [2, 90, 0]}]},
    ],
    "camera": [
        # s1: alongside, over the night cloud deck
        key(0, [6, 2.2, -11], [0, 0.3, 2], 42),
        key(at("s1", 1.0, offset=-0.05), [15, 2.4, 3], [0, -0.3, 0], 38),
        # s2: behind the jet, the storm wall ahead
        key(cut("s2")[1], [-1.5, 2.4, -14], [0, 6, 60], 50),
        key(at("s2", 1.0, offset=-0.05), [-1.0, 1.5, -10.5], [0, 2.5, 40], 46, shake=0.06),
        # s3: the pitot probe icing up, then the jet in turbulence
        key(cut("s3")[1], [1.75, 0.14, 1.9], [0.29, -0.07, 2.66], 36, shake=0.015),
        key(at("s3", word="haywire,", offset=-0.35), [1.5, 0.11, 2.15], [0.29, -0.07, 2.66], 30, shake=0.02),
        key(at("s3", word="haywire,", offset=-0.33), [9, 1.6, 12], [0, 0, 0], 40, shake=0.14),
        key(at("s3", 1.0, offset=-0.05), [11, 1.2, 9], [0, 0, 0], 40, shake=0.14),
        # s4: in profile, so the nose-up climb reads
        key(cut("s4")[1], [18, 0.6, 1], [0, -1.3, 0.5], 31, shake=0.05),
        key(at("s4", 1.0, offset=-0.05), [19, 0, -1], [0, -1.3, 0.5], 31, shake=0.06),
        # s5: from below and ahead, the stalled jet wallowing
        key(cut("s5")[1], [9, -5, 11], [0, 1.2, 0], 40, shake=0.12),
        key(at("s5", word="quiet."), [13, -3, 5], [0, 0.6, 0], 38, shake=0.12),
        key(at("s5", 1.0, offset=-0.05), [17, 0, -2], [0, -0.4, 0], 36, shake=0.1),
        # s6: the fall, then the impact seen from the water
        key(cut("s6")[1], [24, 3, -6], [0, -3, 2], 42, shake=0.1),
        key(at("s6", word="falls,", offset=-0.5), [22, 4, -4], [0, -3, 2], 44, shake=0.1),
        fixed(at("s6", word="hits", offset=-0.3), [962, 8, -30], [973, 2, 0], 42),
        fixed(at("s6", 1.0, offset=-0.05), [964, 6.5, -27], [973, 0.8, 0], 40),
        # s7: the search on a grey morning
        fixed(cut("s7")[1], [948, 9, -48], [978, 0.5, -6], 40),
        fixed(at("s7", 1.0, offset=-0.05), [953, 7, -44], [980, 0.5, -6], 40),
        # s8: down to the seabed, the AUV's light finds the recorder
        fixed(cut("s8")[1], [962, -45, -16], [972, -80, 0], 50),
        fixed(at("s8", word="four"), [966, -75.6, -9], [973, -79.4, 0], 46),
        fixed(at("s8", word="recorders", offset=-0.4), [972.6, -78.1, -2.4], [975.6, -79.6, 1.6], 40),
        fixed(at("s8", 1.0, offset=-0.05), [973.6, -78.7, -1.0], [975.6, -79.7, 1.6], 34),
        # s9: the replay in the storm
        key(cut("s9")[1], [-3, 2.4, -12], [0, 0.4, 4], 42, shake=0.1, follow="jet2"),
        key(at("s9", 1.0, offset=-0.05), [-4.5, 1.6, -9], [0, 0.2, 2], 42, shake=0.1, follow="jet2"),
        # s10-s12: sunrise
        key(cut("s10")[1], [1.8, 0.16, 1.95], [0.29, -0.07, 2.66], 32, follow="jet3"),
        key(at("s10", word="train", offset=-0.6), [1.6, 0.14, 2.1], [0.29, -0.07, 2.66], 30, follow="jet3"),
        key(at("s10", 1.0, offset=-0.05), [15, 2.5, -1], [0, -0.6, 0.8], 36, follow="jet3"),
        key(at("s11", 0.55), [3, 4, -18], [0, 0.5, 4], 40, follow="jet3"),
        key(at("s11", 1.0, offset=-0.05), [1.5, 3, -22], [0, 1, 10], 42, follow="jet3"),
        fixed(cut("s12")[1], [6338, 103, 6], [6420, 100, -4], 40),
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
    build(HERE, [("ch01", "Air France 447", SCENES)], BASE, "Air France 447: what really happened", seed=447)
