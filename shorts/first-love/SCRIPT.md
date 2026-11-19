# FIRST LOVE — the dark psychology of the one that never happened

| | |
|---|---|
| Format | 1080 × 1920 (9:16), 30 fps |
| Runtime | 2:43.8 (163.82 s), 4,915 frames |
| Narration | 384 words, ~148 wpm, one male voice (`voice-01`) |
| Picture | 2D vector, programmatic (Pillow supersampled raster), no stock footage |
| Sound | fully synthesized score + SFX, master −14.9 LUFS |
| Type | Montserrat Black / Inter / JetBrains Mono |
| Palette | void `#0B0D12` · shadow `#161B26` · reality `#4EA8DE` · memory `#E4A261`/`#F4A261` · danger `#E63946` · type `#F1FAEE` |

---

## 1. Research brief (as supplied, used verbatim as the film's spine)

**Neural imprinting / critical-period plasticity.** In adolescence the reward
circuitry (ventral tegmental area, nucleus accumbens) is hyper-responsive to
dopamine while the prefrontal cortex — impulse regulation, reality testing — is
still maturing. The first romantic attachment therefore lands on a brain with no
baseline, and becomes a template for what "love" is supposed to feel like.

**The Zeigarnik effect and incomplete closure.** Unfinished tasks and unresolved
emotional loops are retained more vividly than completed ones. First loves rarely
end by natural exhaustion; they end on timing, distance or immaturity, so the
loop never gets a boring, natural ending — and the mind keeps the file open.

**Euphoric recall and idealisation.** Autobiographical memory strips the friction
and amplifies the peaks. What is remembered is not a person but a highlight reel
fused with the viewer's own lost innocence — an artefact, not a human being.

**The dark leverage.** Internally: every new partner is measured against a ghost,
and no living person beats a memory that never ages or disappoints. Externally:
anyone who knows you are still tethered to that archetype — or the first love
themselves, resurfacing — holds a key that bypasses adult boundaries and returns
you to your most unguarded, compliant self.

> Framing note: this is the popular-science account that the brief asks for, and
> the film voices it as such. It is a stylised explainer, not a clinical claim:
> "imprinting" here is a metaphor for a strong early attachment, not a literal
> neurological lock, and the reward-system story is a simplification of a
> still-debated literature.

---

## 2. Narration (verbatim from the brief) and measured timings

| # | Beat | Words | Measured | Start |
|---|---|---|---|---|
| 1 | THE HOOK | 42 | 16.68 s | 0:00.55 |
| 2 | THE IMPRINT | 79 | 31.08 s | 0:18.33 |
| 3 | THE ZEIGARNIK LOOP | 75 | 31.28 s | 0:50.11 |
| 4 | THE IDEALISATION TRAP | 66 | 26.72 s | 1:22.19 |
| 5 | THE DARK VULNERABILITY | 80 | 33.48 s | 1:49.66 |
| 6 | THE CLOSING SHIFT | 42 | 16.08 s | 2:24.14 |

**On the brief's "110–120 s at 145 wpm":** the supplied script is 384 words, so
at 145 wpm it would be ~2:39 — the 110–120 s target and the script cannot both
hold. The film keeps every word and runs 2:43.8 at ~148 wpm. Trimming to 110 s
means cutting ~130 words (the Imprint and Idealisation beats carry most of it).

---

## 3. Cue sheet — every on-screen word is locked to a spoken word

Times are absolute; "locked to" is the spoken word the animation is keyed to
(`lib/timeline.py: TL.cue()`). Everything is derived from `narration/words.json`,
whose word timings are sentence-snapped to the real pauses in the TTS audio.

### 1 · THE GHOST TRAP — 0.00 → 17.88 s

| abs | on screen | locked to |
|---|---|---|
| 3.01 | NOT A / PERSON. | "haunted" |
| 6.79 | MEMORY ARTIFACT / UNVERIFIED (mono, typed) | "existed" |
| 13.16 | REAL PEOPLE → DISQUALIFIED | "sabotaging" |
| 16.30 | A GHOST. (crimson, snap-zoom) | "ghost" |

Picture: over-the-shoulder POV at a table. A pendant lamp lights an empty chair
across from us; the "person" in it is a scanline hologram — contour traced from a
real seated silhouette, interior made of light, glitching and dissolving into
dust as the voice says *never actually existed*. Cold light then reclaims the
chair. The amber ghost is the only warm object in the frame.

### 2 · NEURAL IMPRINT — 17.88 → 49.81 s

| abs | on screen | locked to |
|---|---|---|
| 22.88 | WHO THEY WERE (struck through) | "who" |
| 25.63 | WHEN THEY HAPPENED | "when" |
| 32.27 | NO BASELINE. | "baseline" |
| 33.47 | `» QUERY: IS THIS PERSON GOOD FOR ME?` | "baseline" |
| 40.57 | NEURAL BLUEPRINT card (stamp + shake) | "blueprint" |
| 42.91 | `» QUERY: DOES THIS FEEL LIKE THE FIRST TIME?` | "subconscious" |

Picture: a measurement grid room, a geometric head profile, a skull chamber. A
spark drops into the neural web and a wavefront etches every edge amber; the
console swaps the question the brain is asking; a blueprint card stamps into the
lower third with the imprint locked.

### 3 · THE ZEIGARNIK LOOP — 49.81 → 81.84 s

| abs | on screen | locked to |
|---|---|---|
| 52.67 | ZEIGARNIK / EFFECT | "Zeigarnik" |
| 62.70 | UNFINISHED / BUSINESS | "laundry" |
| 73.80 | THE STORY NEVER ENDED. | "conclusion" |
| 75.97 | FILE: UNCLOSED (blinking badge) | "file" |

Picture: an "attachment ledger". Track A (10-YR RELATIONSHIP) fills steadily,
closes its ring and desaturates. Track B (FIRST LOVE) accelerates with crimson
spikes, shears off mid-air, and its broken end becomes a loading ring that never
resolves — with a live `OPEN 00:SS` counter that flips to "30 YEARS" on the word
*decades*.

### 4 · EUPHORIC RECALL — 81.84 → 109.31 s

| abs | on screen | locked to |
|---|---|---|
| 87.56 | EUPHORIC / RECALL | "recall" |
| 92.61 | EDITED / REALITY (struck) | "flags" |
| 100.70 | AN ARTIFACT. | "artifact" |
| 104.33 | AT THEIR PEAK. | "peak" |

Picture: a film band with five frames — arguments, waiting, red flags in cold
grey; peak moments in gold. Each flaw is sliced out where it sits and the strip
closes up (`FRAMES RETAINED 5/5 → 2/5`). The surviving gold frames fly into a
plinth and become the bust on it; a glass case closes as the voice says
*guarded*.

### 5 · THE DARK LEVERAGE — 109.31 → 143.59 s

| abs | on screen | locked to |
|---|---|---|
| 115.36 | NOBODY LIVING CAN COMPETE. | "partners" |
| 122.63 | INTENSITY IS NOT LOVE | "intensity" |
| 131.23 | SKELETON KEY | "key" |
| 135.51 | BOUNDARIES DISSOLVED. | "boundaries" |

Picture: a balance. A solid blue figure stands on one pan; an amber hologram
hovers weightless on the other — and the beam tips toward the hologram anyway,
spilling the real figure. Cut to a vault door labelled ADULT BOUNDARIES: bolts
retract one by one, a skeleton key turns without resistance, and the door swings
open on warm light.

### 6 · CLOSE THE FILE — 143.59 → 163.82 s

| abs | on screen | locked to |
|---|---|---|
| 147.06 | A PROTOTYPE. | "prototype" |
| 150.49 | CLOSE THE FILE. | "close" |
| 158.04 | KEEP THE SEAT EMPTY. | "sit" |
| 161.72 | FILE CLOSED (end card) | end of narration |

Picture: back at the table, camera pulling out. The corner file tab — FIRST LOVE
/ PROTOTYPE / OPEN — snaps shut to CLOSED. The hologram powers down, the room
turns from cold blue to warm daylight, and the chair is simply empty. One piano
note, then silence.

---

## 4. Design rules used throughout

- **One idea per frame.** A single graphic metaphor, one statement, one mono
  annotation — never two headline blocks at once.
- **Type is the narrator's hand.** Headlines assemble word by word on the spoken
  word; nothing appears before it is said. Words under scrutiny get struck
  through in crimson.
- **Amber = memory, blue = reality, crimson = danger.** The ghost, the pedestal,
  the vault light and the surviving film frames are amber; the chair, the
  present-tense figure and the lamp are blue.
- **Every frame moves.** Slow push-ins (1.00→1.06 over a scene), tracked
  timelines, drifting particles, flicker on the hologram — no static holds.
- **Furniture, not captions.** A chapter eyebrow (top left), a series mark (top
  right) and a six-segment progress rail (bottom) hold the film together without
  describing the picture.
- **Grain and vignette on every frame**, 3.6–4.0 % grain, so the vector picture
  reads as film rather than slides.
