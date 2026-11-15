"""Builds the animated 9:16 Short "SpaceX caught a spaceship falling from orbit" (English, about 110 s) as ch01.json.

    python longform/starship15_anim/build.py

A 3D recreation of Starship Flight 15 (13-14 November 2026): the catch as a hook, liftoff from Starbase, the booster
aborting its catch and blowing up over the Gulf, orbit and the Starlink deployment, a day in orbit, the belly-first
re-entry, the flip and the catch by the tower's arms, then why it matters and what is next.
Facts: drohnen.de live timeline (launch 13 Nov 22:47 UTC from Pad 2, Booster 22 with 33 Raptor 3 engines, Ship 42 with
six, orbit about 275 km, 26 Starlink V3, about 14 orbits, catch at 21:20 UTC on 14 Nov, T+22:32:34, three engines for
the flip, booster GNC abort and flight termination over the Gulf, "Mechazilla catches Starship!", no V3 booster caught
yet); Ars Technica via ColdCaseTech (two nubs about a foot long, three Raptors lit as the ship swung vertical);
The Verge (a milestone but not a complete success); Satnews / IFLScience (124 m tall, tallest rocket ever built);
Space.com (SpaceX's goal of a fully and rapidly reusable vehicle; ship-to-ship propellant transfer); Basenor (Artemis IV
lunar landing targeted for 2028).
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


SCENES = [
    dict(S("On Saturday, a giant steel spaceship fell back from orbit, flipped upright, and was caught in mid-air by a tower's arms. No spaceship returning from orbit had ever been caught before.",
           W3, T("Starship Flight 15", y=0.13, until=99), T("14 November 2026", y=0.2, red=False, size=0.042, until=99),
           T("First ship caught from orbit", at_word="caught", y=0.27, size=0.044)), id="s1"),
    dict(S("It started on Friday at Starbase, Texas. Starship, the tallest rocket ever built at 124 metres, lit 33 engines and lifted off on its 15th test flight.",
           W3, T("Fri 13 Nov, Starbase, Texas", y=0.13, red=False, size=0.042, until=99), T("124 m: tallest rocket ever", at_word="124", y=0.2, size=0.044),
           T("33 Raptor engines", at_word="33", y=0.27, red=False, size=0.042)), id="s2"),
    dict(S("The plan was a first: catch both stages. But on the way home, the Super Heavy booster detected a guidance problem and called off its catch. It diverted over the Gulf, hovered, and blew itself up just above the water.",
           W3, T("Plan: catch BOTH stages", at_word="both", y=0.13, red=False, size=0.044), T("Booster: guidance problem", at_word="guidance", y=0.2, size=0.044),
           T("Booster lost over the Gulf", at_word="blew", y=0.27, size=0.044)), id="s3"),
    dict(S("The ship kept climbing into orbit, about 275 kilometres up, and released 26 new Starlink satellites.",
           W3, T("Orbit: ~275 km up", at_word="275", y=0.13, red=False, size=0.044), T("26 Starlink V3 satellites", at_word="26", y=0.2, size=0.044)), id="s4"),
    dict(S("Then it circled the Earth for nearly a day: about 14 orbits in 22 and a half hours, the longest Starship flight so far.",
           W3, T("~14 orbits", at_word="14", y=0.13, red=False, size=0.044), T("22.5 hours: longest flight yet", at_word="22", y=0.2, size=0.044)), id="s5"),
    dict(S("On Saturday afternoon, it came home. The ship hit the atmosphere belly first, its black heat shield glowing inside a sheath of plasma.",
           W3, T("Saturday: re-entry", y=0.13, red=False, size=0.044, until=99), T("Heat shield first", at_word="heat", y=0.2, size=0.044)), id="s6"),
    dict(S("Over Texas it fell like a skydiver. Then, close to the tower, three engines lit, and it swung upright.",
           W3, T("Belly-flop fall", at_word="skydiver.", y=0.13, red=False, size=0.044), T("Flip: 3 engines", at_word="lit,", y=0.2, size=0.044)), id="s7"),
    dict(S("It slowed, slid between the arms, and the tower caught it by two small pins, each about a foot long. Caught. A first for any spaceship coming back from orbit.",
           W3, T("Caught by 2 pins, ~30 cm each", at_word="pins,", y=0.13, red=False, size=0.042),
           T("“Mechazilla catches Starship!”", at_word="Caught.", y=0.2, size=0.044)), id="s8"),
    dict(S("Why does it matter? Rockets are usually thrown away after one flight. SpaceX wants a fully and rapidly reusable rocket, refuelled and flown again, like an airliner.",
           W3, T("Most rockets: used once", at_word="thrown", y=0.13, red=False, size=0.044), T("Goal: fully reusable", at_word="fully", y=0.2, size=0.044)), id="s9"),
    dict(S("Next comes refuelling in orbit, one Starship filling another. NASA needs that before Starship can land astronauts on the Moon, a landing now targeted for 2028.",
           W3, T("Next: refuelling in orbit", at_word="refuelling", y=0.13, size=0.044), T("Moon landing target: 2028", at_word="2028.", y=0.2, red=False, size=0.044)), id="s10"),
    dict(S("But it was only half a win. The booster was lost, and SpaceX has yet to catch one of its newest boosters. Next flight, the goal is both.",
           W3, T("Booster: still not caught", at_word="booster", y=0.13, red=False, size=0.044), T("Next goal: catch both", at_word="both.", y=0.2, size=0.044)), id="s11"),
    dict(S("Follow for more true stories.", W3), id="s12"),
]

# ---------------------------------------------------------------- the world (units: metres)
SPACE = {"sky_top": "#000003", "sky": "#02030a", "fog": [6000, 12000], "hemi": 0.25, "ambient": 0.2, "sun": 2.4,
         "sun_color": "#fff6e6", "sun_dir": [60, 30, 40], "cloud": "#ffffff", "ocean": "#1d3b52", "exposure": 1.0}
REENTRY = {"sky_top": "#00000a", "sky": "#0d2450", "fog": [6000, 12000], "hemi": 0.35, "ambient": 0.25, "sun": 2.0,
           "sun_color": "#fff2de", "sun_dir": [40, 40, 30], "cloud": "#ffffff", "ocean": "#1d3b52", "exposure": 1.0}
DAY = {"sky_top": "#3d6fa8", "sky": "#b5d0e6", "fog": [900, 6000], "hemi": 1.25, "ambient": 0.5, "sun": 1.7,
       "sun_color": "#fff3dd", "sun_dir": [30, 50, 60], "cloud": "#e4e9ee", "ocean": "#2f6b8a", "exposure": 1.0}
GOLD = {"sky_top": "#33507e", "sky": "#efb27a", "fog": [900, 6000], "hemi": 1.1, "ambient": 0.5, "sun": 2.0,
        "sun_color": "#ffc58e", "sun_dir": [-70, 16, 40], "cloud": "#f2c9a8", "ocean": "#2c587a", "exposure": 1.0}
DUSK = {"sky_top": "#1d1f3d", "sky": "#d8683a", "fog": [900, 6000], "hemi": 1.0, "ambient": 0.5, "sun": 1.6,
        "sun_color": "#ffb070", "sun_dir": [-80, 10, 30], "cloud": "#e0a080", "ocean": "#24364a", "exposure": 1.0}


def env(t, d):
    return {**d, "at": t}


def fixed(t, pos, look, fov=40, shake=0.0):
    k = {"at": t, "pos": pos, "look": look, "fov": fov}
    if shake:
        k["shake"] = shake
    return k


def key(t, offset, look, follow, fov=46):
    return {"at": t, "follow": follow, "offset": offset, "look_offset": look, "fov": fov}


def cut(scene):
    return at(scene, 0, offset=-0.012), at(scene, 0)


def only(scene_from, scene_to=None):
    scene_to = scene_to or scene_from
    return {"build": {"op": "slide", "offset": [0, 0, 0], "from": at(scene_from, 0), "to": at(scene_from, 0, offset=0.01)},
            "hide": {"at": at(scene_to, 1.0, offset=0.02), "dur": 0.01}}


def still(pos, rot):
    return [{"at": 0, "pos": pos, "rot": rot}, {"at": 1, "pos": pos, "rot": rot}]


E = [0, 0, 0]                      # the small planet for the orbit-count shot
TX, BX, OX = 20000, 30000, 40000   # Starbase, the Gulf, low Earth orbit
CZ = 29                            # tower-local z of the catch spot and the launch mount
A = 100                            # carriage height for a catch
CY = A - 9.65                      # ship centre when it rests on the arms
UP, BELLY = 90, 0                  # pitch: standing / falling belly-down

ENV_BY_SCENE = [("s1", DAY), ("s2", GOLD), ("s3", GOLD), ("s4", SPACE), ("s5", SPACE), ("s6", REENTRY), ("s7", DAY),
                ("s9", GOLD), ("s10", SPACE), ("s11", DUSK)]
envs = [env(0, DAY)]
for k, (sid, d) in enumerate(ENV_BY_SCENE[1:], 1):
    envs += [env(cut(sid)[0], ENV_BY_SCENE[k - 1][1]), env(cut(sid)[1], d)]

LIFT = at("s2", word="lifted")
STAR = [{"type": "starlink", **{"build": {"op": "slide", "offset": [0, 0, 0],
                                          "from": at("s4", word="released", offset=k * 0.42 - 0.01),
                                          "to": at("s4", word="released", offset=k * 0.42)},
                                "hide": {"at": at("s4", 1.0, offset=0.02), "dur": 0.01}},
         "track": [{"at": at("s4", word="released", offset=k * 0.42), "pos": [OX - 8 + k * 2.2, 0.5, 4.8], "rot": [0, 90, 0]},
                   {"at": at("s4", 1.0, offset=0.3), "pos": [OX - 14 + k * 3.2, -3 - k * 0.8, 15 + k * 3.5], "rot": [8 * k, 90 + 9 * k, 4 * k]}]}
        for k in range(9)]

ORBIT_KEYS = []
import math  # noqa: E402
for k in range(14):
    u = k / 13
    th = 0.3 + u * 2.6 * math.pi
    ORBIT_KEYS.append({"at": at("s5", u), "pos": [round(24 * math.cos(th), 3), round(5 * math.sin(th), 3), round(24 * math.sin(th), 3)],
                       "rot": [0, round(-math.degrees(th), 2), 0], "ease": "linear"})

WORLD = {
    "style": "night", "terrain": False, "far": 9000,
    "env": envs,
    "objects": [
        {"type": "stars", "seed": 21, "count": 2400, "size": 1.6},
        {"type": "earth", "pos": E, "r": 20, "seed": 5, "spin": 0.03, "tilt": 20},
        {"type": "earth", "pos": [OX, -640, 0], "r": 420, "seed": 9, "spin": 0.004, "tilt": 10, "halo": False},
        # Starbase: scrubland, the Gulf, the tower, the launch mount
        {"type": "box", "pos": [TX, -1, 0], "w": 6000, "h": 1, "d": 6000, "color": "#8e8a6a"},
        {"type": "box", "pos": [TX, -0.9, 1700], "w": 6000, "h": 1, "d": 2400, "color": "#2f6b8a"},
        {"type": "box", "pos": [TX - 60, 0, -70], "w": 70, "h": 34, "d": 50, "color": "#d9dbde"},
        {"type": "box", "pos": [TX + 80, 0, -90], "w": 40, "h": 18, "d": 40, "color": "#c8cbcf"},
        {"type": "tower", "pos": [TX, 0, 0], "h": 150, "arms": [
            {"at": 0, "y": A, "open": 24}, {"at": at("s1", word="caught"), "y": A, "open": 24},
            {"at": at("s1", word="caught", offset=0.9), "y": A, "open": 0},
            {"at": cut("s2")[0], "y": A, "open": 0}, {"at": cut("s2")[1], "y": 150, "open": 55},
            {"at": cut("s7")[0], "y": 150, "open": 55}, {"at": cut("s7")[1], "y": A, "open": 24},
            {"at": at("s8", word="arms,"), "y": A, "open": 24}, {"at": at("s8", word="tower"), "y": A, "open": 0}]},
        {"type": "mount", "pos": [TX, 0, CZ], "h": 20},
        {"type": "plume", "pos": [TX, 0, CZ], "at": at("s2", word="lit"), "dur": 14, "size": 1.3, "count": 170, **only("s2")},
        # s1: the hook, the catch in one go
        {"type": "starship", "kind": "ship", **only("s1"),
         "burn": [{"at": 0, "b": 0}, {"at": at("s1", word="flipped", offset=-0.4), "b": 0}, {"at": at("s1", word="flipped"), "b": 1},
                  {"at": at("s1", word="caught"), "b": 0.6}, {"at": at("s1", word="caught", offset=0.7), "b": 0}],
         "track": [{"at": at("s1", 0), "pos": [TX, 330, CZ + 90], "rot": [BELLY, 180, 0]},
                   {"at": at("s1", word="flipped"), "pos": [TX, 210, CZ + 30], "rot": [30, 180, 0]},
                   {"at": at("s1", word="upright,"), "pos": [TX, 160, CZ], "rot": [UP, 180, 0]},
                   {"at": at("s1", word="caught"), "pos": [TX, CY + 4, CZ], "rot": [UP, 180, 0]},
                   {"at": at("s1", word="caught", offset=0.8), "pos": [TX, CY, CZ], "rot": [UP, 180, 0]},
                   {"at": at("s1", 1.0), "pos": [TX, CY, CZ], "rot": [UP, 180, 0]}]},
        # s2: the stack on the mount, liftoff
        {"type": "starship", "kind": "booster", "flame": 1.7, **only("s2"),
         "burn": [{"at": 0, "b": 0}, {"at": at("s2", word="lit"), "b": 0}, {"at": at("s2", word="lit", offset=0.6), "b": 1}],
         "track": [{"at": at("s2", 0), "pos": [TX, 55.5, CZ], "rot": [UP, 0, 0]}, {"at": LIFT, "pos": [TX, 55.5, CZ], "rot": [UP, 0, 0]},
                   {"at": at("s2", word="lifted", offset=2.0), "pos": [TX, 66, CZ], "rot": [UP, 0, 0]},
                   {"at": at("s2", 1.0, offset=0.1), "pos": [TX, 150, CZ], "rot": [UP, 0, 0]}]},
        {"type": "starship", "kind": "ship", **only("s2"),
         "track": [{"at": at("s2", 0), "pos": [TX, 117, CZ], "rot": [UP, 180, 0]}, {"at": LIFT, "pos": [TX, 117, CZ], "rot": [UP, 180, 0]},
                   {"at": at("s2", word="lifted", offset=2.0), "pos": [TX, 127.5, CZ], "rot": [UP, 180, 0]},
                   {"at": at("s2", 1.0, offset=0.1), "pos": [TX, 211.5, CZ], "rot": [UP, 180, 0]}]},
        # s3: the booster comes back over the Gulf, hovers, and is destroyed
        {"type": "ocean", "y": 0, "amp": 0.6, "size": 3000, "segs": 160, **only("s3")},
        {"type": "starship", "kind": "booster", "id": "bb", **{"build": {"op": "slide", "offset": [0, 0, 0], "from": at("s3", 0), "to": at("s3", 0, offset=0.01)},
                                                                "hide": {"at": at("s3", word="blew", offset=0.12), "dur": 0.01}},
         "burn": [{"at": 0, "b": 0}, {"at": at("s3", word="Gulf,", offset=-1.2), "b": 0}, {"at": at("s3", word="Gulf,", offset=-0.6), "b": 0.8},
                  {"at": at("s3", word="blew"), "b": 0.6}],
         "track": [{"at": at("s3", 0), "pos": [BX - 150, 520, 0], "rot": [UP, 0, 0]},
                   {"at": at("s3", word="home,"), "pos": [BX - 100, 360, 0], "rot": [UP, 0, 4]},
                   {"at": at("s3", word="guidance"), "pos": [BX - 50, 220, 0], "rot": [UP, 0, -3]},
                   {"at": at("s3", word="Gulf,"), "pos": [BX, 80, 0], "rot": [UP, 0, 0]},
                   {"at": at("s3", word="hovered,"), "pos": [BX, 48, 0], "rot": [UP, 0, 2]},
                   {"at": at("s3", word="blew"), "pos": [BX, 46, 0], "rot": [UP, 0, -2]}]},
        {"type": "blast", "pos": [BX, 14, 0], "at": at("s3", word="blew"), "size": 4.0, "seed": 8},
        {"type": "blast", "pos": [BX, 50, 0], "at": at("s3", word="blew", offset=0.15), "size": 3.0, "seed": 9},
        # s4: in orbit, satellites drifting out of the payload slot
        {"type": "starship", "kind": "ship", **only("s4"), "track": still([OX, 0, 0], [BELLY, 90, 0])},
        *STAR,
        # s5: a small ship circling the small planet
        {"type": "starship", "kind": "ship", "scale": 0.05, "marker": "#ffffff", "marker_size": 110, **only("s5"), "track": ORBIT_KEYS},
        # s6: re-entry, belly first, wrapped in plasma
        {"type": "starship", "kind": "ship", "id": "rs", **only("s6"),
         "plasma": [{"at": 0, "p": 0}, {"at": at("s6", word="atmosphere", offset=-0.6), "p": 0}, {"at": at("s6", word="heat"), "p": 1}],
         "track": [{"at": at("s6", 0), "pos": [OX - 200, 60, 0], "rot": [BELLY, 90, 0]},
                   {"at": at("s6", 1.0, offset=0.2), "pos": [OX + 200, 20, 0], "rot": [BELLY - 4, 90, 0], "ease": "linear"}],
         "wobble": [{"from": at("s6", word="atmosphere"), "to": at("s6", 1.0), "roll": 2.5, "pitch": 1.5, "freq": 1.3}]},
        # s7 to s12: the ship falls, flips, is caught and stays in the arms
        {"type": "starship", "kind": "ship", "id": "cs", **only("s7", "s12"),
         "burn": [{"at": 0, "b": 0}, {"at": at("s7", word="lit,", offset=-0.3), "b": 0}, {"at": at("s7", word="lit,", offset=0.2), "b": 1},
                  {"at": at("s8", word="slowed,"), "b": 0.75}, {"at": at("s8", word="pins,"), "b": 0.5}, {"at": at("s8", word="pins,", offset=0.5), "b": 0}],
         "track": [{"at": at("s7", 0), "pos": [TX, 560, CZ + 170], "rot": [BELLY, 180, 0]},
                   {"at": at("s7", word="skydiver."), "pos": [TX, 400, CZ + 90], "rot": [BELLY + 3, 180, 0]},
                   {"at": at("s7", word="lit,"), "pos": [TX, 270, CZ + 30], "rot": [18, 180, 0]},
                   {"at": at("s7", word="upright."), "pos": [TX, 205, CZ], "rot": [UP, 180, 0]},
                   {"at": at("s8", word="slowed,"), "pos": [TX, 140, CZ], "rot": [UP, 180, 0]},
                   {"at": at("s8", word="arms,"), "pos": [TX, CY + 5, CZ], "rot": [UP, 180, 0]},
                   {"at": at("s8", word="pins,"), "pos": [TX, CY, CZ], "rot": [UP, 180, 0]},
                   {"at": at("s12", 1.0, offset=1), "pos": [TX, CY, CZ], "rot": [UP, 180, 0]}],
         "wobble": [{"from": at("s7", 0), "to": at("s7", word="lit,"), "roll": 3, "pitch": 2, "freq": 0.7}]},
        # s10: two ships tail to tail, one refuelling the other
        {"type": "starship", "kind": "ship", **only("s10"), "track": still([OX, 0, 0], [BELLY, 90, 0])},
        {"type": "starship", "kind": "ship", **only("s10"),
         "track": [{"at": at("s10", 0), "pos": [OX - 80, 0.4, 0.3], "rot": [BELLY, -90, 0]},
                   {"at": at("s10", word="NASA"), "pos": [OX - 57.4, 0, 0], "rot": [BELLY, -90, 0]},
                   {"at": at("s10", 1.0, offset=0.2), "pos": [OX - 57.4, 0, 0], "rot": [BELLY, -90, 0]}]},
    ],
    "camera": [
        # s1: from the ground near the tower, looking up as the ship drops into the arms
        fixed(0, [TX + 120, 18, CZ + 175], [TX, 210, CZ + 40], 48),
        fixed(at("s1", word="upright,"), [TX + 115, 20, CZ + 168], [TX, 140, CZ], 48),
        fixed(at("s1", 1.0, offset=-0.05), [TX + 105, 22, CZ + 155], [TX, 100, CZ], 48),
        # s2: the launch from the scrubland
        fixed(cut("s2")[1], [TX - 150, 10, CZ + 230], [TX, 75, CZ], 46),
        fixed(LIFT, [TX - 148, 10, CZ + 228], [TX, 85, CZ], 46),
        fixed(at("s2", 1.0, offset=-0.05), [TX - 145, 10, CZ + 225], [TX, 165, CZ], 46),
        # s3: over the Gulf, following the booster down
        fixed(cut("s3")[1], [BX - 60, 30, 150], [BX - 150, 500, 0], 52),
        fixed(at("s3", word="guidance"), [BX - 60, 26, 150], [BX - 50, 220, 0], 52),
        fixed(at("s3", word="Gulf,"), [BX - 60, 22, 150], [BX, 72, 0], 52),
        fixed(at("s3", word="blew"), [BX - 60, 22, 150], [BX, 48, 0], 52, shake=0.15),
        fixed(at("s3", 1.0, offset=-0.05), [BX - 66, 22, 156], [BX, 48, 0], 52),
        # s4: in orbit beside the ship
        fixed(cut("s4")[1], [OX - 36, 34, 50], [OX + 2, -26, -8], 50),
        fixed(at("s4", 1.0, offset=-0.05), [OX - 16, 30, 58], [OX + 2, -26, -2], 50),
        # s5: the planet, the ship circling it
        fixed(cut("s5")[1], [0, 26, 110], E, 40),
        fixed(at("s5", 1.0, offset=-0.05), [10, 28, 106], E, 40),
        # s6: alongside the falling ship, from slightly below to see the glowing belly
        key(cut("s6")[1], [-44, -5, 16], [0, 4, 0], "rs", 50),
        key(at("s6", 1.0, offset=-0.05), [-38, -7, 6], [0, 4, 0], "rs", 50),
        # s7: following the fall and the flip
        key(cut("s7")[1], [-120, -30, 30], [0, 0, 0], "cs", 46),
        key(at("s7", word="lit,"), [-105, -26, 10], [0, 0, 0], "cs", 46),
        key(at("s7", 1.0, offset=-0.05), [-100, -30, 0], [0, -6, 0], "cs", 46),
        # s8: a drone's view of the catch
        fixed(cut("s8")[1], [TX + 62, 96, CZ + 58], [TX, 112, CZ - 2], 52),
        fixed(at("s8", word="arms,"), [TX + 58, 94, CZ + 54], [TX, 100, CZ - 2], 52),
        fixed(at("s8", word="Caught."), [TX + 54, 93, CZ + 50], [TX, 97, CZ - 2], 52, shake=0.12),
        fixed(at("s8", 1.0, offset=-0.05), [TX + 50, 92, CZ + 46], [TX, 97, CZ - 2], 52),
        # s9: from the ground at golden hour
        fixed(cut("s9")[1], [TX - 70, 6, CZ + 140], [TX, 88, CZ], 46),
        fixed(at("s9", 1.0, offset=-0.05), [TX - 30, 6, CZ + 155], [TX, 90, CZ], 46),
        # s10: two ships in orbit
        fixed(cut("s10")[1], [OX - 44, 38, 58], [OX - 28, -26, -10], 52),
        fixed(at("s10", 1.0, offset=-0.05), [OX - 34, 34, 52], [OX - 28, -26, -10], 52),
        # s11 to s12: the tower at dusk, pulling away
        fixed(cut("s11")[1], [TX + 150, 30, CZ + 230], [TX, 85, CZ], 46),
        fixed(at("s12", 1.0, offset=0.5), [TX + 185, 42, CZ + 290], [TX, 85, CZ], 46),
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
    build(HERE, [("ch01", "Starship Flight 15", SCENES)], BASE, "SpaceX caught a spaceship falling from orbit", seed=15)
