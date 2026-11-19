"""Supersampled vector graphics surface + camera + film post.

Design rules
------------
* Everything is authored in logical 1080x1920 coordinates.
* A `Cam` (zoom / focus / pan / shake) is baked into the coordinate mapping, so
  push-ins stay razor sharp instead of upscaling pixels.
* Rasterisation happens at S x logical resolution (S=2), then downscales with
  Lanczos -> clean vector edges.
* Emissive light is drawn into quarter-res mask layers, blurred, tinted and
  added in linear-ish float space: cheap bloom that still reads as light.
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from tokens import (AMBER, BLUE, CRIMSON, INK, VOID, VOID_DEEP, WHITE,
                    clamp, lerp, rgba, smoothstep)


class Cam:
    """Logical-space camera: screen = (p - focus) * zoom + centre + pan."""

    __slots__ = ("zoom", "fx", "fy", "px", "py")

    def __init__(self, zoom=1.0, fx=540.0, fy=960.0, px=0.0, py=0.0):
        self.zoom, self.fx, self.fy, self.px, self.py = zoom, fx, fy, px, py

    def copy(self, **kw):
        c = Cam(self.zoom, self.fx, self.fy, self.px, self.py)
        for k, v in kw.items():
            setattr(c, k, v)
        return c

    def with_zoom(self, zoom, fx=None, fy=None):
        return Cam(zoom, self.fx if fx is None else fx, self.fy if fy is None else fy,
                   self.px, self.py)

    def map(self, W, H, pts):
        """pts: sequence of (x, y) logical -> np array logical screen coords."""
        a = np.asarray(pts, dtype=np.float64).reshape(-1, 2)
        a = (a - np.array([self.fx, self.fy])) * self.zoom
        a += np.array([W * 0.5 + self.px, H * 0.5 + self.py])
        return a


# ------------------------------------------------------------------ surface
class Surface:
    """Primitive drawing on a (possibly downscaled) PIL image."""

    def __init__(self, W, H, scale, cam, mode, img, draw):
        self.W, self.H = W, H
        self.scale = scale          # device px per logical px
        self.cam = cam
        self.mode = mode
        self.img = img
        self.d = draw

    # -- mapping helpers
    def _xy(self, x, y):
        p = self.cam.map(self.W, self.H, [(x, y)])[0]
        return p[0] * self.scale, p[1] * self.scale

    def _poly(self, pts):
        p = self.cam.map(self.W, self.H, pts)
        return [(float(a) * self.scale, float(b) * self.scale) for a, b in p]

    def _w(self, w):
        return max(0.5, w * self.cam.zoom * self.scale)

    def col(self, c, a=255):
        if self.mode == "L":
            return int(clamp(a, 0, 255))
        return rgba(c, a)

    # -- primitives
    def poly(self, pts, fill=None, outline=None, w=0, alpha=255):
        pts = self._poly(pts)
        if len(pts) < 2:
            return
        if fill is not None:
            self.d.polygon(pts, fill=self.col(fill, alpha))
        if outline is not None:
            self.d.line(pts + [pts[0]], fill=self.col(outline, alpha),
                        width=max(1, int(round(self._w(w)))), joint="curve")

    def line(self, pts, w=2, color=WHITE, alpha=255, cap=False):
        pts = self._poly(pts)
        if len(pts) < 2:
            return
        lw = max(1, int(round(self._w(w))))
        self.d.line(pts, fill=self.col(color, alpha), width=lw, joint="curve")
        if cap:
            r = lw * 0.5
            for (x, y) in (pts[0], pts[-1]):
                self.d.ellipse([x - r, y - r, x + r, y + r], fill=self.col(color, alpha))

    def dashed(self, pts, w=2, color=WHITE, alpha=255, dash=12, gap=10, phase=0.0):
        pts = np.asarray(pts, dtype=np.float64)
        segs = []
        acc = -phase
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            L = float(np.hypot(*(b - a)))
            if L <= 1e-6:
                continue
            t = 0.0
            while t < L:
                t0 = t
                t1 = min(L, t + dash)
                if (acc + t0) % (dash + gap) < dash:
                    segs.append((a + (b - a) * (t0 / L), a + (b - a) * (t1 / L)))
                t = t1 + gap
            acc += L
        for a, b in segs:
            self.line([tuple(a), tuple(b)], w=w, color=color, alpha=alpha)

    def rect(self, x0, y0, x1, y1, fill=None, outline=None, w=2, alpha=255, r=0,
             outline_alpha=None):
        if r > 0:
            self.rrect(x0, y0, x1, y1, r, fill, outline, w, alpha, outline_alpha)
            return
        a = self._poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
        xs = [p[0] for p in a]
        ys = [p[1] for p in a]
        box = [min(xs), min(ys), max(xs), max(ys)]
        if fill is not None:
            self.d.rectangle(box, fill=self.col(fill, alpha))
        if outline is not None:
            self.d.rectangle(box, outline=self.col(outline, alpha if outline_alpha is None else outline_alpha),
                             width=max(1, int(round(self._w(w)))))

    def rrect(self, x0, y0, x1, y1, r, fill=None, outline=None, w=2, alpha=255,
              outline_alpha=None):
        a = self._poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
        xs = [p[0] for p in a]
        ys = [p[1] for p in a]
        box = [min(xs), min(ys), max(xs), max(ys)]
        rad = max(0.0, r * self.cam.zoom * self.scale)
        if fill is not None:
            self.d.rounded_rectangle(box, rad, fill=self.col(fill, alpha))
        if outline is not None:
            self.d.rounded_rectangle(box, rad, outline=self.col(outline, alpha if outline_alpha is None else outline_alpha),
                                     width=max(1, int(round(self._w(w)))))

    def rect_px(self, x0, y0, x1, y1, color=WHITE, alpha=255):
        """Rectangle in device pixels (carets, full-frame masks)."""
        self.d.rectangle([x0, y0, x1, y1], fill=self.col(color, alpha))

    def ellipse(self, cx, cy, rx, ry=None, fill=None, outline=None, w=2, alpha=255):
        ry = rx if ry is None else ry
        cx, cy = self._xy(cx, cy)
        rx *= self.cam.zoom * self.scale
        ry *= self.cam.zoom * self.scale
        box = [cx - rx, cy - ry, cx + rx, cy + ry]
        if fill is not None:
            self.d.ellipse(box, fill=self.col(fill, alpha))
        if outline is not None:
            self.d.ellipse(box, outline=self.col(outline, alpha),
                           width=max(1, int(round(self._w(w)))))

    def circle(self, cx, cy, r, **kw):
        self.ellipse(cx, cy, r, r, **kw)

    def arc(self, cx, cy, rx, ry, a0, a1, w=2, color=WHITE, alpha=255):
        cx, cy = self._xy(cx, cy)
        rx *= self.cam.zoom * self.scale
        ry *= self.cam.zoom * self.scale
        box = [cx - rx, cy - ry, cx + rx, cy + ry]
        self.d.arc(box, a0, a1, fill=self.col(color, alpha),
                   width=max(1, int(round(self._w(w)))))

    def ring(self, cx, cy, r, w=2, color=WHITE, alpha=255, a0=0, a1=360):
        self.arc(cx, cy, r, r, a0, a1, w=w, color=color, alpha=alpha)

    def bezier(self, p0, p1, p2, p3, n=48):
        out = []
        for i in range(n + 1):
            t = i / n
            u = 1 - t
            out.append((u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
                        u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1]))
        return out

    def quad(self, p0, p1, p2, n=32):
        out = []
        for i in range(n + 1):
            t = i / n
            u = 1 - t
            out.append((u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
                        u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]))
        return out


class Emissive(Surface):
    """Quarter-res luminance buffer used for glows / bloom."""

    def __init__(self, W, H, cam, down=4, blur=0.0, color=WHITE, gain=1.0):
        scale = 1.0 / down
        img = Image.new("L", (max(1, int(W / down)), max(1, int(H / down))), 0)
        super().__init__(W, H, scale, cam, "L", img, ImageDraw.Draw(img))
        self.down = down
        self.blur = blur
        self.color = color
        self.gain = gain

    def col(self, c, a=255):
        return int(clamp(a, 0, 255))


class Frame:
    """One finished frame: drawing surface + emissive passes + film post."""

    def __init__(self, W=1080, H=1920, S=2, bg=VOID):
        self.W, self.H, self.S = W, H, S
        self.bg = bg
        self.img = Image.new("RGB", (W * S, H * S), bg)
        self.d = ImageDraw.Draw(self.img, "RGBA")
        self.cam = Cam()
        self._glows = []          # (Emissive, blur, gain)
        self._overlays = []       # (fn(frame),) composited after grade
        self.flash = 0.0
        self.fade_to_black = 0.0
        self.vignette = 0.62
        self.grain = 0.045
        self.grade_amt = 1.0
        self.aberration = 0.0
        self.tint = None          # (color, amount) full-frame wash

    # -------------------------------------------------- drawing
    def surface(self):
        return Surface(self.W, self.H, self.S, self.cam, "RGBA", self.img, self.d)

    def set_cam(self, cam):
        self.cam = cam

    def glow(self, color=WHITE, blur=48, gain=1.0, down=4):
        e = Emissive(self.W, self.H, self.cam, down=down, blur=blur,
                     color=color, gain=gain)
        self._glows.append(e)
        return e

    def bg_gradient(self, top=(15, 18, 26), bottom=(5, 6, 9), cy=0.55):
        """Vertical + centre-weighted gradient, drawn once per frame at low res."""
        w, h = self.W // 4, self.H // 4
        yy = np.linspace(0, 1, h)[:, None]
        ramp = (yy >= cy).astype(np.float32)
        t = np.where(yy >= cy, 1.0, yy / max(1e-3, cy))
        tt = (t ** 1.6).astype(np.float32)
        base = np.array(bottom, np.float32)[None, None, :] * (1 - tt[..., None]) + \
            np.array(top, np.float32)[None, None, :] * tt[..., None]
        base = np.repeat(base, w, axis=1)
        # radial falloff from the centre
        xx = np.linspace(-1, 1, w)[None, :]
        yv = (yy * 2 - 1)
        r = np.sqrt(xx ** 2 * 0.75 + yv ** 2 * 0.55)
        fall = np.clip(1.0 - 0.55 * r, 0.35, 1.0)[..., None]
        arr = np.clip(base * fall, 0, 255).astype(np.uint8)
        im = Image.fromarray(arr).resize((self.W, self.H), Image.BILINEAR)
        self.img.paste(im, (0, 0), None) if False else None
        # blend as base layer: paste then redraw on top
        self.img.paste(im.resize((self.W * self.S, self.H * self.S), Image.BILINEAR), (0, 0))
        self.d = ImageDraw.Draw(self.img, "RGBA")

    # -------------------------------------------------- finish
    def compose(self, tick=0):
        W, H = self.W, self.H
        small = self.img.resize((W, H), Image.LANCZOS)
        arr = np.asarray(small).astype(np.float32)

        # emissive layers (blurred, tinted, added)
        for e in self._glows:
            m = e.img
            if e.blur > 0:
                m = m.filter(ImageFilter.GaussianBlur(e.blur * (1.0 / e.down)))
            m = m.resize((W, H), Image.BILINEAR)
            mask = np.asarray(m).astype(np.float32) * (e.gain / 255.0)
            col = np.array(e.color, np.float32)
            arr += mask[..., None] * col[None, None, :] * 0.85

        # bloom from real highlights
        lum = arr.max(axis=2)
        hi = np.clip((lum - 168.0) / 87.0, 0, 1)
        if hi.max() > 0.01:
            him = Image.fromarray((hi * 255).astype(np.uint8)).resize((W // 4, H // 4), Image.BILINEAR)
            him = him.filter(ImageFilter.GaussianBlur(9))
            him = him.filter(ImageFilter.GaussianBlur(9))
            hb = np.asarray(him.resize((W, H), Image.BILINEAR)).astype(np.float32) / 255.0
            arr += hb[..., None] * 70.0

        # grade: filmic S-curve, cool shadows, warm highlights
        x = np.clip(arr / 255.0, 0, 1)
        g = x * x * (3 - 2 * x) * 0.34 + x * 0.66
        g = np.clip(g, 0, 1)
        lut_shadow = np.array([-5, -1, 6], np.float32) / 255.0
        lum2 = g.mean(axis=2, keepdims=True)
        g = g + lut_shadow * (1 - lum2) ** 2.4 * self.grade_amt
        g = g + np.array([5, 2, -4], np.float32)[None, None, :] / 255.0 * (lum2 ** 2.6) * self.grade_amt
        g = np.clip(g, 0, 1)

        # vignette
        if self.vignette > 0:
            xx = np.linspace(-1, 1, W)[None, :]
            yy = np.linspace(-1, 1, H)[:, None]
            r = np.sqrt((xx ** 2) * 0.85 + (yy ** 2) * 0.72)
            v = np.clip(1.0 - self.vignette * (r ** 2.1), 0.18, 1.0)[..., None]
            g = g * v

        if self.tint is not None:
            c, amt = self.tint
            g = g * (1 - amt) + (np.array(c, np.float32) / 255.0)[None, None, :] * amt

        if self.flash > 0:
            g = g * (1 - self.flash) + self.flash

        if self.aberration > 0:
            k = self.aberration
            r = np.roll(g[..., 0], int(2 * k), axis=1)
            b = np.roll(g[..., 2], -int(2 * k), axis=1)
            g = np.stack([r, g[..., 1], b], axis=2)

        out = np.clip(g * 255.0, 0, 255).astype(np.uint8)

        if self.grain > 0:
            rng = np.random.default_rng(1000 + tick)
            n = rng.standard_normal((H // 2, W // 2)).astype(np.float32)
            n = np.repeat(np.repeat(n, 2, axis=0), 2, axis=1)[:H, :W]
            grain = (n * (self.grain * 255.0))[..., None]
            out = np.clip(out.astype(np.float32) + grain, 0, 255).astype(np.uint8)

        if self.fade_to_black > 0:
            out = (out.astype(np.float32) * (1.0 - self.fade_to_black)).astype(np.uint8)

        return Image.fromarray(out)
