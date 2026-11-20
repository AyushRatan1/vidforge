"""Stream clipper: find the best moments in a long gameplay/stream recording and cut them into vertical Shorts/Reels.

    python clipper/clip.py analyze  VIDEO OUTDIR            # transcript.json + candidates.json (ranked moments)
    python clipper/clip.py render   VIDEO PLAN.json OUTDIR  # one 1080x1920 MP4 per planned clip

Analysis: speech-to-text runs offline (Whisper base.en via sherpa-onnx, cut into phrases by Silero VAD), and every
second gets an excitement score from loudness spikes over the local baseline, shouting (energy above the speech band),
exclamations in the transcript and visual action (scene-change rate). Windows of 15 to 45 seconds are ranked and the
best non-overlapping ones become candidates, snapped to phrase boundaries so clips start and end on whole sentences.

Rendering (per plan entry {name, start, end, hook, layout?, overlay?, ad?}): a vertical layout (the streamer's facecam
on top and the gameplay below when a facecam is found, otherwise the gameplay over a blurred copy of itself),
word-by-word captions with the spoken word highlighted, a hook banner for the first seconds, a clear "#ad" disclosure
at the start (clipping campaigns require it), and an optional campaign overlay image.
"""
from __future__ import annotations

import json
import math
import os
import re
import subprocess
import sys
import tempfile

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS = os.environ.get("CLIPPER_MODELS", "/home/claude/work/clipper/models")
W, H, FPS = 1080, 1920, 30


def run(cmd):
    subprocess.run(cmd, check=True)


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,r_frame_rate:format=duration", "-of", "json", path],
                         check=True, capture_output=True, text=True).stdout
    j = json.loads(out)
    st = j["streams"][0]
    num, den = (st.get("r_frame_rate") or "30/1").split("/")
    return {"w": int(st["width"]), "h": int(st["height"]), "fps": float(num) / float(den or 1),
            "dur": float(j["format"]["duration"])}


# ------------------------------------------------------------------------------------------------ transcription
def load_audio(video, sr=16000):
    with tempfile.TemporaryDirectory() as d:
        wav = os.path.join(d, "a.wav")
        run(["ffmpeg", "-v", "error", "-y", "-i", video, "-vn", "-ac", "1", "-ar", str(sr), wav])
        a, _ = sf.read(wav, dtype="float32")
    return a, sr


def transcribe(audio, sr, size="base", t_offset=0.0):
    """size "base" for scanning whole chunks, "small" (slower, much better on noisy streams) for the clips' captions."""
    import sherpa_onnx
    d = os.path.join(MODELS, f"sherpa-onnx-whisper-{size}.en")
    rec = sherpa_onnx.OfflineRecognizer.from_whisper(
        encoder=os.path.join(d, f"{size}.en-encoder.int8.onnx"), decoder=os.path.join(d, f"{size}.en-decoder.int8.onnx"),
        tokens=os.path.join(d, f"{size}.en-tokens.txt"), num_threads=os.cpu_count() or 2, language="en", task="transcribe")
    cfg = sherpa_onnx.VadModelConfig()
    cfg.silero_vad.model = os.path.join(MODELS, "silero_vad.onnx")
    cfg.silero_vad.min_silence_duration = 0.25
    cfg.silero_vad.min_speech_duration = 0.2
    cfg.silero_vad.max_speech_duration = 8.0
    cfg.sample_rate = sr
    vad = sherpa_onnx.VoiceActivityDetector(cfg, buffer_size_in_seconds=60)
    segs = []
    win = cfg.silero_vad.window_size
    k = 0
    while k < len(audio):
        vad.accept_waveform(audio[k:k + win])
        k += win
        while not vad.empty():
            segs.append((vad.front.start / sr, np.array(vad.front.samples, dtype=np.float32)))
            vad.pop()
    vad.flush()
    while not vad.empty():
        segs.append((vad.front.start / sr, np.array(vad.front.samples, dtype=np.float32)))
        vad.pop()
    out = []
    for n, (t0, samples) in enumerate(segs):
        s = rec.create_stream()
        try:
            s.set_option("max_tokens_per_second", "16")   # fast talkers: the default (6) truncates phrases
        except Exception:
            pass
        s.accept_waveform(sr, samples)
        rec.decode_stream(s)
        text = s.result.text.strip()
        if not text or re.fullmatch(r"[\W_]*", text) or text.lower() in ("you", "thank you.", "[music]", "(music)"):
            continue
        t1 = t0 + len(samples) / sr
        text = clean_text(text)
        if not text or text.lower().strip(".,!? ") in NOISE_ALONE:
            continue
        t0o, t1o = t0 + t_offset, t1 + t_offset
        out.append({"start": round(t0o, 3), "end": round(t1o, 3), "text": text, "words": spread_words(text, t0o, t1o)})
        if n % 25 == 0:
            print(f"   transcribed {t1 / 60:.1f} min", flush=True)
    return out


# Whisper on game streams hears noise as "(buzzer buzzing)" and loops; it can also mis-hear slurs. Captions keep only
# speech, collapse loops, soften swearing and drop slurs outright.
SLURS = re.compile(r"\b(f[a@]g\w*|n[i1]gg\w*|retard\w*|tr[a@]nn(y|ie)s?)\b", re.I)
SWEARS = {"fuck": "f*ck", "fucking": "f*cking", "fucked": "f*cked", "shit": "sh*t", "bitch": "b*tch", "motherfucker": "m*therf*cker"}


NOISE_ALONE = {"gay", "you", "the", "a", "uh", "um", "hmm", "bye", "so"}   # one-word "phrases" that are usually noise


def clean_text(text):
    text = re.sub(r"[\(\[][^\)\]]*[\)\]]", " ", text)         # (buzzer), [music]
    text = SLURS.sub(" ", text)
    words, out = text.split(), []
    for w in words:
        if len(out) >= 2 and w.lower().strip(".,!?") == out[-1].lower().strip(".,!?") == out[-2].lower().strip(".,!?"):
            continue                                              # "ship ship ship ship" -> "ship ship"
        key = re.sub(r"[^a-z]", "", w.lower())
        if key in SWEARS:
            w = re.sub(key, SWEARS[key], w, flags=re.I)
        out.append(w)
    text = " ".join(w for w in out if w not in ("'s", "'s.", "'s,")).strip(" -")
    text = re.sub(r"\s+([.,!?])", r"\1", text)
    text = re.sub(r"([,.!?])(\s*[,.!?])+", r"\1", text).strip(" ,")
    return "" if not re.search(r"[A-Za-z0-9]", text) else text


def spread_words(text, t0, t1):
    """Whisper gives a phrase, not word times: share the phrase's time by each word's length (plus a little each)."""
    words = text.split()
    wts = [len(re.sub(r"\W", "", w)) + 1.5 for w in words]
    tot = sum(wts) or 1
    t, out = t0, []
    for w, x in zip(words, wts):
        d = (t1 - t0) * x / tot
        out.append({"w": w, "s": round(t, 3), "e": round(t + d, 3)})
        t += d
    return out


# ------------------------------------------------------------------------------------------------ scoring
HYPE = re.compile(r"\b(no way|oh my god|omg|what+|bro+|yo+|let'?s go+|wait|no+|yes+|holy|crazy|insane|run|help|"
                  r"why|dude|chat|bruh|stop|look|ahh+|oh+|wow|dead|died|cops?|police|crash(ed)?|jump(ed)?)\b", re.I)


def features(video, audio, sr, transcript, dur):
    n = int(math.ceil(dur))
    hop = sr
    if len(audio) < n * hop:                       # audio a little shorter than the video: pad, never NaN
        audio = np.concatenate([audio, np.zeros(n * hop - len(audio), dtype=np.float32)])
    rms = np.array([np.sqrt(np.mean(audio[i * hop:(i + 1) * hop] ** 2) + 1e-9) for i in range(n)])
    db = 20 * np.log10(rms + 1e-9)
    base = np.array([np.median(db[max(0, i - 60):i + 60]) for i in range(n)])
    spike = np.clip(db - base, 0, 18) / 18
    # shouting: share of energy above 2 kHz
    from scipy.signal import butter, sosfilt
    hi = sosfilt(butter(4, 2000 / (sr / 2), "high", output="sos"), audio)
    hrms = np.array([np.sqrt(np.mean(hi[i * hop:(i + 1) * hop] ** 2) + 1e-9) for i in range(n)])
    shout = np.clip((hrms / (rms + 1e-9) - 0.18) / 0.3, 0, 1)
    talk = np.zeros(n)
    hype = np.zeros(n)
    for seg in transcript:
        a, b = int(seg["start"]), min(n - 1, int(seg["end"]))
        talk[a:b + 1] = 1
        h = len(HYPE.findall(seg["text"])) + seg["text"].count("!") * 0.5
        hype[a:b + 1] += min(3, h) / 3
    scene = scene_rate(video, n)
    score = 0.38 * spike + 0.2 * shout + 0.22 * np.clip(hype, 0, 1) + 0.12 * scene + 0.08 * talk
    score = np.nan_to_num(score) * (0.35 + 0.65 * talk)   # silence (menus, "starting soon") is never a clip
    return {"db": np.nan_to_num(db).tolist(), "score": score.tolist()}


def scene_rate(video, n):
    """Visual action: count of scene-change frames per second (sampled at 4 fps on a small copy)."""
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-vf",
                          "fps=4,scale=160:-2,select='gt(scene,0.18)',showinfo", "-an", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    r = np.zeros(n)
    for m in re.finditer(r"pts_time:([0-9.]+)", out):
        t = int(float(m.group(1)))
        if t < n:
            r[t] += 1
    return np.clip(r / 2, 0, 1)


def candidates(transcript, score, dur, k=12, lmin=15, lmax=45):
    score = np.array(score)
    n = len(score)
    cs = np.concatenate([[0], np.cumsum(score)])
    bounds = sorted({0.0, dur} | {s["start"] for s in transcript} | {s["end"] for s in transcript})
    starts = [s["start"] for s in transcript] or [0.0]
    ends = [s["end"] for s in transcript] or [dur]
    found = []
    for L in (20, 30, 40):
        for a in range(0, max(1, n - L)):
            b = a + L
            peak = score[a:b].max()
            mean = (cs[b] - cs[a]) / L
            found.append((0.6 * mean + 0.4 * peak, a, b))
    found.sort(reverse=True)
    picks = []
    for sc, a, b in found:
        if any(not (b <= p["start"] - 3 or a >= p["end"] + 3) for p in picks):
            continue
        s0 = max([s for s in starts if s <= a + 0.5] or [a]) - 0.25
        e0 = min([e for e in ends if e >= b - 0.5] or [b]) + 0.35
        s0, e0 = max(0.0, s0), min(dur, e0)
        if any(not (e0 <= p["start"] or s0 >= p["end"]) for p in picks):
            continue
        if e0 - s0 < lmin:
            e0 = min(dur, s0 + lmin)
        if e0 - s0 > lmax:
            e0 = s0 + lmax
        text = " ".join(seg["text"] for seg in transcript if seg["end"] > s0 and seg["start"] < e0)
        picks.append({"start": round(s0, 2), "end": round(e0, 2), "score": round(float(sc), 3), "text": text})
        if len(picks) >= k:
            break
    return sorted(picks, key=lambda p: -p["score"])


def analyze(video, outdir):
    os.makedirs(outdir, exist_ok=True)
    info = probe(video)
    print(f"source {info['w']}x{info['h']} {info['dur'] / 60:.1f} min", flush=True)
    audio, sr = load_audio(video)
    tpath = os.path.join(outdir, "transcript.json")
    if os.path.exists(tpath):                      # re-scoring: keep the transcript we already have
        tr = json.load(open(tpath))
    else:
        tr = transcribe(audio, sr)
        json.dump(tr, open(tpath, "w"), indent=1)
    f = features(video, audio, sr, tr, info["dur"])
    cands = candidates(tr, f["score"], info["dur"])
    json.dump({"source": os.path.abspath(video), "info": info, "candidates": cands},
              open(os.path.join(outdir, "candidates.json"), "w"), indent=1)
    for c in cands:
        print(f"{c['start']:8.1f}-{c['end']:7.1f}  {c['score']:.3f}  {c['text'][:110]}", flush=True)


# ------------------------------------------------------------------------------------------------ layout
def find_facecam(video, start, end, src):
    """Look for a webcam box: a face that stays in roughly the same small region across frames."""
    import cv2
    det = cv2.CascadeClassifier(os.path.join(MODELS, "haarcascade_frontalface_default.xml"))
    boxes = []
    with tempfile.TemporaryDirectory() as d:
        run(["ffmpeg", "-v", "error", "-ss", str(start), "-t", str(max(1.0, end - start)), "-i", video, "-vf",
             "fps=1/2,scale=960:-2", os.path.join(d, "f%03d.jpg")])
        names = sorted(os.listdir(d))
        for name in names:
            im = cv2.imread(os.path.join(d, name))
            g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
            fs = det.detectMultiScale(g, 1.1, 6, minSize=(40, 40))
            if len(fs):
                x, y, w, h = max(fs, key=lambda b: b[2] * b[3])
                sc = src["w"] / im.shape[1]
                boxes.append((x * sc, y * sc, w * sc, h * sc))
    if len(boxes) < max(2, len(names) * 0.5 if 'names' in locals() else 2):
        return None
    b = np.median(np.array(boxes), axis=0)
    spread = np.std(np.array(boxes)[:, :2], axis=0).max()
    cx, cy, fw, fh = b[0] + b[2] / 2, b[1] + b[3] / 2, b[2], b[3]
    if spread > src["w"] * 0.05 or fw > src["w"] * 0.25:
        return None   # a face that moves around or fills the frame is not a corner webcam
    # webcam box ~ 3.2x the face width, 16:9-ish, clamped to the frame
    bw, bh = fw * 3.2, fw * 3.2 * 9 / 16 * 1.25
    x0, y0 = max(0, cx - bw / 2), max(0, cy - bh / 2)
    x0, y0 = min(x0, src["w"] - bw), min(y0, src["h"] - bh)
    return [int(x0), int(y0), int(bw), int(bh)]


# ------------------------------------------------------------------------------------------------ captions (ASS)
def ass_time(t):
    t = max(0.0, t)
    h, m = int(t // 3600), int(t % 3600 // 60)
    return f"{h}:{m:02d}:{t % 60:05.2f}"


def build_ass(transcript, start, end, hook, ad, cap_y, path, font="Inter Display Black"):
    words = [w for seg in transcript for w in seg["words"] if w["e"] > start and w["s"] < end]
    lines = []
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{font},86,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,7,3,5,40,40,0,1
Style: Hook,{font},64,&H00FFFFFF,&H00FFFFFF,&H00000000,&HE6000000,0,0,0,0,100,100,0,0,3,18,0,8,70,70,250,1
Style: Ad,Inter Display ExtraBold,46,&H00FFFFFF,&H00FFFFFF,&H00000000,&HB4000000,0,0,0,0,100,100,0,0,3,12,0,7,60,60,170,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    # caption chunks of up to 3 words (break early at punctuation), current word in yellow, small pop-in
    chunks, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) >= 3 or re.search(r"[.,!?]$", w["w"]):
            chunks.append(cur); cur = []
    if cur:
        chunks.append(cur)
    y = int(H * cap_y)
    for ch in chunks:
        c0, c1 = ch[0]["s"] - start, ch[-1]["e"] - start
        for i, w in enumerate(ch):
            a = w["s"] - start
            b = ch[i + 1]["s"] - start if i + 1 < len(ch) else c1
            if b <= 0 or a >= end - start:
                continue
            parts = []
            for j, x in enumerate(ch):
                t = x["w"].upper().replace("{", "(").replace("}", ")")
                parts.append("{\\c&H004AE1FF&}" + t + "{\\c&H00FFFFFF&}" if j == i else t)
            pop = "{\\fscx108\\fscy108\\t(0,90,\\fscx100\\fscy100)}" if i == 0 else ""
            lines.append(f"Dialogue: 0,{ass_time(a)},{ass_time(b)},Cap,,0,0,0,,{{\\pos({W // 2},{y})}}{pop}{' '.join(parts)}")
    if hook:
        lines.append(f"Dialogue: 1,{ass_time(0)},{ass_time(min(3.2, end - start))},Hook,,0,0,0,,"
                     "{\\fad(80,200)}" + hook.replace("{", "(").replace("}", ")"))
    if ad:
        lines.append(f"Dialogue: 2,{ass_time(0)},{ass_time(min(3.5, end - start))},Ad,,0,0,0,,{{\\fad(0,200)}}{ad}")
    open(path, "w").write(head + "\n".join(lines) + "\n")


# ------------------------------------------------------------------------------------------------ render
def clip_transcript(video, start, end, size="small"):
    """Re-transcribe just the clip window with the better model (times are in the source's clock)."""
    with tempfile.TemporaryDirectory() as d:
        wav = os.path.join(d, "a.wav")
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{start:.3f}", "-t", f"{end - start:.3f}", "-i", video, "-vn",
             "-ac", "1", "-ar", "16000", wav])
        a, sr = sf.read(wav, dtype="float32")
    return transcribe(a, sr, size=size, t_offset=start)


def render_clip(video, transcript, clip, outdir, src):
    start, end = float(clip["start"]), float(clip["end"])
    dur = end - start
    if clip.get("asr", "small") != "base":
        transcript = clip_transcript(video, start, end, clip.get("asr", "small"))
        json.dump(transcript, open(os.path.join(outdir, (clip.get("name") or f"clip_{int(start)}") + ".words.json"), "w"), indent=1)
    name = clip.get("name") or f"clip_{int(start)}"
    layout = clip.get("layout", "auto")
    cam = clip.get("facecam")
    if layout in ("auto", "split") and cam is None:
        cam = find_facecam(video, start, end, src)
    split = cam is not None and layout != "fit"
    with tempfile.TemporaryDirectory() as d:
        ass = os.path.join(d, "c.ass")
        cap_y = clip.get("cap_y") or (0.555 if split else 0.75 if layout == "square" else 0.66)
        build_ass(transcript, start, end, clip.get("hook", ""), clip.get("ad", "#ad"), cap_y, ass)
        if split:
            x, y, w, h = cam
            top_h = int(H * float(clip.get("cam_share", 0.40))) // 2 * 2   # even heights for 4:2:0
            # gameplay: a crop of the full frame (centre by default; game_cx moves it, e.g. away from the cam)
            gh = H - top_h
            gw_src = int(src["h"] * W / gh)
            gcx = float(clip.get("game_cx", 0.5)) * src["w"]
            gx = int(min(max(0, gcx - gw_src / 2), src["w"] - gw_src))
            fc = (f"[0:v]fps={FPS},split=2[s1][s2];"
                  f"[s1]crop={w}:{h}:{x}:{y},scale={W}:{top_h}:force_original_aspect_ratio=increase,crop={W}:{top_h}[cam];"
                  f"[s2]crop={min(gw_src, src['w'])}:{src['h']}:{gx}:0,scale={W}:{gh}[game];"
                  f"[cam][game]vstack=inputs=2,setsar=1[v0]")
        elif layout == "square":
            # IRL / camera shots: a square crop around the action (cx = its centre, share of width) over a blurred copy
            side = src["h"]
            cx = float(clip.get("cx", 0.5)) * src["w"]
            sx = int(min(max(0, cx - side / 2), src["w"] - side))
            fc = (f"[0:v]fps={FPS},split=2[s1][s2];"
                  f"[s1]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=28:2,eq=brightness=-0.15[bg];"
                  f"[s2]crop={side}:{side}:{sx}:0,scale={W}:{W}[fg];[bg][fg]overlay=0:(H-h)/2-150,setsar=1[v0]")
        else:
            fc = (f"[0:v]fps={FPS},split=2[s1][s2];"
                  f"[s1]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=28:2,eq=brightness=-0.12[bg];"
                  f"[s2]scale={W}:-2[fg];[bg][fg]overlay=0:(H-h)/2-140,setsar=1[v0]")
        inputs = ["-ss", f"{start:.3f}", "-t", f"{dur:.3f}", "-i", video]
        last = "[v0]"
        if clip.get("overlay"):
            inputs += ["-i", clip["overlay"]]
            fc += f";[1:v]scale={W}:{H}:force_original_aspect_ratio=decrease[ov];{last}[ov]overlay=(W-w)/2:(H-h)/2[v1]"
            last = "[v1]"
        fontsdir = os.path.join(os.path.dirname(HERE), "assets", "fonts")
        fc += f";{last}subtitles={ass}:fontsdir={fontsdir}[v]"
        out = os.path.join(outdir, name + ".mp4")
        tmp = out[:-4] + ".part.mp4"
        run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", fc, "-map", "[v]", "-map", "0:a:0?",
             "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-profile:v", "high",
             "-c:a", "aac", "-b:a", "160k", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-shortest", "-movflags", "+faststart", tmp])
        os.replace(tmp, out)
    print(f"rendered {out} ({dur:.1f}s, {'split' if split else 'fit'})", flush=True)
    return out


def render(video, plan_path, outdir):
    os.makedirs(outdir, exist_ok=True)
    plan = json.load(open(plan_path))
    tdir = plan.get("analysis") or os.path.dirname(plan_path)
    transcript = json.load(open(os.path.join(tdir, "transcript.json")))
    src = probe(video)
    for clip in plan["clips"]:
        render_clip(video, transcript, clip, outdir, src)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "analyze":
        analyze(sys.argv[2], sys.argv[3])
    elif cmd == "render":
        render(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        sys.exit(__doc__)
