"""Free audio: Kokoro TTS (Hindi + English, CPU), procedural music, ducking and envelopes."""
from __future__ import annotations

import hashlib
import os
import random

import numpy as np
import soundfile as sf
from scipy.signal import fftconvolve, resample_poly

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(ROOT, "models")
CACHE = os.path.join(ROOT, "data", "cache", "tts")
SR = 48000

# voice id -> kokoro language code (Kokoro v1.0 voices are prefixed by language)
VOICES = {
    "hf_alpha": "hi", "hf_beta": "hi", "hm_omega": "hi", "hm_psi": "hi",
    "af_heart": "en-us", "af_bella": "en-us", "af_nicole": "en-us", "af_sky": "en-us", "af_nova": "en-us",
    "af_sarah": "en-us", "af_aoede": "en-us", "af_kore": "en-us", "af_jessica": "en-us", "af_river": "en-us",
    "af_alloy": "en-us", "am_michael": "en-us", "am_fenrir": "en-us", "am_puck": "en-us", "am_adam": "en-us",
    "am_echo": "en-us", "am_eric": "en-us", "am_liam": "en-us", "am_onyx": "en-us", "am_santa": "en-us",
    "bf_emma": "en-gb", "bf_alice": "en-gb", "bf_isabella": "en-gb", "bf_lily": "en-gb", "bm_george": "en-gb",
    "bm_fable": "en-gb", "bm_daniel": "en-gb", "bm_lewis": "en-gb",
    "ef_dora": "es", "em_alex": "es", "em_santa": "es", "ff_siwis": "fr-fr", "if_sara": "it", "im_nicola": "it",
    "pf_dora": "pt-br", "pm_alex": "pt-br", "pm_santa": "pt-br",
}
LANG_BY_PREFIX = {"a": "en-us", "b": "en-gb", "h": "hi", "e": "es", "f": "fr-fr", "i": "it", "p": "pt-br"}
# default narrator per channel language
DEFAULT_VOICE = {"en": "af_heart", "hi": "hm_omega", "hinglish": "hm_omega", "es": "ef_dora", "fr": "ff_siwis",
                 "it": "if_sara", "pt": "pf_dora"}


def voice_lang(voice: str) -> str:
    return VOICES.get(voice) or LANG_BY_PREFIX.get((voice or "a")[0], "en-us")


_kokoro = None


def _engine():
    global _kokoro
    if _kokoro is None:
        from kokoro_onnx import Kokoro
        _kokoro = Kokoro(os.path.join(MODEL_DIR, "kokoro-v1.0.onnx"), os.path.join(MODEL_DIR, "voices-v1.0.bin"))
    return _kokoro


def tts(text: str, voice: str = "hm_omega", speed: float = 1.0, lang: str | None = None) -> np.ndarray:
    """Return mono float32 audio at SR. Cached on disk by (text, voice, speed, lang)."""
    text = (text or "").strip()
    if not text:
        return np.zeros(0, dtype=np.float32)
    if voice not in VOICES:              # "auto", a typo or a voice this model lacks: never go silent over it
        base = (lang or "en").split("-")[0]
        fixed = DEFAULT_VOICE.get(base, "af_heart")
        print(f"[tts] unknown voice {voice!r}, using {fixed}")
        voice = fixed
    lang = lang if lang and "-" in lang or lang in ("hi", "es", "it") else voice_lang(voice)
    key = hashlib.sha1(f"{voice}|{speed}|{lang}|{text}".encode()).hexdigest()[:20]
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, key + ".wav")
    if os.path.exists(path):
        a, _ = sf.read(path, dtype="float32")
        return a
    try:
        samples, sr = _engine().create(text, voice=voice, speed=speed, lang=lang)
        a = resample_poly(np.asarray(samples, dtype=np.float32), SR, sr).astype(np.float32)
        a = _trim(a)
    except Exception as e:  # keep tests alive without a voice model; production runs refuse silence (see below)
        if os.environ.get("VIDFORGE_REQUIRE_VOICE"):
            raise RuntimeError(f"text-to-speech failed for voice {voice!r}: {e}") from e
        print(f"[tts] fallback to silence: {e}")
        return np.zeros(int(SR * max(1.0, len(text) * 0.065)), dtype=np.float32)   # never cached
    sf.write(path, a, SR)
    return a


def _trim(a, thresh=0.01):
    idx = np.where(np.abs(a) > thresh)[0]
    if len(idx) == 0:
        return a
    s = max(0, idx[0] - int(0.03 * SR))
    e = min(len(a), idx[-1] + int(0.08 * SR))
    return a[s:e]


def envelope(track: np.ndarray, fps: int, n_frames: int) -> np.ndarray:
    hop = SR // fps
    env = np.zeros(n_frames, dtype=np.float32)
    for f in range(n_frames):
        seg = track[f * hop:(f + 1) * hop]
        if len(seg):
            env[f] = float(np.sqrt(np.mean(seg ** 2)))
    peak = np.percentile(env[env > 0], 95) if np.any(env > 0) else 1.0
    env = np.clip(env / max(peak, 1e-4), 0, 1)
    # light smoothing so mouths don't flicker
    k = np.array([0.25, 0.5, 0.25])
    return np.convolve(env, k, mode="same").astype(np.float32)


# ------------------------------------------------------------------ music
NOTE = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def _env(n, a=0.005, d=0.3, s=0.0, r=0.05, sr=SR, hold=None):
    t = np.arange(n) / sr
    e = np.where(t < a, t / max(a, 1e-4), 0)
    dec = np.exp(-(t - a) / max(d, 1e-4)) * (1 - s) + s
    e = np.where(t >= a, dec, e)
    if r and n > int(r * sr):
        e[-int(r * sr):] *= np.linspace(1, 0, int(r * sr))
    return e


def _tone(f, dur, harmonics=((1, 1.0),), env=None, vib=0.0, sr=SR):
    n = int(dur * sr)
    t = np.arange(n) / sr
    ph = 2 * np.pi * f * t
    if vib:
        ph += vib * np.sin(2 * np.pi * 5.2 * t) * (t > 0.15)
    out = np.zeros(n)
    for h, a in harmonics:
        out += a * np.sin(ph * h)
    if env is not None:
        out *= env[:n]
    return out


def inst_pluck(f, dur):
    n = int(dur * SR)
    return _tone(f, dur, ((1, 1), (2, 0.35), (3, 0.12)), _env(n, 0.003, 0.35, 0, 0.05))


def inst_marimba(f, dur):
    n = int(dur * SR)
    return _tone(f, dur, ((1, 1), (4, 0.25), (10, 0.05)), _env(n, 0.002, 0.18, 0, 0.03))


def inst_piano(f, dur):
    n = int(dur * SR)
    return _tone(f, dur, ((1, 1), (2, 0.4), (3, 0.18), (4, 0.08)), _env(n, 0.004, 0.7, 0.05, 0.12))


def inst_pad(f, dur):
    n = int(dur * SR)
    e = _env(n, min(0.8, dur / 3), 10, 1.0, min(0.8, dur / 3))
    out = np.zeros(n)
    for det in (-0.12, 0.0, 0.12):
        out += _tone(f * 2 ** (det / 12), dur, ((1, 1), (2, 0.3), (3, 0.12)), e) / 3
    return out


def inst_bass(f, dur):
    n = int(dur * SR)
    return _tone(f, dur, ((1, 1), (2, 0.2)), _env(n, 0.004, 0.25, 0.3, 0.06))


def inst_flute(f, dur):
    n = int(dur * SR)
    e = _env(n, 0.06, 10, 1.0, 0.12)
    tone = _tone(f, dur, ((1, 1), (2, 0.18), (3, 0.06)), e, vib=0.04)
    breath = np.random.default_rng(int(f)).normal(0, 0.03, n) * e
    return tone + breath


def inst_tanpura(f, dur):
    n = int(dur * SR)
    harm = tuple((h, 1.0 / h ** 0.9) for h in range(1, 12))
    return _tone(f, dur, harm, _env(n, 0.02, 1.4, 0.15, 0.3)) * 0.5


def drum_kick(dur=0.35):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 120 * np.exp(-t * 18) + 45
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)


def drum_snare(dur=0.2, rng=None):
    n = int(dur * SR)
    rng = rng or np.random.default_rng(1)
    t = np.arange(n) / SR
    return (rng.normal(0, 1, n) * 0.6 + np.sin(2 * np.pi * 190 * t) * 0.4) * np.exp(-t * 22)


def drum_hat(dur=0.05, rng=None):
    n = int(dur * SR)
    rng = rng or np.random.default_rng(2)
    noise = rng.normal(0, 1, n)
    noise = np.diff(noise, prepend=0)
    return noise * np.exp(-np.arange(n) / SR * 80) * 0.5


def tabla(kind="na", dur=0.3):
    n = int(dur * SR)
    t = np.arange(n) / SR
    if kind == "dha":
        f = 95 * (1 + 0.4 * np.exp(-t * 30))
        low = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)
        return low + 0.5 * np.sin(2 * np.pi * 520 * t) * np.exp(-t * 14)
    return 0.8 * np.sin(2 * np.pi * 540 * t) * np.exp(-t * 16) + 0.2 * np.sin(2 * np.pi * 1080 * t) * np.exp(-t * 25)


MOODS = {
    # root midi, scale intervals, progression as scale degrees, bpm, instruments
    "cosmic": dict(root=57, scale=[0, 2, 3, 5, 7, 8, 10], prog=[0, 5, 2, 6], bpm=84, lead="pluck", pad=True, bass=True, drums="soft", arp=True),
    "playful": dict(root=60, scale=[0, 2, 4, 5, 7, 9, 11], prog=[0, 4, 5, 3], bpm=112, lead="marimba", pad=False, bass=True, drums="bouncy", arp=False, melody=True),
    "mystery": dict(root=50, scale=[0, 2, 3, 5, 7, 8, 10], prog=[0, 5, 3, 4], bpm=72, lead="pluck", pad=True, bass=False, drums="tick", arp=True),
    "epic": dict(root=52, scale=[0, 2, 3, 5, 7, 8, 10], prog=[0, 5, 2, 6], bpm=100, lead="piano", pad=True, bass=True, drums="full", arp=True),
    "calm": dict(root=53, scale=[0, 2, 4, 5, 7, 9, 11], prog=[0, 5, 3, 4], bpm=76, lead="piano", pad=True, bass=False, drums=None, arp=False, melody=True),
    "upbeat": dict(root=55, scale=[0, 2, 4, 5, 7, 9, 11], prog=[0, 4, 5, 3], bpm=118, lead="pluck", pad=False, bass=True, drums="full", arp=True),
    "indian": dict(root=50, scale=[0, 2, 4, 7, 9], prog=[0, 0, 0, 0], bpm=92, lead="flute", pad=False, bass=False, drums="tabla", arp=False, melody=True, drone=True),
    "devotional": dict(root=50, scale=[0, 2, 4, 7, 9], prog=[0, 0, 0, 0], bpm=72, lead="flute", pad=True, bass=False, drums=None, arp=False, melody=True, drone=True),
}

INSTR = {"pluck": inst_pluck, "marimba": inst_marimba, "piano": inst_piano, "flute": inst_flute}


def _add(buf, sig, start):
    s = int(start * SR)
    if s >= len(buf):
        return
    e = min(len(buf), s + len(sig))
    buf[s:e] += sig[: e - s]


def _chord(m, degree):
    sc = m["scale"]
    idx = [degree, degree + 2, degree + 4]
    out = []
    for k in idx:
        octv, pos = divmod(k, len(sc))
        out.append(m["root"] + sc[pos] + 12 * octv)
    return out


def _reverb(x, seconds=1.8, mix=0.22, seed=3):
    n = int(seconds * SR)
    rng = np.random.default_rng(seed)
    ir = rng.normal(0, 1, n) * np.exp(-np.arange(n) / SR * (6.9 / seconds))
    ir[: int(0.012 * SR)] = 0
    ir /= np.sqrt(np.sum(ir ** 2))
    wet = fftconvolve(x, ir)[: len(x)]
    return (1 - mix) * x + mix * wet * 0.6


def music(mood: str, duration: float, seed: int = 1) -> np.ndarray:
    """Procedural, royalty-free background track (mono float32 at SR)."""
    m = MOODS.get(mood, MOODS["cosmic"])
    rnd = random.Random(seed)
    rng = np.random.default_rng(seed)
    beat = 60.0 / m["bpm"]
    bar = beat * 4
    n = int((duration + 2.5) * SR)
    mel = np.zeros(n)
    bed = np.zeros(n)
    drm = np.zeros(n)
    lead = INSTR.get(m["lead"], inst_pluck)
    nbars = int(duration / bar) + 2
    melody_motif = [rnd.choice([0, 1, 2, 2, 4, 4, 5, 7]) for _ in range(8)]
    for b in range(nbars):
        t0 = b * bar
        deg = m["prog"][b % len(m["prog"])]
        chord = _chord(m, deg)
        if m.get("drone"):
            for k, iv in enumerate((0, 7, 12, 0)):
                _add(bed, inst_tanpura(hz(m["root"] - 12 + iv), beat * 1.6) * 0.35, t0 + k * beat)
        if m.get("pad"):
            for note in chord:
                _add(bed, inst_pad(hz(note - 12), bar + 0.3) * 0.13, t0)
        if m.get("bass"):
            pattern = [0, 2] if m["drums"] != "bouncy" else [0, 1, 2, 3]
            for k in pattern:
                _add(bed, inst_bass(hz(chord[0] - 24), beat * (0.9 if len(pattern) == 2 else 0.45)) * 0.32, t0 + k * beat)
        if m.get("arp"):
            seq = chord + [chord[1] + 12]
            for k in range(8):
                note = seq[k % len(seq)] + (12 if b % 4 == 3 and k > 4 else 0)
                _add(mel, lead(hz(note), beat * 0.9) * 0.13, t0 + k * beat / 2)
        if m.get("melody"):
            sc = m["scale"]
            steps = 8 if m["bpm"] > 90 else 4
            for k in range(steps):
                if rnd.random() < (0.22 if b % 2 else 0.12):
                    continue
                d = melody_motif[(k + b * 3) % len(melody_motif)] + (deg if not m.get("drone") else 0)
                octv, pos = divmod(d, len(sc))
                note = m["root"] + 12 + sc[pos] + 12 * octv
                length = bar / steps
                _add(mel, lead(hz(note), length * (1.6 if m["lead"] == "flute" else 1.0)) * (0.16 if m["lead"] != "flute" else 0.11), t0 + k * length)
        dr = m.get("drums")
        if dr in ("full", "bouncy", "soft"):
            for k in range(4):
                if k in (0, 2) or (dr == "bouncy"):
                    _add(drm, drum_kick() * (0.5 if dr != "soft" else 0.3), t0 + k * beat)
                if k in (1, 3) and dr != "soft":
                    _add(drm, drum_snare(rng=rng) * (0.22 if dr == "full" else 0.12), t0 + k * beat)
            for k in range(8):
                _add(drm, drum_hat(rng=rng) * (0.12 if dr != "soft" else 0.06), t0 + k * beat / 2)
        elif dr == "tick":
            for k in range(8):
                _add(drm, drum_hat(rng=rng) * 0.07, t0 + k * beat / 2)
        elif dr == "tabla":
            pat = ["dha", "na", "na", "dha", "dha", "na", "na", "dha"]
            for k, kind in enumerate(pat):
                _add(drm, tabla(kind) * 0.28, t0 + k * beat / 2)
    mix = _reverb(mel, 1.6, 0.3) + _reverb(bed, 2.2, 0.25) + drm
    mix = mix[: int(duration * SR)]
    fade = int(min(1.5, duration / 4) * SR)
    mix[:int(0.3 * SR)] *= np.linspace(0, 1, int(0.3 * SR))
    mix[-fade:] *= np.linspace(1, 0, fade)
    peak = np.max(np.abs(mix)) or 1.0
    return (mix / peak * 0.8).astype(np.float32)


def load_music_file(path: str, duration: float) -> np.ndarray:
    a, sr = sf.read(path, dtype="float32", always_2d=True)
    a = a.mean(axis=1)
    if sr != SR:
        a = resample_poly(a, SR, sr).astype(np.float32)
    n = int(duration * SR)
    if len(a) < n:
        a = np.tile(a, int(np.ceil(n / max(1, len(a)))))
    a = a[:n]
    fade = int(min(1.5, duration / 4) * SR)
    a[-fade:] *= np.linspace(1, 0, fade)
    return a / (np.max(np.abs(a)) or 1.0) * 0.8


def sfx(kind: str) -> np.ndarray:
    t = np.arange(int(0.4 * SR)) / SR
    if kind == "whoosh":
        rng = np.random.default_rng(4)
        n = rng.normal(0, 1, len(t))
        env = np.sin(np.pi * t / t[-1]) ** 2
        from scipy.signal import butter, lfilter
        b, a = butter(2, [400 / (SR / 2), 4000 / (SR / 2)], "band")
        return (lfilter(b, a, n) * env * 0.5).astype(np.float32)
    if kind == "pop":
        f = 500 + 900 * np.exp(-t * 30)
        return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 25) * 0.5).astype(np.float32)
    if kind == "ding":
        return (_tone(1318, 0.4, ((1, 1), (2.76, 0.3)), _env(len(t), 0.002, 0.25)) * 0.35).astype(np.float32)
    return np.zeros(1, dtype=np.float32)


def mixdown(voice: np.ndarray, bed: np.ndarray, duck=0.65, music_gain=0.16) -> np.ndarray:
    n = max(len(voice), len(bed))
    v = np.pad(voice, (0, n - len(voice)))
    m = np.pad(bed, (0, n - len(bed)))
    # sidechain: smoothed voice envelope pulls the music down
    win = int(0.25 * SR)
    env = np.sqrt(np.convolve(v ** 2, np.ones(win) / win, mode="same"))
    env = env / (np.max(env) or 1.0)
    gain = music_gain * (1 - duck * np.clip(env * 3, 0, 1))
    out = v + m * gain
    peak = np.max(np.abs(out)) or 1.0
    if peak > 0.98:
        out = out / peak * 0.98
    return out.astype(np.float32)
