"""Design tokens for FIRST LOVE (dark-psychology 2D explainer).

Every colour, easing curve and font weight used anywhere in the film lives here.
Nothing downstream may invent a colour literal.
"""
import os
from functools import lru_cache

from PIL import ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(ROOT, "fonts")

# ---------------------------------------------------------------- palette
# Global style bible (user brief, 2026-11-19)
VOID      = (11, 13, 18)      # #0B0D12 background void
VOID_DEEP = (6, 7, 10)        # inner shadow / letterbox
SHADOW    = (22, 27, 38)      # #161B26 silhouette fill
SHADOW_HI = (34, 41, 56)      # silhouette rim
BLUE      = (78, 168, 222)    # #4EA8DE cold clinical: reality, present
BLUE_DIM  = (44, 96, 130)
CRIMSON   = (230, 57, 70)     # #E63946 memory trap / danger
CRIMSON_DIM = (112, 30, 40)
AMBER     = (244, 162, 97)    # #F4A261 nostalgia glow
AMBER_DIM = (128, 84, 48)
WHITE     = (241, 250, 238)   # #F1FAEE off-white type
GREY      = (128, 140, 154)
GREY_DIM  = (74, 82, 94)

# semantic aliases
REALITY = BLUE
MEMORY = AMBER
DANGER = CRIMSON
INK = (4, 5, 7)


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def rgba(c, a=255):
    return (c[0], c[1], c[2], int(max(0, min(255, a))))


# ---------------------------------------------------------------- easing
def clamp(x, lo=0.0, hi=1.0):
    return lo if x < lo else hi if x > hi else x


def lerp(a, b, t):
    return a + (b - a) * t


def smoothstep(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def smootherstep(t):
    t = clamp(t)
    return t * t * t * (t * (t * 6 - 15) + 10)


def ease_out_cubic(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def ease_in_cubic(t):
    t = clamp(t)
    return t ** 3


def ease_out_quint(t):
    t = clamp(t)
    return 1 - (1 - t) ** 5


def ease_in_out_cubic(t):
    t = clamp(t)
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


_BEZ_CACHE = {}


def cubic_bezier(x1, y1, x2, y2):
    """CSS-style cubic-bezier easing (returns f(x) for x in 0..1)."""
    key = (round(x1, 4), round(y1, 4), round(x2, 4), round(y2, 4))
    if key in _BEZ_CACHE:
        return _BEZ_CACHE[key]

    def bez(t, p1, p2):
        return 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t * t * p2 + t ** 3

    def f(x):
        x = clamp(x)
        if x <= 0:
            return 0.0
        if x >= 1:
            return 1.0
        lo, hi = 0.0, 1.0
        for _ in range(18):
            mid = (lo + hi) * 0.5
            if bez(mid, x1, x2) < x:
                lo = mid
            else:
                hi = mid
        return bez((lo + hi) * 0.5, y1, y2)

    _BEZ_CACHE[key] = f
    return f


EASE_VECTOR = cubic_bezier(0.22, 1.0, 0.36, 1.0)   # motion language: sharp vector easing
EASE_STANDARD = cubic_bezier(0.4, 0.0, 0.2, 1.0)
EASE_SNAP = cubic_bezier(0.16, 1.0, 0.3, 1.0)


def seg(t, t0, t1):
    """0..1 progress of t through [t0,t1]."""
    if t1 <= t0:
        return 1.0 if t >= t1 else 0.0
    return clamp((t - t0) / (t1 - t0))


def window(t, a, b, fade=0.25):
    """1 inside [a,b] with soft fades of `fade` seconds at both ends."""
    if t < a - fade or t > b + fade:
        return 0.0
    if t < a:
        return ease_out_cubic(seg(t, a - fade, a))
    if t > b:
        return 1 - ease_out_cubic(seg(t, b, b + fade))
    return 1.0


# ---------------------------------------------------------------- type
_FONT_FILES = {
    "black": "Montserrat-Black.ttf",
    "extra": "Montserrat-ExtraBold.ttf",
    "bold": "Montserrat-Bold.ttf",
    "semi": "Inter-SemiBold.ttf",
    "inter": "Inter-Bold.ttf",
    "medium": "Inter-Medium.ttf",
    "mono": "JetBrainsMono-Medium.ttf",
    "mono_bold": "JetBrainsMono-Bold.ttf",
}


@lru_cache(maxsize=256)
def font(name, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, _FONT_FILES[name]), int(round(size)))


def cap_height(name, size):
    """Cap height in px for the given face (measured from the 'H' bbox)."""
    _c = {}
    key = (name, int(size))
    if key in _c:
        return _c[key]
    f = font(name, size)
    l, t, r, b = f.getbbox("H")
    _c[key] = b - t
    return b - t
