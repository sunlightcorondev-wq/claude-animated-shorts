# FIRST LOVE — 2D dark-psychology explainer (1080×1920, 2:44)

A worked example for this skill's *other* register: not the cartoon-3D story, but
the flat, high-contrast, kinetic-type explainer. Everything is drawn
programmatically (Pillow, supersampled), scored and sound-designed with numpy
synthesis, and rendered deterministically from the narration's own word timings.

> Deliverable: `out/video/first_love_1080x1920.mp4` — 1080×1920, 30 fps, 2:43.8,
> H.264 High + AAC 48 kHz stereo, −14.9 LUFS / −1.5 dBFS, 123 MB.
> Built media is git-ignored (the repo carries the source); `python3 build.py`
> regenerates every frame and sample from `lib/`.

## Quick start

```bash
pip install pillow numpy imageio-ffmpeg fonttools brotli   # + system python 3.11
python3 build.py audio        # synth score + SFX, mix under the voice   (~45 s)
python3 build.py render       # 4,915 frames, 2 workers                  (~60 min)
python3 build.py mux          # H.264 + AAC, faststart
python3 build.py qa           # black/frozen/pop scan, loudness, contact sheet
python3 build.py sheet --times 6,30,70,100,130,160 --scale 0.26   # quick look
```

`build.py stills --times 12.5 --scale 0.5` renders one frame at a chosen moment —
handy while designing, since a frame is a pure function of its index.

## How the timing works

The film is built *from the voice*, not the other way round:

1. Six narration beats are generated separately (`narration/s1…s6`), so each
   beat's exact duration is known.
2. `lib/words.py` finds the real pauses in each WAV (RMS envelope), snaps every
   sentence boundary to the nearest pause, and distributes words inside a
   sentence by syllable weight → `narration/words.json`.
3. `lib/timeline.py` lays the scenes out around those beats and exposes
   `TL.cue("s2", "blueprint")` → the local time of that spoken word.
4. Every on-screen statement is keyed to a word, e.g.
   `Kinetic(..., t_in=TL.cue("s5", "intensity") - 0.3)`.

Nothing is hard-coded to a guessed timecode, so re-recording the voice re-times
the whole film.

## Files

| Path | What it is |
|---|---|
| `SCRIPT.md` | Research brief, narration, measured timings, full cue sheet, design rules |
| `build.py` | CLI: stills / sheet / render / audio / mux / qa |
| `lib/timeline.py` | Scene schedule, absolute↔local time, word cues |
| `lib/words.py` | Narration text, pause detection, word timings |
| `lib/gfx.py` | Supersampled vector surface, camera, emissive layers, film post |
| `lib/type.py` | Kinetic type: word rises, strikes, tracking-in mono, badges |
| `lib/motifs.py` | Reusable cast/props: table, chair, scanline hologram, head profile, neural web, film icons |
| `lib/scenes.py` | The six scenes, each a pure function of local time |
| `lib/audio.py` | Synthesized score, SFX, ducking, mix |
| `lib/qa.py` | Frame scan + EBU R128 loudness + contact sheet |
| `fonts/` | Montserrat, Inter, JetBrains Mono (OFL — see `fonts/README.md`) |

## The rendering model

- Author in logical 1080×1920; rasterise at 2× (2160×3840) and downscale with
  Lanczos, so vector edges and type stay sharp.
- The camera is baked into the coordinate mapping (`Cam`: zoom / focus / pan), so
  a push-in re-rasterises instead of upscaling pixels. Type is drawn on a flat
  "UI camera" so it never zooms or drifts with the world.
- Emissive light (lamp cones, glows, the hologram's hot scan band) is drawn into
  quarter-res luminance masks, blurred, tinted and added; then bloom from real
  highlights, filmic curve, cool shadows, vignette, 3.6 % grain.
- The hologram: a real seated silhouette is rasterised to a 1/4-res mask, each
  scanline is reduced to its left/right extent, and the extents become the
  contour (smoothed) plus faint interior light — a person made of nothing but
  light, which dissolves into fragments and dust.

## Look

Void `#0B0D12`, shadow `#161B26`, reality `#4EA8DE`, memory `#F4A261`,
danger `#E63946`, type `#F1FAEE`. Montserrat Black for statements, JetBrains
Mono for annotations and technical furniture. Amber is always memory, blue is
always the present, crimson is always the thing that hurts.

Details and the full cue sheet: `SCRIPT.md`.

## Output

| File | What |
|---|---|
| `out/video/first_love_1080x1920.mp4` | the film (4,914 frames, 6.3 Mbps) |
| `out/video/poster.jpg` | cover frame (the chair, after the file shuts) |
| `out/qa/contact.jpg` | 22-frame contact sheet of the finished file |
| `out/qa/qa.txt`, `qa.json` | frame scan + loudness report |
| `out/preview/` | the three accepted design sheets (S1, S3, S6) |

Final QA on the encoded file: 4,914 frames, mean luma 19.2 (range 0.6–52),
no frozen or white frames, the only dark frames being the four scripted
dip-to-black scene changes (17.9 / 49.8 / 81.8 / 109.3 s); loudness −14.9 LUFS
integrated, LRA 3.7 LU, true peak −1.5 dBFS.

Encode note: film grain is expensive. At CRF 17 the picture encoded to 500 MB+;
the delivered file is CRF 31 with `aq-mode=3` and light deblocking (6.3 Mbps),
which keeps type edges and the glow gradients clean and turns the grain into
soft texture. Encode from the frame sequence, never from a previous encode.

## Notes and limits

- The brief asked for 110–120 s at 145 wpm; its own script is 384 words, which is
  ~2:39 at that pace. The film keeps every word (2:43.8 at ~148 wpm). Cutting to
  ~110 s means removing ~130 words — the Imprint and Idealisation beats are where
  the trim would come from.
- The psychology is the brief's popular-science framing, voiced as such (see the
  framing note in `SCRIPT.md`).
- The narration is TTS; the voice was auditioned for tone (steady, low, unemotional
  in the way the genre wants).
