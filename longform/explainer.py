"""The explainer look for Shorts and Reels (November 2026), modelled on the 3D explainers that reach 500K to 1M views:

- 35 to 50 seconds, about 100 to 130 words, and a new shot every 2.5 to 3.5 seconds;
- the first line is a statement that makes the viewer need the answer ("Nobody has ever caught...");
- plain white captions with a soft shadow, three or four words at a time, low in the frame;
- a small dark context chip at the top of every shot (where a number comes from, "Simplified, not to scale");
- small pill tags pinned to the objects themselves ("212 GB", "waterline");
- physically based materials lit by an HDRI, a photographic sky behind daylight shots;
- a swish on every cut and a hit on the big numbers.

Build scripts import CAPTIONS, SOUND, LOOK, CHIP, TAG and shots() from here.
"""

CAPTIONS = {"style": "clean", "y": 0.73, "size": 0.064, "max_words": 4, "width": 0.86, "uppercase": False}
SOUND = {"cuts": "swish", "cut_gain": 0.3, "pops": 0.12}
LOOK = {"pbr": True, "tone": "aces", "soft": 3}


def at(scene, t=None, word=None, offset=0.0):
    ref = {"scene": scene}
    if word:
        ref["word"] = word
    elif t is not None:
        ref["t"] = t
    if offset:
        ref["offset"] = offset
    return ref


def CHIP(text, at_time=0.05, until=None, y=0.1):
    """The small dark context chip at the top of the frame."""
    el = {"type": "text", "text": text, "x": 0.5, "y": y, "size": 0.03, "color": "#ffffff", "bg": "#14181f",
          "bg_alpha": 0.82, "style": "label", "stroke": False, "enter": "fade", "at": at_time}
    if until is not None:
        el["until"] = until
    return el


def BIG(text, at_word=None, y=0.2, color="#ffffff", size=0.07, at_time=None):
    """A large number or phrase in the upper third (no box), for the one fact a shot is about."""
    el = {"type": "text", "text": text, "x": 0.5, "y": y, "size": size, "color": color, "style": "title",
          "stroke": False, "shadow": True, "enter": "pop"}
    if at_word:
        el["at_word"] = at_word
    else:
        el["at"] = 0.15 if at_time is None else at_time
    return el


def TAG(text, pos=None, follow=None, show=None, offset=None, **kw):
    """A pill label pinned to a point (or to an object id) in the 3D world, shown during the given windows."""
    o = {"type": "tag", "text": text}
    if pos is not None:
        o["pos"] = pos
    if follow is not None:
        o["follow"] = follow
    if offset is not None:
        o["offset"] = offset
    if show is not None:
        o["show"] = show
    o.update(kw)
    return o


def shots(sid, plan, next_sid=None):
    """Camera keys for one scene cut into shots. plan = [(start, pos0, look0, pos1, look1, fov), ...] where start is a
    fraction of the scene (0 for the first shot) or a word; each shot moves from (pos0, look0) to (pos1, look1) and the
    next shot starts with a hard cut. The last shot holds until the next scene's cut."""
    keys = []
    for k, (start, p0, l0, p1, l1, fov) in enumerate(plan):
        t0 = at(sid, 0) if k == 0 else (at(sid, word=start) if isinstance(start, str) else at(sid, start))
        if k + 1 < len(plan):
            nxt = plan[k + 1][0]
            t1 = at(sid, word=nxt, offset=-0.012) if isinstance(nxt, str) else at(sid, nxt, offset=-0.012)
        else:
            t1 = at(next_sid, 0, offset=-0.012) if next_sid else at(sid, 1.0, offset=0.6)
        keys.append({"at": t0, "pos": p0, "look": l0, "fov": fov})
        keys.append({"at": t1, "pos": p1, "look": l1, "fov": fov})
    return keys
