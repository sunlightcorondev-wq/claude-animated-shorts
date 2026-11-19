"""Master timeline: scene schedule, word-locked cues, absolute<->local time.

The picture is built from the narration: each beat's measured duration sets its
scene's length, and every on-screen word animation is keyed to a word in that
beat (via `cue()`), so text lands within a frame or two of the voice.
"""
import json
import math
import os

import words as W

FPS = 30
WIDTH, HEIGHT = 1080, 1920

# key, lead-in before the voice, tail after the voice
SCHEDULE = [
    ("s1", "THE GHOST TRAP", 0.55, 0.65),
    ("s2", "NEURAL IMPRINT", 0.45, 0.40),
    ("s3", "THE ZEIGARNIK LOOP", 0.30, 0.45),
    ("s4", "EUPHORIC RECALL", 0.35, 0.40),
    ("s5", "THE DARK LEVERAGE", 0.35, 0.45),
    ("s6", "CLOSE THE FILE", 0.55, 3.60),
]


class Timeline:
    def __init__(self):
        self.beats = {}
        for key, _title, _lead, _tail in SCHEDULE:
            path = os.path.join(W.NARR, "words.json")
            if os.path.exists(path):
                self.beats = json.load(open(path))
                break
        if not self.beats:
            self.beats = W.build()
        self.scenes = []
        t = 0.0
        for i, (key, title, lead, tail) in enumerate(SCHEDULE):
            dur = self.beats[key]["dur"]
            start = t
            voice = start + lead
            end = voice + dur + tail
            self.scenes.append(dict(i=i + 1, key=key, title=title, start=start,
                                    voice=voice, lead=lead, end=end, dur=end - start,
                                    beat=self.beats[key]))
            t = end
        self.duration = t
        self.frames = int(math.ceil(self.duration * FPS))

    # ---------------------------------------------------------------- queries
    def scene_at(self, t):
        for s in self.scenes:
            if t < s["end"]:
                return s
        return self.scenes[-1]

    def local(self, t):
        s = self.scene_at(t)
        return s, t - s["start"]

    def word_time(self, key, index):
        """Absolute time (seconds) the given word starts."""
        s = next(x for x in self.scenes if x["key"] == key)
        return s["voice"] + s["beat"]["words"][index]["t0"]

    def word_end(self, key, index):
        s = next(x for x in self.scenes if x["key"] == key)
        return s["voice"] + s["beat"]["words"][index]["t1"]

    def cue(self, key, phrase, n=1, offset=0.0):
        """Local scene time of the nth occurrence of `phrase` in the beat's voice."""
        i = W.find(key, phrase, n)
        return self.word_time(key, i) - self.scenes[[s["key"] for s in self.scenes].index(key)]["start"] + offset

    def cue_abs(self, key, phrase, n=1):
        i = W.find(key, phrase, n)
        return self.word_time(key, i)

    def word_span(self, key, phrase, n=1):
        i = W.find(key, phrase, n)
        s = next(x for x in self.scenes if x["key"] == key)
        return self.word_time(key, i) - s["start"], self.word_end(key, i) - s["start"]

    def scene(self, key):
        return next(x for x in self.scenes if x["key"] == key)


TL = Timeline()

if __name__ == "__main__":
    print(f"duration {TL.duration:.2f}s  {TL.frames} frames @ {FPS}fps")
    for s in TL.scenes:
        print(f"  {s['i']} {s['key']} {s['title']:20s} start {s['start']:7.2f} "
              f"voice {s['voice']:7.2f} end {s['end']:7.2f}  ({s['dur']:.2f}s)")
    print("\nlocal cues:")
    for key, phrase in [("s1", "haunted"), ("s1", "ghost"), ("s2", "who"),
                        ("s2", "when"), ("s2", "baseline"), ("s2", "blueprint"),
                        ("s2", "subconscious"), ("s3", "Zeigarnik"), ("s3", "laundry"),
                        ("s3", "abruptly"), ("s3", "file"), ("s3", "decades"),
                        ("s4", "recall"), ("s4", "reel"), ("s4", "artifact"),
                        ("s5", "disqualify"), ("s5", "intensity"), ("s5", "key"),
                        ("s5", "boundaries"), ("s6", "prototype"), ("s6", "close")]:
        t0, t1 = TL.word_span(key, phrase)
        print(f"  {key} {phrase:12s} {t0:7.2f} - {t1:7.2f}")
