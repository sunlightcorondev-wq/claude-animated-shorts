#!/usr/bin/env python3
"""FIRST LOVE - build pipeline.

  python3 build.py stills --times 1,4,9 --scale 0.5 [--tag look]
  python3 build.py sheet  --times 1,4,9,12 --scale 0.28 --out out/preview/sheet.jpg
  python3 build.py render --workers 2 [--start 0 --end 99999]
  python3 build.py audio
  python3 build.py mux
  python3 build.py qa

Everything is deterministic: a frame is a pure function of its index.
"""
import argparse
import glob
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from gfx import Frame
from timeline import FPS, HEIGHT, TL, WIDTH
import scenes

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "out")
FRAMES = os.path.join(OUT, "frames")


def render_time(t, scale=1.0, S=2, scene_key=None):
    scene = TL.scene_at(t) if scene_key is None else TL.scene(scene_idx(scene_key))
    fn = scenes.SCENES[scene["key"]]
    f = Frame(WIDTH, HEIGHT, S)
    fn(f, t - scene["start"], scene)
    img = f.compose(tick=int(round(t * FPS)))
    if scale != 1.0:
        img = img.resize((int(WIDTH * scale), int(HEIGHT * scale)), Image.LANCZOS)
    return img


def scene_idx(key):
    for i, s in enumerate(TL.scenes):
        if s["key"] == key:
            return i
    raise KeyError(key)


def render_frame(i, scale=1.0, S=2):
    return render_time(i / FPS, scale=scale, S=S)


# ------------------------------------------------------------------ stills
def cmd_stills(a):
    os.makedirs(os.path.join(OUT, "stills"), exist_ok=True)
    times = [float(x) for x in a.times.split(",") if x.strip()]
    tag = a.tag or "still"
    paths = []
    for t in times:
        t0 = time.time()
        img = render_time(t, scale=a.scale, S=a.S)
        name = f"{tag}_{t:07.2f}s_{TL.scene_at(t)['key']}.jpg"
        p = os.path.join(OUT, "stills", name)
        img.save(p, quality=92)
        print(f"  {p}  ({time.time() - t0:.2f}s)")
        paths.append(p)
    return paths


def cmd_sheet(a):
    os.makedirs(os.path.join(OUT, "preview"), exist_ok=True)
    times = [float(x) for x in a.times.split(",") if x.strip()]
    scale = a.scale
    w, h = int(WIDTH * scale), int(HEIGHT * scale)
    cols = min(a.cols, len(times))
    rows = (len(times) + cols - 1) // cols
    pad, lab = 10, 26
    sheet = Image.new("RGB", (cols * (w + pad) + pad, rows * (h + pad + lab) + pad),
                      (18, 18, 20))
    d = ImageDraw.Draw(sheet)
    fnt = ImageFont.load_default()
    for k, t in enumerate(times):
        img = render_time(t, scale=scale, S=a.S)
        cx = pad + (k % cols) * (w + pad)
        cy = pad + (k // cols) * (h + pad + lab)
        sheet.paste(img, (cx, cy + lab))
        sc = TL.scene_at(t)
        d.text((cx + 2, cy + 6), f"{t:6.2f}s  {sc['key']}  l={t - sc['start']:5.2f}",
               fill=(235, 235, 235), font=fnt)
    out = a.out or os.path.join(OUT, "preview", "sheet.jpg")
    sheet.save(out, quality=90)
    print(out)
    return out


# ------------------------------------------------------------------ render
def _worker(args):
    lo, hi, scale, S, path = args
    os.makedirs(path, exist_ok=True)
    for i in range(lo, hi):
        p = os.path.join(path, f"{i:05d}.jpg")
        if os.path.exists(p):
            continue
        render_frame(i, scale=scale, S=S).save(p, quality=95, subsampling=0,
                                               optimize=False)
    return hi - lo


def cmd_render(a):
    from multiprocessing import Pool
    os.makedirs(FRAMES, exist_ok=True)
    start = a.start
    end = min(a.end, TL.frames)
    chunk = 60
    jobs = [(i, min(i + chunk, end), 1.0, a.S, FRAMES) for i in range(start, end, chunk)]
    t0 = time.time()
    done = 0
    with Pool(a.workers) as p:
        for n in p.imap_unordered(_worker, jobs):
            done += n
            el = time.time() - t0
            rate = done / max(1e-3, el)
            print(f"  {done}/{end - start} frames  {rate:.2f} f/s  eta "
                  f"{(end - start - done) / max(1e-3, rate) / 60:.1f} min", flush=True)


# ------------------------------------------------------------------ audio
def cmd_audio(a):
    import audio
    audio.build()


def cmd_mux(a):
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    os.makedirs(os.path.join(OUT, "video"), exist_ok=True)
    silent = os.path.join(OUT, "video", "picture.mp4")
    final = os.path.join(OUT, "video", "first_love_1080x1920.mp4")
    # film grain is brutal for x264: CRF 17 -> 500 MB+. aq-mode 3 + light
    # deblocking keeps type edges clean and the grain soft at ~6 Mbps.
    cmd = [ff, "-y", "-framerate", str(FPS), "-i", os.path.join(FRAMES, "%05d.jpg"),
           "-c:v", "libx264", "-preset", a.preset, "-crf", str(a.crf),
           "-pix_fmt", "yuv420p",
           "-x264-params", "aq-mode=3:deblock=1,1:keyint=60:min-keyint=30:bframes=3",
           silent]
    subprocess.run(cmd, check=True)
    mix = os.path.join(OUT, "audio", "mix.wav")
    cmd2 = [ff, "-y", "-i", silent, "-i", mix, "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
            "-movflags", "+faststart", final]
    subprocess.run(cmd2, check=True)
    print(final)
    return final


def cmd_qa(a):
    import qa
    mp4 = os.path.join(OUT, "video", "first_love_1080x1920.mp4")
    rep = qa.main_path(mp4)
    times = [2, 8, 14, 22, 30, 38, 46, 54, 62, 70, 78, 86, 94, 102, 110, 118,
             126, 134, 142, 148, 154, 160]
    print(qa.contact(mp4, os.path.join(OUT, "qa", "contact.jpg"), times))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("stills")
    p.add_argument("--times", required=True)
    p.add_argument("--scale", type=float, default=0.5)
    p.add_argument("--S", type=int, default=2)
    p.add_argument("--tag")
    p.set_defaults(fn=cmd_stills)

    p = sub.add_parser("sheet")
    p.add_argument("--times", required=True)
    p.add_argument("--scale", type=float, default=0.26)
    p.add_argument("--cols", type=int, default=6)
    p.add_argument("--S", type=int, default=2)
    p.add_argument("--out")
    p.set_defaults(fn=cmd_sheet)

    p = sub.add_parser("render")
    p.add_argument("--workers", type=int, default=2)
    p.add_argument("--scale", type=float, default=1.0)
    p.add_argument("--S", type=int, default=2)
    p.add_argument("--start", type=int, default=0)
    p.add_argument("--end", type=int, default=10 ** 9)
    p.set_defaults(fn=cmd_render)

    p = sub.add_parser("audio")
    p.set_defaults(fn=cmd_audio)

    p = sub.add_parser("mux")
    p.add_argument("--crf", type=int, default=31)
    p.add_argument("--preset", default="medium")
    p.set_defaults(fn=cmd_mux)

    p = sub.add_parser("qa")
    p.set_defaults(fn=cmd_qa)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
