"""Sound for FIRST LOVE: synthesized score + SFX, ducked under the narration.

Everything is generated from the same timeline the picture uses, so every cue
lands on its word. Output: out/audio/mix.wav (48 kHz stereo, 24-bit), plus stems
and cues.md.
"""
import math
import os
import wave

import numpy as np

from timeline import TL
import words as W

SR = 48000
N = int(round(TL.duration * SR))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "out", "audio")
RNG = np.random.default_rng(20261119)


# ---------------------------------------------------------------- utilities
def buf():
    return np.zeros((N, 2), dtype=np.float64)


def tt(dur):
    return np.arange(int(dur * SR)) / SR


def add(dst, sig, t0, gain=1.0, pan=0.0):
    i0 = int(round(t0 * SR))
    if sig.ndim == 1:
        l = math.cos((pan + 1) * math.pi / 4)
        r = math.sin((pan + 1) * math.pi / 4)
        sig = np.stack([sig * l, sig * r], axis=1)
    n = min(len(sig), N - i0)
    if n > 0 and i0 >= 0:
        dst[i0:i0 + n] += sig[:n] * gain


def fade(x, a=0.01, r=0.05):
    n = len(x)
    ai, ri = min(n, int(a * SR)), min(n, int(r * SR))
    if ai > 0:
        x[:ai] *= np.linspace(0, 1, ai) ** 0.6
    if ri > 0:
        x[-ri:] *= np.linspace(1, 0, ri) ** 1.4
    return x


def env_exp(dur, attack=0.005, decay=None):
    t = tt(dur)
    a = np.clip(t / max(1e-4, attack), 0, 1)
    d = np.exp(-t / (decay if decay else dur / 3.0))
    return a * d


def fft_filter(x, lo=None, hi=None, slope=1.0):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    m = np.ones_like(f)
    if lo:
        m *= 1 / (1 + (lo / np.maximum(f, 1e-3)) ** (4 * slope))
    if hi:
        m *= 1 / (1 + (f / hi) ** (4 * slope))
    return np.fft.irfft(X * m, len(x))


def noise(dur):
    return RNG.standard_normal(int(dur * SR)) * 0.5


def sine(f, dur, phase=0.0):
    return np.sin(2 * np.pi * f * tt(dur) + phase)


# ---------------------------------------------------------------- instruments
def pad(freqs, dur, gain=1.0, attack=2.0, release=3.0, bright=1.0, drift=0.06):
    """Slow detuned drone: sine partials with a gentle beating and air."""
    t = tt(dur)
    out = np.zeros_like(t)
    for f in freqs:
        for det in (-drift, 0.0, drift):
            ff = f * (1 + det * 0.01)
            out += np.sin(2 * np.pi * ff * t + RNG.uniform(0, 6.28))
            if bright > 0.3:
                out += bright * 0.30 * np.sin(2 * np.pi * ff * 2 * t + RNG.uniform(0, 6.28))
            if bright > 0.7:
                out += bright * 0.12 * np.sin(2 * np.pi * ff * 3.01 * t)
    lfo = 1 + 0.18 * np.sin(2 * np.pi * 0.06 * t + RNG.uniform(0, 6.28))
    out *= lfo / (len(freqs) * 3)
    a = np.clip(t / max(0.01, attack), 0, 1)
    r = np.clip((dur - t) / max(0.01, release), 0, 1)
    return out * a * r * gain


def sub_drop(t0, f0=78, f1=26, dur=1.6, gain=1.0):
    t = tt(dur)
    f = f1 + (f0 - f1) * np.exp(-t / 0.22)
    phase = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(phase) * np.exp(-t / (dur * 0.45))
    x[:int(0.004 * SR)] *= np.linspace(0, 1, int(0.004 * SR))
    return x * gain


def thud(dur=0.5, f=64, gain=1.0):
    t = tt(dur)
    body = np.sin(2 * np.pi * f * t * np.exp(-t * 2.2)) * np.exp(-t * 9)
    click = fft_filter(noise(dur), hi=1800) * np.exp(-t * 90)
    return (body * 0.9 + click * 0.5) * gain


def chime(f, dur=2.4, gain=1.0, bright=1.0):
    t = tt(dur)
    x = np.zeros_like(t)
    for k, a in ((1, 1.0), (2.01, 0.5), (3.02, 0.28), (4.97, 0.16), (6.9, 0.08)):
        x += a * np.sin(2 * np.pi * f * k * t) * np.exp(-t * (1.6 + k * 0.5))
    x[:int(0.002 * SR)] *= np.linspace(0, 1, int(0.002 * SR))
    return x * gain * bright


def glass(t0f, dur=1.2, gain=1.0):
    return chime(t0f, dur, gain)


def tick(gain=1.0, f=2100, dur=0.05):
    t = tt(dur)
    body = np.sin(2 * np.pi * f * t) * np.exp(-t * 160)
    n = fft_filter(noise(dur), lo=1200, hi=8000) * np.exp(-t * 220)
    return (body * 0.5 + n * 0.7) * gain


def crackle(dur, density=7.0, gain=1.0):
    t = tt(dur)
    x = np.zeros_like(t)
    n = int(density * dur)
    for _ in range(n):
        i = RNG.integers(0, len(t) - 200)
        L = RNG.integers(20, 160)
        amp = RNG.uniform(0.2, 1.0) ** 3
        x[i:i + L] += amp * RNG.standard_normal(L) * np.exp(-np.arange(L) / 18)
    return fft_filter(x, lo=900, hi=11000) * gain


def hiss(dur, gain=1.0, lo=400, hi=7000):
    t = tt(dur)
    x = fft_filter(noise(dur), lo=lo, hi=hi)
    x *= 0.6 + 0.4 * np.sin(2 * np.pi * 0.7 * t)
    return x * gain


def whoosh(dur=0.9, f0=300, f1=2600, gain=1.0, down=True):
    t = tt(dur)
    x = noise(dur)
    # moving band: crossfade between two filtered copies
    a = fft_filter(x, lo=f0 * 0.7, hi=f0 * 2.2)
    b = fft_filter(x, lo=f1 * 0.7, hi=f1 * 2.2)
    p = (t / dur) ** 1.5
    if down:
        p = 1 - p
    return (a * (1 - p) + b * p) * np.sin(np.pi * t / dur) ** 1.4 * gain


def snip(gain=1.0):
    t = tt(0.22)
    x = fft_filter(noise(0.22), lo=2500, hi=14000) * np.exp(-t * 55)
    y = np.sin(2 * np.pi * 3200 * t) * np.exp(-t * 70)
    return (x * 0.8 + y * 0.4) * gain


def click(gain=1.0, f=900):
    t = tt(0.09)
    return (np.sin(2 * np.pi * f * t) * np.exp(-t * 90) +
            fft_filter(noise(0.09), lo=600, hi=6000) * np.exp(-t * 120) * 0.6) * gain


def riser(dur=2.2, f0=90, f1=420, gain=1.0):
    t = tt(dur)
    f = f0 * (f1 / f0) ** (t / dur)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.5
    x += fft_filter(noise(dur), lo=500, hi=9000) * 0.35
    return x * (t / dur) ** 2 * gain


def tape_stop(dur=0.7, gain=1.0, f=120):
    t = tt(dur)
    f = f * (1 - t / dur) ** 2 + 8
    x = np.sin(2 * np.pi * np.cumsum(f) / SR)
    x += fft_filter(noise(dur), lo=100, hi=3000) * 0.25
    return x * (1 - t / dur) ** 1.2 * gain


def piano(f=220, dur=3.4, gain=1.0, vel=1.0):
    t = tt(dur)
    x = np.zeros_like(t)
    partials = [(1, 1.0, 1.4), (2.0, 0.42, 2.2), (2.99, 0.22, 2.9), (4.02, 0.12, 3.6),
                (5.05, 0.07, 4.4), (6.1, 0.04, 5.2)]
    for k, a, d in partials:
        det = 1 + RNG.normal(0, 0.0006)
        x += a * np.sin(2 * np.pi * f * k * det * t + RNG.uniform(0, 6.28)) * np.exp(-t * d * 0.55)
    x[:int(0.006 * SR)] *= np.linspace(0, 1, int(0.006 * SR))
    return x * gain * vel * 0.5


def heartbeat(dur=0.7, gain=1.0, f=52):
    t = tt(dur)
    a = np.sin(2 * np.pi * f * t * (1 + 0.05 * np.exp(-t * 20))) * np.exp(-t * 8)
    b = np.sin(2 * np.pi * f * 0.9 * np.maximum(t - 0.16, 0)) * np.exp(-np.maximum(t - 0.16, 0) * 9)
    b[:int(0.16 * SR)] = 0
    return (a + 0.6 * b) * gain


# ---------------------------------------------------------------- narration
def voice_stem():
    out = buf()
    cues = []
    for s in TL.scenes:
        path = os.path.join(W.NARR, s["beat"]["file"])
        a, sr = W.load_wav(path)
        a = np.interp(np.arange(int(len(a) * SR / sr)) * sr / SR,
                      np.arange(len(a)), a).astype(np.float64)
        g = 0.96 / (np.abs(a).max() + 1e-9)
        a = fade(a * g, 0.004, 0.06)
        add(out, a, s["voice"], 1.0)
        cues.append((s["key"], s["voice"], s["voice"] + len(a) / SR))
    return out, cues


# ---------------------------------------------------------------- music
def music_stem(duck_env):
    m = buf()
    sc = {s["key"]: s for s in TL.scenes}

    # S1 - low A minor drone, sparse, with a heartbeat
    a0, a1 = sc["s1"]["start"], sc["s1"]["end"]
    add(m, pad([55.0, 82.5, 110.0], a1 - a0 + 1.0, 0.55, attack=2.5, release=3.0,
               bright=0.5), a0)
    for k in range(4):
        add(m, heartbeat(0.8, 0.5), a0 + 1.4 + k * 2.6)

    # S2 - the room tightens: F drone, slow pulse
    b0, b1 = sc["s2"]["start"], sc["s2"]["end"]
    add(m, pad([43.65, 87.3, 130.8, 174.6], b1 - b0 + 1.5, 0.62, attack=3.0,
               release=3.5, bright=0.75), b0)
    for k in range(9):
        add(m, heartbeat(0.6, 0.35, f=46), b0 + 2.0 + k * 3.2)

    # S3 - clockwork: D drone plus a tick that accelerates into the break
    c0, c1 = sc["s3"]["start"], sc["s3"]["end"]
    add(m, pad([73.42, 110.0, 146.8], c1 - c0 + 1.0, 0.5, attack=2.0, release=3.0,
               bright=0.6), c0)
    tk = 1.0
    tcur = c0 + 2.0
    while tcur < c1 - 1.0:
        add(m, tick(0.22), tcur)
        tcur += tk
        tk = max(0.42, tk * 0.985)

    # S4 - warmer, suspended: A minor add9, slow build to the pedestal chord
    d0, d1 = sc["s4"]["start"], sc["s4"]["end"]
    add(m, pad([55.0, 82.5, 138.6, 164.8], d1 - d0 + 1.0, 0.55, attack=3.0,
               release=4.0, bright=0.8), d0)
    art = TL.cue("s4", "artifact")
    for k, f in enumerate((261.6, 329.6, 392.0, 523.3)):
        add(m, chime(f, 3.6, 0.10), d0 + art + k * 0.12)

    # S5 - A minor with a heavier pulse; drops away for the vault
    e0, e1 = sc["s5"]["start"], sc["s5"]["end"]
    add(m, pad([55.0, 82.5, 116.5, 155.6], e1 - e0 + 1.0, 0.58, attack=2.5,
               release=3.0, bright=0.65), e0)
    for k in range(8):
        add(m, heartbeat(0.7, 0.34, f=44), e0 + 1.0 + k * 2.1)
    key = TL.cue("s5", "key")
    add(m, pad([116.5, 174.6], 4.0, 0.30, attack=1.0, release=2.0, bright=0.4),
        e0 + key)

    # S6 - warm resolution, then silence; the last piano note rings alone
    f0, f1 = sc["s6"]["start"], sc["s6"]["end"]
    close = TL.cue("s6", "close")
    add(m, pad([55.0, 82.5, 110.0, 164.8], (close + 1.6) - f0, 0.42, attack=2.5,
               release=2.0, bright=0.7), f0)
    end_t = sc["s6"]["lead"] + sc["s6"]["beat"]["dur"]
    add(m, piano(220.0, 5.5, 0.55), f0 + end_t + 1.1)
    add(m, piano(329.6, 5.0, 0.28), f0 + end_t + 1.32)

    # gentle side-chaining against the voice
    m *= duck_env[:, None]
    return m


def build_duck(cues, depth=0.42, smooth=0.25):
    env = np.ones(N)
    hop = int(0.02 * SR)
    for (k, v0, v1) in cues:
        i0, i1 = int(v0 * SR), min(N, int(v1 * SR))
        env[i0:i1] = np.minimum(env[i0:i1], 1 - depth)
    # smooth
    k = int(smooth * SR)
    win = np.hanning(2 * k + 1)
    win /= win.sum()
    env = np.convolve(env, win, mode="same")
    return np.clip(env, 0.4, 1.0)


# ---------------------------------------------------------------- sfx
def sfx_stem():
    x = buf()
    sc = {s["key"]: s for s in TL.scenes}
    s1, s2, s3 = sc["s1"], sc["s2"], sc["s3"]
    s4, s5, s6 = sc["s4"], sc["s5"], sc["s6"]

    # ---- S1
    add(x, sub_drop(0.0, 82, 24, 2.0, 1.1), s1["start"] + 0.02)
    add(x, crackle(11.5, density=9, gain=0.30), s1["start"] + 0.5)
    add(x, hiss(16.0, 0.10, lo=200, hi=5200), s1["start"] + 0.4)
    c_diss = TL.cue("s1", "existed")
    add(x, whoosh(2.6, 500, 120, 0.22, down=True), s1["start"] + c_diss - 0.2)
    add(x, glass(1046.5, 1.6, 0.20), s1["start"] + c_diss + 0.4)
    c_ghost = TL.cue("s1", "ghost")
    add(x, glass(1568.0, 1.8, 0.26), s1["start"] + c_ghost)
    add(x, sub_drop(0.0, 96, 30, 1.1, 0.85), s1["start"] + c_ghost)
    add(x, snip(0.5), s1["start"] + c_ghost + 0.02)

    # ---- S2
    c_base = TL.cue("s2", "baseline")
    c_carve = TL.cue("s2", "carving")
    c_blue = TL.cue("s2", "blueprint")
    add(x, riser(2.0, 80, 520, 0.30), s2["start"] + c_base - 2.0)
    add(x, sub_drop(0.0, 110, 34, 1.2, 0.75), s2["start"] + c_base)
    add(x, crackle(7.0, density=13, gain=0.22), s2["start"] + c_base + 0.2)
    for k in range(16):
        add(x, click(0.10, 1200 + k * 90), s2["start"] + c_base + 0.5 + k * 0.30)
    add(x, thud(0.9, 58, 1.0), s2["start"] + c_blue + 0.02)
    add(x, chime(880.0, 1.4, 0.14), s2["start"] + c_blue + 0.05)

    # ---- S3
    c_abrupt = TL.cue("s3", "abruptly")
    add(x, hiss(20.0, 0.06, lo=150, hi=4000), s3["start"] + 0.2)
    add(x, tape_stop(0.55, 0.55, 150), s3["start"] + c_abrupt + 0.02)
    add(x, snip(0.9), s3["start"] + c_abrupt + 0.06)
    add(x, sub_drop(0.0, 120, 40, 0.9, 0.9), s3["start"] + c_abrupt + 0.03)
    add(x, pad([110.0, 164.8], s3["end"] - (s3["start"] + c_abrupt) - 0.5, 0.16,
               attack=0.6, release=1.0, bright=0.2),
        s3["start"] + c_abrupt + 0.4)
    c_file = TL.cue("s3", "file")
    add(x, chime(660.0, 2.0, 0.16), s3["start"] + c_file)

    # ---- S4
    c_flags = TL.cue("s4", "flags")
    c_art = TL.cue("s4", "artifact")
    add(x, hiss(14.0, 0.13, lo=300, hi=6500), s4["start"] + 0.2)
    for k in range(3):
        add(x, snip(0.65), s4["start"] + c_flags + 0.15 + k * 0.60)
    add(x, whoosh(1.2, 200, 1800, 0.16), s4["start"] + c_art - 0.6)
    add(x, thud(1.0, 70, 0.5), s4["start"] + c_art + 0.6)
    for k, f in enumerate((261.6, 329.6, 392.0)):
        add(x, piano(f, 4.0, 0.22), s4["start"] + c_art + 1.0 + k * 0.10)

    # ---- S5 (scale + vault)
    c_disq = TL.cue("s5", "disqualify")
    c_second = TL.cue("s5", "Second")
    c_key = TL.cue("s5", "key")
    c_bound = TL.cue("s5", "boundaries")
    add(x, thud(1.4, 72, 0.55), s5["start"] + c_disq + 2.2)
    add(x, snip(0.35), s5["start"] + c_disq + 2.25)
    add(x, whoosh(0.8, 300, 1600, 0.35), s5["start"] + c_second + 0.2)
    add(x, thud(0.7, 62, 0.7), s5["start"] + c_second + 1.0)
    for k in range(4):
        add(x, click(0.5, 700 + k * 120), s5["start"] + c_key + 1.6 + k * 0.34)
    add(x, pad([58.3, 87.3], 3.0, 0.22, attack=0.2, release=1.5, bright=0.3),
        s5["start"] + c_key + 1.0)
    add(x, whoosh(1.6, 200, 3200, 0.40, down=False), s5["start"] + c_bound - 0.2)
    add(x, sub_drop(0.0, 90, 28, 1.4, 0.7), s5["start"] + c_bound + 0.1)

    # ---- S6
    c_close = TL.cue("s6", "close")
    c_proto = TL.cue("s6", "prototype")
    add(x, snip(0.4), s6["start"] + c_proto + 0.1)
    add(x, snip(0.55), s6["start"] + c_close + 0.2)
    add(x, thud(0.5, 90, 0.35), s6["start"] + c_close + 0.2)
    add(x, glass(1318.5, 2.4, 0.10), s6["start"] + c_close + 0.9)
    end_t = s6["lead"] + s6["beat"]["dur"]
    add(x, sub_drop(0.0, 70, 22, 2.6, 0.55), s6["start"] + end_t + 0.9)
    return x


# ---------------------------------------------------------------- mix
def write_wav(path, stereo, bits=24):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    x = np.clip(stereo, -1.0, 1.0)
    if bits == 24:
        i = (x * 8388607).astype(np.int32)
        raw = b"".join(int(v).to_bytes(3, "little", signed=True) for v in i.reshape(-1)[:4000])
        # write per-sample 3-byte packing in blocks (fast path via numpy below)
        arr = i.reshape(-1).astype(np.int32)
        b = np.empty(arr.size * 3, dtype=np.uint8)
        b[0::3] = (arr & 0xFF).astype(np.uint8)
        b[1::3] = ((arr >> 8) & 0xFF).astype(np.uint8)
        b[2::3] = ((arr >> 16) & 0xFF).astype(np.uint8)
        payload = b.tobytes()
        sampwidth = 3
    else:
        payload = (x * 32767).astype(np.int16).tobytes()
        sampwidth = 2
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(sampwidth)
        w.setframerate(SR)
        w.writeframes(payload)


def rms(x):
    return float(np.sqrt(np.mean(x ** 2) + 1e-12))


def db(v):
    return 20 * math.log10(max(v, 1e-9))


def build():
    os.makedirs(OUT, exist_ok=True)
    print("  voice...")
    voice, cues = voice_stem()
    duck = build_duck(cues)
    print("  music...")
    music = music_stem(duck)
    print("  sfx...")
    sfx = sfx_stem()

    # reference = voice RMS while speaking
    vmask = np.zeros(N, dtype=bool)
    for (_k, v0, v1) in cues:
        vmask[int(v0 * SR):min(N, int(v1 * SR))] = True
    v_ref = rms(voice[vmask])
    print(f"  voice RMS {db(v_ref):.1f} dBFS")

    m_gain = (v_ref / max(1e-9, rms(music[vmask]))) * 10 ** (-17.0 / 20)
    s_gain = (v_ref / max(1e-9, rms(sfx[vmask]))) * 10 ** (-11.0 / 20)
    mix = voice * 1.0 + music * m_gain + sfx * s_gain

    # gentle bus glue: soft clip + peak normalise to -1.5 dBFS
    peak = np.abs(mix).max()
    mix = np.tanh(mix / max(1e-9, peak) * 1.15) / math.tanh(1.15)
    mix *= 10 ** (-1.5 / 20)

    write_wav(os.path.join(OUT, "voice.wav"), voice)
    write_wav(os.path.join(OUT, "music.wav"), music * m_gain)
    write_wav(os.path.join(OUT, "sfx.wav"), sfx * s_gain)
    write_wav(os.path.join(OUT, "mix.wav"), mix)
    print(f"  mix: {N / SR:.2f}s  peak {db(np.abs(mix).max()):.1f} dBFS  "
          f"rms {db(rms(mix)):.1f} dBFS")
    return dict(voice=v_ref, music=m_gain, sfx=s_gain)


if __name__ == "__main__":
    build()
