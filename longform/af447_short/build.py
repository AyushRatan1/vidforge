"""Builds the 9:16 Short "Air France 447: what really happened" (English, about 80 seconds) as ch01.json.

    python longform/af447_short/build.py

Facts: BEA final report (5 July 2012) as summarised by Wikipedia; Paris Court of Appeal verdict of 21 May 2026
(Al Jazeera). Footage is illustrative stock (Pexels, Pixabay), pinned by id from the candidate sheets.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from kit import S, build  # noqa: E402

PICK = {  # name -> "pexels:<id>" / "pixabay:<id>" (clip) or int (Pixabay still), from the candidate sheets
    "plane_night": "pixabay:142647", "storm": "pixabay:16160", "pitot_ice": 4765504, "cockpit": "pixabay:51016",
    "alarm": "pixabay:242", "ocean_dark": "pixabay:212057", "search_ship": "pixabay:170300", "deep_sea": "pixabay:13823",
    "verdict": "pixabay:34258", "training": "pixabay:51021", "court": "pixabay:162047", "ending": "pixabay:88270",
}
FALLBACK = {"type": "gradient", "colors": ["#141b26", "#06090e"]}


def V(name, dim=0.25, move="in"):
    ref = PICK[name]
    if isinstance(ref, int):
        return {"type": "footage", "image_id": ref, "move": move, "dim": dim, "fallback": FALLBACK}
    return {"type": "footage", "video": ref, "dim": dim, "fallback": FALLBACK}


def T(text, at_word=None, y=0.16, until=None):
    el = {"type": "text", "text": text, "x": 0.5, "y": y, "size": 0.052, "color": "#ffffff", "bg": "#c62828",
          "style": "label", "stroke": False, "enter": "pop"}
    if at_word:
        el["at_word"] = at_word
    else:
        el["at"] = 0.2
    if until:
        el["until"] = until
    return el


SCENES = [
    S("In 2009, a jet carrying 228 people vanished over the Atlantic. The answer was hiding four kilometres under the sea.",
      V("plane_night"), T("Air France 447", y=0.16), T("1 June 2009", y=0.23)),
    S("Air France 447, Rio to Paris. After midnight it flies into a wall of storms, and the captain goes for his rest break.",
      V("storm")),
    S("Ice crystals block the pitot tubes, the probes that measure speed. The readings go haywire, and the autopilot switches off.",
      V("pitot_ice"), T("Pitot tubes iced", at_word="pitot")),
    S("The co-pilot takes manual control and pulls the nose up. The jet climbs, loses speed, and stalls.",
      V("cockpit"), T("STALL", at_word="stalls.")),
    S("The stall alarm blares. But when the plane got too slow, the computer ignored its own data and went quiet. Pushing the nose down, the right move, made the alarm come back.",
      V("alarm")),
    S("The captain rushes back, but it is too late. For three and a half minutes the jet falls, nose up, and hits the ocean. No one survives.",
      V("ocean_dark"), T("3 min 30 s", at_word="three")),
    S("Wreckage is found within days. The black boxes are not.",
      V("search_ship")),
    S("Then in April 2011, a sonar search finds the wreck almost four kilometres down. Both recorders still work.",
      V("deep_sea"), T("3,980 m deep", at_word="four")),
    S("The verdict: frozen sensors, a confusing alarm, and pilots never trained to fly by hand up there.",
      V("verdict")),
    S("The sensors were replaced, and pilots now train for exactly this kind of stall.",
      V("training")),
    S("And in May 2026, a Paris court found Airbus and Air France guilty of manslaughter. Airbus plans to appeal.",
      V("court"), T("Guilty, 21 May 2026", at_word="guilty")),
    S("Follow for more true stories.",
      V("ending")),
]

BASE = {
    "language": "en", "voice": "bm_george", "speed": 1.08, "aspect": "9:16", "made_for_kids": False,
    "footage": "auto", "transition": "fade",
    "music": {"mood": "mystery", "volume": 0.1},
    "captions": {"style": "karaoke", "y": 0.6, "size": 0.084, "max_words": 2, "highlight": "#ffd54a",
                 "uppercase": False},
    "overlay": {"handle": "@hypercurious96", "progress_bar": False},
}

if __name__ == "__main__":
    build(HERE, [("ch01", "Air France 447", SCENES)], BASE, "Air France 447: what really happened", seed=447)
