"""Reusable vector cast and props.

All coordinates are logical px. Figures are built from thick round-capped
strokes plus ellipses, so a silhouette stays crisp at any camera zoom and can be
re-used as a wireframe (the ghost) or an outline (the hologram).
"""
import math

import numpy as np

from PIL import Image, ImageDraw

from gfx import Surface
from tokens import (AMBER, BLUE, CRIMSON, SHADOW, SHADOW_HI, VOID, WHITE, clamp,
                    ease_out_cubic, lerp, mix, rgba, smootherstep)


# ------------------------------------------------------------------ chairs
def chair(g, x, y_seat, s=1.0, facing=1, color=SHADOW, alpha=255, rim=None,
          rim_alpha=0):
    f = facing

    def X(dx):
        return x + dx * s * f

    def Y(dy):
        return y_seat + dy * s

    legs = [(72, 0, 14, 185), (-72, 0, 12, 185)]
    if rim and rim_alpha:
        for dx, dy, w, h in legs:
            g.rect(X(dx) - (w / 2 if f > 0 else -w / 2) - 2, Y(dy) - 2,
                   X(dx) + (w / 2 if f > 0 else -w / 2) + 2, Y(dy + h) + 2,
                   fill=rim, alpha=int(rim_alpha * 0.5))
    # seat
    g.rrect(X(-86), Y(-8), X(86), Y(12), 5 * s, fill=color, alpha=alpha)
    # legs
    for dx, dy, w, h in legs:
        g.rrect(X(dx) - w / 2, Y(dy), X(dx) + w / 2, Y(dy + h), 3 * s,
                fill=color, alpha=alpha)
    # back: a slab behind the sitter
    bx = -74
    g.rrect(X(bx) - 9 * s, Y(-196), X(bx) + 9 * s, Y(-4), 6 * s, fill=color, alpha=alpha)
    g.rrect(X(bx) - 16 * s, Y(-212), X(bx) + 16 * s, Y(-186), 4 * s, fill=color,
            alpha=alpha)
    if rim and rim_alpha:
        g.rrect(X(bx) - 12 * s, Y(-200), X(bx) + 12 * s, Y(-6), 6 * s,
                outline=rim, w=1.5, alpha=int(rim_alpha * 0.8))


def table(g, cx, y_top, w=680.0, s=1.0, color=SHADOW, alpha=255, rim=None,
          rim_alpha=0, thickness=16.0):
    x0, x1 = cx - w / 2, cx + w / 2
    if rim and rim_alpha:
        g.line([(x0, y_top - 3), (x1, y_top - 3)], w=3.2, color=rim,
               alpha=int(rim_alpha))
    g.rrect(x0, y_top, x1, y_top + thickness, 4 * s, fill=color, alpha=alpha)
    # legs
    for lx in (x0 + 34, x1 - 34):
        g.rrect(lx - 8 * s, y_top + thickness, lx + 8 * s,
                y_top + thickness + 320 * s, 3 * s, fill=color, alpha=alpha)
    g.rrect(x0 + 40, y_top + thickness + 250 * s, x1 - 40,
            y_top + thickness + 262 * s, 2 * s, fill=color,
            alpha=int(alpha * 0.85))


def table_persp(g, cx, y_top, w=800.0, s=1.0, color=(12, 14, 19), alpha=255,
                rim=(80, 92, 112), rim_alpha=110, depth=40.0, leg_to=1560.0,
                top_color=(22, 27, 36), far_w=None):
    """Table with a visible receding top face, so it reads as furniture."""
    back = y_top - depth * s
    fw = w if far_w is None else far_w
    g.poly([(cx - fw / 2, back), (cx + fw / 2, back),
            (cx + w / 2, y_top), (cx - w / 2, y_top)], fill=top_color, alpha=alpha)
    g.line([(cx - fw / 2, back), (cx + fw / 2, back)], w=2.4, color=rim,
           alpha=rim_alpha)
    g.rrect(cx - w / 2, y_top, cx + w / 2, y_top + 20 * s, 5 * s, fill=color,
            alpha=alpha)
    g.line([(cx - w / 2, y_top + 20 * s), (cx + w / 2, y_top + 20 * s)], w=1.2,
           color=rim, alpha=int(rim_alpha * 0.5))
    for lx in (cx - w / 2 + 52, cx + w / 2 - 52):
        g.rrect(lx - 10 * s, y_top + 20 * s, lx + 10 * s, leg_to, 3 * s, fill=color,
                alpha=alpha)
        g.line([(lx - 10 * s, y_top + 20 * s), (lx - 10 * s, leg_to)], w=1.2,
               color=rim, alpha=int(rim_alpha * 0.35))


# ------------------------------------------------------------------ figure
def seated_figure(g, x, y_seat, s=1.0, facing=1, color=SHADOW, alpha=255, rim=None,
                  rim_alpha=0, lean=0.0, part="body", arm_alpha=None, nose=True,
                  rim_dir=(6.0, -5.0)):
    """Side-view seated silhouette. Origin: hips at (x, y_seat).

    Built from a torso polyline, an arm resting on the table top, thick thigh and
    shin strokes and a bean head with a nose bump, so the shape still reads as a
    person at 40 px tall.
    """
    f = facing

    def P(dx, dy):
        return (x + dx * s * f, y_seat + dy * s)

    def W(w):
        return w * s

    hip = P(0, 4)
    waist = P(-10 - lean * 18, -150)
    chest = P(-16 - lean * 34, -296)
    shoulder = P(-14 - lean * 44, -378)
    head = P(4 - lean * 62, -470)
    knee = P(100, -2)
    ankle = P(106, 176)
    toe = P(154, 184)
    elbow = P(52, -286)
    wrist = P(150, -196)

    rim_d = rim_dir if rim_dir else (0.0, 0.0)

    def limb(a, b, w, col, al, off=(0.0, 0.0)):
        g.line([(a[0] + off[0], a[1] + off[1]), (b[0] + off[0], b[1] + off[1])],
               w=w, color=col, alpha=al, cap=True)

    def ell(a, b, col, al, off=(0.0, 0.0)):
        g.ellipse(a[0] + off[0], a[1] + off[1], b[0], b[1], fill=col, alpha=al)

    def body(col, al, widen=0.0, off=(0.0, 0.0)):
        limb(hip, knee, W(48 + widen), col, al, off)
        limb(knee, ankle, W(40 + widen), col, al, off)
        limb(ankle, toe, W(26 + widen), col, al, off)
        limb(hip, waist, W(64 + widen), col, al, off)
        limb(waist, chest, W(70 + widen), col, al, off)
        limb(chest, shoulder, W(66 + widen), col, al, off)
        ell(shoulder, (W(37 + widen / 2), W(33 + widen / 2)), col, al, off)
        # neck + head
        limb(P(-2, -398), P(2, -436), W(30 + widen), col, al, off)
        ell(head, (W(44 + widen / 2), W(52 + widen / 2)), col, al, off)
        if nose:
            ell((head[0] + W(41 * f), head[1] + W(6)), (W(11), W(12)), col, al, off)
            ell((head[0] + W(19 * f), head[1] + W(27)), (W(25), W(23)), col, al, off)
            ell((head[0] - W(9 * f), head[1] - W(9)), (W(41), W(45)), col, al, off)

    def arm(col, al, widen=0.0, off=(0.0, 0.0)):
        limb(shoulder, elbow, W(30 + widen), col, al, off)
        limb(elbow, wrist, W(26 + widen), col, al, off)
        g.circle(wrist[0] + off[0], wrist[1] + off[1], W(15 + widen / 2), fill=col,
                 alpha=al)

    if part == "body":
        if rim and rim_alpha:
            body(rim, rim_alpha, widen=2.0, off=rim_d)
        body(color, alpha)
    if part == "arm":
        al = alpha if arm_alpha is None else arm_alpha
        if rim and rim_alpha:
            arm(rim, rim_alpha, widen=2.0, off=rim_d)
        arm(color, al)
    return dict(hip=hip, knee=knee, ankle=ankle, toe=toe, shoulder=shoulder,
                head=head, elbow=elbow, wrist=wrist, chest=chest)


# ------------------------------------------------------------------ ghost
def _mesh_points(pose, n=26):
    """Deterministic points over the figure's body, for the wireframe mesh."""
    hip, knee, ankle, shoulder, head, elbow, wrist, chest = (
        pose["hip"], pose["knee"], pose["ankle"], pose["shoulder"], pose["head"],
        pose["elbow"], pose["wrist"], pose["chest"])
    rng = np.random.default_rng(7)
    pts = []
    bones = [(hip, chest), (chest, shoulder), (shoulder, elbow), (elbow, wrist),
             (hip, knee), (knee, ankle)]
    for i in range(n):
        a, b = bones[i % len(bones)]
        j = rng.uniform(0.08, 0.92)
        off = rng.normal(0, 6, 2)
        pts.append((lerp(a[0], b[0], j) + off[0], lerp(a[1], b[1], j) + off[1]))
    for ang in range(8):
        a = ang / 8 * 2 * math.pi
        pts.append((head[0] + math.cos(a) * 34, head[1] + math.sin(a) * 40))
    pts += [elbow, wrist, knee, ankle, shoulder, chest]
    return pts


def ghost_figure(g, x, y_seat, s=1.0, facing=1, t=0.0, alpha=255, progress=0.0,
                 color=AMBER, mesh=True, flicker=1.0, lean=0.0, glow=None):
    """Translucent wireframe of the same seated figure, dissolving with progress."""
    pose = seated_figure(g, x, y_seat, s=s, facing=facing, color=color, alpha=0,
                         lean=lean, part="none")
    fl = 0.74 + 0.26 * math.sin(t * 7.3) * math.sin(t * 2.1)
    rng = np.random.default_rng(int(t * 24) + 11)
    dropout = 1.0 - flicker * (0.45 if rng.random() < 0.05 else 0.0)
    keep = 1.0 - smootherstep(progress)
    a = alpha * fl * dropout * keep
    if a <= 1:
        return
    a = int(clamp(a, 0, 255))
    # ectoplasm volume: the same silhouette, barely there
    g_body = seated_figure(g, x, y_seat, s=s, facing=facing, color=color,
                           alpha=int(a * 0.16), lean=lean, part="body")
    # skeleton strokes, broken into segments that shorten as it dissolves
    bones = [(pose["hip"], pose["chest"]), (pose["chest"], pose["shoulder"]),
             (pose["shoulder"], pose["elbow"]), (pose["elbow"], pose["wrist"]),
             (pose["hip"], pose["knee"]), (pose["knee"], pose["ankle"]),
             (pose["ankle"], pose["toe"])]
    for i, (p0, p1) in enumerate(bones):
        nseg = 7
        for j in range(nseg):
            r = np.random.default_rng(i * 31 + j)
            t0 = j / nseg + r.uniform(0, 0.025)
            t1 = min(1.0, t0 + (1.0 / nseg) * keep * 1.2)
            if t1 <= t0:
                continue
            a2 = int(a * (0.55 + 0.45 * r.random()))
            g.line([(lerp(p0[0], p1[0], t0), lerp(p0[1], p1[1], t0)),
                    (lerp(p0[0], p1[0], t1), lerp(p0[1], p1[1], t1))],
                   w=2.6 * s, color=color, alpha=a2)
    hx, hy = pose["head"]
    g.arc(hx, hy, 45 * s, 53 * s, 200, 200 + 300 * keep, w=2.8 * s, color=color, alpha=a)
    g.arc(hx, hy, 45 * s, 53 * s, 208 + 300 * keep, 500, w=2.8 * s, color=color,
          alpha=int(a * 0.55))
    if mesh:
        pts = _mesh_points(pose)
        r = np.random.default_rng(5)
        for i in range(len(pts)):
            for j in range(i + 1, min(len(pts), i + 4)):
                if r.random() < 0.5:
                    g.line([pts[i], pts[j]], w=1.1 * s, color=color,
                           alpha=int(a * 0.22))
        for (px, py) in pts:
            g.circle(px, py, 2.1 * s, fill=color, alpha=int(a * 0.6))
    if glow is not None:
        glow.line([pose["hip"], pose["chest"], pose["shoulder"]], w=26 * s, color=255,
                  alpha=int(a * 0.5), cap=True)
        glow.ellipse(hx, hy, 52 * s, 60 * s, fill=255, alpha=int(a * 0.85))
        glow.ellipse(pose["wrist"][0], pose["wrist"][1], 26 * s, 26 * s, fill=255,
                     alpha=int(a * 0.5))
    # glitch bands: horizontal slices nudged sideways
    if flicker > 0:
        rg = np.random.default_rng(int(t * 15) + 3)
        for _ in range(2):
            if rg.random() < 0.45:
                by = y_seat - rg.uniform(40, 500) * s
                bh = rg.uniform(3, 8) * s
                shift = rg.normal(0, 9) * s
                g.rect(x - 110 * s + shift, by, x + 160 * s + shift, by + bh,
                       fill=VOID, alpha=int(a * 0.5))


def scan_hologram(g, draw_fn, t=0.0, alpha=255, progress=0.0, color=AMBER,
                  glow=None, step=15.0, down=4, band_speed=200.0, flicker=1.0,
                  deep=False, contour=True, fill=0.46):
    """Hologram of any silhouette: traced contour + faint interior scan lines.

    `draw_fn(surface)` paints the figure into a 1/down mask. Each scan row gives a
    left/right extent: those extents become the vertical contour polylines (which
    is what makes it read as a body), the rows in between become dim light.
    """
    keep = 1.0 - smootherstep(progress)
    if keep <= 0.01:
        return
    W4, H4 = g.W // down, g.H // down
    mask = Image.new("L", (W4, H4), 0)
    sur = Surface(g.W, g.H, 1.0 / down, g.cam, "L", mask, ImageDraw.Draw(mask))
    draw_fn(sur)
    m = np.asarray(mask) > 70
    fl = 0.82 + 0.18 * math.sin(t * 8.1) * math.sin(t * 2.3)
    rg = np.random.default_rng(int(t * 18) + 5)
    band = (t * band_speed) % (H4 + 160)
    a0 = alpha * fl * (1.0 - 0.35 * smootherstep(progress))
    scale_dev = down * g.scale
    px_w = max(1, int(round(1.6 * g.cam.zoom * g.scale)))
    row_step = max(1, int(round(step / down)))
    left, right = [], []
    for yy in range(0, H4):
        idx = np.flatnonzero(m[yy])
        if idx.size == 0:
            continue
        x0, x1 = idx[0], idx[-1]
        ydev = yy * scale_dev
        if yy % row_step == 0:
            # interior light between the contours
            a = a0 * fill * (0.70 + 0.30 * rg.random())
            g.d.line([(x0 * scale_dev, ydev), (x1 * scale_dev, ydev)],
                     fill=rgba(color, int(clamp(a, 0, 255))), width=max(1, px_w - 1))
        d = abs(yy - (H4 - band)) / 60.0
        hot = max(0.0, 1.0 - d * d)
        if hot > 0.02:
            a = a0 * (0.10 + 0.55 * hot)
            g.d.line([(x0 * scale_dev, ydev), (x1 * scale_dev, ydev)],
                     fill=rgba(color, int(clamp(a, 0, 255))), width=px_w)
            if glow is not None:
                glow.line([(x0 * scale_dev / scale_dev, ydev / scale_dev),
                           (x1 * scale_dev / scale_dev, ydev / scale_dev)],
                          w=7, color=255, alpha=int(110 * hot * keep), cap=True)
        # contour points
        left.append((float(x0), yy))
        right.append((float(x1), yy))
    if contour and len(left) > 4:
        def smooth(pts):
            xs = np.array([p[0] for p in pts], dtype=np.float64)
            for _ in range(3):
                xs = np.convolve(np.pad(xs, 2, mode="edge"), [0.15, 0.2, 0.3, 0.2, 0.15],
                                 mode="valid")
            return [(float(xs[i]), pts[i][1]) for i in range(len(pts))]

        for pts, al in ((smooth(left), 1.0), (smooth(right), 0.9)):
            step2 = 2
            for k in range(0, len(pts) - 1, 9):
                chunk = pts[k:k + 10:step2]
                if len(chunk) < 2 or rg.random() < progress * 0.9:
                    continue
                poly = [(p[0] * scale_dev, p[1] * scale_dev) for p in chunk]
                g.d.line(poly, fill=rgba(color, int(clamp(a0 * al * 1.18, 0, 255))),
                         width=px_w + 1, joint="curve")
    # stray floating fragments (dust motes of light)
    r = np.random.default_rng(9)
    for _ in range(7):
        rx = g.W * r.uniform(0.05, 0.95)
        ry = g.H * r.uniform(0.1, 0.8)
        g.line([(rx, ry), (rx, ry + r.uniform(14, 46))], w=1.0, color=color,
               alpha=int(a0 * 0.12))


# ------------------------------------------------------------------ dust
class Dust:
    """Deterministic particle field: spawn, rise, fade."""

    def __init__(self, n=90, seed=3, box=(150, 1080, 1000, 1500), rise=(8, 46),
                 life=(1.6, 4.2), size=(0.9, 2.6)):
        rng = np.random.default_rng(seed)
        self.n = n
        self.x = rng.uniform(box[0], box[1], n)
        self.y = rng.uniform(box[2], box[3], n)
        self.vy = rng.uniform(rise[0], rise[1], n)
        self.ph = rng.uniform(0, 6.28, n)
        self.freq = rng.uniform(0.6, 2.2, n)
        self.amp = rng.uniform(3, 16, n)
        self.life = rng.uniform(life[0], life[1], n)
        self.off = rng.uniform(0, 1, n)
        self.size = rng.uniform(size[0], size[1], n)
        self.glow = rng.uniform(0.25, 1.0, n)

    def draw(self, g, t, color=AMBER, alpha=1.0, spread=1.0, glow_layer=None):
        for i in range(self.n):
            age = (t + self.off[i] * self.life[i]) % self.life[i]
            p = age / self.life[i]
            env = math.sin(math.pi * p) ** 1.2
            x = self.x[i] + math.sin(t * self.freq[i] + self.ph[i]) * self.amp[i] * spread
            y = self.y[i] - self.vy[i] * age
            a = int(clamp(255 * env * self.glow[i] * alpha * 0.85, 0, 255))
            if a <= 2:
                continue
            g.circle(x, y, self.size[i], fill=color, alpha=a)
            if glow_layer is not None and self.size[i] > 1.7:
                glow_layer.circle(x, y, self.size[i] * 2.6, fill=255,
                                  alpha=int(a * 0.5))


# ------------------------------------------------------------------ light
def spotlight(g, cx, cy, rx, ry, color=BLUE, intensity=1.0, glow=None, blur=70):
    """Soft elliptical pool of light. Uses an emissive layer when provided."""
    layer = glow if glow is not None else g
    layer.ellipse(cx, cy, rx, ry, fill=255 if glow is not None else color,
                  alpha=int(clamp(255 * intensity, 0, 255)))


def floor_pool(frame, cx, cy, rx, ry, color=BLUE, intensity=0.9, blur=64):
    e = frame.glow(color=color, blur=blur, gain=intensity, down=4)
    e.ellipse(cx, cy, rx, ry, fill=255, alpha=210)
    return e


def vignette_spot(frame, cx, cy, rx, ry):
    """Darkens everything outside an ellipse (used for the cold pool in S1)."""
    pass


# ------------------------------------------------------------------ icons
def heart(g, cx, cy, r, color=CRIMSON, alpha=255, w=3, fill=True):
    p = []
    for i in range(64):
        a = i / 63 * 2 * math.pi
        x = 16 * math.sin(a) ** 3
        y = -(13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a)
              - math.cos(4 * a))
        p.append((cx + x * r / 16, cy + y * r / 16))
    g.poly(p, fill=color if fill else None, outline=None if fill else color,
           w=w, alpha=alpha)


def warn_triangle(g, cx, cy, r, color=CRIMSON, alpha=255, w=3.4):
    pts = [(cx, cy - r), (cx + r * 1.05, cy + r * 0.78), (cx - r * 1.05, cy + r * 0.78)]
    g.poly(pts, outline=color, w=w, alpha=alpha)
    g.rect(cx - r * 0.055, cy - r * 0.34, cx + r * 0.055, cy + r * 0.26, fill=color,
           alpha=alpha)
    g.circle(cx, cy + r * 0.47, r * 0.075, fill=color, alpha=alpha)


def clock_icon(g, cx, cy, r, color=AMBER, alpha=255, w=3.0, t=0.0):
    g.circle(cx, cy, r, outline=color, w=w, alpha=alpha)
    for k in range(12):
        a = k / 12 * 2 * math.pi
        r0, r1 = r * 0.80, r * 0.92
        g.line([(cx + math.cos(a) * r0, cy + math.sin(a) * r0),
                (cx + math.cos(a) * r1, cy + math.sin(a) * r1)], w=w * 0.6,
               color=color, alpha=int(alpha * 0.8))
    for k, ln in ((0, 0.52), (1, 0.70)):
        a = -math.pi / 2 + (t * 6.0 if k else t * 0.5) + (0.5 if k else 0)
        g.line([(cx, cy), (cx + math.cos(a) * r * ln, cy + math.sin(a) * r * ln)],
               w=w * 1.1, color=color, alpha=alpha, cap=True)


def phone_icon(g, cx, cy, r, color=CRIMSON, alpha=255, w=3.0, crack=0.0):
    x0, y0, x1, y1 = cx - r * 0.62, cy - r, cx + r * 0.62, cy + r
    g.rrect(x0, y0, x1, y1, r * 0.16, outline=color, w=w, alpha=alpha)
    g.rect(cx - r * 0.20, y0 + r * 0.12, cx + r * 0.20, y0 + r * 0.20, fill=color,
           alpha=int(alpha * 0.7))
    if crack > 0:
        p = [(cx - r * 0.1, cy - r * 0.5), (cx + r * 0.14, cy - r * 0.05),
             (cx - r * 0.06, cy + r * 0.12), (cx + r * 0.18, cy + r * 0.58)]
        g.line(p, w=w * 0.8, color=color, alpha=int(alpha * clamp(crack)))


def two_figures(g, cx, cy, r, color=CRIMSON, alpha=255, gap=1.0, w=3.0):
    """Two minimal figures drifting apart (distance)."""
    for sgn in (-1, 1):
        hx = cx + sgn * r * (0.32 + 0.28 * gap)
        g.circle(hx, cy - r * 0.55, r * 0.22, outline=color, w=w, alpha=alpha)
        g.line([(hx, cy - r * 0.30), (hx, cy + r * 0.35)], w=w, color=color, alpha=alpha)
        g.line([(hx, cy - r * 0.10), (hx - sgn * r * 0.26, cy + r * 0.22)], w=w,
               color=color, alpha=alpha)
    g.dashed([(cx - r * 0.5, cy + r * 0.62), (cx + r * 0.5, cy + r * 0.62)], w=w * 0.7,
             color=color, alpha=int(alpha * 0.6), dash=8, gap=9)


def calendar_icon(g, cx, cy, r, color=AMBER, alpha=255, w=3.0):
    g.rrect(cx - r * 0.8, cy - r * 0.7, cx + r * 0.8, cy + r * 0.8, r * 0.1,
            outline=color, w=w, alpha=alpha)
    g.line([(cx - r * 0.8, cy - r * 0.35), (cx + r * 0.8, cy - r * 0.35)], w=w,
           color=color, alpha=alpha)
    for i in range(2):
        g.line([(cx - r * 0.5 + i * r * 0.7, cy - r * 0.95),
                (cx - r * 0.5 + i * r * 0.7, cy - r * 0.62)], w=w * 1.2, color=color,
               alpha=alpha)
    for i in range(3):
        for j in range(2):
            g.circle(cx - r * 0.45 + i * r * 0.45, cy + r * 0.05 + j * r * 0.42,
                     r * 0.09, fill=color, alpha=int(alpha * 0.75))


# ------------------------------------------------------------------ over-the-shoulder cast
def back_figure(g, cx, y_head, s=1.0, color=SHADOW, alpha=255, rim=None,
                rim_alpha=0, rim_dir=(-6.0, 7.0), head_r=(150.0, 162.0), bottom=1980.0):
    """A person seen from behind: the classic 'alone at the table' foreground."""
    hx, hy = head_r

    def shape(col, al, off=(0.0, 0.0)):
        ox, oy = off
        # head
        g.ellipse(cx + ox, y_head + oy, hx * s, hy * s, fill=col, alpha=al)
        # neck
        g.rrect(cx - 56 * s + ox, y_head + hy * s * 0.62 + oy, cx + 56 * s + ox,
                y_head + hy * s + 40 * s + oy, 18 * s, fill=col, alpha=al)
        # shoulders: rounded trapezoid
        top = y_head + hy * s * 0.92
        w_top, w_bot = 250 * s, 470 * s
        g.poly([(cx - w_top + ox, top + oy), (cx + w_top + ox, top + oy),
                (cx + w_bot + ox, bottom + oy), (cx - w_bot + ox, bottom + oy)],
               fill=col, alpha=al)
        g.rrect(cx - w_top - 40 * s + ox, top - 30 * s + oy, cx + w_top + 40 * s + ox,
                top + 90 * s + oy, 70 * s, fill=col, alpha=al)

    if rim and rim_alpha:
        shape(rim, rim_alpha, rim_dir)
    shape(color, alpha)


def chair_front(g, cx, y_seat, s=1.0, color=SHADOW, alpha=255, rim=None,
                rim_alpha=0, w=248.0, top=300.0):
    """Front-facing chair (its back shows above the table)."""
    x0, x1 = cx - w * s / 2, cx + w * s / 2
    ytop = y_seat - top * s
    g.rrect(x0 - 9 * s, ytop + 40 * s, x0 + 9 * s, y_seat, 4 * s, fill=color,
            alpha=alpha)
    g.rrect(x1 - 9 * s, ytop + 40 * s, x1 + 9 * s, y_seat, 4 * s, fill=color,
            alpha=alpha)
    # bowed top rail: unmistakably a chair back
    g.arc(cx, ytop + 104 * s, w / 2, 96 * s, 196, 344, w=20 * s, color=color,
          alpha=alpha)
    g.rrect(x0 + 18 * s, ytop + 150 * s, x1 - 18 * s, ytop + 172 * s, 6 * s,
            fill=color, alpha=int(alpha * 0.9))
    if rim and rim_alpha:
        g.arc(cx, ytop + 104 * s, w / 2 + 10 * s, 104 * s, 198, 342, w=1.8 * s,
              color=rim, alpha=rim_alpha)
        g.line([(x0 + 18 * s, ytop + 150 * s), (x1 - 18 * s, ytop + 150 * s)],
               w=1.6 * s, color=rim, alpha=int(rim_alpha * 0.6))


def front_figure(g, cx, y_head, s=1.0, color=SHADOW, alpha=255, rim=None,
                 rim_alpha=0, lean=0.0, part="body", table_y=1315.0,
                 hand=(-86.0, 74.0)):
    """Seated person facing the camera: head, shoulders, arms onto the table."""
    head_r = (63.0, 70.0)
    shoulder_y = y_head + 96 * s
    hip_y = y_head + 430 * s
    h_l = (cx - 118 * s, shoulder_y + 26 * s)
    h_r = (cx + 118 * s, shoulder_y + 26 * s)
    hand_l = (cx + hand[0] * s, table_y - 12 * s)
    hand_r = (cx + hand[1] * s, table_y - 12 * s)

    def body(col, al):
        g.ellipse(cx, y_head, head_r[0] * s, head_r[1] * s, fill=col, alpha=al)
        # neck
        g.rrect(cx - 23 * s, y_head + 44 * s, cx + 23 * s, shoulder_y - 2 * s,
                10 * s, fill=col, alpha=al)
        # shoulders: trapezoid, wider at the top, plus rounded deltoids
        g.poly([(cx - 150 * s, shoulder_y + 4 * s), (cx + 150 * s, shoulder_y + 4 * s),
                (cx + 104 * s, hip_y), (cx - 104 * s, hip_y)], fill=col, alpha=al)
        g.ellipse(cx - 146 * s, shoulder_y + 26 * s, 32 * s, 40 * s, fill=col,
                  alpha=al)
        g.ellipse(cx + 146 * s, shoulder_y + 26 * s, 32 * s, 40 * s, fill=col,
                  alpha=al)

    if part == "body":
        if rim and rim_alpha:
            body(rim, rim_alpha)
        body(color, alpha)
    if part == "arms":
        for (sx, sy), (hx2, hy2) in (((h_l), hand_l), ((h_r), hand_r)):
            ex = (sx + hx2) * 0.5 + (14 * s if hx2 > sx else -14 * s)
            ey = (sy + hy2) * 0.5 + 30 * s
            if rim and rim_alpha:
                g.line([(sx, sy), (ex, ey)], w=34 * s, color=rim, alpha=rim_alpha,
                       cap=True)
                g.line([(ex, ey), (hx2, hy2)], w=30 * s, color=rim, alpha=rim_alpha,
                       cap=True)
            g.line([(sx, sy), (ex, ey)], w=34 * s, color=color, alpha=alpha, cap=True)
            g.line([(ex, ey), (hx2, hy2)], w=30 * s, color=color, alpha=alpha, cap=True)
            g.ellipse(hx2, hy2, 26 * s, 18 * s, fill=color, alpha=alpha)
    return dict(head=(cx, y_head), head_r=head_r, shoulder_y=shoulder_y,
                hip_y=hip_y, hand_l=hand_l, hand_r=hand_r)


def forearm(g, p0, p1, w=62.0, color=SHADOW, alpha=255, rim=None, rim_alpha=0,
            hand=(30.0, 22.0), rim_dir=(-6.0, 7.0)):
    """A forearm entering frame from the bottom, with a resting hand."""
    def draw(col, al, off=(0.0, 0.0)):
        g.line([(p0[0] + off[0], p0[1] + off[1]), (p1[0] + off[0], p1[1] + off[1])],
               w=w, color=col, alpha=al, cap=True)
        g.ellipse(p1[0] + off[0] + hand[0] * 0.35, p1[1] + off[1] - hand[1] * 0.2,
                  hand[0], hand[1], fill=col, alpha=al)
        g.ellipse(p1[0] + off[0] + hand[0] * 0.9, p1[1] + off[1] - hand[1] * 0.55,
                  hand[0] * 0.62, hand[1] * 0.62, fill=col, alpha=al)
    if rim and rim_alpha:
        draw(rim, rim_alpha, rim_dir)
    draw(color, alpha)


def cup(g, cx, cy, r=26.0, alpha=255, body=(36, 42, 55), rim_col=(96, 110, 132),
        liquid=None, steam=0.0, t=0.0):
    """Table cup seen slightly from above: body + elliptical rim + handle."""
    g.rrect(cx - r * 0.82, cy - r * 0.6, cx + r * 0.82, cy + r * 1.05, r * 0.24,
            fill=body, alpha=alpha)
    g.ellipse(cx, cy - r * 0.6, r * 0.82, r * 0.3, fill=(14, 17, 23), alpha=alpha)
    g.arc(cx, cy - r * 0.6, r * 0.82, r * 0.3, 0, 360, w=2.0, color=rim_col,
          alpha=int(alpha * 0.9))
    g.arc(cx + r * 0.86, cy + r * 0.05, r * 0.42, r * 0.42, -84, 84, w=2.4,
          color=rim_col, alpha=int(alpha * 0.85))
    if liquid:
        g.ellipse(cx, cy - r * 0.56, r * 0.66, r * 0.22, fill=liquid,
                  alpha=int(alpha * 0.85))
    if steam > 0:
        for k in range(3):
            ph = t * 0.9 + k * 2.1
            pts = []
            for i in range(14):
                yy = cy - r * 0.9 - i * r * 0.16
                xx = cx + math.sin(ph + i * 0.5) * r * 0.12 * (i / 14 + 0.2)
                pts.append((xx, yy))
            g.line(pts, w=2.2, color=(200, 216, 234), alpha=int(70 * steam))


# ------------------------------------------------------------------ head profile
def catmull(pts, closed=True, samples=16):
    out, n = [], len(pts)
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0, p1 = pts[(i - 1) % n], pts[i]
        p2, p3 = pts[(i + 1) % n], pts[(i + 2) % n]
        for j in range(samples):
            t = j / samples
            t2, t3 = t * t, t * t * t
            out.append((0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t +
                               (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
                               (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3),
                        0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t +
                               (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
                               (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)))
    return out


_HEAD_PTS = [(0.045, 0.620), (0.060, 0.360), (0.220, 0.120), (0.460, 0.050),
             (0.700, 0.130), (0.820, 0.300), (0.845, 0.420), (0.860, 0.460),
             (0.975, 0.575), (0.900, 0.605), (0.945, 0.648), (0.885, 0.672),
             (0.935, 0.705), (0.915, 0.775), (0.845, 0.815), (0.720, 0.845),
             (0.585, 0.855), (0.545, 1.000), (0.200, 1.000)]


def head_path(cx, cy, w, h, facing=1):
    return [(cx + (px - 0.5) * w * facing, cy + (py - 0.52) * h)
            for px, py in catmull(_HEAD_PTS, samples=18)]


def head_profile(g, cx, cy, w=700, h=720, facing=1, fill=(15, 18, 25), alpha=255,
                 outline=(70, 84, 106), w_line=3.0, outline_alpha=200, inner=None):
    pts = head_path(cx, cy, w, h, facing)
    g.poly(pts, fill=fill, outline=outline, w=w_line, alpha=alpha)
    if inner:
        g.poly(pts, outline=inner, w=w_line * 0.5, alpha=int(alpha * 0.6))
    return pts


def skull_grid(g, cx, cy, w, h, facing=1, color=(70, 84, 106), alpha=40, step=46):
    """Dotted measurement grid clipped roughly to the skull."""
    pts = head_path(cx, cy, w, h, facing)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    poly = np.array(pts)
    yy = y0 + step
    while yy < y1:
        xx = x0 + step * 0.5
        while xx < x1:
            # ray casting
            inside = False
            j = len(poly) - 1
            for i in range(len(poly)):
                xi, yi = poly[i]
                xj, yj = poly[j]
                if ((yi > yy) != (yj > yy)) and (xx < (xj - xi) * (yy - yi) / (yj - yi + 1e-9) + xi):
                    inside = not inside
                j = i
            if inside:
                g.circle(xx, yy, 1.5, fill=color, alpha=alpha)
            xx += step
        yy += step


# ------------------------------------------------------------------ neural web
class Web:
    """Organic neural graph: scattered nodes, 3 nearest neighbours, curved edges,
    and a wavefront that lights them up from the inside out."""

    def __init__(self, cx, cy, r, seed=5, n=46, min_d=54.0):
        rng = np.random.default_rng(seed)
        pts = []
        tries = 0
        while len(pts) < n and tries < 20000:
            tries += 1
            a = rng.uniform(0, 2 * math.pi)
            rad = r * math.sqrt(rng.uniform(0.02, 1.0))
            p = (cx + math.cos(a) * rad, cy + math.sin(a) * rad * 0.9)
            if all(math.dist(p, q) > min_d for q in pts):
                pts.append(p)
        self.cx, self.cy, self.r = cx, cy, r
        self.nodes = pts
        self.edges = []
        for i, p in enumerate(pts):
            near = sorted(((math.dist(p, q), j) for j, q in enumerate(pts) if j != i))[:3]
            for dist, j in near:
                key = (min(i, j), max(i, j))
                if key not in self.edges:
                    self.edges.append(key)
        self.dist = [math.dist(p, (cx, cy)) for p in pts]
        # tendrils: roots that run out of the web toward the rest of the body
        order = sorted(range(len(pts)), key=lambda k: -self.dist[k])
        self.tendrils = []
        for k in order[:7]:
            p = pts[k]
            vx, vy = p[0] - cx, p[1] - cy
            L = math.hypot(vx, vy) or 1.0
            ext = min(r * 0.30, (0.96 * r - math.hypot(vx, vy)) + 26)
            ext = max(10.0, ext)
            self.tendrils.append((p, (p[0] + vx / L * ext, p[1] + vy / L * ext)))

    def draw(self, g, t=0.0, wave=None, lit=0.0, color=AMBER, base_alpha=46,
             glow=None, node_scale=1.0):
        ex = sorted(((self.dist[i] + self.dist[j]) * 0.5, i, j) for i, j in self.edges)
        for d, i, j in ex:
            p, q = self.nodes[i], self.nodes[j]
            on = (d <= wave) if wave is not None else ((d / self.r) <= lit)
            # slight bow so edges feel organic
            mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
            vx, vy = q[0] - p[0], q[1] - p[1]
            L = math.hypot(vx, vy) or 1.0
            bow = 0.10 * L
            ctrl = (mx - vy / L * bow, my + vx / L * bow)
            path = g.quad(p, ctrl, q, n=10)
            if on:
                a = int(clamp(196 + 50 * math.sin(t * 5.2 + d * 0.09), 0, 255))
                g.line(path, w=2.2 * node_scale, color=color, alpha=a)
                if glow is not None:
                    glow.line(path, w=5, color=255, alpha=80)
            else:
                g.line(path, w=1.2, color=color, alpha=int(base_alpha * 0.55))
        for k, (x, y) in enumerate(self.nodes):
            on = (self.dist[k] <= wave) if wave is not None else ((self.dist[k] / self.r) <= lit)
            g.circle(x, y, (3.6 if on else 2.2) * node_scale, fill=color,
                     alpha=245 if on else int(base_alpha * 1.2))
            if on and glow is not None:
                glow.circle(x, y, 10, fill=255, alpha=110)
        for (p, q) in self.tendrils:
            on = math.dist(p, (self.cx, self.cy)) <= (wave if wave is not None else self.r + 1)
            g.line([p, q], w=1.6, color=color, alpha=150 if on else int(base_alpha * 0.5))
            if on and glow is not None:
                glow.line([p, q], w=4, color=255, alpha=70)


def shockwave(g, cx, cy, r, alpha=160, color=WHITE, w=2.0):
    if r > 1 and alpha > 2:
        g.circle(cx, cy, r, outline=glow_color(color), w=w, alpha=int(alpha))


def glow_color(c):
    return c
