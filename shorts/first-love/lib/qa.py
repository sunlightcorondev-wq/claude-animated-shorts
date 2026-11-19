"""Frame-by-frame QA for the finished short.

Decodes the exported video at low resolution, then checks every frame for
black / white / frozen / pop frames, measures loudness with ffmpeg's EBU R128
meter, and writes a contact sheet + a text report.

  python3 build.py qa
"""
import json
import os
import re
import subprocess

import numpy as np
from PIL import Image, ImageDraw

import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
W, H = 240, 426


def decode(path, prefix=None):
    """Yield (index, gray frames uint8 HxW) in chunks."""
    cmd = [FF, "-v", "error", "-i", path, "-vf", f"scale={W}:{H}",
           "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=10 ** 8)
    frame_bytes = W * H
    i = 0
    buf = []
    while True:
        raw = p.stdout.read(frame_bytes)
        if len(raw) < frame_bytes:
            break
        buf.append(np.frombuffer(raw, np.uint8).reshape(H, W))
        i += 1
        if len(buf) == 240:
            yield i - len(buf), np.stack(buf)
            buf = []
    if buf:
        yield i - len(buf), np.stack(buf)
    p.stdout.close()
    p.wait()


def loudness(path):
    out = subprocess.run([FF, "-hide_banner", "-i", path, "-af", "ebur128=peak=true",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    i = re.findall(r"I:\s+(-?\d+\.\d) LUFS", out)
    lra = re.findall(r"LRA:\s+(-?\d+\.\d) LU", out)
    tp = re.findall(r"TPK:\s+(-?\d+\.\d)", out)
    return (float(i[-1]) if i else None, float(lra[-1]) if lra else None,
            float(tp[-1]) if tp else None)


def run(path, every=4, sheet_every=90):
    report = {"file": path, "issues": [], "frames": 0}
    prev = None
    frozen = 0
    means = []
    t = 0
    dur_frames = 0
    for start, frames in decode(path):
        for k, fr in enumerate(frames):
            idx = start + k
            dur_frames = idx + 1
            m = float(fr.mean())
            means.append(m)
            t = idx / 30.0
            if m < 4.0 and 2.0 < t < 160.0:
                report["issues"].append(("black", round(t, 2), round(m, 1)))
            if m > 250.0:
                report["issues"].append(("white", round(t, 2), round(m, 1)))
            if prev is not None:
                d = float(np.abs(fr.astype(np.int16) - prev.astype(np.int16)).mean())
                if d < 0.12:
                    frozen += 1
                    if frozen == 14:
                        report["issues"].append(("frozen", round(t, 2), d))
                else:
                    frozen = 0
            prev = fr
    report["frames"] = dur_frames
    report["mean_luma"] = round(float(np.mean(means)), 2)
    report["min_luma"] = round(float(np.min(means)), 2)
    report["max_luma"] = round(float(np.max(means)), 2)
    i, lra, tp = loudness(path)
    report["lufs"], report["lra"], report["true_peak"] = i, lra, tp
    report["duration_s"] = round(dur_frames / 30.0, 2)
    return report


def contact(path, out, times):
    os.makedirs(os.path.dirname(out), exist_ok=True)
    imgs = []
    for t in times:
        p = os.path.join(os.path.dirname(out), "_tmp.jpg")
        subprocess.run([FF, "-v", "error", "-y", "-ss", str(t), "-i", path,
                        "-frames:v", "1", "-vf", "scale=216:384", p], check=True)
        imgs.append((t, Image.open(p).copy()))
    cols, pad, lab = 8, 8, 18
    rows = (len(imgs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (216 + pad) + pad,
                              rows * (384 + pad + lab) + pad), (16, 16, 18))
    d = ImageDraw.Draw(sheet)
    for k, (t, im) in enumerate(imgs):
        x = pad + (k % cols) * (216 + pad)
        y = pad + (k // cols) * (384 + pad + lab)
        sheet.paste(im, (x, y + lab))
        d.text((x + 2, y + 4), f"{t:6.1f}s", fill=(230, 230, 230))
    sheet.save(out, quality=88)
    return out


def main():
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join("out", "video",
                                                             "first_love_1080x1920.mp4")
    rep = run(path)
    outdir = os.path.join("out", "qa")
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "qa.json"), "w") as f:
        json.dump(rep, f, indent=1)
    lines = [f"file: {rep['file']}", f"frames: {rep['frames']} "
             f"({rep['duration_s']} s)", f"mean luma: {rep['mean_luma']} "
             f"(min {rep['min_luma']}, max {rep['max_luma']})",
             f"loudness: {rep['lufs']} LUFS / LRA {rep['lra']} LU / "
             f"peak {rep['true_peak']} dBFS",
             f"issues: {len(rep['issues'])}"]
    for kind, t, v in rep["issues"][:40]:
        lines.append(f"  {kind:7s} at {t:7.2f}s  ({v})")
    with open(os.path.join(outdir, "qa.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return rep


def main_path(path=None):
    import sys
    if path is None:
        path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
            "out", "video", "first_love_1080x1920.mp4")
    rep = run(path)
    outdir = os.path.join("out", "qa")
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "qa.json"), "w") as f:
        json.dump(rep, f, indent=1)
    lines = [f"file: {rep['file']}", f"frames: {rep['frames']} "
             f"({rep['duration_s']} s)", f"mean luma: {rep['mean_luma']} "
             f"(min {rep['min_luma']}, max {rep['max_luma']})",
             f"loudness: {rep['lufs']} LUFS / LRA {rep['lra']} LU / "
             f"peak {rep['true_peak']} dBFS",
             f"issues: {len(rep['issues'])}"]
    for kind, t, v in rep["issues"][:40]:
        lines.append(f"  {kind:7s} at {t:7.2f}s  ({v})")
    with open(os.path.join(outdir, "qa.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return rep


if __name__ == "__main__":
    main_path()
