"""Builds the ~48-second 9:16 Short "Cascadia: the fault that gives some beaches fifteen minutes" (ch01.json),
in the explainer look (longform/explainer.py).

    python longform/cascadia_short/build.py

Facts: USGS event page for the 1700 Cascadia earthquake (M9, about 9 PM on 26 January 1700, dated by the "orphan
tsunami" written down in Japan on 27-28 January 1700); Oregon Encyclopedia / USGS (fault from Vancouver Island to
northern California, about 1,000 km; ghost forests from sudden subsidence); NYT / Oregon (a Cascadia tsunami reaches
some shorelines within 15 minutes); Cascadia Rising scenario via GovTech (shaking 3 to 6 minutes); Dura et al., PNAS
2025, via BBC Science Focus (coast can drop more than 2.5 m within minutes); Washington DNR modelling (flooding depths
of 60 to 100 ft, about 30 m, on Pacific beaches); ViewSpace / USGS Professional Paper 1707 (the wave reached Japan
after about 10 hours); USGS National Seismic Hazard Model via Science Focus (15% chance of M8+ in the next 50 years).
The cutaway is simplified and exaggerated (labelled on screen).
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from kit import S, build  # noqa: E402
from explainer import CAPTIONS, SOUND, LOOK, CHIP, TAG, at, shots  # noqa: E402

W3 = {"type": "world3d"}

SCENES = [
    dict(S("A fault off America's Pacific coast last broke in 1700. Next time, some beaches get about fifteen minutes.",
           W3, CHIP("Cascadia subduction zone")), id="s1"),
    dict(S("It's Cascadia: a thousand kilometres of fault, from Vancouver Island to northern California.",
           W3, CHIP("Source: USGS")), id="s2"),
    dict(S("An ocean plate slides under North America, but its edge is stuck, so the coast bends like a spring.",
           W3, CHIP("Simplified cutaway, not to scale")), id="s3"),
    dict(S("When it slips, a magnitude 9 shakes the region for up to six minutes.",
           W3, CHIP("FEMA Cascadia Rising scenario")), id="s4"),
    dict(S("The coast drops up to two and a half metres, and the sea floor heaves the ocean up.",
           W3, CHIP("Dura et al., PNAS 2025")), id="s5"),
    dict(S("Waves up to 30 metres can reach some beaches in about fifteen minutes.",
           W3, CHIP("Washington DNR tsunami model")), id="s6"),
    dict(S("In 1700, that wave crossed the Pacific and hit Japan about ten hours later.",
           W3, CHIP("USGS: the orphan tsunami of 1700")), id="s7"),
    dict(S("Odds of a magnitude 8 or bigger in the next 50 years: about 15 percent. Would you live there?",
           W3, CHIP("USGS National Seismic Hazard Model")), id="s8"),
]
ORDER = [f"s{k}" for k in range(1, 9)]

# ---------------------------------------------------------------- environments
SPACE = {"sky_top": "#000003", "sky": "#02030a", "fog": [3000, 6000], "hemi": 0.2, "ambient": 0.1, "sun": 2.4,
         "sun_color": "#fff6e6", "sun_dir": [25, 45, 60], "cloud": "#ffffff", "ocean": "#1d3b52", "exposure": 1.0,
         "hdri": "none"}
DAY = {"sky_top": "#5b8fc9", "sky": "#cfe0ee", "fog": [300, 1400], "hemi": 0.35, "ambient": 0.15, "sun": 2.2,
       "sun_color": "#fff1dc", "sun_dir": [-40, 60, 50], "cloud": "#ffffff", "ocean": "#1f4e6b", "exposure": 1.0,
       "hdri": "clear", "env_intensity": 0.9}

# ---------------------------------------------------------------- the globe: lon -124 faces +z, no spin, no tilt
R_E = 20.0
PHI0 = (-124 + 180) / 360 * 2 * math.pi
ROT0 = math.atan2(math.cos(PHI0), math.sin(PHI0))


def gdir(lat, lon):
    """Unit vector from the globe's centre to (lat, lon), in world space (matches the runtime's sphere mapping)."""
    phi, th = (lon + 180) / 360 * 2 * math.pi, math.radians(90 - lat)
    x, y, z = -math.cos(phi) * math.sin(th), math.cos(th), math.sin(phi) * math.sin(th)
    a = ROT0
    return [x * math.cos(a) + z * math.sin(a), y, -x * math.sin(a) + z * math.cos(a)]


def gcam(lat, lon, dist, look_r=0.0):
    d = gdir(lat, lon)
    return [v * dist for v in d], [v * look_r for v in d]


FAULT = [[50.6, -128.6], [49.2, -127.2], [48.0, -126.0], [46.5, -125.3], [44.5, -125.2], [42.5, -125.0], [40.4, -124.9]]
P_WIDE, L_WIDE = gcam(42, -118, 78, 0)
P_WIDE2, L_WIDE2 = gcam(44, -121, 66, 0)
P_PNW, L_PNW = gcam(45.5, -123, 46, R_E * 0.92)
P_PNW2, L_PNW2 = gcam(45.5, -123.5, 42, R_E * 0.92)
P_PAC, L_PAC = gcam(36, -172, 82, 0)
P_PAC2, L_PAC2 = gcam(36, -176, 76, 0)

# ---------------------------------------------------------------- the cutaway (local units, squashed 0.35 along x)
CX, SX, DZF = 5000, 0.35, 16.3


def cw(x, y):
    """Front-face point of the cutaway, from its local coordinates."""
    return [CX + x * SX, y, DZF]


C_WIDE = ([CX - 4, 4, 136], [CX, -17, 0])
C_WIDE2 = ([CX - 8, 7, 126], [CX, -16, 0])
C_LOCK = ([CX - 10, 2, 46], [CX - 3, -8, 0])
C_LOCK2 = ([CX - 8, 1, 40], [CX - 3, -8, 0])
C_COAST = ([CX - 4, 8, 44], [CX + 5, -1, 0])
C_COAST2 = ([CX - 2, 6.5, 38], [CX + 5.5, -0.8, 0])

PLAN = {
    "s1": [(0, P_WIDE, L_WIDE, P_WIDE2, L_WIDE2, 40, SPACE),
           ("fifteen", P_PNW, L_PNW, P_PNW2, L_PNW2, 40, SPACE)],
    "s2": [(0, P_PNW2, L_PNW2, P_PNW, L_PNW, 40, SPACE)],
    "s3": [(0, C_WIDE[0], C_WIDE[1], C_WIDE2[0], C_WIDE2[1], 40, DAY),
           ("stuck,", C_LOCK[0], C_LOCK[1], C_LOCK2[0], C_LOCK2[1], 40, DAY)],
    "s4": [(0, C_LOCK2[0], C_LOCK2[1], C_LOCK[0], C_LOCK[1], 40, DAY),
           ("shakes", C_COAST[0], C_COAST[1], C_COAST2[0], C_COAST2[1], 40, DAY)],
    "s5": [(0, C_WIDE2[0], C_WIDE2[1], C_WIDE[0], C_WIDE[1], 40, DAY)],
    "s6": [(0, C_COAST[0], C_COAST[1], C_COAST2[0], C_COAST2[1], 40, DAY)],
    "s7": [(0, P_PAC, L_PAC, P_PAC2, L_PAC2, 40, SPACE)],
    "s8": [(0, C_COAST2[0], C_COAST2[1], C_COAST[0], C_COAST[1], 40, DAY),
           ("Would", P_WIDE2, L_WIDE2, P_WIDE, L_WIDE, 40, SPACE)],
}

CAMERA, ENVS = [], []
for k, sid in enumerate(ORDER):
    nxt = ORDER[k + 1] if k + 1 < len(ORDER) else None
    plan = PLAN[sid]
    keys = shots(sid, [p[:6] for p in plan], nxt)
    if sid == "s4":   # the shaking: from the slip to the end of the scene
        for kk in keys:
            kk["shake"] = 0.35
    CAMERA += keys
    for j, p in enumerate(plan):
        start = p[0]
        t1 = at(sid, 0) if j == 0 else (at(sid, word=start) if isinstance(start, str) else at(sid, start))
        t0 = {**t1, "offset": t1.get("offset", 0) - 0.012}
        if ENVS:
            ENVS.append({**ENVS[-1], "at": t0})
        ENVS.append({**p[6], "at": t1})
ENVS[0] = {**ENVS[0], "at": 0}
CAMERA[0] = {**CAMERA[0], "at": 0}
# no shake before the slip itself
CAMERA[next(i for i, kk in enumerate(CAMERA) if kk.get("shake"))]["shake"] = 0.0

SLIP = at("s4", word="slips,")
WORLD = {
    "style": "night", "terrain": False, "far": 6000, "shadows": False,
    "look": LOOK,
    "env": ENVS,
    "objects": [
        {"type": "stars", "seed": 21, "count": 2400, "size": 1.6},
        {"type": "earth", "pos": [0, 0, 0], "r": R_E, "real": True, "spin": 0.0, "tilt": 0, "face_lon": -124, "clouds": 0.55,
         "lines": [{"pts": FAULT, "color": "#ff3b30", "reveal": [{"at": at("s1", 0.15), "p": 0}, {"at": at("s1", 0.6), "p": 1}]}],
         "pins": [{"id": "van", "lat": 49.6, "lon": -125.6}, {"id": "sea", "lat": 47.6, "lon": -122.3},
                  {"id": "pdx", "lat": 45.5, "lon": -122.7}, {"id": "men", "lat": 40.44, "lon": -124.4},
                  {"id": "jpn", "lat": 39.6, "lon": 141.95}, {"id": "src", "lat": 46.5, "lon": -125.3}],
         "ripples": [{"lat": 46.5, "lon": -125.3, "from": at("s7", 0.05), "speed": 21, "max": 80, "width": 1.8}]},
        TAG("Vancouver Island", follow="van", dot=True, show=[{"from": at("s2", word="Vancouver"), "to": at("s2", 1.0)}]),
        TAG("Seattle", follow="sea", dot=True, show=[{"from": at("s1", word="fifteen"), "to": at("s2", 1.0)}]),
        TAG("Portland", follow="pdx", dot=True, show=[{"from": at("s1", word="fifteen"), "to": at("s2", 1.0)}]),
        TAG("Northern California", follow="men", dot=True, show=[{"from": at("s2", word="northern"), "to": at("s2", 1.0)}]),
        TAG("Japan · 27 Jan 1700", follow="jpn", dot=True, show=[{"from": at("s7", word="Japan"), "to": at("s7", 1.0)}],
            accent="#7fe3ff"),
        TAG("Cascadia", follow="src", dot=True, show=[{"from": at("s7", 0), "to": at("s7", word="Japan")}], accent="#ff3b30"),
        # the cutaway
        {"type": "subduction", "pos": [CX, 0, 0], "sx": SX, "seed": 5,
         "strain": [{"at": 0, "s": 0}, {"at": at("s3", word="stuck,"), "s": 0.15}, {"at": at("s3", 1.0), "s": 1.0}],
         "slip": SLIP, "arrive": at("s6", 0, offset=0.9),
         "ghost": [{"at": at("s8", 0), "g": 0}, {"at": at("s8", 0.6), "g": 1}]},
        TAG("Juan de Fuca plate", pos=cw(-38, -9.6), show=[{"from": at("s3", 0.08), "to": at("s3", word="stuck,")}], accent="#7fb0ff"),
        TAG("North American plate", pos=cw(26, -9), show=[{"from": at("s3", 0.2), "to": at("s3", word="stuck,")}], accent="#ffb36b"),
        TAG("Locked", pos=cw(-9.5, -9.4), dot=True, show=[{"from": at("s3", word="stuck,"), "to": at("s4", word="slips,")}], accent="#ff3b30"),
        TAG("Sea floor jumps up", pos=cw(-7, -5.6), dot=True, show=[{"from": at("s5", word="sea"), "to": at("s5", 1.0)}]),
        TAG("Coast drops", pos=cw(13.5, 0.4), dot=True, show=[{"from": at("s5", word="drops"), "to": at("s5", 1.0)}]),
        TAG("Up to 30 m", pos=cw(8, 5.2), show=[{"from": at("s6", word="30"), "to": at("s6", 1.0)}], accent="#7fe3ff"),
        TAG("Ghost forest", pos=cw(28, 5.5), dot=True, show=[{"from": at("s8", 0.35), "to": at("s8", word="Would")}]),
    ],
    "camera": CAMERA,
}

BASE = {
    "language": "en", "voice": "bm_george", "speed": 1.08, "aspect": "9:16", "fps": 60, "made_for_kids": False,
    "footage": "off", "transition": "none",
    "music": {"mood": "mystery", "volume": 0.1},
    "captions": CAPTIONS,
    "overlay": {"handle": "@hypercurious96", "progress_bar": False},
    "sound": {**SOUND, "first": "riser", "first_gain": 0.3,
              "hits": [{"at": SLIP, "kind": "boom", "gain": 0.6},
                       {"at": at("s5", word="drops"), "kind": "hit", "gain": 0.4},
                       {"at": at("s6", word="30"), "kind": "hit", "gain": 0.45},
                       {"at": at("s8", word="15"), "kind": "hit", "gain": 0.45}]},
    "world3d": WORLD,
}

if __name__ == "__main__":
    build(HERE, [("ch01", "Cascadia", SCENES)], BASE, "Cascadia: the fault that gives some beaches fifteen minutes", seed=31)
