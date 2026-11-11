"""Builds the animated 9:16 Short "The 34 km gap that sets your petrol price" (English, about 95 seconds) as ch01.json.

    python longform/hormuz_anim/build.py

A 3D recreation (engine/world3d_runtime gulf kit): tankers in the Strait of Hormuz between two coasts, the closure of
28 February 2026, a missile strike, mines, the stranded fleet, the stop-go of ceasefires, India's reroute, and the
attacks of early November.
Facts: Wikipedia "2026 Strait of Hormuz crisis" (timeline to 25 Sep 2026); Al Jazeera, 7 Nov 2026 (UKMTO weekly
figures); Marine Insight, 5 Nov 2026 (Iran's exemption for Indian, Chinese, Qatari and Iraqi ships); News on AIR,
11 Mar 2026 (70% of India's crude sourced outside Hormuz).
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


def PRICE(a, b, at_word=None, dur=1.6, until=None, at_time=None, y=0.22):
    el = {"type": "counter", "from": a, "to": b, "prefix": "Brent  $", "suffix": " / barrel", "grouping": "western",
          "count_dur": dur, "x": 0.5, "y": y, "size": 0.05, "color": "#ffd54a", "bg": "#14181f", "bg_alpha": 0.85,
          "style": "label", "stroke": False, "enter": "pop"}
    if at_word:
        el["at_word"] = at_word
    else:
        el["at"] = 0.2 if at_time is None else at_time
    if until:
        el["until"] = until
    return el


SCENES = [
    dict(S("There is a 34 kilometre gap of water that decides what you pay for petrol. And right now, it is a war zone.",
           W3, T("Strait of Hormuz", y=0.13), T("34 km wide", at_word="gap", y=0.2, red=False, size=0.042)), id="s1"),
    dict(S("The Strait of Hormuz, between Iran and Oman. In a normal year, a fifth of the world's oil sails through here, around 20 million barrels a day. And a fifth of its liquefied gas.",
           W3, T("IRAN", y=0.10, red=False, size=0.04, until=99), T("OMAN", y=0.9, red=False, size=0.04, until=99),
           T("20 million barrels a day", at_word="20", y=0.2), T("20% of the world's LNG", at_word="liquefied", y=0.27, red=False, size=0.042)), id="s2"),
    dict(S("On 28 February 2026, the US and Israel struck Iran. Iran's Revolutionary Guard answered by closing the strait. Ship traffic fell 70 percent overnight.",
           W3, T("28 February 2026", y=0.13, red=False, size=0.042, until=5.0), T("STRAIT CLOSED", at_word="closing", y=0.13),
           T("Traffic down 70%", at_word="fell", y=0.2, red=False, size=0.042)), id="s3"),
    dict(S("Then the attacks began. Tankers hit by missiles and drones. Mines laid in the shipping lanes. Within days, Indian seafarers were among the dead.",
           W3, T("Missile strikes", at_word="missiles", y=0.13, until=5.5), T("Mines in the lanes", at_word="Mines", y=0.2, until=6.5),
           T("Indian crew killed, 1 to 2 March", at_word="Indian", y=0.13, red=False, size=0.04)), id="s4"),
    dict(S("Within ten days, Brent crude crossed 100 dollars a barrel. By 19 March, Dubai crude hit a record 166.",
           W3, PRICE(72, 100, at_word="crossed", dur=2.0, until=5.2), T("Dubai crude: $166, a record", at_word="record", y=0.22)), id="s5"),
    dict(S("Two thousand ships and twenty thousand sailors were trapped inside the Gulf. Insurers pulled out.",
           W3, T("2,000 ships stranded", at_word="Two", y=0.13), T("20,000 sailors", at_word="twenty", y=0.2, red=False, size=0.042)), id="s6"),
    dict(S("A ceasefire in April reopened it. Ten days later it closed again. A deal in June, broken in July. Each time, the tankers stopped.",
           W3, T("8 April: ceasefire", at_word="ceasefire", y=0.13, red=False, size=0.042),
           T("18 April: closed again", at_word="closed", y=0.2, red=False, size=0.042),
           T("17 June: deal.  8 July: broken", at_word="deal", y=0.27, red=False, size=0.042)), id="s7"),
    dict(S("Why does India care? We import about 90 percent of our crude oil, and nearly a third of it came through this strait.",
           W3, T("India: ~90% of crude is imported", at_word="90", y=0.13, red=False, size=0.042),
           T("~30% of it via Hormuz", at_word="third", y=0.2)), id="s8"),
    dict(S("So India rerouted. By March, 70 percent of its crude was being bought from outside the Gulf. And Iran now lets Indian ships through, for a fee.",
           W3, T("70% of crude now sourced outside the Gulf", at_word="70", y=0.13, red=False, size=0.04),
           T("Indian ships allowed, for a fee", at_word="fee.", y=0.2, red=False, size=0.042)), id="s9"),
    dict(S("This month, eleven ships were attacked in a single week. Three of them sank. Traffic is still 65 percent below normal.",
           W3, T("11 ships attacked in one week", at_word="eleven", y=0.13), T("3 sank", at_word="Three", y=0.2),
           T("Traffic still 65% below normal", at_word="65", y=0.27, red=False, size=0.04)), id="s10"),
    dict(S("Mediators are talking. Iran has seven demands. The US has its blockade. And every tanker that waits out here adds a few rupees to your fuel bill.",
           W3, T("Iran: 7 demands", at_word="seven", y=0.13, red=False, size=0.042),
           T("US: naval blockade", at_word="blockade.", y=0.2, red=False, size=0.042)), id="s11"),
    dict(S("Follow for more true stories.", W3), id="s12"),
]

# ---------------------------------------------------------------- the world
NIGHT = {"sky_top": "#02050c", "sky": "#17223a", "fog": [140, 900], "hemi": 0.6, "ambient": 0.25, "sun": 1.3,
         "sun_color": "#a9bce8", "sun_dir": [-30, 60, -45], "cloud": "#5a6684", "ocean": "#0b1a2a", "exposure": 1.05}
MAP = {"sky_top": "#5d6d80", "sky": "#c4b9a6", "fog": [700, 2600], "hemi": 1.15, "ambient": 0.5, "sun": 1.4,
       "sun_color": "#f3e6cf", "sun_dir": [25, 46, 30], "cloud": "#d6d1c6", "ocean": "#2d4f66", "exposure": 1.0}
HAZE = {"sky_top": "#5d6d80", "sky": "#c4b9a6", "fog": [120, 760], "hemi": 1.15, "ambient": 0.5, "sun": 1.4,
        "sun_color": "#f3e6cf", "sun_dir": [25, 46, 30], "cloud": "#d6d1c6", "ocean": "#2d4f66", "exposure": 1.0}
DAY = {"sky_top": "#3f6ea0", "sky": "#a9c6de", "fog": [160, 980], "hemi": 1.3, "ambient": 0.5, "sun": 1.6,
       "sun_color": "#fff3dd", "sun_dir": [30, 60, 20], "cloud": "#e4e9ee", "ocean": "#1f5572", "exposure": 1.0}
DUSK = {"sky_top": "#1d1f3d", "sky": "#d8683a", "fog": [110, 700], "hemi": 0.9, "ambient": 0.4, "sun": 1.9,
        "sun_color": "#ffb070", "sun_dir": [-80, 10, 20], "cloud": "#e0a080", "ocean": "#24364a", "exposure": 1.0}
DAWN = {"sky_top": "#22325c", "sky": "#f2b47a", "fog": [140, 900], "hemi": 1.0, "ambient": 0.42, "sun": 2.3,
        "sun_color": "#ffc48a", "sun_dir": [80, 14, -25], "cloud": "#f7d6c8", "ocean": "#2c4a66", "exposure": 1.0}


def env(t, d):
    return {**d, "at": t}


def key(t, offset, look, fov=40, shake=0.0, follow="t1", ease=None, roll=0):
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


def slide_in(scene):
    return {"op": "slide", "offset": [0, 0, 0], "from": at(scene, 0), "to": at(scene, 0, offset=0.01)}


SAND = {"colors": ["#8c7b62", "#7a6b55", "#9a8a6e"], "top": "#a4967a", "facet": 14, "band": 2.2, "jag": 0.05}
# the two coasts: Iran to the north (+z), the Musandam peninsula of Oman to the south (-z); lanes run along x
COASTS = [
    {"type": "hill", "pos": [0, 0, 175], "w": 1500, "d": 220, "h": 14, "sides": 26, "seed": 11, **SAND},
    {"type": "hill", "pos": [260, 0, 235], "w": 520, "d": 180, "h": 34, "sides": 14, "seed": 12, **SAND},
    {"type": "hill", "pos": [-420, 0, 240], "w": 520, "d": 170, "h": 26, "sides": 14, "seed": 13, **SAND},
    {"type": "hill", "pos": [40, 0, -175], "w": 1400, "d": 210, "h": 18, "sides": 26, "seed": 14, **SAND},
    {"type": "hill", "pos": [-120, 0, -230], "w": 440, "d": 170, "h": 46, "sides": 14, "seed": 15, **SAND},
    {"type": "hill", "pos": [330, 0, -225], "w": 400, "d": 150, "h": 38, "sides": 14, "seed": 16, **SAND},
]
# the stranded fleet, far west inside the Gulf (seen from above in s6)
FLEET = [{"type": "tanker", "pos": [-900 + (k % 5) * 58 + (k // 5) * 17, 0, -40 + (k // 5) * 52 + (k % 3) * 9], "heading": 60 + (k * 37) % 50,
          "length": 22 + (k % 3) * 3, "seed": k + 3, "build": slide_in("s6"), "hide": {"at": at("s7", 0, offset=-0.01), "dur": 0.01}}
         for k in range(15)]


def convoy(ids, x0, gap, stop_at=None, go_at=None, speed=10.0, z=0, seed=0):
    """Tankers heading east (+x) in line astern; the convoy halts between stop_at and go_at."""
    objs = []
    for k, i in enumerate(ids):
        x = x0 - k * gap
        pts = [{"at": 0, "pos": [x, 0, z + (k % 2) * 6 - 3], "rot": [0, 90, 0]}]
        if stop_at:
            pts.append({"at": stop_at, "pos": [x + 60, 0, z + (k % 2) * 6 - 3], "rot": [0, 90, 0], "ease": "linear"})
            pts.append({"at": go_at, "pos": [x + 60, 0, z + (k % 2) * 6 - 3], "rot": [0, 90, 0], "ease": "linear"})
            pts.append({"at": at("s12", 1.0), "pos": [x + 120, 0, z + (k % 2) * 6 - 3], "rot": [0, 90, 0], "ease": "linear"})
        objs.append({"type": "tanker", "id": i, "length": 24, "seed": seed + k, "track": pts})
    return objs


HIT = [60, 0, 3]     # tanker t2 when the missile lands (s4)
HIT2 = [3300, 0, 0]  # the November strike (s10), on a separate stretch of sea

WORLD = {
    "style": "night", "terrain": False,
    "env": [
        env(0, NIGHT), env(cut("s2")[0], NIGHT), env(cut("s2")[1], MAP), env(cut("s3")[0], MAP), env(cut("s3")[1], NIGHT),
        env(at("s4", 1.0), NIGHT), env(cut("s5")[0], NIGHT), env(cut("s5")[1], DAWN), env(cut("s6")[0], DAWN), env(cut("s6")[1], DAY),
        env(cut("s8")[0], DAY), env(cut("s8")[1], HAZE), env(cut("s10")[0], HAZE), env(cut("s10")[1], DUSK),
        env(cut("s11")[0], DUSK), env(cut("s11")[1], DAWN),
    ],
    "lightning": [{"from": at("s3", word="struck"), "to": at("s3", word="answered"), "rate": 2.2, "seed": 3, "strength": 0.9}],
    "objects": [
        {"type": "ocean", "y": 0, "amp": 0.5, "size": 1400, "segs": 170},
        {"type": "clouds", "seed": 4, "layers": [{"y": [120, 190], "count": 50, "size": [14, 30], "from": at("s3", 0), "to": at("s12", 1.0, offset=1)}]},
        *COASTS,
        # the main convoy through the strait (t1 leads, t2 is hit in s4, t3 is the Indian tanker of s8 to s9)
        {"type": "tanker", "id": "t1", "length": 24, "seed": 1, "track": [
            {"at": 0, "pos": [-40, 0, -6], "rot": [0, 90, 0]},
            {"at": at("s3", word="closing"), "pos": [120, 0, -6], "rot": [0, 90, 0], "ease": "linear"},
            {"at": at("s3", word="fell"), "pos": [132, 0, -2], "rot": [0, 70, 0], "ease": "linear"},
            {"at": at("s5", 1.0), "pos": [132, 0, -2], "rot": [0, 70, 0], "ease": "linear"}]},
        {"type": "tanker", "id": "t2", "length": 26, "seed": 2, "fire": {"at": at("s4", word="missiles"), "z": 2, "size": 1.2, "dur": 17},
         "track": [
            {"at": 0, "pos": [-110, 0, 4], "rot": [0, 90, 0]},
            {"at": at("s3", word="closing"), "pos": [50, 0, 4], "rot": [0, 90, 0], "ease": "linear"},
            {"at": at("s3", word="fell"), "pos": [HIT[0], 0, HIT[2]], "rot": [0, 88, 0], "ease": "linear"},
            {"at": at("s4", word="missiles", offset=-0.01), "pos": HIT, "rot": [0, 88, 0], "ease": "linear"},
            {"at": at("s4", word="missiles", offset=0.25), "pos": HIT, "rot": [0, 88, 4], "ease": "linear"},
            {"at": at("s5", 1.0), "pos": [HIT[0] + 2, -1.2, HIT[2]], "rot": [0, 88, 9], "ease": "linear"}]},
        {"type": "tanker", "id": "t3", "length": 24, "seed": 3, "track": [
            {"at": 0, "pos": [-180, 0, -4], "rot": [0, 90, 0]},
            {"at": at("s3", word="closing"), "pos": [-20, 0, -4], "rot": [0, 90, 0], "ease": "linear"},
            {"at": at("s3", word="fell"), "pos": [-12, 0, -4], "rot": [0, 90, 0], "ease": "linear"},
            {"at": at("s5", 1.0), "pos": [-12, 0, -4], "rot": [0, 90, 0], "ease": "linear"}]},
        {"type": "tanker", "id": "t4", "length": 22, "seed": 4, "track": [
            {"at": 0, "pos": [-250, 0, 8], "rot": [0, 90, 0]},
            {"at": at("s3", word="closing"), "pos": [-90, 0, 8], "rot": [0, 90, 0], "ease": "linear"},
            {"at": at("s3", word="fell"), "pos": [-82, 0, 8], "rot": [0, 90, 0], "ease": "linear"},
            {"at": at("s5", 1.0), "pos": [-82, 0, 8], "rot": [0, 90, 0], "ease": "linear"}]},
        # the fast patrol boat that crosses the lane as the strait closes
        {"type": "ship", "id": "pb", "length": 9, "color": "#4a5560", "track": [
            {"at": at("s3", word="Guard"), "pos": [160, 0, 90], "rot": [0, 200, 0]},
            {"at": at("s4", 0.3), "pos": [150, 0, -30], "rot": [0, 190, 0], "ease": "linear"}],
         "hide": {"at": at("s4", 1.0), "dur": 0.01}},
        # the missile and the blast (s4)
        {"type": "missile", "id": "m1", "length": 2.4, "build": slide_in("s4"),
         "hide": {"at": at("s4", word="missiles"), "dur": 0.01},
         "track": [{"at": at("s4", 0), "pos": [HIT[0] + 30, 70, 260], "rot": [-16, 185, 0]},
                   {"at": at("s4", word="missiles"), "pos": [HIT[0] + 1, 2.4, HIT[2]], "rot": [-16, 185, 0], "ease": "linear"}]},
        {"type": "blast", "pos": [HIT[0] + 1, 2.2, HIT[2]], "at": at("s4", word="missiles"), "size": 1.3, "seed": 5},
        *[{"type": "mine", "pos": [HIT[0] - 30 + k * 7, 0, 12 + (k % 3) * 4], "r": 1.1, "seed": k,
           "build": {"op": "slide", "offset": [0, 0, 0], "from": at("s4", word="Mines", offset=-0.3), "to": at("s4", word="Mines", offset=-0.29)}} for k in range(5)],
        *FLEET,
        # s7 stop-go convoy, on its own stretch (x around 1500)
        *convoy(["c1", "c2", "c3"], 1560, 48, stop_at=at("s7", word="closed"), go_at=at("s7", word="deal,"), z=0, seed=20),
        # s8 to s9: the Indian tanker through the strait with an escort alongside
        {"type": "tanker", "id": "ind", "length": 26, "seed": 30, "deck": "#2f6b3a", "track": [
            {"at": at("s8", 0), "pos": [-200, 0, -4], "rot": [0, 90, 0]},
            {"at": at("s9", 1.0, offset=0.1), "pos": [60, 0, -4], "rot": [0, 90, 0], "ease": "linear"}]},
        {"type": "ship", "id": "esc", "length": 10, "color": "#3b4652", "track": [
            {"at": at("s8", 0), "pos": [-186, 0, 16], "rot": [0, 90, 0]},
            {"at": at("s9", 1.0, offset=0.1), "pos": [74, 0, 16], "rot": [0, 90, 0], "ease": "linear"}]},
        # s10: the November attack, a tanker sinking
        {"type": "tanker", "id": "nv", "length": 26, "seed": 40, "fire": {"at": at("s10", word="attacked"), "z": -3, "size": 1.3},
         "track": [{"at": at("s10", 0), "pos": [HIT2[0] - 20, 0, 0], "rot": [0, 90, 0]},
                   {"at": at("s10", word="attacked", offset=-0.01), "pos": HIT2, "rot": [0, 90, 0], "ease": "linear"},
                   {"at": at("s10", word="Three"), "pos": [HIT2[0] + 4, -0.6, 0], "rot": [-4, 90, 6], "ease": "linear"},
                   {"at": at("s10", 1.0), "pos": [HIT2[0] + 8, -3.2, 0], "rot": [-14, 90, 12], "ease": "linear"}]},
        {"type": "tanker", "id": "nv2", "length": 24, "seed": 41, "track": [
            {"at": at("s10", 0), "pos": [HIT2[0] - 90, 0, 40], "rot": [0, 90, 0]},
            {"at": at("s10", 1.0), "pos": [HIT2[0] - 50, 0, 40], "rot": [0, 90, 0], "ease": "linear"}]},
        {"type": "missile", "id": "m2", "length": 2.4, "build": slide_in("s10"),
         "hide": {"at": at("s10", word="attacked"), "dur": 0.01},
         "track": [{"at": at("s10", 0), "pos": [HIT2[0] + 40, 60, 230], "rot": [-15, 190, 0]},
                   {"at": at("s10", word="attacked"), "pos": [HIT2[0] - 2, 2.4, 1], "rot": [-15, 190, 0], "ease": "linear"}]},
        {"type": "blast", "pos": [HIT2[0] - 2, 2.2, 1], "at": at("s10", word="attacked"), "size": 1.4, "seed": 6},
        # s11 to s12: tankers waiting at anchor at dawn, east of the strait
        *[{"type": "tanker", "pos": [5000 + (k % 4) * 70 + (k // 4) * 25, 0, -30 + (k // 4) * 60 + (k % 2) * 12], "heading": 40 + (k * 29) % 60,
           "length": 22 + (k % 3) * 3, "seed": 50 + k, "build": slide_in("s11")} for k in range(10)],
    ],
    "camera": [
        # s1: low over the water at night, a tanker sliding past with its lights on
        key(0, [-16, 3.5, 30], [0, 1.5, 0], 44),
        key(at("s1", 1.0, offset=-0.05), [-30, 4.5, 26], [0, 2, 0], 44),
        # s2: the map view, descending over the strait
        fixed(cut("s2")[1], [0, 390, -10], [0, 0, 0], 50),
        fixed(at("s2", 1.0, offset=-0.05), [60, 330, -140], [40, 0, 10], 50),
        # s3: night again, flashes on the horizon, the patrol boat cuts across and the convoy halts
        fixed(cut("s3")[1], [-10, 16, -34], [110, 6, 40], 46),
        fixed(at("s3", word="closing"), [10, 13, -32], [120, 4, 20], 44),
        fixed(at("s3", 1.0, offset=-0.05), [30, 10, -30], [130, 3, 10], 42),
        # s4: the missile comes in, the strike close up, then the mines
        fixed(cut("s4")[1], [HIT[0] - 34, 9, -30], [HIT[0] + 6, 12, 40], 46),
        fixed(at("s4", word="missiles", offset=-0.1), [HIT[0] - 30, 7, -30], [HIT[0] + 2, 3, 2], 44),
        fixed(at("s4", word="missiles", offset=0.1), [HIT[0] - 28, 6, -28], [HIT[0] + 2, 3, 2], 44, shake=0.5),
        fixed(at("s4", word="drones."), [HIT[0] - 26, 6, -26], [HIT[0] + 2, 4, 2], 44, shake=0.08),
        fixed(at("s4", word="Mines", offset=-0.01), [HIT[0] - 26, 6, -26], [HIT[0] + 2, 4, 2], 44),
        fixed(at("s4", word="Mines"), [HIT[0] - 31, 2.4, 6], [HIT[0] - 23, 0.4, 14], 46),
        fixed(at("s4", word="Indian", offset=-0.01), [HIT[0] - 29, 2.2, 7], [HIT[0] - 21, 0.4, 15], 46),
        fixed(at("s4", word="Indian"), [HIT[0] - 50, 12, -45], [HIT[0] + 2, 4, 2], 42),
        fixed(at("s4", 1.0, offset=-0.05), [HIT[0] - 54, 13, -48], [HIT[0] + 2, 4, 2], 42),
        # s5: dawn, the burning tanker from a distance, the convoy stopped behind it
        fixed(cut("s5")[1], [HIT[0] - 130, 14, -20], [HIT[0], 6, 0], 40),
        fixed(at("s5", 1.0, offset=-0.05), [HIT[0] - 110, 12, -18], [HIT[0], 6, 0], 40),
        # s6: the stranded fleet from above
        fixed(cut("s6")[1], [-820, 180, -260], [-800, 0, 20], 50),
        fixed(at("s6", 1.0, offset=-0.05), [-780, 130, -200], [-800, 0, 20], 48),
        # s7: the stop-go convoy, following the leader
        key(cut("s7")[1], [-30, 9, -36], [0, 2, 10], 44, follow="c1"),
        key(at("s7", 1.0, offset=-0.05), [-40, 12, -30], [-10, 2, 10], 44, follow="c1"),
        # s8: on the Indian tanker's deck, then alongside
        key(cut("s8")[1], [0, 3.6, -8.0], [0, 1.2, 20], 50, follow="ind"),
        key(at("s8", word="third", offset=-0.3), [0, 3.5, -7.6], [0, 1.2, 20], 50, follow="ind"),
        key(at("s8", word="third", offset=-0.28), [26, 7, 6], [0, 1.5, 0], 42, follow="ind"),
        key(at("s8", 1.0, offset=-0.05), [28, 7, -4], [0, 1.5, 0], 42, follow="ind"),
        # s9: through the strait with the escort, coasts either side
        key(cut("s9")[1], [-28, 14, -40], [0, 2, 14], 46, follow="ind"),
        key(at("s9", word="fee.", offset=-0.5), [-14, 9, -34], [0, 2, 10], 46, follow="ind"),
        key(at("s9", 1.0, offset=-0.05), [-10, 8, -32], [0, 2, 8], 46, follow="ind"),
        # s10: dusk, the November strike and the sinking
        fixed(cut("s10")[1], [HIT2[0] - 40, 8, -34], [HIT2[0], 3, 0], 44),
        fixed(at("s10", word="attacked", offset=0.05), [HIT2[0] - 38, 7, -32], [HIT2[0], 3, 0], 44, shake=0.5),
        fixed(at("s10", word="Three", offset=-0.2), [HIT2[0] - 32, 6, -30], [HIT2[0] + 2, 2, 0], 42, shake=0.05),
        fixed(at("s10", 1.0, offset=-0.05), [HIT2[0] - 24, 5, -36], [HIT2[0] + 4, 0, 0], 42),
        # s11 to s12: the waiting fleet at dawn
        fixed(cut("s11")[1], [4960, 40, -170], [5100, 0, 20], 46),
        fixed(at("s11", 1.0, offset=-0.05), [5000, 30, -150], [5100, 0, 20], 46),
        fixed(at("s12", 1.0, offset=0.5), [5020, 26, -140], [5100, 0, 20], 46),
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
    build(HERE, [("ch01", "Strait of Hormuz", SCENES)], BASE, "The 34 km gap that sets your petrol price", seed=34)
