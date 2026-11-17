"""Builds the animated 9:16 Short "This jet fell 27,000 feet in one minute" (English, about 115 s) as ch01.json.

    python longform/learjet_anim/build.py

A 3D recreation of what is known so far about the Learjet 60 (N722BD) crash near Greenacres, Florida, on Sunday
1 November 2026: the crew's ice report as a hook, the departure from Austin, light clear ice and moderate turbulence at
35,000 ft, the approved climb to 37,000 ft, the mayday and overspeed, the 27,000 ft loss in a minute, signs of an
in-flight break-up and the left elevator found in three pieces 1.3 to 3.8 miles away, the impact near Greenacres, the
debris field, the recovered cockpit voice recorder and the open questions. No cause is stated: the NTSB has not
established one.
Facts: NTSB investigation page ERA27MA026 (updates 5, 8 and 9 Nov: debris on roofs, cleared areas include a high
school, CVR recovered at the initial impact site and sent to the Vehicle Recorders Laboratory in Washington); NTSB
briefing via CBS12/KMPH (departed Austin-Bergstrom for North Eleuthera, 2 crew and 7 passengers, about 12:47 p.m. at
35,000 ft light clear ice and moderate turbulence, altitude deviations of about 700 ft, minus 47 C, handling the ice,
asked to climb to 37,000 ft and approved, less than 30 seconds later descending and mayday, "in an overspeed condition
descending", crater in the roadway, one man in a vehicle with a leg injury, debris field about half a mile by
four-tenths of a mile including ball fields, businesses and homes); CBS News ("we're managing the ice", "Mayday,
Mayday, we're descending 10,000 feet per minute"); Military & Aerospace Electronics (about 20,000 ft/min, roughly
27,000 ft in one minute, most of the left elevator in three pieces 1.3 to 3.8 miles from the main site, not determined
whether the separation contributed or resulted, no probable cause, review of aircraft, crew actions and weather);
AIN (Chapman: some evidence of break-up before impact); AeroCorner (preliminary report usually about a month after,
around the start of December); AeroXplorer (final report can take a year or longer).
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


def T(text, at_word=None, y=0.13, until=None, red=True, size=0.044, at_time=None):
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
    dict(S("At 35,000 feet over Florida, a pilot radioed: we're managing the ice. Moments later, the jet was falling at about 20,000 feet a minute.",
           W3, T("Learjet 60, 1 Nov 2026", size=0.046, until=99), T("“We're managing the ice”", at_word="managing", y=0.2, red=False),
           T("About -20,000 ft/min", at_word="falling", y=0.27)), id="s1"),
    dict(S("On Sunday, the first of November, a Learjet 60 left Austin, Texas, for the Bahamas, with two pilots and seven passengers.",
           W3, T("Austin to North Eleuthera, Bahamas", at_word="Austin,", red=False), T("2 pilots, 7 passengers", at_word="two", y=0.2, red=False)), id="s2"),
    dict(S("Over South Florida, at 35,000 feet, the crew reported light clear ice and moderate turbulence, with the altitude swinging by about 700 feet.",
           W3, T("35,000 ft", at_word="35,000", red=False), T("Light clear ice, moderate turbulence", at_word="light", y=0.2),
           T("±700 ft", at_word="700", y=0.27, red=False)), id="s3"),
    dict(S("It was minus 47 degrees outside. The pilot said they were handling the ice, then asked to climb to 37,000 feet. Controllers approved.",
           W3, T("-47°C outside", at_word="minus", red=False), T("Climb to 37,000 ft: approved", at_word="climb", y=0.2, red=False)), id="s4"),
    dict(S("Less than 30 seconds later, the jet was descending. The pilot called: Mayday, Mayday, we're descending 10,000 feet per minute. Then a final transmission: overspeed, descending.",
           W3, T("< 30 seconds later", red=False), T("MAYDAY", at_word="Mayday,", y=0.2, size=0.05), T("Overspeed", at_word="overspeed,", y=0.27)), id="s5"),
    dict(S("Flight tracking data showed it losing about 27,000 feet in a single minute.",
           W3, T("About 27,000 ft lost in 1 minute", at_word="27,000")), id="s6"),
    dict(S("The NTSB says there are signs it was breaking up before impact. Most of the left elevator, part of the tail, was found in three pieces, up to 3.8 miles away. Whether that caused the dive, or came from it, is not yet known.",
           W3, T("Signs of break-up before impact", at_word="breaking", red=False), T("Left elevator: 3 pieces", at_word="three", y=0.2),
           T("1.3 to 3.8 miles from the crash", at_word="3.8", y=0.27, red=False)), id="s7"),
    dict(S("Just before 1 p.m., it hit a road near Greenacres, in Palm Beach County. All nine people on board were killed. A man in a car nearby was injured.",
           W3, T("Greenacres, Florida, ~12:50 p.m.", at_word="Greenacres,", red=False), T("All 9 on board killed", at_word="nine", y=0.2)), id="s8"),
    dict(S("It left a crater in the road. Debris landed on rooftops, ball fields and a high school, across an area about half a mile long.",
           W3, T("Debris field: about half a mile", at_word="half", red=False)), id="s9"),
    dict(S("On November 9th, investigators recovered the cockpit voice recorder. It is now being examined in a lab in Washington.",
           W3, T("Cockpit voice recorder found, 9 Nov", at_word="cockpit", red=False), T("NTSB lab, Washington", at_word="lab", y=0.2, red=False)), id="s10"),
    dict(S("So what caused it? The NTSB has not said. It is examining the ice, the weather, the aircraft and the crew's actions. A preliminary report is expected around early December. A final cause could take a year or more.",
           W3, T("Cause: not yet known", at_word="caused"), T("Preliminary report: ~early Dec", at_word="preliminary", y=0.2, red=False),
           T("Final report: a year or more", at_word="final", y=0.27, red=False)), id="s11"),
    dict(S("Follow for the findings when they come out.", W3), id="s12"),
]

# ---------------------------------------------------------------- the world (the airliner kit's units: the jet is about 6.2 long)
STORM = {"sky_top": "#3a4250", "sky": "#6c7684", "fog": [22, 140], "hemi": 1.0, "ambient": 0.5, "sun": 0.8,
         "sun_color": "#dfe6ee", "sun_dir": [20, 60, 30], "cloud": "#7d8794", "ocean": "#3a4a58", "exposure": 1.05}
FALL = {**STORM, "fog": [40, 330], "sky": "#5e6876"}
SUNNY = {"sky_top": "#2f63a8", "sky": "#a9c8e6", "fog": [120, 600], "hemi": 1.2, "ambient": 0.5, "sun": 1.8,
         "sun_color": "#fff4e0", "sun_dir": [40, 50, 20], "cloud": "#f4f6f8", "ocean": "#2f6b8a", "exposure": 1.0}
TOWN = {"sky_top": "#56606c", "sky": "#9aa4ae", "fog": [90, 560], "hemi": 1.15, "ambient": 0.55, "sun": 0.9,
        "sun_color": "#eef0f2", "sun_dir": [30, 60, 20], "cloud": "#8e98a2", "ocean": "#3a4a58", "exposure": 1.0}
LAB = {"sky_top": "#05070c", "sky": "#141c2a", "fog": [20, 120], "hemi": 0.7, "ambient": 0.35, "sun": 1.6,
       "sun_color": "#ffffff", "sun_dir": [30, 60, 40], "cloud": "#202838", "ocean": "#101820", "exposure": 1.05}

ORDER = [f"s{k}" for k in range(1, 13)]
ENV_BY_SCENE = {"s1": STORM, "s2": SUNNY, "s3": STORM, "s4": STORM, "s5": STORM, "s6": FALL, "s7": FALL,
                "s8": TOWN, "s9": TOWN, "s10": LAB, "s11": STORM, "s12": STORM}
HOOK, DEP, TX, LX, RX = -20000, -10000, 20000, 30000, 40000   # the hook, the departure, the town, the lab, the replay
V = 15                                                          # cruise speed in units per second


def env(t, d):
    return {**d, "at": t}


def cut(scene):
    return at(scene, 0, offset=-0.012), at(scene, 0)


def only(scene_from, scene_to=None):
    scene_to = scene_to or scene_from
    return {"build": {"op": "slide", "offset": [0, 0, 0], "from": at(scene_from, 0), "to": at(scene_from, 0, offset=0.01)},
            "hide": {"at": at(scene_to, 1.0, offset=0.02), "dur": 0.01}}


envs = [env(0, STORM)]
for k, sid in enumerate(ORDER[1:], 1):
    envs += [env(cut(sid)[0], ENV_BY_SCENE[ORDER[k - 1]]), env(cut(sid)[1], ENV_BY_SCENE[sid])]


def fixed(t, pos, look, fov=44, shake=0.0):
    k = {"at": t, "pos": pos, "look": look, "fov": fov}
    if shake:
        k["shake"] = shake
    return k


def follow(t, target, offset, look, fov=44, shake=0.0):
    k = {"at": t, "follow": target, "offset": offset, "look_offset": look, "fov": fov}
    if shake:
        k["shake"] = shake
    return k


END = lambda s: at(s, 1.0, offset=-0.05)  # noqa: E731
SHOTS = {
    "s1": [follow(cut("s1")[1], "h1", [5.5, 1.2, 7], [0, 0, -1], 40, 0.05), follow(at("s1", word="Moments"), "h1", [6, 1.6, 6], [0, -0.5, -1], 40, 0.1),
           follow(END("s1"), "h1", [7, 3, 4], [0, -1, 0], 42, 0.2)],
    "s2": [follow(cut("s2")[1], "dj", [-9, 2.5, -12], [0, 0, 2], 42), follow(END("s2"), "dj", [-11, 3, 4], [0, 0, 0], 42)],
    "s3": [follow(cut("s3")[1], "lj", [-7, 1.5, 5], [0, 0, 0], 42, 0.08), follow(at("s3", word="turbulence,"), "lj", [-6, 1.2, 7], [0, 0, 0], 42, 0.14),
           follow(END("s3"), "lj", [-6.5, 1.4, 6], [0, 0, 0], 42, 0.12)],
    "s4": [follow(cut("s4")[1], "lj", [-0.7, 1.0, 1.9], [-1.5, -0.2, 0.0], 50, 0.05), follow(at("s4", word="climb"), "lj", [-0.9, 1.1, 1.7], [-1.5, -0.2, 0.0], 50, 0.05),
           follow(at("s4", word="climb", offset=0.9), "lj", [-10, 1.5, 3], [0, 0, 0], 42, 0.08), follow(END("s4"), "lj", [-11, 2, 1], [0, 0.5, 0], 42, 0.08)],
    "s5": [follow(cut("s5")[1], "lj", [-10, 3, 6], [0, 0, 0], 44, 0.12), follow(at("s5", word="Mayday,"), "lj", [-11, 4, 5], [0, -0.5, 0], 44, 0.2),
           follow(END("s5"), "lj", [-12, 6, 3], [0, -1, 0], 46, 0.25)],
    "s6": [follow(cut("s6")[1], "lj", [-28, -32, 22], [0, -4, 4], 48, 0.1), follow(END("s6"), "lj", [-30, -30, 18], [0, -4, 4], 48, 0.1)],
    "s7": [follow(cut("s7")[1], "lj", [-2.4, 7.2, -1.2], [-0.5, 3.2, -0.3], 46, 0.08), follow(at("s7", word="elevator,", offset=0.6), "lj", [-2.8, 8.4, -1.6], [-0.6, 3.6, -0.3], 48, 0.12),
           follow(at("s7", word="Whether"), "lj", [-12, 5, -6], [0, 0, 0], 46, 0.18), follow(END("s7"), "lj", [-14, 7, -2], [0, -1, 0], 46, 0.2)],
    "s8": [fixed(cut("s8")[1], [TX + 150, 9, 250], [TX, 32, 0], 42), fixed(at("s8", word="hit"), [TX + 148, 9, 248], [TX, 22, 0], 42, 0.12),
           fixed(END("s8"), [TX + 140, 10, 240], [TX, 24, 0], 42)],
    "s9": [fixed(cut("s9")[1], [TX + 95, 72, 125], [TX, 0, 0], 46), fixed(END("s9"), [TX + 55, 80, 145], [TX, 0, 0], 46)],
    "s10": [fixed(cut("s10")[1], [LX + 3.6, 2.6, 4.4], [LX, 1.1, 0], 40), fixed(END("s10"), [LX - 2.6, 2.3, 4.8], [LX, 1.1, 0], 40)],
    "s11": [follow(cut("s11")[1], "lj3", [-8, 2, 6], [0, 0, 0], 42, 0.06), follow(END("s11"), "lj3", [-6, 1.5, 10], [0, 0, 0], 42, 0.06)],
    "s12": [follow(cut("s12")[1], "lj3", [-10, 3, 2], [0, 0, 0], 42), follow(at("s12", 1.0, offset=0.6), "lj3", [-16, 4, -6], [0, 0, 0], 42)],
}
CAMERA = []
for k, sid in enumerate(ORDER):
    CAMERA += SHOTS[sid]
    if k + 1 < len(ORDER):
        CAMERA.append({**SHOTS[sid][-1], "at": cut(ORDER[k + 1])[0]})
CAMERA[0] = {**CAMERA[0], "at": 0}

# the main jet, s3 to s7: cruise in the cloud, the climb, the dive (positions assume about 2.5 words a second)
LJ_TRACK = [
    {"at": at("s3", 0), "pos": [0, 100, 0], "rot": [2, 90, 0]},
    {"at": at("s4", 0), "pos": [V * 9, 100, 0], "rot": [2, 90, 0]},
    {"at": at("s4", word="climb"), "pos": [V * 15, 100, 0], "rot": [2, 90, 0]},
    {"at": at("s5", 0), "pos": [V * 18.5, 103, 0], "rot": [7, 90, 0]},
    {"at": at("s5", word="descending."), "pos": [V * 21, 100, 0], "rot": [-12, 90, 8]},
    {"at": at("s5", word="Mayday,"), "pos": [V * 23.5, 90, 0], "rot": [-25, 90, 18]},
    {"at": at("s5", 1.0), "pos": [V * 29, 50, 0], "rot": [-45, 90, 30]},
    {"at": at("s6", 1.0), "pos": [V * 31.5, -20, 0], "rot": [-55, 90, 34]},
    {"at": at("s7", 1.0, offset=1.0), "pos": [V * 40, -270, 0], "rot": [-60, 90, 40]},
]
WORLD = {
    "style": "night", "terrain": False, "far": 1500,
    "env": envs,
    "lightning": [{"from": at("s1", 0), "to": at("s1", 1.0), "rate": 0.5, "seed": 3, "strength": 0.6},
                  {"from": at("s3", 0), "to": at("s7", 0.3), "rate": 0.5, "seed": 5, "strength": 0.6},
                  {"from": at("s11", 0), "to": at("s12", 1.0), "rate": 0.4, "seed": 9, "strength": 0.5}],
    "objects": [
        # cloud layers: the storm around the jet, the deck below the departure, the overcast over the town
        {"type": "clouds", "seed": 4, "layers": [
            {"y": [70, 140], "count": 150, "size": [8, 16], "from": at("s1", 0), "to": at("s1", 1.0, offset=0.05), "fade": 0.01},
            {"y": [70, 140], "count": 150, "size": [8, 16], "from": at("s3", 0), "to": at("s7", 1.0, offset=0.05), "fade": 0.01},
            {"y": [70, 140], "count": 150, "size": [8, 16], "from": at("s11", 0), "to": at("s12", 1.0, offset=1), "fade": 0.01}]},
        {"type": "clouds", "seed": 8, "layers": [{"y": [10, 32], "count": 110, "size": [12, 24], "from": at("s2", 0), "to": at("s2", 1.0, offset=0.05), "fade": 0.01}]},
        {"type": "clouds", "seed": 12, "box": 420, "layers": [{"y": [70, 110], "count": 90, "size": [14, 26], "from": at("s8", 0), "to": at("s9", 1.0, offset=0.05), "fade": 0.01}]},
        # rain streaks past the jet
        {"type": "streaks", "follow": "h1", "from": at("s1", 0), "to": at("s1", 1.0), "count": 300, "box": [10, 7, 10], "dir": [-1, -0.25, 0], "speed": 45, "len": 1.0, "opacity": 0.4},
        {"type": "streaks", "follow": "lj", "from": at("s3", 0), "to": at("s4", 1.0), "count": 300, "box": [10, 7, 10], "dir": [-1, -0.25, 0], "speed": 45, "len": 1.0, "opacity": 0.4},
        {"type": "streaks", "follow": "lj", "from": at("s5", 0.3), "to": at("s7", 1.0), "count": 340, "box": [12, 9, 12], "dir": [-0.55, 1, 0], "speed": 60, "len": 1.4, "opacity": 0.45},
        {"type": "streaks", "follow": "lj3", "from": at("s11", 0), "to": at("s12", 1.0), "count": 260, "box": [10, 7, 10], "dir": [-1, -0.25, 0], "speed": 40, "len": 1.0, "opacity": 0.35},
        # the ground under the dive
        {"type": "box", "pos": [V * 30, -400, 0], "w": 5000, "h": 1, "d": 5000, "color": "#4f5a48"},
        # s1: the hook
        {"type": "bizjet", "id": "h1", **only("s1"), "ice": {"from": at("s1", 0), "to": at("s1", word="ice.")},
         "track": [{"at": at("s1", 0), "pos": [HOOK, 100, 0], "rot": [2, 90, 0]},
                   {"at": at("s1", word="Moments"), "pos": [HOOK + V * 5.5, 100, 0], "rot": [-4, 90, 5]},
                   {"at": at("s1", 1.0, offset=0.2), "pos": [HOOK + V * 9.5, 80, 0], "rot": [-38, 90, 24]}],
         "wobble": [{"from": at("s1", 0), "to": at("s1", 1.0), "roll": 3, "pitch": 1.5, "freq": 0.6}]},
        # s2: the departure over the cloud deck
        {"type": "bizjet", "id": "dj", **only("s2"),
         "track": [{"at": at("s2", 0), "pos": [DEP, 58, 0], "rot": [8, 90, 0]}, {"at": at("s2", 1.0, offset=0.2), "pos": [DEP + V * 9, 76, 0], "rot": [8, 90, 0]}]},
        # s3 to s7: the main jet
        {"type": "bizjet", "id": "lj", **only("s3", "s7"), "ice": {"from": at("s3", word="ice"), "to": at("s4", word="handling")},
         "elevator": {"at": at("s7", word="elevator,")}, "track": LJ_TRACK,
         "wobble": [{"from": at("s3", 0), "to": at("s5", 0.4), "roll": 4, "pitch": 2, "freq": 0.55},
                    {"from": at("s5", 0.4), "to": at("s7", 1.0), "roll": 6, "pitch": 3, "freq": 0.8}]},
        # s8: the town, Military Trail, the dive and the impact seen from a distance
        {"type": "box", "pos": [TX, -1, 0], "w": 2400, "h": 1, "d": 2400, "color": "#6f7d5a"},
        {"type": "box", "pos": [TX, -0.95, 0], "w": 8, "h": 1.0, "d": 2000, "color": "#3b3e42"},
        *[{"type": "box", "pos": [TX, -0.96, z], "w": 2000, "h": 1.0, "d": 4, "color": "#44474b"} for z in (-240, -150, -60, 60, 150, 240)],
        {"type": "box", "pos": [TX + 45, -0.9, 95], "w": 46, "h": 1.0, "d": 46, "color": "#5f8f4a"},
        {"type": "box", "pos": [TX + 45, -0.85, 95], "w": 14, "h": 1.0, "d": 14, "color": "#b58a5a", "rot": 45},
        {"type": "box", "pos": [TX - 60, 0, -105], "w": 52, "h": 7, "d": 22, "color": "#d8cdb8"},
        {"type": "box", "pos": [TX - 78, 0, -80], "w": 18, "h": 7, "d": 34, "color": "#cfc4ae"},
        {"type": "town", "area": [TX + 10, -400, TX + 320, 400], "count": 260, "scale": 2.4, "seed": 3,
         "colors": ["#efe6d6", "#e8d9c4", "#f2efe8", "#d9e2e6", "#e9d6c8"]},
        {"type": "town", "area": [TX - 320, -400, TX - 10, 400], "count": 260, "scale": 2.4, "seed": 7,
         "colors": ["#efe6d6", "#e8d9c4", "#f2efe8", "#d9e2e6", "#e9d6c8"]},
        {"type": "trees", "area": [TX - 320, -400, TX + 320, 400], "count": 220, "scale": 1.7, "seed": 5},
        {"type": "bizjet", "id": "lj2", "build": {"op": "slide", "offset": [0, 0, 0], "from": at("s8", 0), "to": at("s8", 0, offset=0.01)},
         "hide": {"at": at("s8", word="hit", offset=0.02), "dur": 0.01},
         "track": [{"at": at("s8", 0), "pos": [TX - 75, 140, -20], "rot": [-62, 90, 38]}, {"at": at("s8", word="hit"), "pos": [TX, 1, 0], "rot": [-66, 90, 44]}]},
        {"type": "blast", "pos": [TX, 0.5, 0], "at": at("s8", word="hit"), "size": 2.4, "burn": 16, "seed": 4},
        # s9: the crater and the debris
        {"type": "crater", "pos": [TX, 0, 0], "r": 3, "water": True, **only("s9")},
        {"type": "wreckage", "pos": [TX, 0, 0], "spread": 70, "count": 90, "size": 0.7, "seed": 23, **only("s9")},
        # s10: the cockpit voice recorder on a lab bench
        {"type": "box", "pos": [LX, 0, 0], "w": 3.2, "h": 0.9, "d": 2.0, "color": "#3a3f47"},
        {"type": "box", "pos": [LX, -1, 0], "w": 60, "h": 1, "d": 60, "color": "#1c222b"},
        {"type": "recorder", "pos": [LX, 0.9, 0], "scale": 2.6, "rot": 30},
        # s11 to s12: the jet in the cloud again, the question still open
        {"type": "bizjet", "id": "lj3", **only("s11", "s12"), "ice": {"from": at("s11", 0), "to": at("s11", 0.5)},
         "track": [{"at": at("s11", 0), "pos": [RX, 100, 0], "rot": [2, 90, 0]}, {"at": at("s12", 1.0, offset=1), "pos": [RX + V * 22, 100, 0], "rot": [2, 90, 0]}],
         "wobble": [{"from": at("s11", 0), "to": at("s12", 1.0), "roll": 3, "pitch": 1.5, "freq": 0.5}]},
    ],
    "camera": CAMERA,
}

BASE = {
    "language": "en", "voice": "bm_george", "speed": 1.08, "aspect": "9:16", "made_for_kids": False,
    "footage": "off", "transition": "none",
    "music": {"mood": "mystery", "volume": 0.1},
    "captions": {"style": "karaoke", "y": 0.62, "size": 0.08, "max_words": 2, "highlight": "#ffd54a",
                 "uppercase": False},
    "overlay": {"handle": "@hypercurious96", "progress_bar": False},
    "world3d": WORLD,
}

if __name__ == "__main__":
    build(HERE, [("ch01", "Learjet 60, Greenacres", SCENES)], BASE, "This jet fell 27,000 feet in one minute. What we know.", seed=17)
