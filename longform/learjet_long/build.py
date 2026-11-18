"""Builds the 16:9 long video "The Learjet 60 crash: everything we know" (English, about 9 minutes, 60 fps) as ch01.json.

    python longform/learjet_long/build.py

A 3D documentary of what is publicly known about the Learjet 60 (N722BD) crash near Greenacres, Florida, on Sunday
1 November 2026, in nine chapters. No cause is stated: the NTSB has not established one. Every on-screen claim comes
from the sources below; illustrative visuals (the map, the radar cells, the wing section, the gauge, the chart) are
labelled or described as illustrations in the narration or the description.
Facts: NTSB briefings and updates via CBS12/KMPH/ABC News 4 (Chapman, Monville), Aviation Week (Bill Carey, 10 Nov),
AVweb, CBS Austin, WPTV, UPI, CBS12, Fox News, CBS News, Military & Aerospace Electronics, The Flying Engineer (tracking,
weather observation, FOX 13 audio report, CNN radar analysis, NTSB process), AeroCorner (overspeed, preliminary timing),
Wikipedia (Learjet 60 specifications), FAA AC 00-24C via AOPA, FAA blog, AC 00-24A, AvnWx (clear ice), FAA-H-8083-28
via icinganalysis (clear ice hard to see), USAF Air Weather Service (ice distorts lifting surfaces).
"""
import json
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


def T(text, at_word=None, y=0.1, until=None, red=False, size=0.027, at_time=None):
    el = {"type": "text", "text": text, "x": 0.5, "y": y, "size": size, "color": "#ffffff",
          "bg": "#c62828" if red else "#14181f", "bg_alpha": 0.88, "style": "label", "stroke": False, "enter": "pop"}
    if at_word:
        el["at_word"] = at_word
    else:
        el["at"] = 0.3 if at_time is None else at_time
    if until:
        el["until"] = until
    return el


def CH(title):   # chapter card at the top of a chapter's first scene
    return T(title, y=0.09, red=True, size=0.03, at_time=0.2, until=4.0)


# (id, chapter title or None, narration, labels)
SCRIPT = [
    # ---- cold open
    ("s01", None, "At 12:47 on a Sunday afternoon, 35,000 feet above South Florida, a pilot told air traffic control that his jet was picking up ice, and that it was manageable.",
     [T("1 Nov 2026, 12:47 p.m.", at_word="12:47"), T("35,000 ft", at_word="35,000", y=0.17)]),
    ("s02", None, "About three minutes later, the jet hit a road in a Florida neighbourhood. All nine people on board were killed.",
     [T("All 9 on board killed", at_word="nine", red=True)]),
    ("s03", None, "Investigators have found signs that it began breaking apart in the sky. This is everything we know so far about the Learjet 60 crash near Greenacres, and the questions that are still open.",
     [T("The Learjet 60 crash: what we know", at_word="everything", size=0.034)]),
    # ---- the flight
    ("s04", "The flight", "It was Sunday, the first of November 2026. At Austin-Bergstrom International Airport in Texas, a Learjet 60 took off for North Eleuthera, an island in the Bahamas.",
     [T("Austin, Texas to North Eleuthera, Bahamas", at_word="Austin-Bergstrom", y=0.17)]),
    ("s05", None, "The Learjet 60 is a mid-size business jet built by Bombardier in Wichita, Kansas. It is about 18 metres long, and carries two pilots and up to eight passengers.",
     [T("Learjet 60: 17.9 m long, 13.3 m wingspan", at_word="18"), T("2 pilots, up to 8 passengers", at_word="two", y=0.17)]),
    ("s06", None, "This one was flying as a charter under the rules known as Part 135, operated by a Fort Lauderdale company, Aurora Aviation, which does business as Upper Jets. On board were two pilots and seven passengers, among them a young family.",
     [T("Part 135 charter: Aurora Aviation (Upper Jets)", at_word="Part"), T("2 pilots, 7 passengers", at_word="pilots", y=0.17)]),
    ("s07", None, "Flight tracking shows the jet climbing as high as 41,000 feet, then settling at around 35,000 feet as it headed east.",
     [T("Route shown is illustrative", at_time=0.3, y=0.8, size=0.018)]),
    # ---- into the storms
    ("s08", "Into the storms", "Over South Florida, the weather was turning. Heavy rain and thunderstorms were sweeping across the region that afternoon.",
     [T("Radar cells are illustrative", at_word="Heavy", y=0.8, size=0.018)]),
    ("s09", None, "A weather observation taken about 15 minutes before the crash reported a thunderstorm nearby, visibility of three miles, and gusts to 19 knots.",
     [T("~15 min before: thunderstorm nearby", at_word="thunderstorm"), T("Visibility 3 miles, gusts 19 knots", at_word="visibility", y=0.17)]),
    ("s10", None, "CNN reported that radar and tracking data suggest the jet passed through a stronger storm cell a few minutes before it began to fall. That is a media analysis, not an NTSB finding.",
     [T("Media analysis, not an NTSB finding", at_word="media", red=True)]),
    ("s11", None, "Why do pilots fear thunderstorms? Inside a storm, powerful updrafts and downdrafts can move air by more than 3,000 feet a minute, and the clash between them creates violent turbulence.",
     [T("Updrafts and downdrafts: 3,000+ ft/min", at_word="updrafts")]),
    ("s12", None, "The FAA's guidance is blunt. Penetration of any thunderstorm can lead to an aircraft accident and fatalities to those on board. Pilots are advised to stay at least 20 miles away from severe storms.",
     [T("FAA AC 00-24C", at_word="FAA's"), T("Stay 20+ miles from severe storms", at_word="20", y=0.17)]),
    ("s13", None, "Storms also carry water high above the freezing level, where it can stay liquid even far below zero. When these supercooled drops hit a wing, they freeze.",
     [T("Supercooled water", at_word="supercooled")]),
    # ---- ice at 35,000 feet
    ("s14", "Ice at 35,000 feet", "At about 12:47, the crew told controllers in Miami that they were in light, clear ice and moderate turbulence, with the altitude swinging by about 700 feet.",
     [T("Light clear ice, moderate turbulence", at_word="light,"), T("Altitude swings of ~700 ft", at_word="700", y=0.17)]),
    ("s15", None, "Clear ice forms from larger drops that don't freeze instantly. The water runs back along the wing, and freezes into a smooth, heavy sheet.",
     [T("Clear ice (illustration)", at_word="Clear")]),
    ("s16", None, "Because it is clear, it is hard to see. And as it builds up, it distorts the shape of the wing, which can degrade control of the aircraft.",
     []),
    ("s17", None, "The outside air temperature was minus 47 degrees Celsius. The crew said they were handling the ice.",
     [T("-47°C outside", at_word="minus")]),
    ("s18", None, "Then they reported picking up precipitation, and asked to climb to 37,000 feet. Controllers approved.",
     [T("Request: climb to 37,000 ft", at_word="climb"), T("Approved", at_word="approved.", y=0.17)]),
    # ---- the fall
    ("s19", "The fall", "Less than 30 seconds later, the crew reported that the jet was descending, and declared an emergency.",
     [T("< 30 seconds later", at_word="Less", red=True)]),
    ("s20", None, "Mayday, Mayday, the pilot called. We're descending 10,000 feet per minute.",
     [T("MAYDAY", at_word="Mayday,", red=True, size=0.034)]),
    ("s21", None, "Another transmission said the plane was in an overspeed condition, descending.",
     [T("“Overspeed condition, descending”", at_word="overspeed")]),
    ("s22", None, "Every jet has a maximum operating speed. Overspeed means it is flying faster than that limit, and a warning sounds in the cockpit. It describes what the jet is doing, not why.",
     [T("Overspeed: past the maximum operating speed", at_word="Overspeed")]),
    ("s23", None, "According to reports of the radio audio, the pilot then called out passing 22,000 feet, in a 60 degree bank.",
     [T("Reported: 22,000 ft, 60° bank", at_word="22,000")]),
    ("s24", None, "Tracking data shows the jet falling from about 35,250 feet to about 8,750 feet in roughly one minute.",
     [T("35,250 ft to 8,750 ft in ~1 minute", at_word="35,250")]),
    ("s25", None, "Estimates of the descent rate vary, from about 20,000 feet a minute in the pilot's call, to more than 30,000 by other estimates. At 30,000 feet a minute, that is more than 500 kilometres an hour, straight down.",
     [T("~20,000 to 30,000+ ft/min", at_word="vary,"), T("30,000 ft/min ≈ 550 km/h downward", at_word="500", y=0.17)]),
    # ---- breaking apart
    ("s26", "Breaking apart", "Two days later, the NTSB said it had recovered most of the jet's left elevator, in three pieces, between 1.3 and 3.8 miles from where the jet hit the ground.",
     [T("Left elevator: 3 pieces", at_word="three"), T("1.3 to 3.8 miles from the impact", at_word="1.3", y=0.17)]),
    ("s27", None, "The elevator is the hinged part of the tail that controls the plane's pitch, whether the nose goes up or down. On the Learjet 60, it sits high on top of the tail.",
     [T("Elevator: controls pitch", at_word="pitch,")]),
    ("s28", None, "Finding it that far away, the NTSB said, suggests parts separated before the jet hit the ground. Board member Tom Chapman put it this way. We do have some evidence that there was some breakup of the aircraft before impact.",
     [T("Distances shown as rings; direction not published", at_time=0.3, y=0.8, size=0.018), T("Tom Chapman, NTSB", at_word="Chapman", y=0.17)]),
    ("s29", None, "What investigators don't yet know is whether the elevator coming off helped cause the dive, or whether the forces of the dive tore it off.",
     [T("Cause or result? Not yet known", at_word="know", red=True)]),
    ("s30", None, "By November the 8th, investigators had identified parts from both wings, both engines, the flight deck, the tail, the left elevator, the ailerons, and several flap tracks. Some pieces went to NTSB labs in Washington.",
     [T("Wings, engines, flight deck, tail, elevator", at_word="wings,")]),
    # ---- greenacres
    ("s31", "Greenacres", "The jet came down at about 12:50, on South Military Trail near Greenacres in Palm Beach County, beside a mobile home park.",
     [T("South Military Trail, Greenacres", at_word="Military"), T("~12:50 p.m.", at_word="12:50,", y=0.17)]),
    ("s32", None, "People who called 911 described hearing what sounded like a bomb.",
     []),
    ("s33", None, "The impact left a crater in the roadway. Before investigators could reach the wreckage, crews had to remove an unstable utility pole, and drain water from the crater.",
     [T("Crater filled with water", at_word="drain")]),
    ("s34", None, "Debris spread across an area about half a mile long and four tenths of a mile wide, onto rooftops, ball fields, businesses and homes.",
     [T("Debris field: ~0.5 × 0.4 miles", at_word="half")]),
    ("s35", None, "Areas searched and cleared included a mobile home community, a plaza, a self-storage site and a high school.",
     []),
    ("s36", None, "On the ground, one man in a car leaving the area was hurt, with a leg injury. Residents of the mobile home community were kept away from their homes for days before they could return.",
     [T("1 person hurt on the ground", at_word="hurt,")]),
    # ---- the investigation
    ("s37", "The investigation", "The NTSB is leading the investigation, with the FAA assisting.",
     []),
    ("s38", None, "On November the 9th, investigators recovered the cockpit voice recorder, at the site of the initial impact. It was sent to the NTSB's Vehicle Recorders Laboratory in Washington.",
     [T("Cockpit voice recorder recovered, 9 Nov", at_word="cockpit")]),
    ("s39", None, "A cockpit voice recorder captures the conversations and sounds in the cockpit. It could show what the pilots saw, said and did in those last minutes. It is not yet known what this one captured.",
     [T("What it captured: not yet released", at_word="known", red=True)]),
    ("s40", None, "Investigators say they will look at the condition of the aircraft, the actions of the crew, and the weather, along with what the pilots and controllers knew, and when.",
     [T("Aircraft · crew · weather · ATC", at_word="condition")]),
    ("s41", None, "Chapman has said it is too early to say whether the jet flew through an active thunderstorm.",
     [T("Thunderstorm penetration: not determined", at_word="early")]),
    # ---- what happens next
    ("s42", "What happens next", "The NTSB usually publishes a preliminary report within about 30 days, listing facts only. That would put it around the start of December.",
     [T("Preliminary report: ~early December", at_word="preliminary")]),
    ("s43", None, "The final report, with the probable cause, often takes a year or two.",
     [T("Final report: often 1 to 2 years", at_word="final")]),
    ("s44", None, "Until then, what we have is a sequence. Ice and turbulence at 35,000 feet. A request to climb. A mayday, and an overspeed. A fall of about 27,000 feet in a minute, and part of the tail found miles from the crash. What connects them is still unknown.",
     [T("Cause: not yet determined", at_word="unknown.", red=True)]),
    ("s45", None, "Nine people lost their lives on the first of November. We'll update this story when the NTSB's findings are released. To follow it, subscribe to Hypercurious.",
     [T("In memory of the nine people on board", at_word="Nine", y=0.17), T("Subscribe: Hypercurious", at_word="subscribe", y=0.24)]),
]

SCENES, CHAPTER_STARTS = [], []
for sid, chap, text, labels in SCRIPT:
    els = list(labels)
    if chap:
        els = [CH(chap)] + [dict(e, y=round(e["y"] + 0.07, 3)) if e["y"] < 0.5 else e for e in els]
        CHAPTER_STARTS.append((sid, chap))
    SCENES.append(dict(S(text, W3, *els), id=sid))
ORDER = [s for s, *_ in SCRIPT]

# ---------------------------------------------------------------- environments
STORM = {"sky_top": "#3a4250", "sky": "#6c7684", "fog": [22, 150], "hemi": 1.0, "ambient": 0.5, "sun": 0.8,
         "sun_color": "#dfe6ee", "sun_dir": [20, 60, 30], "cloud": "#7d8794", "ocean": "#3a4a58", "exposure": 1.05}
FALL = {**STORM, "fog": [40, 330], "sky": "#5e6876"}
SUNNY = {"sky_top": "#2f63a8", "sky": "#bcd6ee", "fog": [150, 700], "hemi": 1.2, "ambient": 0.5, "sun": 1.8,
         "sun_color": "#fff4e0", "sun_dir": [40, 50, 20], "cloud": "#f4f6f8", "ocean": "#2f6b8a", "exposure": 1.0}
STUDIO = {"sky_top": "#04070d", "sky": "#0d1624", "fog": [200, 900], "hemi": 0.9, "ambient": 0.5, "sun": 1.4,
          "sun_color": "#ffffff", "sun_dir": [30, 60, 40], "cloud": "#202838", "ocean": "#101820", "exposure": 1.05}
TOWN = {"sky_top": "#56606c", "sky": "#9aa4ae", "fog": [90, 560], "hemi": 1.15, "ambient": 0.55, "sun": 0.9,
        "sun_color": "#eef0f2", "sun_dir": [30, 60, 20], "cloud": "#8e98a2", "ocean": "#3a4a58", "exposure": 1.0}
DUSK = {"sky_top": "#1f2440", "sky": "#c98a6a", "fog": [120, 620], "hemi": 0.9, "ambient": 0.45, "sun": 1.0,
        "sun_color": "#ffb48a", "sun_dir": [-70, 10, 30], "cloud": "#a07c78", "ocean": "#2a3a4c", "exposure": 1.05}
SKYSTORM = {**STORM, "fog": [200, 1400], "sky": "#77818f", "sky_top": "#3d4552"}

ENV_BY_SCENE = {"s01": STORM, "s02": TOWN, "s03": STORM, "s04": SUNNY, "s05": STUDIO, "s06": SUNNY, "s07": STUDIO,
                "s08": STUDIO, "s09": TOWN, "s10": STUDIO, "s11": SKYSTORM, "s12": SKYSTORM, "s13": STUDIO,
                "s14": STORM, "s15": STUDIO, "s16": STUDIO, "s17": STORM, "s18": STORM, "s19": STORM, "s20": STORM,
                "s21": STUDIO, "s22": STUDIO, "s23": FALL, "s24": STUDIO, "s25": STUDIO, "s26": FALL, "s27": STUDIO,
                "s28": STUDIO, "s29": FALL, "s30": STUDIO, "s31": TOWN, "s32": TOWN, "s33": TOWN, "s34": TOWN,
                "s35": TOWN, "s36": DUSK, "s37": STUDIO, "s38": STUDIO, "s39": STUDIO, "s40": STORM, "s41": SKYSTORM,
                "s42": STUDIO, "s43": STUDIO, "s44": STORM, "s45": DUSK}


def env(t, d):
    return {**d, "at": t}


def cut(scene):
    return at(scene, 0, offset=-0.012), at(scene, 0)


def only(scene_from, scene_to=None):
    scene_to = scene_to or scene_from
    return {"build": {"op": "slide", "offset": [0, 0, 0], "from": at(scene_from, 0), "to": at(scene_from, 0, offset=0.01)},
            "hide": {"at": at(scene_to, 1.0, offset=0.02), "dur": 0.01}}


envs = [env(0, ENV_BY_SCENE["s01"])]
for k, sid in enumerate(ORDER[1:], 1):
    envs += [env(cut(sid)[0], ENV_BY_SCENE[ORDER[k - 1]]), env(cut(sid)[1], ENV_BY_SCENE[sid])]

# ---------------------------------------------------------------- regions (x offsets; the jet is about 6.2 long)
OPEN, DEP, STU, CRU, TX, MAPX, CBX, AFX, GX, PX, DX, HX, LX, TAIL, RPL = (
    -20000, -40000, -60000, 0, 20000, 100000, 120000, 140000, 160000, 180000, 200000, 220000, 240000, 60000, 260000)
V = 15


def fixed(t, pos, look, fov=40, shake=0.0):
    k = {"at": t, "pos": pos, "look": look, "fov": fov}
    if shake:
        k["shake"] = shake
    return k


def follow(t, target, offset, look, fov=40, shake=0.0):
    k = {"at": t, "follow": target, "offset": offset, "look_offset": look, "fov": fov}
    if shake:
        k["shake"] = shake
    return k


END = lambda s: at(s, 1.0, offset=-0.05)  # noqa: E731
SHOTS = {
    "s01": [follow(cut("s01")[1], "jo", [7, 1.4, 9], [0, 0, -1], 38, 0.05), follow(END("s01"), "jo", [6, 1.1, 5], [0, 0, -1], 38, 0.07)],
    "s02": [fixed(cut("s02")[1], [TX + 260, 14, 330], [TX, 40, 0], 36), fixed(END("s02"), [TX + 240, 13, 310], [TX, 38, 0], 36)],
    "s03": [follow(cut("s03")[1], "jt0", [-3.5, 7.5, -1.5], [-0.5, 3.2, -0.3], 42, 0.08), follow(END("s03"), "jt0", [-6, 9, -6], [0, 2, 0], 44, 0.12)],
    "s04": [fixed(cut("s04")[1], [DEP - 30, 2.2, 14], [DEP - 5, 1.4, 0], 40), fixed(at("s04", word="took"), [DEP - 10, 3, 16], [DEP + 25, 3, 0], 42),
            fixed(END("s04"), [DEP + 20, 6, 22], [DEP + 75, 14, 0], 44)],
    "s05": [fixed(cut("s05")[1], [STU + 9, 2.6, 8], [STU, 0.8, 0], 38), fixed(at("s05", word="18"), [STU + 2, 4.0, 11], [STU, 0.8, 0], 38),
            fixed(END("s05"), [STU - 8, 2.8, 8], [STU, 0.8, 0], 38)],
    "s06": [follow(cut("s06")[1], "jd", [-12, 3, -16], [0, 0, 3], 40), follow(END("s06"), "jd", [-14, 4, 6], [0, 0, 0], 40)],
    "s07": [fixed(cut("s07")[1], [MAPX - 15, 150, 62], [MAPX - 8, 0, 2], 40), fixed(END("s07"), [MAPX + 15, 140, 58], [MAPX + 12, 0, 2], 40)],
    "s08": [fixed(cut("s08")[1], [MAPX + 35, 70, 62], [MAPX + 52, 0, 6], 40), fixed(END("s08"), [MAPX + 52, 46, 48], [MAPX + 58, 0, 5], 40)],
    "s09": [fixed(cut("s09")[1], [TX + 200, 6, -260], [TX, 30, 0], 38), fixed(END("s09"), [TX + 185, 7, -245], [TX, 32, 0], 38)],
    "s10": [fixed(cut("s10")[1], [MAPX + 50, 30, 36], [MAPX + 61, 0, 4], 38), fixed(END("s10"), [MAPX + 70, 24, 33], [MAPX + 62, 0, 4], 38)],
    "s11": [fixed(cut("s11")[1], [CBX + 60, 70, 230], [CBX, 75, 30], 42), fixed(END("s11"), [CBX + 30, 80, 205], [CBX, 80, 30], 42)],
    "s12": [fixed(cut("s12")[1], [CBX + 120, 330, 380], [CBX, 30, 0], 44), fixed(END("s12"), [CBX + 40, 380, 360], [CBX, 30, 0], 44)],
    "s13": [fixed(cut("s13")[1], [AFX + 2, 1.6, 16], [AFX + 2, 0, 0], 40), fixed(END("s13"), [AFX + 1, 1.3, 13], [AFX + 1.5, 0.3, 0], 40)],
    "s14": [follow(cut("s14")[1], "jc", [-7, 1.5, 6], [0, 0, 0], 40, 0.1), follow(END("s14"), "jc", [-6, 1.3, 8], [0, 0, 0], 40, 0.14)],
    "s15": [fixed(cut("s15")[1], [AFX + 1.5, 1.2, 12], [AFX + 1.5, 0.4, 0], 40), fixed(END("s15"), [AFX + 0.5, 0.9, 8], [AFX + 0.8, 0.5, 0], 40)],
    "s16": [fixed(cut("s16")[1], [AFX + 4, 2.5, 15], [AFX + 4, 0.5, 0], 40), fixed(END("s16"), [AFX + 5, 2, 13], [AFX + 5, 0.6, 0], 40)],
    "s17": [follow(cut("s17")[1], "jc", [-0.7, 1.0, 1.9], [-1.5, -0.2, 0.0], 46, 0.05), follow(END("s17"), "jc", [-0.9, 1.1, 1.7], [-1.5, -0.2, 0.0], 46, 0.05)],
    "s18": [follow(cut("s18")[1], "jc", [-10, 1.5, 3], [0, 0, 0], 40, 0.08), follow(END("s18"), "jc", [-11, 2, 1], [0, 0.5, 0], 40, 0.08)],
    "s19": [follow(cut("s19")[1], "jc", [-10, 3, 6], [0, 0, 0], 40, 0.12), follow(END("s19"), "jc", [-11, 4, 5], [0, -0.5, 0], 40, 0.2)],
    "s20": [follow(cut("s20")[1], "jc", [-11, 5, 4], [0, -1, 0], 42, 0.22), follow(END("s20"), "jc", [-12, 6, 3], [0, -1, 0], 42, 0.25)],
    "s21": [fixed(cut("s21")[1], [GX, -1.5, 36], [GX, -1.5, 0], 40), fixed(END("s21"), [GX + 1, -1.2, 33], [GX, -1.5, 0], 40)],
    "s22": [fixed(cut("s22")[1], [GX + 3, -1, 34], [GX, -1.8, 0], 40), fixed(END("s22"), [GX - 2, -1.2, 35], [GX, -1.8, 0], 40)],
    "s23": [follow(cut("s23")[1], "jc", [-28, -30, 22], [0, -4, 4], 44, 0.1), follow(END("s23"), "jc", [-30, -28, 18], [0, -4, 4], 44, 0.1)],
    "s24": [fixed(cut("s24")[1], [PX + 2, 1, 40], [PX, 0, 0], 40), fixed(END("s24"), [PX - 1, 0.5, 37], [PX, 0, 0], 40)],
    "s25": [fixed(cut("s25")[1], [PX + 8, -2, 32], [PX + 6, -3, 0], 40), fixed(END("s25"), [PX + 10, -3, 30], [PX + 8, -4, 0], 40)],
    "s26": [follow(cut("s26")[1], "jt", [-2.4, 7.2, -1.2], [-0.5, 3.2, -0.3], 44, 0.08), follow(at("s26", word="three", offset=0.6), "jt", [-2.8, 8.4, -1.6], [-0.6, 3.6, -0.3], 46, 0.12),
            follow(END("s26"), "jt", [-8, 9, -4], [0, 2, 0], 46, 0.15)],
    "s27": [fixed(cut("s27")[1], [STU - 5, 3.4, -8.5], [STU, 1.9, -2.9], 34), fixed(END("s27"), [STU + 4, 3.8, -8.5], [STU, 2.0, -3.0], 34)],
    "s28": [fixed(cut("s28")[1], [DX, 420, 520], [DX, 0, 0], 42), fixed(END("s28"), [DX + 100, 380, 460], [DX, 0, 0], 42)],
    "s29": [follow(cut("s29")[1], "jt2", [-12, 5, -6], [0, 0, 0], 44, 0.15), follow(END("s29"), "jt2", [-14, 7, -2], [0, -1, 0], 44, 0.2)],
    "s30": [fixed(cut("s30")[1], [HX + 18, 11, 20], [HX, 0, 0], 40), fixed(END("s30"), [HX - 12, 10, 23], [HX, 0, 0], 40)],
    "s31": [fixed(cut("s31")[1], [TX + 260, 12, 330], [TX, 32, 0], 36), fixed(at("s31", word="Greenacres"), [TX + 255, 12, 325], [TX, 22, 0], 36, 0.1),
            fixed(END("s31"), [TX + 245, 12, 315], [TX, 26, 0], 36)],
    "s32": [fixed(cut("s32")[1], [TX + 180, 5, -200], [TX, 30, 0], 38), fixed(END("s32"), [TX + 170, 5, -190], [TX, 34, 0], 38)],
    "s33": [fixed(cut("s33")[1], [TX + 22, 16, 26], [TX, 0, 0], 40), fixed(END("s33"), [TX - 18, 14, 28], [TX, 0, 0], 40)],
    "s34": [fixed(cut("s34")[1], [TX + 120, 60, 150], [TX, 0, 0], 42), fixed(END("s34"), [TX + 70, 62, 170], [TX, 0, 0], 42)],
    "s35": [fixed(cut("s35")[1], [TX - 140, 55, -10], [TX - 50, 0, -70], 42), fixed(END("s35"), [TX - 120, 58, -40], [TX - 50, 0, -80], 42)],
    "s36": [fixed(cut("s36")[1], [TX + 160, 30, 220], [TX + 40, 4, 40], 40), fixed(END("s36"), [TX + 140, 34, 240], [TX + 40, 4, 40], 40)],
    "s37": [fixed(cut("s37")[1], [HX - 18, 9, 18], [HX, 0.5, 0], 40), fixed(END("s37"), [HX - 22, 8, -6], [HX, 0.5, 0], 40)],
    "s38": [fixed(cut("s38")[1], [LX + 3.6, 2.6, 4.4], [LX, 1.1, 0], 38), fixed(END("s38"), [LX - 2.6, 2.3, 4.8], [LX, 1.1, 0], 38)],
    "s39": [fixed(cut("s39")[1], [LX + 1.8, 1.6, 2.4], [LX, 1.0, 0], 38), fixed(END("s39"), [LX - 1.6, 1.5, 2.6], [LX, 1.0, 0], 38)],
    "s40": [follow(cut("s40")[1], "jr", [-8, 2, 6], [0, 0, 0], 40, 0.06), follow(END("s40"), "jr", [-6, 1.5, 10], [0, 0, 0], 40, 0.06)],
    "s41": [fixed(cut("s41")[1], [CBX - 40, 100, 200], [CBX - 60, 95, 60], 42), fixed(END("s41"), [CBX + 10, 100, 190], [CBX, 95, 60], 42)],
    "s42": [fixed(cut("s42")[1], [PX + 2, 1, 40], [PX, 0, 0], 40), fixed(END("s42"), [PX - 1, 0.5, 37], [PX, 0, 0], 40)],
    "s43": [fixed(cut("s43")[1], [PX - 2, 0.5, 36], [PX, 0, 0], 40), fixed(END("s43"), [PX - 3, 0.2, 34], [PX, 0, 0], 40)],
    "s44": [follow(cut("s44")[1], "jr", [-10, 3, 2], [0, 0, 0], 40, 0.05), follow(END("s44"), "jr", [-22, 6, -10], [0, 0, 0], 40, 0.04)],
    "s45": [fixed(cut("s45")[1], [TX + 200, 40, 260], [TX, 20, 0], 40), fixed(at("s45", 1.0, offset=0.6), [TX + 260, 70, 320], [TX, 40, 0], 40)],
}
CAMERA = []
for k, sid in enumerate(ORDER):
    CAMERA += SHOTS[sid]
    if k + 1 < len(ORDER):
        CAMERA.append({**SHOTS[sid][-1], "at": cut(ORDER[k + 1])[0]})
CAMERA[0] = {**CAMERA[0], "at": 0}

# ---------------------------------------------------------------- the map (built from a land mask)
BOUNDS = [-100.0, 22.0, -74.0, 32.0]
try:
    import numpy as np
    from global_land_mask import globe
    lat = np.linspace(BOUNDS[3], BOUNDS[1], 230)
    lon = np.linspace(BOUNDS[0], BOUNDS[2], 600)
    LO, LA = np.meshgrid(lon, lat)
    ROWS = ["".join("1" if v else "0" for v in r) for r in globe.is_land(LA, LO)]
except ImportError:   # the map stays blank rather than failing the build
    ROWS = ["0" * 600] * 230
AUS, GRN, ELE = (-97.67, 30.19), (-80.14, 26.62), (-76.68, 25.48)
ROUTE = [AUS, (-93.5, 29.3), (-88.5, 28.0), (-84.0, 27.0), GRN, (-78.6, 26.0), ELE]

# ---------------------------------------------------------------- objects
CLOUD_WINDOWS = [("s01", "s01"), ("s03", "s03"), ("s14", "s14"), ("s17", "s20"), ("s23", "s23"), ("s26", "s26"), ("s29", "s29"),
                 ("s40", "s40"), ("s44", "s44")]
JC_TRACK = [   # the main jet: s14 cruise, s17 ice, s18 climb, s19 to s20 the dive, s23 below the cloud
    {"at": at("s14", 0), "pos": [CRU, 100, 0], "rot": [2, 90, 0]},
    {"at": at("s14", 1.0), "pos": [CRU + V * 11, 100, 0], "rot": [2, 90, 0]},
    {"at": at("s17", 0), "pos": [CRU + V * 11, 100, 0], "rot": [2, 90, 0]},
    {"at": at("s18", 0), "pos": [CRU + V * 17, 100, 0], "rot": [2, 90, 0]},
    {"at": at("s18", word="climb"), "pos": [CRU + V * 20, 100, 0], "rot": [3, 90, 0]},
    {"at": at("s19", 0), "pos": [CRU + V * 24, 103, 0], "rot": [7, 90, 0]},
    {"at": at("s19", word="descending,"), "pos": [CRU + V * 26.5, 99, 0], "rot": [-14, 90, 8]},
    {"at": at("s20", 0), "pos": [CRU + V * 29, 88, 0], "rot": [-28, 90, 20]},
    {"at": at("s20", 1.0), "pos": [CRU + V * 33, 60, 0], "rot": [-45, 90, 34]},
    {"at": at("s23", 0), "pos": [CRU + V * 34, 50, 0], "rot": [-50, 90, 55]},
    {"at": at("s23", 1.0, offset=0.5), "pos": [CRU + V * 38, -40, 0], "rot": [-58, 90, 60]},
]
JC_SHOWN = [("s14", "s14"), ("s17", "s20"), ("s23", "s23")]


def town():
    objs = [
        {"type": "box", "pos": [TX, -1, 0], "w": 2400, "h": 1, "d": 2400, "color": "#6f7d5a"},
        {"type": "box", "pos": [TX, -0.95, 0], "w": 8, "h": 1.0, "d": 2000, "color": "#3b3e42"},
        *[{"type": "box", "pos": [TX, -0.96, z], "w": 2000, "h": 1.0, "d": 4, "color": "#44474b"} for z in (-240, -150, -60, 60, 150, 240)],
        {"type": "box", "pos": [TX + 45, -0.9, 95], "w": 46, "h": 1.0, "d": 46, "color": "#5f8f4a"},
        {"type": "box", "pos": [TX + 45, -0.85, 95], "w": 14, "h": 1.0, "d": 14, "color": "#b58a5a", "rot": 45},
        {"type": "box", "pos": [TX - 60, 0, -105], "w": 52, "h": 7, "d": 22, "color": "#d8cdb8"},
        {"type": "box", "pos": [TX - 78, 0, -80], "w": 18, "h": 7, "d": 34, "color": "#cfc4ae"},
        {"type": "town", "area": [TX + 60, -400, TX + 320, 400], "count": 220, "scale": 2.4, "seed": 3, "colors": ["#efe6d6", "#e8d9c4", "#f2efe8", "#d9e2e6", "#e9d6c8"]},
        {"type": "town", "area": [TX - 320, -400, TX - 10, 400], "count": 260, "scale": 2.4, "seed": 7, "colors": ["#efe6d6", "#e8d9c4", "#f2efe8", "#d9e2e6", "#e9d6c8"]},
        {"type": "trees", "area": [TX - 320, -400, TX + 320, 400], "count": 220, "scale": 1.7, "seed": 5},
    ]
    # the mobile home park beside the road: rows of long low homes
    for r in range(6):
        for c in range(9):
            objs.append({"type": "box", "pos": [TX + 12 + r * 7.5, 0, -40 + c * 8.5], "w": 3, "h": 2.2, "d": 6.5, "color": ["#e9e4da", "#dfe7ea", "#efe2cf"][(r + c) % 3]})
    return objs


DIVE_TOWN = {"type": "bizjet", "id": "jtown", "build": {"op": "slide", "offset": [0, 0, 0], "from": at("s31", 0), "to": at("s31", 0, offset=0.01)},
             "hide": {"at": at("s31", word="Greenacres", offset=0.02), "dur": 0.01},
             "track": [{"at": at("s31", 0), "pos": [TX - 75, 140, -20], "rot": [-62, 90, 38]}, {"at": at("s31", word="Greenacres"), "pos": [TX, 1, 0], "rot": [-66, 90, 44]}]}

WORLD = {
    "style": "night", "terrain": False, "far": 3000, "shadows": False,
    "env": envs,
    "lightning": [{"from": at(a, 0), "to": at(b, 1.0), "rate": 0.45, "seed": 3 + i, "strength": 0.55} for i, (a, b) in enumerate(CLOUD_WINDOWS)],
    "objects": [
        {"type": "clouds", "seed": 4, "layers": [{"y": [70, 140], "count": 170, "size": [8, 16], "from": at(a, 0), "to": at(b, 1.0, offset=0.05), "fade": 0.01} for a, b in CLOUD_WINDOWS]},
        {"type": "clouds", "seed": 8, "layers": [{"y": [10, 32], "count": 110, "size": [12, 24], "from": at("s06", 0), "to": at("s06", 1.0, offset=0.05), "fade": 0.01}]},
        {"type": "clouds", "seed": 12, "box": 420, "layers": [{"y": [70, 110], "count": 90, "size": [14, 26], "from": at(a, 0), "to": at(b, 1.0, offset=0.05), "fade": 0.01}
                                                            for a, b in (("s02", "s02"), ("s09", "s09"), ("s31", "s35"))]},
        *[{"type": "streaks", "follow": f, "from": at(a, 0), "to": at(b, 1.0), "count": 300, "box": [10, 7, 10], "dir": d, "speed": 45, "len": 1.0, "opacity": 0.4}
          for f, a, b, d in (("jo", "s01", "s01", [-1, -0.25, 0]), ("jc", "s14", "s14", [-1, -0.25, 0]), ("jc", "s17", "s18", [-1, -0.25, 0]),
                             ("jc", "s19", "s20", [-0.55, 1, 0]), ("jc", "s23", "s23", [-0.55, 1, 0]), ("jt", "s26", "s26", [-0.55, 1, 0]),
                             ("jt0", "s03", "s03", [-0.55, 1, 0]), ("jt2", "s29", "s29", [-0.55, 1, 0]), ("jr", "s40", "s40", [-1, -0.25, 0]), ("jr", "s44", "s44", [-1, -0.25, 0]))],
        # s01: the opening jet in the cloud, icing
        {"type": "bizjet", "id": "jo", **only("s01"), "ice": {"from": at("s01", 0), "to": at("s01", word="manageable.")},
         "track": [{"at": at("s01", 0), "pos": [OPEN, 100, 0], "rot": [2, 90, 0]}, {"at": at("s01", 1.0, offset=0.2), "pos": [OPEN + V * 11, 100, 0], "rot": [2, 90, 0]}],
         "wobble": [{"from": at("s01", 0), "to": at("s01", 1.0), "roll": 3, "pitch": 1.5, "freq": 0.6}]},
        # s03, s26, s29: the diving jet, seen from the tail (the elevator tears off in s03 and s26)
        {"type": "bizjet", "id": "jt0", **only("s03"), "elevator": {"at": at("s03", word="breaking")},
         "track": [{"at": at("s03", 0), "pos": [TAIL, 60, 0], "rot": [-55, 90, 30]}, {"at": at("s03", 1.0, offset=0.5), "pos": [TAIL + V * 9, -120, 0], "rot": [-60, 90, 40]}]},
        {"type": "bizjet", "id": "jt", **only("s26"), "elevator": {"at": at("s26", word="elevator,")},
         "track": [{"at": at("s26", 0), "pos": [TAIL + 2000, 60, 0], "rot": [-55, 90, 30]}, {"at": at("s26", 1.0, offset=0.5), "pos": [TAIL + 2000 + V * 10, -160, 0], "rot": [-60, 90, 40]}]},
        {"type": "bizjet", "id": "jt2", **only("s29"), "elevator": {"at": at("s29", 0.45)},
         "track": [{"at": at("s29", 0), "pos": [TAIL + 4000, 60, 0], "rot": [-55, 90, 30]}, {"at": at("s29", 1.0, offset=0.5), "pos": [TAIL + 4000 + V * 10, -160, 0], "rot": [-60, 90, 40]}]},
        {"type": "box", "pos": [TAIL + 2000, -400, 0], "w": 9000, "h": 1, "d": 5000, "color": "#4f5a48"},
        # s04 and s06: Austin, the take-off and the climb
        {"type": "box", "pos": [DEP, -1, 0], "w": 3000, "h": 1, "d": 3000, "color": "#8b8a5e"},
        {"type": "box", "pos": [DEP + 60, -0.94, 0], "w": 400, "h": 1, "d": 9, "color": "#3d4045"},
        *[{"type": "box", "pos": [DEP - 120 + k * 8, -0.9, 0], "w": 4, "h": 1, "d": 0.4, "color": "#e8e8e2"} for k in range(46)],
        {"type": "trees", "area": [DEP - 600, -600, DEP + 900, -30], "count": 140, "scale": 2.0, "seed": 9},
        {"type": "trees", "area": [DEP - 600, 30, DEP + 900, 600], "count": 140, "scale": 2.0, "seed": 10},
        {"type": "bizjet", "id": "jdep", "gear": True, **only("s04"),
         "track": [{"at": at("s04", 0), "pos": [DEP - 20, 0.75, 0], "rot": [0, 90, 0]},
                   {"at": at("s04", word="took"), "pos": [DEP + 8, 0.75, 0], "rot": [0, 90, 0]},
                   {"at": at("s04", word="took", offset=2.2), "pos": [DEP + 50, 2.6, 0], "rot": [9, 90, 0]},
                   {"at": at("s04", 1.0, offset=0.3), "pos": [DEP + 130, 16, 0], "rot": [11, 90, 0]}]},
        {"type": "bizjet", "id": "jd", **only("s06"),
         "track": [{"at": at("s06", 0), "pos": [DEP + 500, 58, 0], "rot": [8, 90, 0]}, {"at": at("s06", 1.0, offset=0.2), "pos": [DEP + 500 + V * 15, 80, 0], "rot": [8, 90, 0]}]},
        # s05 and s27: the studio
        {"type": "gridfloor", "pos": [STU, 0, 0], "size": 60, "div": 30},
        {"type": "bizjet", "pos": [STU, 0.75, 0], "rot": 35, "lights": False, "gear": True, **only("s05")},
        {"type": "bizjet", "pos": [STU, 0.75, 0], "rot": 0, "lights": False, "gear": True, "elev_color": "#ffc93c", **only("s27")},
        # the main jet
        {"type": "bizjet", "id": "jc", "ice": {"from": at("s14", word="ice"), "to": at("s17", word="handling")}, "track": JC_TRACK,
         "build": {"op": "slide", "offset": [0, 0, 0], "from": at("s14", 0), "to": at("s14", 0, offset=0.01)}, "hide": {"at": at("s23", 1.0, offset=0.02), "dur": 0.01},
         "wobble": [{"from": at("s14", 0), "to": at("s19", 0.4), "roll": 4, "pitch": 2, "freq": 0.55}, {"from": at("s19", 0.4), "to": at("s23", 1.0), "roll": 6, "pitch": 3, "freq": 0.8}]},
        {"type": "box", "pos": [CRU + 500, -400, 0], "w": 5000, "h": 1, "d": 5000, "color": "#4f5a48"},
        # s07, s08, s10: the map
        {"type": "mapboard", "pos": [MAPX, 0, 0], "bounds": BOUNDS, "rows": ROWS, "size": [232, 100], "line_w": 0.45, "marker_size": 5,
         "pins": [{"lon": AUS[0], "lat": AUS[1], "label": "Austin"}, {"lon": GRN[0], "lat": GRN[1], "label": "Greenacres", "color": "#ff5252", "dx": -120, "dy": -62},
                  {"lon": ELE[0], "lat": ELE[1], "label": "North Eleuthera", "dx": 14, "dy": 48}, {"lon": -80.2, "lat": 25.77, "label": "Miami", "color": "#9fb4c8", "size": 26, "dx": -110, "dy": 30}],
         "route": ROUTE, "reveal": [{"at": at("s07", 0), "p": 0}, {"at": at("s07", 1.0), "p": 0.78}],
         "marker": [{"at": at("s07", 0), "p": 0}, {"at": at("s07", 1.0), "p": 0.78}],
         "storms": [{"lon": -80.4, "lat": 26.7, "r": 0.9}, {"lon": -81.2, "lat": 26.1, "r": 0.6}, {"lon": -80.0, "lat": 27.4, "r": 0.5}],
         "storm_op": [{"at": at("s08", 0), "o": 0}, {"at": at("s08", word="Heavy"), "o": 0.9}], "seed": 9},
        # s09, s02, s31 to s36, s45: Greenacres
        *town(),
        {"type": "blast", "pos": [TX, 0.5, 0], "at": at("s31", word="Greenacres"), "size": 2.4, "burn": 12, "seed": 4},
        {"type": "blast", "pos": [TX, 0.5, 0], "at": at("s02", 0, offset=-1.0), "size": 2.0, "burn": 9, "seed": 5},
        {"type": "crater", "pos": [TX, 0, 0], "r": 3, "water": True, **only("s33", "s35")},
        {"type": "wreckage", "pos": [TX, 0, 0], "spread": 80, "count": 110, "size": 0.7, "seed": 23, **only("s33", "s35")},
        {"type": "pole", "pos": [TX + 6, 0, 3], "h": 12, "lean": 18, **only("s33")},
        DIVE_TOWN,
        # s11, s12, s41: the thunderstorm explainer
        {"type": "box", "pos": [CBX, -1, 0], "w": 3000, "h": 1, "d": 3000, "color": "#4c5848"},
        {"type": "cumulus", "pos": [CBX, 0, 0], "h": 170, "r": 42, "seed": 6},
        {"type": "flow", "from": [CBX - 34, 10, 62], "to": [CBX - 34, 150, 62], "color": "#ff6a4a", "size": 5, "count": 7, "speed": 0.3,
         "op": [{"at": at("s11", 0), "o": 0}, {"at": at("s11", word="updrafts"), "o": 0.95}, {"at": at("s11", 1.0), "o": 0.95}, {"at": at("s11", 1.0, offset=0.02), "o": 0}]},
        {"type": "flow", "from": [CBX + 34, 140, 62], "to": [CBX + 34, 10, 62], "color": "#4aa8ff", "size": 5, "count": 7, "speed": 0.3,
         "op": [{"at": at("s11", 0), "o": 0}, {"at": at("s11", word="downdrafts"), "o": 0.95}, {"at": at("s11", 1.0), "o": 0.95}, {"at": at("s11", 1.0, offset=0.02), "o": 0}]},
        {"type": "ring", "pos": [CBX, 0, 0], "r": 150, "w": 3, "op": [{"at": at("s12", 0), "o": 0}, {"at": at("s12", word="20"), "o": 0.9}, {"at": at("s12", 1.0), "o": 0.9}, {"at": at("s12", 1.0, offset=0.02), "o": 0}]},
        {"type": "bizjet", "id": "jcb", "scale": 2.2, **only("s41"),
         "track": [{"at": at("s41", 0), "pos": [CBX - 150, 95, 60], "rot": [0, 90, 0]}, {"at": at("s41", 1.0, offset=0.3), "pos": [CBX + 40, 95, 60], "rot": [0, 90, 0]}]},
        # s13, s15, s16: the wing section in a stream of droplets
        {"type": "gridfloor", "pos": [AFX, -4, 0], "size": 80, "div": 40},
        {"type": "airfoil", "pos": [AFX, 0, 0], "chord": 10, "span": 6, "drops": 170,
         "ice": [{"at": at("s13", 0), "i": 0}, {"at": at("s13", word="freeze."), "i": 0.12}, {"at": at("s15", 0), "i": 0.15}, {"at": at("s15", 1.0), "i": 0.7},
                 {"at": at("s16", 0), "i": 0.7}, {"at": at("s16", 1.0), "i": 1.0}],
         "flow": [{"at": 0, "f": 1}]},
        # s21, s22: the speed gauge
        {"type": "gauge", "pos": [GX, 0, 0], "size": 9, "red": 0.8, "label": "AIRSPEED",
         "value": [{"at": at("s21", 0), "v": 0.62}, {"at": at("s21", word="overspeed"), "v": 0.78}, {"at": at("s21", 1.0), "v": 0.93},
                   {"at": at("s22", 0), "v": 0.55}, {"at": at("s22", word="maximum"), "v": 0.79}, {"at": at("s22", word="Overspeed"), "v": 0.9}, {"at": at("s22", 1.0), "v": 0.92}]},
        # s24, s25, s42, s43: the altitude chart and the timeline panel
        {"type": "plot", "pos": [PX, 0, 0], "w": 40, "h": 22, "xlabel": "time (illustrative)",
         "yticks": [{"v": 0, "label": "0"}, {"v": 0.25, "label": "10,000 ft"}, {"v": 0.5, "label": "20,000 ft"}, {"v": 0.75, "label": "30,000 ft"}, {"v": 1.0, "label": "40,000 ft"}],
         "data": [[0, 0.875], [0.2, 0.89], [0.3, 0.86], [0.4, 0.885], [0.5, 0.88], [0.56, 0.885], [0.6, 0.88], [0.86, 0.22], [0.95, 0.0]],
         "reveal": [{"at": at("s24", 0), "p": 0}, {"at": at("s24", word="falling"), "p": 0.6}, {"at": at("s24", word="minute."), "p": 0.9},
                    {"at": at("s25", 0), "p": 1}], **only("s24", "s25")},
        {"type": "plot", "pos": [PX, 0, 0], "w": 40, "h": 22, "xlabel": "", "yticks": [],
         "xticks": [{"v": 0.0, "label": "1 Nov: crash", "align": "left"}, {"v": 0.12, "label": "~early Dec: preliminary report", "align": "left", "row": 1}, {"v": 1.0, "label": "1 to 2 years: final report", "align": "right"}],
         "data": [[0, 0.45], [0.12, 0.45], [1, 0.45]], "color": "#7fd0ff", "line_w": 0.35,
         "reveal": [{"at": at("s42", 0), "p": 0}, {"at": at("s42", word="December."), "p": 0.12}, {"at": at("s43", 0), "p": 0.12}, {"at": at("s43", 1.0), "p": 1}], **only("s42", "s43")},
        # s28: the distances, as rings around the impact point (the direction has not been published)
        {"type": "gridfloor", "pos": [DX, 0, 0], "size": 1200, "div": 24, "color": "#141a22", "line": "#2a3442"},
        {"type": "ring", "pos": [DX, 0, 0], "r": 105, "w": 3, "color": "#ffd54a", "op": [{"at": at("s28", 0), "o": 0}, {"at": at("s28", 0.15), "o": 0.95}]},
        {"type": "ring", "pos": [DX, 0, 0], "r": 306, "w": 4, "color": "#ffd54a", "op": [{"at": at("s28", 0), "o": 0}, {"at": at("s28", 0.3), "o": 0.95}]},
        {"type": "ring", "pos": [DX, 0, 0], "r": 8, "w": 8, "color": "#ff5252", "op": [{"at": 0, "o": 1}]},
        # s30, s37: the hangar layout of recovered wreckage, with investigators
        {"type": "gridfloor", "pos": [HX, 0, 0], "size": 70, "div": 35},
        {"type": "wreckage", "pos": [HX, 0, 0], "spread": 14, "count": 70, "size": 1.2, "seed": 31},
        *[{"type": "person", "pos": [HX + dx, 0, dz], "scale": 1.8, "turban": False, "cloth": "#22324a", "top": "#1d2b40", "skin": "#c99a76", "rot": r}
          for dx, dz, r in ((-12, 6, 60), (10, -8, 200), (4, 13, 150), (-6, -12, 320))],
        # s38, s39: the recorder on the lab bench
        {"type": "gridfloor", "pos": [LX, -0.01, 0], "size": 40, "div": 20},
        {"type": "box", "pos": [LX, 0, 0], "w": 3.2, "h": 0.9, "d": 2.0, "color": "#3a3f47"},
        {"type": "recorder", "pos": [LX, 0.9, 0], "scale": 2.6, "rot": 30},
        # s40, s44: the jet in the cloud again
        {"type": "bizjet", "id": "jr", "ice": {"from": at("s40", 0), "to": at("s40", 0.5)},
         "build": {"op": "slide", "offset": [0, 0, 0], "from": at("s40", 0), "to": at("s40", 0, offset=0.01)}, "hide": {"at": at("s44", 1.0, offset=0.02), "dur": 0.01},
         "track": [{"at": at("s40", 0), "pos": [RPL, 100, 0], "rot": [2, 90, 0]}, {"at": at("s44", 1.0, offset=1), "pos": [RPL + V * 60, 100, 0], "rot": [2, 90, 0]}],
         "wobble": [{"from": at("s40", 0), "to": at("s44", 1.0), "roll": 3, "pitch": 1.5, "freq": 0.5}]},
    ],
    "camera": CAMERA,
}

BASE = {
    "language": "en", "voice": "bm_george", "speed": 1.04, "aspect": "16:9", "fps": 60, "made_for_kids": False,
    "category": "education", "footage": "off", "transition": "none",
    "music": {"mood": "mystery", "volume": 0.07},
    "captions": {"style": "karaoke", "y": 0.9, "size": 0.026, "max_words": 7, "highlight": "#ffd54a",
                 "box": "#000000", "box_alpha": 0.45, "uppercase": False},
    "overlay": {"handle": "@hypercurious96", "progress_bar": False},
    "world3d": WORLD,
}

if __name__ == "__main__":
    build(HERE, [("ch01", "Learjet 60, Greenacres", SCENES)], BASE, "The Learjet 60 crash: everything we know so far", seed=18)
    with open(os.path.join(HERE, "chapters.json"), "w") as f:
        json.dump(CHAPTER_STARTS, f)
