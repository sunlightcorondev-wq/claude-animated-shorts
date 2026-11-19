"""Kinetic typography.

All on-screen words go through here: word-by-word rises, snap-ins, strikes,
tracking-in mono labels, badges. Timing is expressed in local scene seconds and
is driven by word cues from `timeline.py`.

Positions are logical (1080x1920); glyph runs are mapped once and then advanced
in device pixels so tracking stays exact at any camera zoom.
"""
from dataclasses import dataclass, field

from tokens import (AMBER, BLUE, CRIMSON, EASE_VECTOR, GREY, WHITE, clamp,
                    ease_out_cubic, font, mix, rgba, seg)


def measure_line(text, fname, size, tracking=0.0, space_extra=0.0):
    """Widths in logical px for the given logical font size."""
    f = font(fname, size)
    words = text.split()
    out, x = [], 0.0
    space = f.getlength(" ") + tracking + space_extra
    for w in words:
        wl = sum(f.getlength(c) for c in w) + tracking * max(0, len(w) - 1)
        out.append([w, x, wl])
        x += wl + space
    return out, max(0.0, x - space)


def _run(g, x, baseline, text, fname, size, color, alpha, tracking):
    """Draw a glyph run starting at logical (x, baseline), returns end x (logical)."""
    if alpha <= 1 or not text:
        return x
    zs = g.cam.zoom * g.scale
    f = font(fname, size * zs)
    px, py = g.cam.map(g.W, g.H, [(x, baseline)])[0]
    px, py = px * g.scale, py * g.scale
    fill = rgba(color, int(alpha))
    adv = tracking * zs
    for ch in text:
        g.d.text((px, py), ch, font=f, fill=fill, anchor="ls")
        px += f.getlength(ch) + adv
    return x + (px / g.scale - g.cam.map(g.W, g.H, [(0, baseline)])[0][0] * 0) * 0 + \
        (px / g.scale - g.cam.map(g.W, g.H, [(x, baseline)])[0][0])


def draw_word(g, x, baseline, word, fname, size, color, alpha, tracking=0.0):
    if alpha > 1:
        _run(g, x, baseline, word, fname, size, color, alpha, tracking)


@dataclass
class Kinetic:
    """A block of text that assembles word by word."""
    lines: list
    size: int = 84
    fname: str = "black"
    color: tuple = WHITE
    x: float = 540
    y: float = 500                 # baseline of the first line
    align: str = "center"
    lh: float = 1.14
    tracking: float = -1.0
    space_extra: float = 0.0
    t_in: float = 0.0
    stagger: float = 0.055
    dur: float = 0.40
    rise: float = 30.0
    alpha_in: float = 1.0
    t_out: float = None
    out_dur: float = 0.28
    drift: float = 0.0
    scale_in: float = 0.0
    emphasis: dict = field(default_factory=dict)
    emph_scale: float = 0.05
    shadow: float = 0.0

    def word_count(self):
        return sum(len(l.split()) for l in self.lines)

    def end_time(self):
        return self.t_in + max(0, self.word_count() - 1) * self.stagger + self.dur

    def draw(self, g, t):
        if t < self.t_in - 0.02:
            return
        out_a = 1.0
        if self.t_out is not None and t > self.t_out:
            out_a = 1.0 - ease_out_cubic(seg(t, self.t_out, self.t_out + self.out_dur))
            if out_a <= 0.01:
                return
        k = 0
        for li, line in enumerate(self.lines):
            words, total = measure_line(line, self.fname, self.size, self.tracking,
                                        self.space_extra)
            if self.align == "center":
                x0 = self.x - total / 2
            elif self.align == "right":
                x0 = self.x - total
            else:
                x0 = self.x
            base = self.y + li * self.size * self.lh + self.drift * max(0.0, t - self.t_in)
            for w, wx, ww in words:
                p = EASE_VECTOR(seg(t, self.t_in + k * self.stagger,
                                    self.t_in + k * self.stagger + self.dur))
                if p <= 0.001:
                    k += 1
                    continue
                a = 255 * p * out_a * self.alpha_in
                dy = (1 - p) * self.rise
                sc = 1.0 + self.scale_in * (1 - p)
                emph = self.emphasis.get(k)
                col = self.color
                if emph in ("crimson", "amber", "blue", "white", "grey"):
                    col = {"crimson": CRIMSON, "amber": AMBER, "blue": BLUE,
                           "white": WHITE, "grey": GREY}[emph]
                if emph and emph not in ("strike",):
                    sc *= 1.0 + self.emph_scale * p
                sz = self.size * sc
                draw_x = x0 + wx - ww * (sc - 1.0) * 0.5
                if self.shadow > 0:
                    draw_word(g, draw_x + 3, base + dy + 5, w, self.fname, sz,
                              (0, 0, 0), a * 0.5 * self.shadow, self.tracking)
                draw_word(g, draw_x, base + dy, w, self.fname, sz, col, a, self.tracking)
                if emph == "underline":
                    uy = base + dy + self.size * 0.16
                    uw = ww * EASE_VECTOR(seg(t, self.t_in + k * self.stagger + 0.10,
                                              self.t_in + k * self.stagger + 0.46))
                    g.line([(draw_x, uy), (draw_x + max(1, uw), uy)], w=4.5,
                           color=col, alpha=a)
                if emph == "strike":
                    sp = EASE_VECTOR(seg(t, self.t_in + k * self.stagger + self.dur,
                                         self.t_in + k * self.stagger + self.dur + 0.26))
                    if sp > 0:
                        yy = base + dy - self.size * 0.25
                        g.line([(draw_x - 8, yy), (draw_x - 8 + (ww + 16) * sp, yy)],
                               w=max(4, self.size * 0.05), color=CRIMSON, alpha=a,
                               cap=True)
                k += 1


def mono(g, text, x, y, size=26, color=BLUE, alpha=210, tracking=5.0, align="left",
         fname="mono"):
    words, total = measure_line(text, fname, size, tracking)
    x0 = x - total / 2 if align == "center" else (x - total if align == "right" else x)
    _run(g, x0, y, text, fname, size, color, alpha, tracking)
    return total


def type_on(g, text, x, y, t, t0, cps=34.0, size=26, color=BLUE, alpha=220,
            tracking=3.0, caret=True, fname="mono", align="left", caret_alpha=230):
    """Typewriter reveal; returns reveal fraction 0..1."""
    n = len(text)
    shown = 0 if t <= t0 else min(n, int((t - t0) * cps))
    _words, total = measure_line(text, fname, size, tracking)
    x0 = x - total / 2 if align == "center" else (x - total if align == "right" else x)
    if shown > 0:
        _run(g, x0, y, text[:shown], fname, size, color, alpha, tracking)
    if caret and shown < n and int(t * 2.4) % 2 == 0:
        pw, _ = measure_line(text[:shown] + " ", fname, size, tracking)
        cx = x0 + (pw if shown > 0 else 0)
        px, py = g.cam.map(g.W, g.H, [(cx + 2, y)])[0]
        g.rect_px(px * g.scale, (py - size * 0.74) * g.scale,
                  px * g.scale + size * 0.46 * g.cam.zoom * g.scale,
                  (py + size * 0.04) * g.scale, color, caret_alpha)
    return shown / max(1, n)


def badge(g, x, y, text, color=CRIMSON, size=22, alpha=255, fill_alpha=30,
          tracking=4.0, blink=1.0, pad=(18, 13), w=1.4):
    """Outlined mono badge; x, y = centre."""
    tw = measure_line(text, "mono_bold", size, tracking)[1]
    h = size * 2.0
    a = int(clamp(alpha * blink, 0, 255))
    g.rrect(x - tw / 2 - pad[0], y - h / 2, x + tw / 2 + pad[0], y + h / 2, 3,
            fill=color, alpha=int(fill_alpha * (a / 255.0)), outline=color, w=w,
            outline_alpha=a)
    _run(g, x - tw / 2, y + size * 0.36, text, "mono_bold", size, color, a, tracking)
    return tw + pad[0] * 2
