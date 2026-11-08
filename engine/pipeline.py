"""Episode spec -> finished MP4 (+ thumbnail, QA stills, manifest). CPU only, no paid APIs."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import subprocess
import time

import numpy as np
import soundfile as sf

from . import audio as A
from .renderer import Renderer

ASPECTS = {"9:16": (1080, 1920), "16:9": (1920, 1080), "1:1": (1080, 1080), "4:5": (1080, 1350)}


def normalize(spec: dict) -> dict:
    s = copy.deepcopy(spec)
    s.setdefault("fps", 30)
    s["fps"] = int(s["fps"])
    W, H = ASPECTS.get(s.get("aspect", "9:16"), ASPECTS["9:16"])
    if s.get("preview"):
        W, H = W // 2, H // 2
    s["_W"], s["_H"] = W, H
    s.setdefault("voice", "hm_omega")
    s.setdefault("speed", 1.0)
    s.setdefault("transition", "fade")
    s.setdefault("music", {"mood": "cosmic"})
    scenes = s.get("scenes") or []
    if not scenes:
        raise ValueError("spec has no scenes")
    for k, sc in enumerate(scenes):
        sc.setdefault("id", f"s{k + 1}")
        sc.setdefault("elements", [])
        for j, el in enumerate(sc["elements"]):
            el.setdefault("id", f"{sc['id']}_e{j}")
    return s


def _place(buf, sig, start_s):
    a = int(start_s * A.SR)
    if a >= len(buf) or len(sig) == 0:
        return
    b = min(len(buf), a + len(sig))
    buf[a:b] += sig[: b - a]


def build_timeline(spec: dict, voices: list) -> list:
    fps = spec["fps"]
    tl, frame = [], 0
    for k, (sc, v) in enumerate(zip(spec["scenes"], voices)):
        lead = float(sc.get("lead", 0.12 if k == 0 else 0.3))
        tail = float(sc.get("tail", 0.4))
        vdur = len(v) / A.SR
        dur = max(float(sc.get("min_duration", 2.0)), lead + vdur + tail) + float(sc.get("hold", 0))
        n = int(round(dur * fps))
        tl.append({"start_frame": frame, "frames": n, "dur": n / fps, "start": frame / fps,
                   "voice_start": lead, "voice_dur": vdur})
        frame += n
    return tl


def word_time(narration: str, word: str, voice_start: float, voice_dur: float) -> float | None:
    """Estimate when `word` is spoken (same proportional model the captions use)."""
    words = (narration or "").split()
    if not words or not word:
        return None
    weights = [len(w) + 2 for w in words]
    total = sum(weights)
    acc = 0
    target = word.strip().lower()
    for w, wt in zip(words, weights):
        if target in w.lower() or w.lower().strip(".,!?।:;") == target:
            return voice_start + voice_dur * acc / total
        acc += wt
    # multi-word phrases
    joined = " ".join(words).lower()
    idx = joined.find(target)
    if idx >= 0:
        before = len(joined[:idx].split())
        acc = sum(weights[:before])
        return voice_start + voice_dur * acc / total
    return None


def resolve_word_cues(spec: dict, tl: list):
    """Elements may use `at_word` (and optional `at_offset`) instead of a numeric `at`."""
    for sc, seg in zip(spec["scenes"], tl):
        cue_text = sc.get("narration", "")
        cap = sc.get("caption")
        for el in sc.get("elements", []):
            w = el.get("at_word")
            if not w:
                continue
            t = word_time(cue_text, w, seg["voice_start"], seg["voice_dur"])
            if t is None and cap:
                t = word_time(cap, w, seg["voice_start"], seg["voice_dur"])
            if t is not None:
                el["at"] = max(0.0, t + float(el.get("at_offset", -0.1)))


def resolve_footage(spec: dict, tl: list, out_dir: str) -> list:
    """For every scene whose background is {"type": "footage"}: search, pick, download and cut a stock clip to
    the canvas size and scene length (<out>/footage_<i>.mp4). Anything that fails (no key, no results, download
    or ffmpeg error, spec "footage": "off") swaps the background for its `fallback` so rendering never fails.
    Returns the records for the manifest: [{"scene", "provider", "id", "credit", "page_url"}]."""
    from . import footage as F
    W, H, fps = spec["_W"], spec["_H"], spec["fps"]
    mode = spec.get("footage", "auto") or "auto"
    orientation = "landscape" if W > H else ("square" if W == H else "portrait")
    used, records, cache = set(), [], {}
    for i, (sc, seg) in enumerate(zip(spec["scenes"], tl)):
        bg = sc.get("background") or {}
        if bg.get("type") != "footage":
            continue
        fallback = bg.get("fallback") or dict(F.DEFAULT_FALLBACK)
        if fallback.get("type") == "footage":
            fallback = dict(F.DEFAULT_FALLBACK)
        bg.pop("_file", None)
        bg.pop("_clip", None)
        bg.pop("_last_frame", None)
        prepared = None
        clip = None
        if mode != "off":
            query = str(bg.get("query", "")).strip()
            if query not in cache:
                cache[query] = F.search(query, orientation=orientation)
            clip = F.pick(cache[query], seg["dur"], exclude=used, query=query + f"#{i}")
            if clip:
                src = F.fetch(clip)
                if src:
                    try:
                        dst = os.path.join(out_dir, f"footage_{i + 1:02d}.mp4")
                        prepared = F.prepare(src, dst, W, H, seg["dur"] + 0.5, fps,
                                             start=float(bg.get("start", 0) or 0), speed=float(bg.get("speed", 1) or 1))
                    except Exception as e:  # corrupt download, odd codec: fall back
                        F.log.warning("footage prepare failed for scene %d: %s", i + 1, e)
                        prepared = None
        if prepared is None or clip is None:
            sc["background"] = fallback
            continue
        used.add(clip["id"])
        bg["_file"] = prepared
        bg["_clip"] = f"{clip['provider']}_{clip['id']}"
        bg["_last_frame"] = F.extract_frame(prepared, max(0.0, seg["dur"] - 1.0 / fps), prepared[:-4] + "_last.png")
        records.append({"scene": i, "provider": clip["provider"], "id": clip["id"], "credit": clip.get("credit"),
                        "page_url": clip.get("page_url")})
    return records


def _engine_version() -> str:
    h = hashlib.sha1()
    here = os.path.dirname(os.path.abspath(__file__))
    for name in sorted(os.listdir(here)):
        if name.endswith(".py"):
            with open(os.path.join(here, name), "rb") as f:
                h.update(f.read())
    return h.hexdigest()[:10]


ENGINE_VERSION = _engine_version()


def _scene_key(spec, i, tl, voice):
    prev = spec["scenes"][i - 1] if i > 0 else None
    blob = json.dumps({
        "engine": ENGINE_VERSION,
        "scene": spec["scenes"][i], "prev": prev, "seg": tl[i], "prevseg": tl[i - 1] if i else None,
        "W": spec["_W"], "H": spec["_H"], "fps": spec["fps"], "cap": spec.get("captions"),
        "ov": spec.get("overlay"), "tr": spec.get("transition"), "bg": spec.get("background"),
        "total": sum(s["frames"] for s in tl), "v": hashlib.sha1(voice.tobytes()).hexdigest(),
        "clip": (spec["scenes"][i].get("background") or {}).get("_clip"),
    }, sort_keys=True, default=str)
    return hashlib.sha1(blob.encode()).hexdigest()[:16]


def render_episode(spec: dict, out_dir: str, progress=None, stills_only: bool = False) -> dict:
    """Render a spec. Returns paths and stats. `progress(stage, frac)` is optional."""
    t0 = time.time()
    p = progress or (lambda stage, frac: None)
    spec = normalize(spec)
    os.makedirs(out_dir, exist_ok=True)
    work = os.path.join(out_dir, "work")
    os.makedirs(work, exist_ok=True)

    # 1. voice
    voices = []
    for k, sc in enumerate(spec["scenes"]):
        p("voice", k / len(spec["scenes"]))
        voices.append(A.tts(sc.get("narration", ""), sc.get("voice", spec["voice"]), float(sc.get("speed", spec["speed"])),
                            sc.get("lang", spec.get("lang"))))
    tl = build_timeline(spec, voices)
    resolve_word_cues(spec, tl)
    p("footage", 0)
    footage = resolve_footage(spec, tl, out_dir)
    total_frames = sum(s["frames"] for s in tl)
    duration = total_frames / spec["fps"]

    # 2. audio bed
    p("audio", 0)
    vtrack = np.zeros(int(duration * A.SR) + A.SR, dtype=np.float32)
    for sc, seg, v in zip(spec["scenes"], tl, voices):
        _place(vtrack, v, seg["start"] + seg["voice_start"])
        for fx in sc.get("sfx", []) or []:
            name, at = (fx, 0.0) if isinstance(fx, str) else (fx.get("kind"), float(fx.get("at", 0)))
            _place(vtrack, A.sfx(name) * 0.6, seg["start"] + at)
        for el in sc.get("elements", []) or []:  # element-level sound on entrance, e.g. a pop per balloon
            if el.get("sfx"):
                _place(vtrack, A.sfx(el["sfx"]) * 0.45, seg["start"] + float(el.get("at", 0)))
    mus = spec.get("music") or {}
    if mus.get("file") and os.path.exists(mus["file"]):
        bed = A.load_music_file(mus["file"], duration + 1)
    elif mus.get("mood", "cosmic") != "none":
        bed = A.music(mus.get("mood", "cosmic"), duration + 1, seed=int(mus.get("seed", 7)))
    else:
        bed = np.zeros_like(vtrack)
    mixed = A.mixdown(vtrack, bed, duck=float(mus.get("duck", 0.6)), music_gain=float(mus.get("volume", 0.18)))
    mixed = mixed[: int(duration * A.SR)]
    wav = os.path.join(work, "mix.wav")
    sf.write(wav, mixed, A.SR)
    amp = A.envelope(vtrack, spec["fps"], total_frames)

    rnd = Renderer(spec, tl, amp)

    # 3. QA stills + thumbnail
    stills = []
    for i, seg in enumerate(tl):
        for frac in (0.18, 0.62):
            path = os.path.join(out_dir, f"still_{i + 1:02d}_{int(frac * 100)}.jpg")
            rnd.still(i, seg["dur"] * frac, path)
            stills.append(path)
    th = spec.get("thumbnail") or {"scene": 0, "t": 1.4}
    thumb = os.path.join(out_dir, "thumbnail.jpg")
    rnd.still(min(int(th.get("scene", 0)), len(tl) - 1), float(th.get("t", 1.4)), thumb)
    if stills_only:
        return {"stills": stills, "thumbnail": thumb, "duration": duration, "timeline": tl, "footage": footage}

    # 4. scenes (cached by content hash so editing one scene only re-renders it; parallel on multi-core machines)
    files, todo = [], []
    for i in range(len(tl)):
        key = _scene_key(spec, i, tl, voices[i])
        path = os.path.join(work, f"scene_{i + 1:02d}_{key}.mp4")
        files.append(path)
        if not os.path.exists(path):
            todo.append((i, path))
    workers = render_workers(len(todo))
    if workers <= 1:
        for k, (i, path) in enumerate(todo):
            p("render", k / max(1, len(todo)))
            rnd.encode_scene(i, path)
    else:
        import multiprocessing as mp
        from concurrent.futures import ProcessPoolExecutor, as_completed
        ctx = mp.get_context("fork")
        threads = max(1, (os.cpu_count() or 2) // workers)
        with ProcessPoolExecutor(workers, mp_context=ctx, initializer=_init_worker, initargs=(spec, tl, amp)) as ex:
            futs = [ex.submit(_encode_worker, i, path, threads) for i, path in todo]
            for k, f in enumerate(as_completed(futs)):
                f.result()
                p("render", (k + 1) / len(todo))

    # 5. concat + mux
    p("assemble", 0)
    lst = os.path.join(work, "concat.txt")
    with open(lst, "w") as f:
        for fp in files:
            f.write(f"file '{os.path.abspath(fp)}'\n")
    silent = os.path.join(work, "video.mp4")
    _ff(["-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent + ".part.mp4"])
    os.replace(silent + ".part.mp4", silent)
    final = os.path.join(out_dir, spec.get("output_name", "final.mp4"))
    _ff(["-i", silent, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
         "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000", "-c:a", "aac", "-b:a", "192k",
         "-shortest", "-movflags", "+faststart", final + ".part.mp4"])
    os.replace(final + ".part.mp4", final)
    p("done", 1)
    manifest = {
        "video": final, "thumbnail": thumb, "stills": stills, "duration": round(duration, 2),
        "size": f"{spec['_W']}x{spec['_H']}", "fps": spec["fps"], "scenes": len(tl),
        "render_seconds": round(time.time() - t0, 1), "title": spec.get("title"), "footage": footage,
    }
    with open(os.path.join(out_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    return manifest


def render_workers(n_scenes: int) -> int:
    """Parallel scene renders: one Python drawer per spare core (env VIDFORGE_WORKERS overrides)."""
    env = os.environ.get("VIDFORGE_WORKERS")
    if env:
        return max(1, min(int(env), n_scenes))
    cores = os.cpu_count() or 2
    return max(1, min(n_scenes, cores - 1 if cores > 2 else 1, 6))


_W = {}


def _init_worker(spec, tl, amp):
    _W["r"] = Renderer(spec, tl, amp)


def _encode_worker(i, path, threads):
    _W["r"].encode_scene(i, path, threads=threads)
    return path


def _ff(args):
    cmd = ["ffmpeg", "-y", "-loglevel", "error"] + args
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {' '.join(cmd)}\n{r.stderr[-2000:]}")


def clean_work(out_dir: str):
    shutil.rmtree(os.path.join(out_dir, "work"), ignore_errors=True)
