"""Narration text + word-level timing.

The TTS gives us one file per beat, so we derive word timings:
  1. detect real speech spans from the RMS envelope (so lines land on actual pauses),
  2. snap every sentence boundary to the nearest pause,
  3. distribute the words inside a sentence by syllable weight.

`timeline.py` then resolves cues like ("s1", "ghost") to a local scene time, which is
what every on-screen word animation is keyed to.
"""
import json
import os
import re
import wave

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NARR = os.path.join(ROOT, "narration")

# Verbatim narration, split into the six beats of the brief.
SCRIPT = {
    "s1": "You don't miss your first love. You're being haunted by a version of them "
          "that never actually existed. And if you don't realize how that trap works, "
          "you will spend the rest of your life sabotaging real people to protect a ghost.",
    "s2": "Here is the uncomfortable truth: your first love wasn't special because of who "
          "they were. They were special because of when they happened. When you experience "
          "romantic attachment for the very first time, your brain doesn't have a baseline. "
          "It floods your underdeveloped reward system with raw dopamine and oxytocin, "
          "carving a permanent neural blueprint. From that moment on, your subconscious "
          "stops asking, is this person good for me? And starts asking, does this feel "
          "like the first time?",
    "s3": "Then comes the psychological lock: the Zeigarnik Effect. The human mind is wired "
          "to obsess over unfinished business. Most first loves don't end because the spark "
          "slowly died out over ten years of paying rent and folding laundry. They end "
          "abruptly, cut short by distance, immaturity, or timing. Because the story never "
          "reached a boring, natural conclusion, your brain refuses to close the file. It "
          "keeps the loop running silently in the background for decades.",
    "s4": "And over time, your memory starts lying to you. Through a bias called euphoric "
          "recall, your brain edits out the awkwardness, the immaturity, and the red flags, "
          "leaving behind a high definition highlight reel. You aren't missing a human being "
          "anymore. You're worshiping an artifact. A frozen snapshot of who they were at "
          "their peak, fused with who you were before the world made you guarded.",
    "s5": "Here is where it turns dangerous. First, you use that phantom standard to quietly "
          "disqualify healthy, present partners who actually show up. Because real intimacy "
          "feels calm, while your brain was trained to mistake intensity for love. Second, if "
          "that person ever steps back into your life years later, they hold an unfair "
          "psychological skeleton key. One familiar phrase, one hit of nostalgia, and your "
          "adult boundaries dissolve, reverting you back to the most unguarded, easily "
          "manipulated version of yourself.",
    "s6": "Your first love wasn't your soulmate. They were a prototype. Honor what that "
          "chapter taught you, then close the file. Because as long as you keep a seat saved "
          "for a ghost, no one real will ever be able to sit down.",
}

FILES = {
    "s1": "s1_hook.wav", "s2": "s2_imprint.wav", "s3": "s3_zeigarnik.wav",
    "s4": "s4_recall.wav", "s5": "s5_danger.wav", "s6": "s6_close.wav",
}

VOWELS = "aeiouy"


def syllables(word):
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return 1
    n, prev = 0, False
    for ch in w:
        v = ch in VOWELS
        if v and not prev:
            n += 1
        prev = v
    if w.endswith("e") and n > 1 and not w.endswith("le"):
        n -= 1
    return max(1, n)


def load_wav(path):
    w = wave.open(path)
    sr = w.getframerate()
    a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    if w.getnchannels() > 1:
        a = a.reshape(-1, w.getnchannels()).mean(axis=1)
    return a, sr


def speech_spans(a, sr, hop=0.02, min_sil=0.16):
    """Return [(start, end)] of voiced regions in seconds."""
    h = int(sr * hop)
    n = len(a) // h
    rms = np.sqrt((a[:n * h].reshape(n, h) ** 2).mean(axis=1) + 1e-12)
    thr = max(0.012, np.percentile(rms, 12) + 0.11 * (np.percentile(rms, 95) - np.percentile(rms, 12)))
    voiced = rms > thr
    spans, i, n = [], 0, len(voiced)
    while i < n:
        if voiced[i]:
            j = i
            while j < n and voiced[j]:
                j += 1
            spans.append((i * hop, j * hop))
            i = j
        else:
            i += 1
    merged = []
    for s in spans:
        if merged and s[0] - merged[-1][1] < min_sil:
            merged[-1] = (merged[-1][0], s[1])
        else:
            merged.append(list(s) if False else (s[0], s[1]))
    return merged


def beat_words(key):
    words = SCRIPT[key].split()
    # sentence boundaries: word index that starts a sentence
    starts = [0]
    for i, w in enumerate(words[:-1]):
        if re.search(r"[.?!:]$", w):
            starts.append(i + 1)
    return words, starts


def beat_timing(key):
    a, sr = load_wav(os.path.join(NARR, FILES[key]))
    dur = len(a) / sr
    words, sent_starts = beat_words(key)
    spans = speech_spans(a, sr)
    if spans:
        speech_start, speech_end = spans[0][0], spans[-1][1]
    else:
        speech_start, speech_end = 0.0, dur
    speech_start = max(0.0, speech_start - 0.05)
    speech_end = min(dur, speech_end + 0.06)
    total_w = sum(syllables(w) for w in words)
    span_t = speech_end - speech_start
    # proportional time per sentence start, then snap to a pause centre
    bounds = [speech_start]
    cum = 0
    pauses = [(spans[i][1] + spans[i + 1][0]) * 0.5 for i in range(len(spans) - 1)]
    for si, wstart in enumerate(sent_starts[1:], start=1):
        cum = sum(syllables(w) for w in words[:wstart])
        guess = speech_start + span_t * cum / total_w
        best, bestd = None, 0.42
        for p in pauses:
            d = abs(p - guess)
            if d < bestd:
                best, bestd = p, d
        bounds.append(best if best is not None else guess)
    bounds.append(speech_end)
    # distribute within each sentence
    times = [0.0] * len(words)
    for si in range(len(sent_starts)):
        i0 = sent_starts[si]
        i1 = sent_starts[si + 1] if si + 1 < len(sent_starts) else len(words)
        t0, t1 = bounds[si], bounds[si + 1]
        seg_w = sum(syllables(w) for w in words[i0:i1])
        cur = t0
        for i in range(i0, i1):
            d = (t1 - t0) * syllables(words[i]) / max(1, seg_w)
            times[i] = (cur, cur + d)
            cur += d
    return {"key": key, "file": FILES[key], "dur": dur, "words": words,
            "times": times, "spans": spans, "voiced": (speech_start, speech_end)}


def build(save=True):
    out = {}
    for key in SCRIPT:
        bt = beat_timing(key)
        out[key] = {"dur": bt["dur"], "file": bt["file"],
                    "words": [{"w": w, "t0": round(a, 3), "t1": round(b, 3)}
                              for w, (a, b) in zip(bt["words"], bt["times"])]}
    if save:
        with open(os.path.join(NARR, "words.json"), "w") as f:
            json.dump(out, f, indent=1)
    return out


def find(key, phrase, occurrence=1):
    """Return (word_index, time) of the nth occurrence of a phrase in a beat."""
    words = SCRIPT[key].split()
    needle = phrase.lower().split()
    hits = []
    for i in range(len(words) - len(needle) + 1):
        if [w.lower().strip(".,:;?!") for w in words[i:i + len(needle)]] == needle:
            hits.append(i)
    if len(hits) < occurrence:
        raise KeyError(f"{phrase!r} #{occurrence} not in {key}")
    return hits[occurrence - 1]


if __name__ == "__main__":
    data = build()
    for k, v in data.items():
        print(f"{k}: {v['dur']:.2f}s  {len(v['words'])} words  "
              f"first={v['words'][0]['t0']:.2f} last={v['words'][-1]['t1']:.2f}")
    print("\ncue check:")
    for k, phrase in [("s1", "ghost"), ("s1", "haunted"), ("s2", "baseline"),
                      ("s2", "blueprint"), ("s3", "Zeigarnik"), ("s3", "file"),
                      ("s3", "decades"), ("s4", "recall"), ("s4", "artifact"),
                      ("s5", "intensity"), ("s5", "skeleton"), ("s5", "boundaries"),
                      ("s6", "prototype"), ("s6", "close")]:
        i = find(k, phrase)
        w = data[k]["words"][i]
        print(f"  {k:3s} {phrase:12s} -> word {i:3d}  {w['t0']:6.2f}s")
