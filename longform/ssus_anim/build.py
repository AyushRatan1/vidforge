"""Builds the animated 9:16 Short "America sank its fastest ship ever, on purpose" (English, about 115 s) as ch01.json.

    python longform/ssus_anim/build.py

A 3D recreation of the deliberate sinking of the SS United States off Destin, Florida (Wednesday 11 November 2026):
the sinking as a hook, the 1952 record crossing, the famous passengers, retirement in 1969 and the decades at a
Philadelphia dock, the purchase for a reef, the preparation (no explosives: funnels off, portholes out, holes cut),
the long flooding into the night, the lean and the plunge, then the wreck resting upright on the seabed.
Facts: AP via WECT/WFSB/ADN (cloudy afternoon start, predicted as little as an hour, leaned to one side and quickly
submerged, 128 fuel and lubricant tanks filled so it rests evenly, no explosives under federal rules, 10x10 ft holes,
400+ portholes removed, 180 ft / 55 m deep, top deck about 60 ft / 18 m down, shallow enough for inexperienced
divers, about 25 miles SW of Destin, $13.5 million, 65 ft funnels removed for a museum, tuna, marlin and swordfish
habitat, 990 ft / 302 m, 1952 maiden voyage at almost 66 km/h through a gale, 800+ crossings, Truman, Eisenhower,
Kennedy, Grace Kelly, Elizabeth Taylor, decommissioned 1969, Philadelphia dock from 1996; Coleen O'Malley's quote);
ABC7 (Gibbs: "you can't burn her, you can't catch her and you can't sink her", via Bill Magee); Al Jazeera (longer
than Titanic, 3 days 10 hours 40 minutes, record never broken by another passenger liner, bought for $1 million in
2024); PhillyVoice (nearly 30 years docked in South Philadelphia, world's largest artificial reef); gCaptain (fastest
ocean liner ever built); WHOI (resting upright).
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


def T(text, at_word=None, y=0.15, until=None, red=True, size=0.044, at_time=None):
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
    dict(S("Her designer used to say: you can't burn her, you can't catch her, and you can't sink her. Last Wednesday night, America sank her on purpose. And she did not go quietly.",
           W3, T("SS United States", y=0.13, size=0.05, until=99), T("Sunk on purpose, 11 Nov 2026", at_word="purpose.", y=0.2, red=False, size=0.042)), id="s1"),
    dict(S("This is the SS United States. At 302 metres, she is longer than the Titanic. In 1952, on her very first voyage, she crossed the Atlantic in three days and ten hours.",
           W3, T("302 m: longer than Titanic", at_word="302", y=0.13), T("1952: Atlantic in 3 days 10 h", at_word="1952,", y=0.2, red=False)), id="s2"),
    dict(S("She averaged almost 66 kilometres an hour, through a gale. No passenger liner has ever crossed faster.",
           W3, T("~66 km/h average", at_word="66", y=0.13, red=False), T("Record never beaten", at_word="No", y=0.2)), id="s3"),
    dict(S("Presidents Truman, Eisenhower and Kennedy sailed on her, and so did Grace Kelly and Elizabeth Taylor. She made more than 800 crossings.",
           W3, T("Truman, Eisenhower, JFK", at_word="Presidents", y=0.13, red=False), T("Grace Kelly, Elizabeth Taylor", at_word="Grace", y=0.2, red=False),
           T("800+ crossings", at_word="800", y=0.27)), id="s4"),
    dict(S("Then jets took over. She was retired in 1969, and for almost 30 years she sat rusting at a dock in Philadelphia.",
           W3, T("1969: retired", at_word="1969,", y=0.13), T("~30 years at a Philadelphia dock", at_word="30", y=0.2, red=False)), id="s5"),
    dict(S("In 2024, a Florida county bought her for one million dollars. The plan: sink her, and turn her into the world's largest artificial reef.",
           W3, T("Bought for $1 million", at_word="million", y=0.13, red=False), T("Plan: world's largest reef", at_word="largest", y=0.2)), id="s6"),
    dict(S("Explosives were not allowed. So crews took off her famous funnels, pulled out over 400 portholes, and cut big holes in her decks, to let the sea in.",
           W3, T("No explosives allowed", at_word="Explosives", y=0.13), T("400+ portholes removed", at_word="400", y=0.2, red=False),
           T("10 x 10 ft holes in the decks", at_word="holes", y=0.27, red=False)), id="s7"),
    dict(S("On Wednesday afternoon, about 25 miles off Destin, Florida, they opened the valves. Organisers thought she could sink in as little as an hour.",
           W3, T("11 Nov: 25 miles off Destin", at_word="Wednesday", y=0.13, red=False), T("Expected: about an hour", at_word="little", y=0.2)), id="s8"),
    dict(S("It took hours. Crews had to fill 128 tanks with water, so she would settle evenly. Night fell, and she was still afloat. One organiser said: she will not lay down without a fight.",
           W3, T("128 tanks to flood", at_word="128", y=0.13, red=False), T("Still afloat after dark", at_word="Night", y=0.2)), id="s9"),
    dict(S("Then, late that night, she leaned to one side, and slipped beneath the waves.",
           W3, T("Gone", at_word="slipped", y=0.13, size=0.05)), id="s10"),
    dict(S("Today she rests upright on the seabed, 55 metres down. Her top deck is just 18 metres below the surface, shallow enough for new divers.",
           W3, T("Upright, 55 m down", at_word="55", y=0.13, red=False), T("Top deck: 18 m below the surface", at_word="18", y=0.2, red=False)), id="s11"),
    dict(S("The plan is for tuna, marlin and swordfish to move in. The fastest liner ever built is now the world's largest artificial reef. Would you dive it?",
           W3, T("The plan: tuna, marlin, swordfish", at_word="tuna,", y=0.13, red=False), T("World's largest artificial reef", at_word="largest", y=0.2)), id="s12"),
    dict(S("Follow for more true stories.", W3), id="s13"),
]

# ---------------------------------------------------------------- the world (units: metres)
NIGHT = {"sky_top": "#02050d", "sky": "#1e2d48", "fog": [350, 1450], "hemi": 0.95, "ambient": 0.45, "sun": 1.3,
         "sun_color": "#a9bcdc", "sun_dir": [60, 40, 50], "cloud": "#2a3348", "ocean": "#0d2032", "exposure": 1.3}
MORNING = {"sky_top": "#4a78b0", "sky": "#f0c89a", "fog": [500, 1450], "hemi": 1.15, "ambient": 0.5, "sun": 2.0,
           "sun_color": "#ffd9a8", "sun_dir": [-60, 22, 50], "cloud": "#f2d2b2", "ocean": "#2b5d7d", "exposure": 1.0}
GALE = {"sky_top": "#3c4a5a", "sky": "#8d9aa6", "fog": [300, 1300], "hemi": 1.0, "ambient": 0.55, "sun": 1.1,
        "sun_color": "#e8eef2", "sun_dir": [30, 50, 20], "cloud": "#9aa6b0", "ocean": "#33505f", "exposure": 1.0}
LINER_NIGHT = {"sky_top": "#010309", "sky": "#121e36", "fog": [300, 1400], "hemi": 0.5, "ambient": 0.3, "sun": 0.55,
               "sun_color": "#9fb4d8", "sun_dir": [40, 40, -30], "cloud": "#202a40", "ocean": "#0a1726", "exposure": 1.15}
DUSK = {"sky_top": "#2a2d52", "sky": "#e48a5a", "fog": [400, 1450], "hemi": 1.0, "ambient": 0.5, "sun": 1.5,
        "sun_color": "#ffb27a", "sun_dir": [-70, 12, 30], "cloud": "#e0a080", "ocean": "#2a3a4c", "exposure": 1.0}
DAY = {"sky_top": "#3d6fa8", "sky": "#b5d0e6", "fog": [500, 1450], "hemi": 1.25, "ambient": 0.5, "sun": 1.7,
       "sun_color": "#fff3dd", "sun_dir": [30, 50, 60], "cloud": "#e4e9ee", "ocean": "#2f6b8a", "exposure": 1.0}
OVERCAST = {"sky_top": "#5d6b78", "sky": "#b9c2c9", "fog": [400, 1450], "hemi": 1.15, "ambient": 0.6, "sun": 1.0,
            "sun_color": "#f2f2ee", "sun_dir": [20, 60, 30], "cloud": "#b0b8c0", "ocean": "#3c5a6a", "exposure": 1.0}
EVENING = {"sky_top": "#262a44", "sky": "#9a7e86", "fog": [400, 1450], "hemi": 0.9, "ambient": 0.45, "sun": 0.9,
           "sun_color": "#f0b48a", "sun_dir": [-70, 8, 20], "cloud": "#8a7c86", "ocean": "#22323f", "exposure": 1.05}
UNDER = {"sky_top": "#01101c", "sky": "#0b4560", "fog": [8, 170], "hemi": 0.95, "ambient": 0.45, "sun": 0.7,
         "sun_color": "#6fb0d0", "sun_dir": [0, 60, 10], "cloud": "#04121f", "ocean": "#04121f", "exposure": 1.1}

ORDER = ["s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8", "s9", "s10", "s11", "s12", "s13"]
SEA, PHL = 6000, -6000          # the Atlantic in the 1950s, the Philadelphia dock; the reef site is at the origin
REST = -45                      # liner centre when the keel sits on the seabed at -55


def env(t, d):
    return {**d, "at": t}


def cut(scene):
    return at(scene, 0, offset=-0.012), at(scene, 0)


def only(scene_from, scene_to=None):
    scene_to = scene_to or scene_from
    return {"build": {"op": "slide", "offset": [0, 0, 0], "from": at(scene_from, 0), "to": at(scene_from, 0, offset=0.01)},
            "hide": {"at": at(scene_to, 1.0, offset=0.02), "dur": 0.01}}


ENV_BY_SCENE = {"s1": NIGHT, "s2": MORNING, "s3": GALE, "s4": LINER_NIGHT, "s5": DUSK, "s6": DAY, "s7": OVERCAST,
                "s8": OVERCAST, "s9": EVENING, "s10": NIGHT, "s11": UNDER, "s12": UNDER, "s13": UNDER}
envs = [env(0, NIGHT)]
for k, sid in enumerate(ORDER[1:], 1):
    envs += [env(cut(sid)[0], ENV_BY_SCENE[ORDER[k - 1]] if ORDER[k - 1] != "s9" else NIGHT), env(cut(sid)[1], ENV_BY_SCENE[sid])]
    if sid == "s9":   # night falls during s9
        envs += [env(at("s9", word="Night", offset=-1.5), EVENING), env(at("s9", word="Night", offset=1.0), NIGHT)]


# ---------------------------------------------------------------- cameras: one list per scene, held until the cut
def fixed(t, pos, look, fov=46, shake=0.0):
    k = {"at": t, "pos": pos, "look": look, "fov": fov}
    if shake:
        k["shake"] = shake
    return k


def follow(t, offset, look, fov=46, target="us"):
    return {"at": t, "follow": target, "offset": offset, "look_offset": look, "fov": fov}


END = lambda s: at(s, 1.0, offset=-0.05)  # noqa: E731
SHOTS = {
    # s1: from a spectator boat at night, the stripped liner leaning and going under
    "s1": [fixed(cut("s1")[1], [118, 16, 268], [0, 2, 60], 48), fixed(END("s1"), [108, 13, 252], [0, -2, 55], 48)],
    # s2: a drone rising from behind the liner at sea in the morning
    "s2": [follow(cut("s2")[1], [120, 22, -250], [0, 12, 40], 46), follow(at("s2", word="1952,"), [180, 70, -60], [0, 10, 20], 46),
           follow(END("s2"), [230, 120, 160], [0, 6, 0], 46)],
    # s3: ahead of the bow in a gale, the bow knifing toward the lens
    "s3": [follow(cut("s3")[1], [70, 14, 270], [0, 12, 120], 46), follow(END("s3"), [55, 10, 225], [0, 12, 110], 46)],
    # s4: a slow pass along the lit windows at night
    "s4": [follow(cut("s4")[1], [95, 20, 70], [0, 16, 20], 48), follow(END("s4"), [95, 26, -50], [0, 18, -10], 48)],
    # s5: at the Philadelphia dock, a jet passing overhead, the paint fading
    "s5": [fixed(cut("s5")[1], [PHL - 95, 9, 330], [PHL, 45, 0], 48), fixed(at("s5", word="1969,"), [PHL - 110, 10, 320], [PHL, 24, 0], 48),
           fixed(END("s5"), [PHL - 130, 12, 300], [PHL, 18, 0], 48)],
    # s6: a drone circling the rusting liner
    "s6": [fixed(cut("s6")[1], [PHL + 210, 140, -170], [PHL, 6, 10], 46), fixed(END("s6"), [PHL + 240, 130, 90], [PHL, 6, 0], 46)],
    # s7: looking down on the decks: funnels lifted off, portholes out, holes cut
    "s7": [fixed(cut("s7")[1], [PHL - 60, 230, 170], [PHL, 15, 10], 50), fixed(at("s7", word="portholes,"), [PHL - 95, 30, 120], [PHL, 6, 40], 46),
           fixed(at("s7", word="holes"), [PHL - 40, 190, 120], [PHL, 18, 0], 50), fixed(END("s7"), [PHL - 30, 200, 100], [PHL, 18, -10], 50)],
    # s8: the site off Destin, the boats gathering
    "s8": [fixed(cut("s8")[1], [270, 62, 240], [0, 4, 10], 48), fixed(END("s8"), [245, 50, 225], [0, 3, 10], 48)],
    # s9: evening into night
    "s9": [fixed(cut("s9")[1], [-235, 24, 205], [0, 3, 0], 48), fixed(END("s9"), [-210, 18, 185], [0, 0, 0], 48)],
    # s10: low, from a boat: the lean and the plunge
    "s10": [fixed(cut("s10")[1], [-125, 15, 270], [0, 2, 60], 48), fixed(at("s10", word="slipped"), [-116, 13, 258], [0, -1, 58], 48, shake=0.06),
            fixed(END("s10"), [-112, 12, 252], [0, -4, 55], 48)],
    # s11: underwater, the bow out of the blue, then over the top deck with the divers
    "s11": [fixed(cut("s11")[1], [70, -40, 230], [0, -30, 130], 50), fixed(at("s11", word="down."), [55, -30, 190], [0, -24, 110], 50),
            follow(at("s11", word="18"), [1.5, 3.5, -9], [0, -2, 25], 52, "d1"), follow(END("s11"), [1.2, 3, -7.5], [0, -2, 25], 52, "d1")],
    # s12: alongside the hull, the reef growing and the fish arriving
    "s12": [fixed(cut("s12")[1], [-55, -30, -10], [0, -22, 15], 50), fixed(END("s12"), [-80, -26, 30], [0, -22, 10], 50)],
    # s13: rising away toward the light
    "s13": [fixed(cut("s13")[1], [-90, -20, 40], [0, -26, 0], 50), fixed(at("s13", 1.0, offset=0.6), [-110, -5, 60], [0, -28, 0], 50)],
}
CAMERA = []
for k, sid in enumerate(ORDER):
    shots = SHOTS[sid]
    CAMERA += shots
    if k + 1 < len(ORDER):
        CAMERA.append({**shots[-1], "at": cut(ORDER[k + 1])[0]})
CAMERA[0] = {**CAMERA[0], "at": 0}

# ---------------------------------------------------------------- objects
Z_END = 700   # the liner's run across the Atlantic during s2 to s4 (about 22 m/s)
LINER_TRACK = [
    {"at": at("s2", 0), "pos": [SEA, 0, 0], "rot": [0, 0, 0], "ease": "linear"},
    {"at": cut("s5")[0], "pos": [SEA, 0, Z_END], "rot": [0, 0, 0]},
    {"at": cut("s5")[1], "pos": [PHL, 0, 0], "rot": [0, 0, 0]},
    {"at": cut("s8")[0], "pos": [PHL, 0, 0], "rot": [0, 0, 0]},
    {"at": cut("s8")[1], "pos": [0, 0, 0], "rot": [0, 0, 0]},
    {"at": at("s8", 1.0), "pos": [0, -2.5, 0], "rot": [0, 0, 0]},
    {"at": at("s9", word="Night"), "pos": [0, -5, 0], "rot": [-0.4, 0, 1]},
    {"at": at("s10", 0), "pos": [0, -6.5, 0], "rot": [-0.5, 0, 2]},
    {"at": at("s10", word="side,"), "pos": [0, -9, 0], "rot": [-0.8, 0, 16]},
    {"at": at("s10", word="slipped"), "pos": [0, -12, 0], "rot": [-1, 0, 21]},
    {"at": at("s10", 1.0, offset=-0.02), "pos": [0, -42, 0], "rot": [-2, 0, 27]},
    {"at": cut("s11")[0], "pos": [0, -42, 0], "rot": [-2, 0, 27]},
    {"at": cut("s11")[1], "pos": [0, REST, 0], "rot": [0, 0, 0]},
    {"at": at("s13", 1.0, offset=1), "pos": [0, REST, 0], "rot": [0, 0, 0]},
]
HOOK_TRACK = [
    {"at": at("s1", 0), "pos": [0, -8, 0], "rot": [-0.6, 0, 6]},
    {"at": at("s1", word="night,"), "pos": [0, -9, 0], "rot": [-0.8, 0, 12]},
    {"at": at("s1", word="quietly.", offset=-0.6), "pos": [0, -12, 0], "rot": [-1, 0, 20]},
    {"at": at("s1", 1.0, offset=0.1), "pos": [0, -48, 0], "rot": [-2, 0, 27]},
]

WORLD = {
    "style": "night", "terrain": False, "far": 6000,
    "env": envs,
    "objects": [
        {"type": "ocean", "y": 0, "amp": 0.5, "size": 3000, "segs": 160},
        # the reef site: seabed 55 m down, spectator boats, the foam where she went under
        {"type": "seabed", "pos": [0, -55, 0], "size": 1400, "seed": 4, "clear": 260, "color": "#8a8468"},
        {"type": "flotilla", "pos": [0, 0, 0], "count": 46, "r0": 270, "r1": 720, "seed": 31,
         "lights": [{"at": 0, "l": 1}, {"at": cut("s2")[0], "l": 1}, {"at": cut("s2")[1], "l": 0},
                    {"at": at("s9", word="Night", offset=-1.5), "l": 0}, {"at": at("s9", word="Night", offset=1.0), "l": 1}]},
        {"type": "foam", "pos": [0, 0.75, 0], "w": 90, "l": 360, "seed": 3,
         "op": [{"at": 0, "o": 0}, {"at": at("s1", 1.0, offset=-0.7), "o": 0}, {"at": at("s1", 1.0), "o": 0.8},
                {"at": cut("s2")[0], "o": 0.8}, {"at": cut("s2")[1], "o": 0},
                {"at": at("s10", word="slipped", offset=0.6), "o": 0}, {"at": at("s10", 1.0, offset=-0.05), "o": 0.85},
                {"at": cut("s11")[0], "o": 0.7}, {"at": cut("s11")[1], "o": 0}]},
        # Philadelphia: the pier, sheds, the waterfront and the skyline
        {"type": "box", "pos": [PHL + 30, -4, 0], "w": 28, "h": 7, "d": 440, "color": "#8c8a84"},
        {"type": "box", "pos": [PHL + 36, 3, -30], "w": 16, "h": 11, "d": 220, "color": "#6f655a"},
        {"type": "box", "pos": [PHL + 594, -4, 0], "w": 1100, "h": 6, "d": 3000, "color": "#4f534d"},
        {"type": "towers", "area": [PHL + 300, -700, PHL + 900, 700], "count": 150, "scale": 2.2, "lit": 0.5, "glow": 0.55, "seed": 14},
        {"type": "airliner", "scale": 7.5, "gear": False, "lights": True, "livery": 3, **only("s5"),
         "track": [{"at": at("s5", 0), "pos": [PHL - 60, 300, -560], "rot": [8, 0, 0]},
                   {"at": at("s5", word="1969,", offset=0.6), "pos": [PHL - 70, 150, 520], "rot": [8, 0, 0], "ease": "linear"}]},
        # the hook: the stripped liner going under at night
        {"type": "liner", "funnels": False, "rust": [{"at": 0, "r": 0.8}], "holes": [{"at": 0, "h": 1}], "ports": [{"at": 0, "p": 1}],
         "lights": [{"at": 0, "l": 1}], **only("s1"), "track": HOOK_TRACK},
        # the liner, from her record years to the seabed
        {"type": "liner", "id": "us", **only("s2", "s13"), "track": LINER_TRACK,
         "wobble": [{"from": at("s2", 0), "to": at("s4", 1.0), "roll": 0.5, "pitch": 0.25, "freq": 0.12}],
         "wake": [{"at": 0, "w": 1}, {"at": cut("s5")[0], "w": 1}, {"at": cut("s5")[1], "w": 0}],
         "lit": [{"at": 0, "l": 0}, {"at": cut("s4")[0], "l": 0}, {"at": cut("s4")[1], "l": 1}, {"at": cut("s5")[0], "l": 1}, {"at": cut("s5")[1], "l": 0}],
         "rust": [{"at": 0, "r": 0}, {"at": at("s5", word="1969,"), "r": 0.05}, {"at": at("s5", 1.0), "r": 0.75}],
         "lift": [{"at": 0, "y": 0}, {"at": at("s7", word="funnels,", offset=-0.3), "y": 0}, {"at": at("s7", word="funnels,", offset=1.4), "y": 70}],
         "ports": [{"at": 0, "p": 0}, {"at": at("s7", word="portholes,", offset=-0.3), "p": 0}, {"at": at("s7", word="portholes,", offset=0.5), "p": 1}],
         "holes": [{"at": 0, "h": 0}, {"at": at("s7", word="holes"), "h": 0}, {"at": at("s7", word="holes", offset=0.9), "h": 1}],
         "lights": [{"at": 0, "l": 0}, {"at": at("s9", word="Night"), "l": 0}, {"at": at("s9", word="Night", offset=1.0), "l": 1},
                    {"at": cut("s11")[0], "l": 1}, {"at": cut("s11")[1], "l": 0}],
         "growth": [{"at": 0, "g": 0}, {"at": at("s12", word="tuna,"), "g": 0.05}, {"at": at("s12", word="reef."), "g": 1}]},
        # the reef: fish arriving, divers over the top deck
        {"type": "fish", "pos": [0, -40, 0], "count": 420, "r0": 26, "r1": 160, "y0": -12, "y1": 30, "size": 0.8, "seed": 77,
         "n": [{"at": 0, "n": 30}, {"at": at("s12", word="tuna,"), "n": 30}, {"at": at("s12", word="reef."), "n": 420}]},
        {"type": "diver", "id": "d1", "scale": 1.2, "seed": 1, **only("s11", "s13"),
         "track": [{"at": at("s11", 0), "pos": [-5, -14, 90], "rot": [0, 180, 0]}, {"at": at("s13", 1.0), "pos": [-3, -14, -20], "rot": [0, 180, 0], "ease": "linear"}]},
        {"type": "diver", "scale": 1.2, "seed": 2, "suit": "#2a1f1f", "fin": "#e0b02a", **only("s11", "s13"),
         "track": [{"at": at("s11", 0), "pos": [3, -12, 100], "rot": [0, 185, 0]}, {"at": at("s13", 1.0), "pos": [6, -11, -8], "rot": [0, 185, 0], "ease": "linear"}]},
    ],
    "camera": CAMERA,
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
    build(HERE, [("ch01", "SS United States", SCENES)], BASE, "America sank its fastest ship ever, on purpose", seed=16)
