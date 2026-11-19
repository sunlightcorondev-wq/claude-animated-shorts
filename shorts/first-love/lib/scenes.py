"""The six scenes.

Each scene is a pure function of local time: `sceneN(frame, t)` -> None.
No state is carried between frames, so any frame can be rendered alone (that is
what makes the stills / QA / parallel render passes exact).
"""
import math

import numpy as np

import motifs as M
from gfx import Cam
from timeline import FPS, HEIGHT, TL, WIDTH
from tokens import (AMBER, AMBER_DIM, BLUE, BLUE_DIM, CRIMSON, CRIMSON_DIM, GREY,
                    GREY_DIM, INK, SHADOW, SHADOW_HI, VOID, VOID_DEEP, WHITE,
                    EASE_SNAP, EASE_VECTOR, clamp, ease_in_cubic, ease_out_cubic,
                    ease_out_quint, font, lerp, mix, rgba, seg, smoothstep,
                    smootherstep, window)
from type import Kinetic, badge, draw_word, measure_line, mono, type_on

PX = 1080.0
DARK, GOLD = 0, 1


# ------------------------------------------------------------------ helpers
def cam_keys(t, keys):
    """keys: [(time, zoom, fx, fy), ...]; smootherstep between, EASE_SNAP if tup has 5."""
    if t <= keys[0][0]:
        k = keys[0]
        return Cam(k[1], k[2], k[3])
    for i in range(len(keys) - 1):
        a, b = keys[i], keys[i + 1]
        if a[0] <= t <= b[0]:
            u = seg(t, a[0], b[0])
            ease = b[4] if len(b) > 4 else smootherstep
            u = ease(u)
            return Cam(lerp(a[1], b[1], u), lerp(a[2], b[2], u), lerp(a[3], b[3], u))
    k = keys[-1]
    return Cam(k[1], k[2], k[3])


def shake(t, t0, amp=10.0, dur=0.34, seed=1):
    if t < t0 or t > t0 + dur:
        return 0.0, 0.0
    p = 1.0 - seg(t, t0, t0 + dur)
    r = np.random.default_rng(int(t * FPS) + seed)
    return r.normal(0, amp * p), r.normal(0, amp * p)


def chrome(f, g, scene, t, accent=BLUE, alpha=1.0):
    """Editorial furniture: chapter eyebrow, series mark, segmented progress rail."""
    i, title = scene["i"], scene["title"]
    a = int(215 * alpha)
    mono(g, f"{i:02d}", 62, 152, size=32, color=accent, alpha=a, tracking=2)
    g.line([(104, 122), (104, 152)], w=2.2, color=accent, alpha=int(a * 0.55))
    mono(g, title, 128, 152, size=23, color=WHITE, alpha=int(a * 0.86), tracking=5.2)
    mono(g, "FIRST LOVE", 1018, 152, size=19, color=GREY, alpha=int(a * 0.60),
         tracking=5.0, align="right")

    y = HEIGHT - 58
    g.line([(62, y), (WIDTH - 62, y)], w=1.0, color=GREY_DIM, alpha=int(70 * alpha))
    n = len(TL.scenes)
    x0, x1 = 62, WIDTH - 62
    w = (x1 - x0 - (n - 1) * 14) / n
    for k in range(n):
        bx = x0 + k * (w + 14)
        done = k < i - 1
        cur = k == i - 1
        col = accent if cur else (WHITE if done else GREY)
        al = 215 if cur else (60 if done else 26)
        g.rect(bx, y + 9, bx + w, y + 12, fill=col, alpha=int(al * alpha))


def ui_cam(g):
    """Type and chrome live on their own flat camera: the world can push in, the
    type stays exactly where it was designed."""
    g.cam = Cam(1.0, 540.0, 960.0)


def hero(f, g, lines, t, t_in, size=96, y=470, x=540, color=WHITE, **kw):
    k = Kinetic(lines=lines, size=size, y=y, x=x, color=color, t_in=t_in, **kw)
    k.draw(g, t)
    return k


# ================================================================== S1
TABLE_FAR, TABLE_NEAR = 1300.0, 1636.0
GHOST_CX, GHOST_HEAD_Y, GHOST_SEAT = 706.0, 852.0, TABLE_FAR


def pov_room(f, g, t, lamp=700.0, wall_gain=0.34, ghost_alpha=0.0, ghost_progress=0.0,
             ghost_glow=0.0, cold=0.0, warm=0.0, hands=1.0, fade=0.0,
             chair_rim=0.0, table_rim=140):
    """Shared staging for S1 and S6: we are sitting at the table, looking across it.

    Returns the ghost's key points so scenes can attach cues to them.
    """
    f.bg_gradient(top=(28, 36, 50), bottom=(6, 7, 11), cy=0.32)
    wall_col = mix((104, 132, 164), (214, 182, 142), warm)
    wall = f.glow(color=wall_col, blur=150, gain=wall_gain, down=4)
    wall.ellipse(lamp - 20, 820, 470, 560, fill=255, alpha=190)

    # floor + wall seam
    g.rect(0, TABLE_NEAR + 60, WIDTH, HEIGHT, fill=(5, 6, 9), alpha=255)
    g.line([(1030, 260), (1030, TABLE_NEAR + 60)], w=1.0, color=SHADOW_HI, alpha=18)

    # pendant lamp
    g.line([(lamp, 0), (lamp, 470)], w=2.2, color=(48, 56, 70), alpha=255)
    g.poly([(lamp - 44, 470), (lamp + 44, 470), (lamp + 78, 540), (lamp - 78, 540)],
           fill=(28, 34, 45), alpha=255)
    g.line([(lamp - 78, 540), (lamp + 78, 540)], w=2.0, color=(62, 74, 92), alpha=255)
    f.glow(color=(228, 240, 255), blur=26, gain=1.0, down=4).ellipse(lamp, 552, 24, 24,
                                                                     fill=255, alpha=255)
    g.ellipse(lamp, 552, 12, 12, fill=(244, 250, 255), alpha=255)
    cone_col = mix((150, 180, 216), (255, 210, 158), warm)
    cone = f.glow(color=cone_col, blur=80, gain=0.28 + 0.08 * warm, down=4)
    cone.poly([(lamp - 24, 556), (lamp + 24, 556), (lamp + 330, TABLE_NEAR + 40),
               (lamp - 330, TABLE_NEAR + 40)], fill=255, alpha=140)
    cone2 = f.glow(color=mix((208, 226, 248), (255, 232, 198), warm), blur=50,
                   gain=0.16, down=4)
    cone2.poly([(lamp - 12, 558), (lamp + 12, 558), (lamp + 150, TABLE_NEAR + 40),
                (lamp - 150, TABLE_NEAR + 40)], fill=255, alpha=110)

    # far chair
    M.chair_front(g, GHOST_CX, GHOST_SEAT, s=1.0, color=(8, 10, 14), alpha=255,
                  rim=(72, 86, 110), rim_alpha=int(26 + 95 * chair_rim), w=330,
                  top=286)

    # the seat's aura
    if ghost_glow > 0.01:
        f.glow(color=AMBER, blur=90, gain=0.16 * ghost_glow, down=4).ellipse(
            GHOST_CX, 1030, 230, 330, fill=255, alpha=170)
        f.glow(color=AMBER, blur=40, gain=0.30 * ghost_glow, down=4).ellipse(
            GHOST_CX, TABLE_FAR + 6, 150, 22, fill=255, alpha=190)
    if cold > 0.01:
        f.glow(color=BLUE, blur=54, gain=0.52 * cold, down=4).ellipse(
            GHOST_CX, 1080, 180, 320, fill=255, alpha=160)
        f.glow(color=BLUE, blur=46, gain=0.40 * cold, down=4).ellipse(
            GHOST_CX, TABLE_FAR + 4, 210, 30, fill=255, alpha=150)

    # the ghost
    if ghost_alpha > 0.01:
        def _draw(sur):
            M.front_figure(sur, GHOST_CX, GHOST_HEAD_Y, s=1.20, color=WHITE,
                           alpha=255, table_y=TABLE_FAR, part="body")
            M.front_figure(sur, GHOST_CX, GHOST_HEAD_Y, s=1.20, color=WHITE,
                           alpha=255, table_y=TABLE_FAR, part="arms",
                           hand=(-205.0, 178.0))
        gl = f.glow(color=AMBER, blur=54, gain=0.55 * ghost_glow, down=4)
        M.scan_hologram(g, _draw, t=t, alpha=236 * ghost_alpha, progress=ghost_progress,
                        color=AMBER, glow=gl, step=16.0, band_speed=190)

    # table in perspective
    M.table_persp(g, 540, TABLE_NEAR, w=1240, far_w=700, s=1.0, color=(9, 11, 16),
                  alpha=255, rim=(104, 118, 142), rim_alpha=int(table_rim),
                  depth=TABLE_NEAR - TABLE_FAR, leg_to=TABLE_NEAR + 80,
                  top_color=(26, 32, 42))

    # cups: theirs far and untouched, ours near
    f.glow(color=(0, 0, 0), blur=26, gain=0.0, down=4)
    g.ellipse(GHOST_CX + 148, TABLE_FAR + 60, 46, 13, fill=(4, 5, 8), alpha=200)
    g.ellipse(250, TABLE_NEAR - 60, 78, 22, fill=(4, 5, 8), alpha=200)
    M.cup(g, GHOST_CX + 148, TABLE_FAR + 54, r=32, alpha=225,
          liquid=(120, 78, 44) if warm < 0.5 else (150, 120, 70), t=t)
    M.cup(g, 250, TABLE_NEAR - 66, r=64, alpha=250, t=t,
          liquid=(40, 30, 24), steam=0.45 * hands)

    # our forearm + hand on the table
    if hands > 0.02:
        M.forearm(g, (760, 2000), (700, TABLE_NEAR + 30), w=92,
                  color=(9, 11, 16), alpha=int(250 * hands),
                  rim=(104, 126, 156), rim_alpha=int(120 * hands),
                  rim_dir=(12.0, 4.0), hand=(52, 30))
    return dict(ghost=(GHOST_CX, GHOST_HEAD_Y), seat=(GHOST_CX, GHOST_SEAT))


def scene1(f, t, s):
    """THE GHOST TRAP - across the table from a guest made of light."""
    cue_ghost = TL.cue("s1", "ghost")
    cue_dissolve = TL.cue("s1", "existed")
    cue_spend = TL.cue("s1", "sabotaging")

    zoom = 1.0 + 0.05 * ease_out_cubic(seg(t, 0, cue_ghost))
    fx, fy = 540, 1080
    if t > cue_ghost - 0.10:
        p = EASE_SNAP(seg(t, cue_ghost - 0.10, cue_ghost + 0.20))
        zoom = lerp(1.05, 1.22, p)
        fx, fy = lerp(540, 706, p), lerp(1080, 1090, p)
    sx, sy = shake(t, cue_ghost - 0.05, amp=13, dur=0.32, seed=4)
    f.set_cam(Cam(zoom, fx, fy, sx, sy))
    g = f.surface()
    fade_in = 1.0 - ease_out_cubic(seg(t, 0.0, 1.25))
    f.vignette = 0.54
    f.grain = 0.036

    prog = smootherstep(seg(t, cue_dissolve - 0.7, cue_dissolve + 3.0))
    cold = clamp(seg(t, cue_dissolve + 1.8, cue_dissolve + 4.2))
    pov_room(f, g, t, ghost_alpha=1.0 - fade_in * 0.85, ghost_progress=prog,
             ghost_glow=(1.0 - prog) * (1 - fade_in * 0.6), cold=cold,
             hands=0.0, fade=fade_in)

    _s1_dust().draw(g, t, color=(214, 228, 246), alpha=0.24 + 0.6 * prog)
    if prog > 0.04:
        _s1_burst().draw(g, t, color=AMBER, alpha=prog * 0.95)

    # ---------------- type
    ui_cam(g)
    hero_kw = dict(tracking=-2.0, stagger=0.085, lh=1.08)
    if t < cue_ghost + 1.5:
        Kinetic(lines=["NOT A", "PERSON."], size=104, y=372, x=88, align="left",
                color=WHITE, t_in=TL.cue("s1", "haunted") - 0.12,
                t_out=TL.cue("s1", "protect") - 0.65, out_dur=0.26,
                **hero_kw).draw(g, t)
        if t > cue_dissolve - 0.4:
            type_on(g, "MEMORY ARTIFACT / UNVERIFIED", 90, 596, t,
                    cue_dissolve - 0.4, cps=26, size=24, color=AMBER, alpha=205,
                    tracking=5.2, caret=False)
    if t > cue_ghost - 0.30:
        Kinetic(lines=["A GHOST."], size=112, y=470, x=88, align="left",
                color=CRIMSON, t_in=cue_ghost - 0.30, tracking=-3.0, stagger=0.09,
                rise=44, scale_in=0.05, emph_scale=0.04).draw(g, t)
    if t > cue_spend - 0.2:
        a = window(t, cue_spend, cue_ghost - 0.5, fade=0.4)
        if a > 0:
            mono(g, "REAL PEOPLE \u2192 DISQUALIFIED", 90, 660, size=24,
                 color=GREY, alpha=int(180 * a), tracking=4.8)

    chrome(f, g, s, t, accent=CRIMSON if t > cue_ghost - 0.3 else BLUE)
    if t < 1.1:
        f.fade_to_black = 1.0 - ease_out_cubic(seg(t, 0.0, 1.10))
    if t > s["dur"] - 0.25:
        f.fade_to_black = ease_in_cubic(seg(t, s["dur"] - 0.25, s["dur"]))


_S1_DUST = None
_S1_BURST = None


def _s1_dust():
    global _S1_DUST
    if _S1_DUST is None:
        _S1_DUST = M.Dust(n=60, seed=11, box=(520, 700, 1010, 1500),
                          rise=(5, 20), life=(3.0, 7.0), size=(0.7, 1.7))
    return _S1_DUST


def _s1_burst():
    global _S1_BURST
    if _S1_BURST is None:
        _S1_BURST = M.Dust(n=120, seed=23, box=(640, 760, 900, 1260),
                           rise=(30, 100), life=(1.5, 3.6), size=(0.8, 2.2))
    return _S1_BURST


# ================================================================== S2
_WEB = None


def _s2_web():
    global _WEB
    if _WEB is None:
        _WEB = M.Web(492, 900, 250, seed=11, n=44, min_d=58)
    return _WEB


def scene2(f, t, s):
    """NEURAL IMPRINT - the first attachment etches a template."""
    c_who = TL.cue("s2", "who")
    c_when = TL.cue("s2", "when")
    c_base = TL.cue("s2", "baseline")
    c_carve = TL.cue("s2", "carving")
    c_blue = TL.cue("s2", "blueprint")
    c_sub = TL.cue("s2", "subconscious")
    dur = s["dur"]

    keys = [(0, 1.02, 540, 880), (6, 1.05, 520, 900), (13.5, 1.0, 520, 930),
            (c_base - 0.2, 1.0, 520, 930),
            (c_base + 1.4, 1.15, 512, 916, EASE_SNAP), (c_carve + 2.2, 1.10, 512, 940),
            (c_blue - 0.5, 1.10, 512, 980),
            (c_blue + 0.5, 1.0, 540, 1010, EASE_SNAP), (dur, 1.05, 540, 1120)]
    cam = cam_keys(t, keys)
    sx, sy = shake(t, c_blue + 0.04, amp=16, dur=0.36, seed=7)
    cam = cam.copy(px=cam.px + sx, py=cam.py + sy)
    f.set_cam(cam)

    f.bg_gradient(top=(23, 30, 42), bottom=(5, 6, 9), cy=0.26)
    g = f.surface()
    f.vignette = 0.58
    f.grain = 0.036

    # blueprint wall: faint measurement grid behind everything
    led = 1.0
    for yy in range(180, HEIGHT, 64):
        g.line([(0, yy), (WIDTH, yy)], w=1.0, color=(120, 140, 170), alpha=10)
    for xx in range(0, WIDTH, 64):
        g.line([(xx, 0), (xx, HEIGHT)], w=1.0, color=(120, 140, 170), alpha=8)

    # ---------------- head + skull chamber
    head_pts = M.head_path(512, 900, 690, 715)
    fill = mix((14, 17, 23), (19, 23, 31), 0.5)
    g.poly(head_pts, fill=fill, alpha=255)
    g.poly(head_pts, outline=(96, 112, 136), w=3.2, alpha=150)
    # chamber arc
    g.arc(512, 900, 260, 300, 168, 372, w=2.0, color=(120, 138, 164), alpha=55)
    M.skull_grid(g, 512, 900, 690, 715, color=(120, 140, 170), alpha=26, step=44)

    web = _s2_web()
    wave_r = -1.0
    if t > c_base + 0.30:
        wave_r = 320 * ease_out_quint(seg(t, c_base + 0.30, c_carve + 2.4))
    gl = f.glow(color=AMBER, blur=34, gain=0.85, down=4)
    web.draw(g, t=t, wave=(wave_r if wave_r >= 0 else None), color=AMBER,
             base_alpha=40, glow=(gl if wave_r > 0 else None))

    # the spark
    if t > c_base - 0.55:
        drop = EASE_SNAP(seg(t, c_base - 0.55, c_base + 0.12))
        sy0 = lerp(430, 884, drop)
        a = int(255 * clamp(seg(t, c_base - 0.55, c_base - 0.2)))
        if t < c_base + 0.35:
            g.line([(512, sy0 - 130), (512, sy0)], w=3.0, color=AMBER, alpha=int(a * 0.5))
        g.circle(512, sy0, 9, fill=WHITE, alpha=a)
        f.glow(color=AMBER, blur=26, gain=1.0, down=4).ellipse(512, sy0, 40, 40,
                                                              fill=255, alpha=a)
    for k in range(3):
        t0 = c_base + 0.10 + k * 0.26
        if t > t0:
            p = ease_out_quint(seg(t, t0, t0 + 1.5))
            g.circle(486, 884, 60 + 620 * p, outline=WHITE, w=1.8,
                     alpha=int(90 * (1 - p) * (1 - p)))

    # ---------------- type
    ui_cam(g)
    if t < c_base - 0.3:
        Kinetic(lines=["WHO THEY WERE"], size=74, y=352, x=540, align="center",
                color=WHITE, t_in=c_who - 0.25, emphasis={2: "strike"},
                tracking=-1.5, stagger=0.07,
                t_out=c_when + 4.6, out_dur=0.3).draw(g, t)
        if t > c_when - 0.05:
            Kinetic(lines=["WHEN THEY HAPPENED"], size=74, y=462, x=540,
                    align="center", color=WHITE, t_in=c_when - 0.05,
                    emphasis={2: "amber", 1: "amber"}, tracking=-1.5, stagger=0.07,
                    t_out=c_when + 4.6, out_dur=0.3).draw(g, t)
    else:
        Kinetic(lines=["NO BASELINE."], size=94, y=384, x=540, align="center",
                color=WHITE, t_in=c_base + 0.05, tracking=-2.0, stagger=0.08,
                t_out=c_blue - 0.85, out_dur=0.28).draw(g, t)

    # console: the question the brain keeps asking
    if t > c_base + 1.1 and t < c_blue - 0.6:
        a = window(t, c_base + 1.1, c_blue - 0.6, fade=0.35)
        mono(g, "\u00bb", 122, 1352, size=30, color=AMBER, alpha=int(210 * a))
        type_on(g, "QUERY: IS THIS PERSON GOOD FOR ME?", 158, 1352, t,
                c_base + 1.25, cps=30, size=27, color=WHITE, alpha=int(215 * a),
                tracking=2.2, caret=False)
        if t > c_sub:
            mono(g, "QUERY: DOES THIS FEEL LIKE THE FIRST TIME?", 158, 1404,
                 size=27, color=AMBER, alpha=int(230 * window(t, c_sub, c_blue - 0.6,
                                                              fade=0.3)), tracking=2.2)
    # ---------------- blueprint card
    if t > c_blue - 0.32:
        p = EASE_SNAP(seg(t, c_blue - 0.32, c_blue + 0.18))
        y0 = lerp(2100, 1452, p)
        if y0 < 1900:
            _blueprint_card(f, g, y0, t, c_blue)

    chrome(f, g, s, t, accent=AMBER if t > c_when else BLUE)

    # split-screen reveal
    if t < 1.35:
        gap = smootherstep(seg(t, 0.05, 1.20)) * (HEIGHT * 0.55)
        g.rect_px(0, 0, WIDTH * f.S, (HEIGHT / 2 - gap / 2) * f.S, (4, 5, 8), 255)
        g.rect_px(0, (HEIGHT / 2 + gap / 2) * f.S, WIDTH * f.S, HEIGHT * f.S,
                  (4, 5, 8), 255)
        for yy in ((HEIGHT / 2 - gap / 2), (HEIGHT / 2 + gap / 2)):
            g.rect_px(0, yy * f.S, WIDTH * f.S, (yy + 2) * f.S, AMBER, 200)
    if t > dur - 0.2:
        f.fade_to_black = ease_in_cubic(seg(t, dur - 0.2, dur))


def _blueprint_card(f, g, y0, t, c_blue):
    x0, x1 = 76, 1004
    h = 372
    g.rect(x0, y0, x1, y0 + h, fill=(12, 15, 21), alpha=245)
    g.rect(x0, y0, x1, y0 + h, outline=AMBER, w=1.6, alpha=190)
    # grid
    for xx in range(int(x0) + 24, int(x1), 36):
        g.line([(xx, y0 + 2), (xx, y0 + h - 2)], w=1.0, color=AMBER, alpha=12)
    for yy in range(int(y0) + 24, int(y0 + h), 36):
        g.line([(x0 + 2, yy), (x1 - 2, yy)], w=1.0, color=AMBER, alpha=12)
    # corner ticks
    for (cx, cy, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y0 + h, 1, -1),
                             (x1, y0 + h, -1, -1)):
        g.line([(cx, cy + 26 * dy), (cx, cy)], w=2.4, color=AMBER, alpha=220)
        g.line([(cx, cy), (cx + 26 * dx, cy)], w=2.4, color=AMBER, alpha=220)
    mono(g, "NEURAL BLUEPRINT", x0 + 40, y0 + 92, size=34, color=WHITE,
         alpha=240, tracking=4.0)
    mono(g, "IMPRINT LOCKED  /  t\u2080", x0 + 40, y0 + 140, size=22, color=AMBER,
         alpha=210, tracking=4.2)
    mono(g, "BASELINE: NONE", x0 + 40, y0 + 246, size=22, color=GREY, alpha=190,
         tracking=3.4)
    mono(g, "PERMANENT", x0 + 40, y0 + 296, size=22, color=CRIMSON, alpha=200,
         tracking=3.4)
    # right: mini neural signature
    rng = np.random.default_rng(3)
    cxc, cyc = x1 - 210, y0 + 176
    g.circle(cxc, cyc, 104, outline=AMBER, w=1.2, alpha=70)
    g.circle(cxc, cyc, 68, outline=AMBER, w=1.0, alpha=45)
    for k in range(9):
        a0 = rng.uniform(0, 6.28)
        r0, r1 = rng.uniform(20, 60), rng.uniform(80, 100)
        g.line([(cxc + math.cos(a0) * r0, cyc + math.sin(a0) * r0),
                (cxc + math.cos(a0) * r1 * 1.1, cyc + math.sin(a0) * r1)],
               w=1.6, color=AMBER, alpha=140)
    for k in range(5):
        g.arc(cxc, cyc, 30 + k * 18, 30 + k * 18, rng.uniform(0, 360),
              rng.uniform(60, 200), w=1.2, color=AMBER, alpha=90)


# ================================================================== S3
TRACK_X0, TRACK_X1 = 176.0, 932.0
TRACK_A_Y, TRACK_B_Y = 902.0, 1246.0


def _track_bar(g, x0, y, frac, color, alpha=255, h=26, cap=True, spikes=None,
               jagged=False, t=0.0, dim=0.0):
    x1 = x0 + frac * (TRACK_X1 - x0)
    if frac <= 0.001:
        return x1
    x1 = max(x1, x0 + 6)
    col = mix(color, (110, 118, 130), dim)
    g.rrect(x0, y, x1, y + h, 4, fill=col, alpha=int(alpha * (1 - 0.35 * dim)))
    if spikes:
        rng = np.random.default_rng(91)
        sx = x0 + 8
        while sx < x1 - 8:
            hh = spikes * (0.35 + rng.random() * 0.9) * (0.55 + 0.45 * math.sin(t * 3 + sx * 0.05))
            g.rect(sx, y - hh, sx + 3, y - 2, fill=color, alpha=int(200 * (1 - dim)))
            sx += 11
    if cap:
        g.rect(x1 - 4, y - 6, x1, y + h + 6, fill=WHITE, alpha=int(200 * (1 - dim)))
    if jagged:
        # sheared end: three teeth
        pts = [(x1, y), (x1 + 16, y + h * 0.4), (x1 + 5, y + h * 0.6),
               (x1 + 18, y + h), (x1, y + h)]
        g.poly(pts, fill=col, alpha=int(alpha * (1 - 0.35 * dim)))
    return x1


def scene3(f, t, s):
    """THE ZEIGARNIK LOOP - one track closes, the other snaps and keeps spinning."""
    c_zeig = TL.cue("s3", "Zeigarnik")
    c_laundry = TL.cue("s3", "laundry")
    c_abrupt = TL.cue("s3", "abruptly")
    c_conc = TL.cue("s3", "conclusion")
    c_file = TL.cue("s3", "file")
    c_dec = TL.cue("s3", "decades")
    dur = s["dur"]

    break_x_default = TRACK_X0 + 0.66 * (TRACK_X1 - TRACK_X0)
    zoom0 = 1.0
    keys = [(0, 1.02, 540, 1000), (4, 1.02, 540, 1010),
            (c_abrupt - 1.2, 1.03, 580, 1060),
            (c_abrupt + 0.30, 1.05, 596, 1120, EASE_SNAP),
            (c_conc + 1.0, 1.02, 580, 1090),
            (c_file - 0.6, 1.06, 604, 1080),
            (dur, 1.07, 604, 1080)]
    cam = cam_keys(t, keys)
    sx, sy = shake(t, c_abrupt + 0.02, amp=15, dur=0.34, seed=11)
    cam = cam.copy(px=cam.px + sx, py=cam.py + sy)
    f.set_cam(cam)

    f.bg_gradient(top=(22, 28, 40), bottom=(5, 6, 9), cy=0.3)
    g = f.surface()
    f.vignette = 0.58
    f.grain = 0.036

    # the loop, drawing itself forever in the background
    for k, (rr, al) in enumerate(((430, 16), (528, 9))):
        spin = t * (7 if k == 0 else -5)
        for seg_i in range(0, 360, 30):
            g.arc(540, 1040, rr, rr * 0.94, spin + seg_i, spin + seg_i + 20, w=1.6,
                  color=CRIMSON, alpha=al)
    # measurement grid
    for yy in range(240, HEIGHT, 72):
        g.line([(0, yy), (WIDTH, yy)], w=1.0, color=(110, 130, 160), alpha=9)
    for xx in range(0, WIDTH, 72):
        g.line([(xx, 0), (xx, HEIGHT)], w=1.0, color=(110, 130, 160), alpha=7)

    # ---------------- track A: the one that closed
    a_closed = clamp(seg(t, c_laundry - 0.2, c_laundry + 1.4))
    a_frac = ease_out_cubic(seg(t, 0.6, c_laundry - 0.2))
    a_dim = clamp(seg(t, c_laundry + 0.6, c_laundry + 2.4))
    # the ledger panel
    px0, py0, px1, py1 = 108, 742, 972, 1336
    g.rrect(px0, py0, px1, py1, 6, fill=(10, 13, 19), alpha=232)
    g.rrect(px0, py0, px1, py1, 6, outline=(96, 110, 132), w=1.4, alpha=110)
    g.line([(px0 + 1, py0 + 66), (px1 - 1, py0 + 66)], w=1.0, color=(96, 110, 132),
           alpha=80)
    mono(g, "ATTACHMENT LEDGER", px0 + 28, py0 + 42, size=20, color=WHITE, alpha=200,
         tracking=4.4)
    mono(g, "2 RECORDS", px1 - 28, py0 + 42, size=18, color=GREY, alpha=160,
         tracking=3.6, align="right")
    # right-hand status ticks
    for k in range(6):
        g.line([(px1 - 28, py1 - 34 - k * 14), (px1 - 28 - 12, py1 - 34 - k * 14)],
               w=1.2, color=(120, 136, 160), alpha=45)

    # grooves behind each track
    g.rect(TRACK_X0, TRACK_A_Y + 12, TRACK_X1, TRACK_A_Y + 14, fill=(80, 92, 108),
           alpha=55)
    g.rect(TRACK_X0, TRACK_B_Y + 12, TRACK_X1, TRACK_B_Y + 14, fill=(80, 92, 108),
           alpha=45)
    for xx in range(int(TRACK_X0), int(TRACK_X1) + 1, 82):
        g.line([(xx, TRACK_B_Y + 40), (xx, TRACK_B_Y + 48)], w=1.2,
               color=(110, 124, 146), alpha=60)
    if a_frac > 0:
        mono(g, "A / 10-YR RELATIONSHIP", TRACK_X0, TRACK_A_Y - 34, size=22,
             color=GREY, alpha=int(190 * (1 - 0.3 * a_dim)), tracking=4.0)
        ax1 = _track_bar(g, TRACK_X0, TRACK_A_Y, a_frac, (150, 160, 172), alpha=230,
                         dim=a_dim, t=t)
        if a_closed > 0.02:
            # the loop closes: a ring at the end of track A
            r = 30
            g.arc(ax1 + 18, TRACK_A_Y + 13, r, r, -90, -90 + 360 * a_closed, w=5.0,
                  color=BLUE if a_dim < 0.5 else (150, 160, 172), alpha=235)
            if a_closed > 0.9:
                mono(g, "CLOSED", ax1 + 58, TRACK_A_Y + 21, size=20, color=GREY,
                     alpha=int(200 * window(t, c_laundry + 0.7, dur)), tracking=3.6)


    # ---------------- track B: the one that broke
    b_frac = 0.66 * ease_out_quint(seg(t, c_abrupt - 5.2, c_abrupt + 0.05))
    broke = t > c_abrupt + 0.05
    if t > 1.0:
        mono(g, "B / FIRST LOVE", TRACK_X0, TRACK_B_Y - 34, size=22, color=CRIMSON,
             alpha=225, tracking=4.0)
        b_end = _track_bar(g, TRACK_X0, TRACK_B_Y, max(0.005, b_frac), CRIMSON,
                           alpha=250, spikes=26, jagged=broke, t=t)

        if broke:
            # sheared end + a loop that never resolves
            ring_c = (b_end + 96, TRACK_B_Y + 13)
            spin = (t - c_abrupt) * 210
            for k, (rr, al, sp) in enumerate(((56, 235, 1.0), (40, 150, -1.5),
                                              (74, 70, 0.6))):
                a0 = spin * sp + k * 90
                g.arc(ring_c[0], ring_c[1], rr, rr, a0, a0 + 250, w=4.0 if k == 0 else 2.0,
                      color=CRIMSON, alpha=al)
            glr = f.glow(color=CRIMSON, blur=40, gain=0.5 + 0.15 * math.sin(t * 4.0), down=4)
            glr.ellipse(ring_c[0], ring_c[1], 78, 78, fill=255, alpha=120)
            # jagged debris drifting from the break
            rng = np.random.default_rng(4)
            for k in range(9):
                dxx = rng.uniform(10, 220) * (1 - math.exp(-(t - c_abrupt) * 0.7))
                dyy = rng.uniform(-90, 60)
                g.rect(b_end + dxx, TRACK_B_Y + dyy, b_end + dxx + 7, TRACK_B_Y + dyy + 4,
                       fill=CRIMSON, alpha=int(190 * max(0, 1 - (t - c_abrupt) / 3.2)))
            # freeze-frame shockwave at the break
            p = seg(t, c_abrupt + 0.05, c_abrupt + 1.1)
            if p < 1:
                g.circle(b_end, TRACK_B_Y + 13, 40 + 420 * ease_out_quint(p),
                         outline=WHITE, w=2.2, alpha=int(120 * (1 - p) ** 2))


    # pulses along track B while it runs
    if t > 2.0 and not broke:
        for k in range(3):
            ph = (t * 1.7 + k / 3) % 1.0
            pxx = TRACK_X0 + ph * (TRACK_X1 - TRACK_X0)
            g.line([(pxx, TRACK_B_Y - 30), (pxx, TRACK_B_Y + 56)], w=2.4, color=CRIMSON,
                   alpha=int(120 * (1 - ph)))

    # ---------------- type
    ui_cam(g)
    Kinetic(lines=["ZEIGARNIK"], size=104, y=372, x=540, align="center", color=WHITE,
            t_in=c_zeig - 0.3, tracking=-2.0, stagger=0.08,
            t_out=c_zeig + 3.4, out_dur=0.3).draw(g, t)
    Kinetic(lines=["EFFECT"], size=104, y=490, x=540, align="center", color=CRIMSON,
            t_in=c_zeig + 0.34, tracking=-1.0, stagger=0.08,
            t_out=c_zeig + 3.4, out_dur=0.3).draw(g, t)
    if t > c_laundry - 2.2:
        Kinetic(lines=["UNFINISHED"], size=72, y=372, x=540, align="center",
                color=WHITE, t_in=c_laundry - 2.2, tracking=2.0, stagger=0.07,
                t_out=c_abrupt + 1.6, out_dur=0.28).draw(g, t)
        Kinetic(lines=["BUSINESS"], size=72, y=472, x=540, align="center",
                color=WHITE, t_in=c_laundry - 1.75, tracking=2.0, stagger=0.07,
                t_out=c_abrupt + 1.6, out_dur=0.28).draw(g, t)
    if t > c_conc + 0.2:
        Kinetic(lines=["THE STORY", "NEVER ENDED."], size=66, y=1700, x=540,
                align="center", color=WHITE, t_in=c_conc + 0.2, tracking=-1.0,
                stagger=0.07, t_out=c_file - 0.8, out_dur=0.3).draw(g, t)
    if t > c_file - 0.35:
        blink = 0.55 + 0.45 * (1.0 if math.sin(t * 7.5) > -0.2 else 0.25)
        badge(g, 540, 1704, "FILE: UNCLOSED", color=CRIMSON, size=27, blink=blink,
              tracking=5.0, pad=(26, 18))

    # open-loop counter, pinned to the frame (not the camera)
    open_t = max(0.0, t - c_abrupt)
    if t > c_abrupt + 0.4:
        label = "OPEN  00:%02d" % int(open_t) if t < c_dec else "OPEN  30 YEARS"
        mono(g, "LOOP STATE", 1018, 214, size=18, color=GREY, alpha=150,
             tracking=4.0, align="right")
        mono(g, label, 1018, 268, size=32,
             color=CRIMSON if t < c_dec else WHITE, alpha=240, tracking=4.4,
             align="right")
        g.rect(854, 288, 1018, 292, fill=CRIMSON,
               alpha=int(170 + 70 * math.sin(t * 5)))

    chrome(f, g, s, t, accent=CRIMSON if t > c_zeig else BLUE)
    if t > dur - 0.2:
        f.fade_to_black = ease_in_cubic(seg(t, dur - 0.2, dur))


# ================================================================== S4
FILM_Y = 1006.0
FRAMES = [
    ("phone", DARK), ("clock", DARK), ("warn", DARK), ("sun", GOLD), ("heart", GOLD),
]


def _film_icon(g, kind, cx, cy, r, color, alpha, t=0.0, crack=1.0, glow=None):
    if kind == "phone":
        M.phone_icon(g, cx, cy, r, color=color, alpha=alpha, w=3.2, crack=crack)
    elif kind == "clock":
        M.clock_icon(g, cx, cy, r, color=color, alpha=alpha, w=3.2, t=t)
    elif kind == "warn":
        M.warn_triangle(g, cx, cy, r * 0.92, color=color, alpha=alpha, w=3.4)
    elif kind == "sun":
        g.circle(cx, cy, r * 0.34, fill=color, alpha=alpha)
        for k in range(8):
            a = k / 8 * 2 * math.pi + t * 0.2
            g.line([(cx + math.cos(a) * r * 0.5, cy + math.sin(a) * r * 0.5),
                    (cx + math.cos(a) * r * 0.78, cy + math.sin(a) * r * 0.78)],
                   w=3.0, color=color, alpha=alpha)
    elif kind == "smile":
        g.arc(cx, cy - r * 0.1, r * 0.62, r * 0.62, 20, 160, w=4.0, color=color,
              alpha=alpha)
        g.circle(cx - r * 0.28, cy - r * 0.38, r * 0.075, fill=color, alpha=alpha)
        g.circle(cx + r * 0.28, cy - r * 0.38, r * 0.075, fill=color, alpha=alpha)
    elif kind == "heart":
        M.heart(g, cx, cy, r * 0.8, color=color, alpha=alpha, fill=False, w=3.4)


def scene4(f, t, s):
    """EUPHORIC RECALL - the reel gets edited until only the highlight survives."""
    c_recall = TL.cue("s4", "recall")
    c_flags = TL.cue("s4", "flags")
    c_reel = TL.cue("s4", "reel")
    c_art = TL.cue("s4", "artifact")
    c_peak = TL.cue("s4", "peak")
    c_guard = TL.cue("s4", "guarded")
    dur = s["dur"]

    keys = [(0, 1.04, 540, 845), (5, 1.02, 540, 885), (c_flags, 1.0, 520, 925),
            (c_art - 1.0, 1.06, 540, 985), (c_peak, 1.12, 540, 1065, EASE_SNAP),
            (dur, 1.16, 540, 1125)]
    f.set_cam(cam_keys(t, keys))
    g = f.surface()
    f.bg_gradient(top=(26, 30, 40), bottom=(5, 6, 9), cy=0.3)
    f.vignette = 0.56
    f.grain = 0.036

    # projector wash
    f.glow(color=(196, 168, 128), blur=140, gain=0.16, down=4).ellipse(
        540, 900, 520, 420, fill=255, alpha=170)
    for k in range(14):
        yy = 300 + k * 48
        g.line([(0, yy), (WIDTH, yy)], w=1.0, color=(120, 130, 150), alpha=6)

    # ---------------- the reel
    fw, fh, gap = 176.0, 232.0, 16.0
    n = len(FRAMES)
    total_w = n * fw + (n - 1) * gap
    x_start = 540 - total_w / 2
    cut_t0 = c_flags + 0.15

    def _cut_time(i):
        return cut_t0 + sum(1 for q in range(i) if FRAMES[q][1] == DARK) * 0.60

    offsets, pos = [], 0.0
    for i, (kind, mood) in enumerate(FRAMES):
        closed = 0.0
        for j in range(i):
            if FRAMES[j][1] == DARK:
                closed += (fw + gap) * EASE_SNAP(seg(t, _cut_time(j), _cut_time(j) + 0.5))
        offsets.append(pos - closed)
        pos += fw + gap

    drift = -20 * ease_out_cubic(seg(t, 0, dur))
    merge = ease_out_cubic(seg(t, c_art - 1.1, c_art + 1.6))
    band_l = x_start + offsets[0] + drift - 26
    band_r = x_start + offsets[-1] + drift + fw + 26
    # film band + sprockets
    band_a = int(255 * (1 - merge))
    g.rect(band_l, FILM_Y - fh / 2 - 26, band_r, FILM_Y + fh / 2 + 26,
           fill=(12, 15, 21), alpha=band_a)
    g.rect(band_l, FILM_Y - fh / 2 - 26, band_r, FILM_Y + fh / 2 + 26,
           outline=(74, 84, 100), w=1.2, alpha=int(90 * (1 - merge)))
    for yy in (FILM_Y - fh / 2 - 18, FILM_Y + fh / 2 + 8):
        xx = band_l + 12
        while xx < band_r - 12:
            g.rrect(xx, yy, xx + 13, yy + 10, 2.5, fill=(30, 36, 46), alpha=band_a)
            xx += 26

    kept = sum(1 for (k2, m2) in FRAMES if m2 == GOLD) + \
        sum(1 for (k2, m2) in FRAMES if m2 == DARK and seg(t, 0, 0) >= 0)
    cut_count = sum(1 for i, (k2, m2) in enumerate(FRAMES) if m2 == DARK
                    and t > _cut_time(i) + 0.5)
    kept = len(FRAMES) - cut_count
    anno_a = int(190 * (1 - merge))
    # annotations are frame furniture, not strip-attached: fixed margins so the
    # camera push and the shrinking band can never collide or crop them
    ann_y = FILM_Y - fh / 2 - 52
    mono(g, "AUTOBIOGRAPHICAL MEMORY", 120, ann_y,
         size=18, color=GREY, alpha=anno_a, tracking=3.8)
    mono(g, "RECONSTRUCTED", 960, ann_y, size=18, color=GREY,
         alpha=anno_a, tracking=3.8, align="right")
    mono(g, "FRAMES RETAINED  %d / %d" % (kept, len(FRAMES)), 120,
         FILM_Y + fh / 2 + 62, size=20, color=AMBER if kept < len(FRAMES) else GREY,
         alpha=int(210 * (1 - clamp(seg(t, c_art - 1.6, c_art - 0.9)))), tracking=3.8)
    g.rect(band_l, FILM_Y + fh / 2 + 78, band_r, FILM_Y + fh / 2 + 81,
           fill=(70, 80, 96), alpha=int(90 * (1 - merge)))
    g.rect(band_l, FILM_Y + fh / 2 + 78,
           band_l + (band_r - band_l) * kept / len(FRAMES), FILM_Y + fh / 2 + 81,
           fill=AMBER, alpha=int(190 * (1 - merge)))

    for i, (kind, mood) in enumerate(FRAMES):
        fx = x_start + offsets[i] + drift
        if mood == DARK:
            p = seg(t, _cut_time(i), _cut_time(i) + 0.5)
            if p >= 1:
                continue
            a = 255 * (1 - ease_in_cubic(p))
            yoff = -110 * ease_in_cubic(p)
            sc = 1 - 0.5 * ease_in_cubic(p)
            col = (176, 186, 198)
        else:
            # surviving frames fly into the plinth and become it
            a = 255.0 * (1 - clamp(seg(t, c_art - 0.6, c_art + 0.9)))
            yoff, sc = 0.0, 1.0
            col = AMBER
            if merge > 0:
                fly = ease_in_cubic(seg(t, c_art - 0.8, c_art + 0.7))
                fx = lerp(fx, 540 - fw / 2 + (i - 3) * 26, fly)
                yoff = lerp(0, 200, fly)
                sc = lerp(1.0, 0.35, fly)
        if a <= 2:
            continue
        cx, cy = fx + fw / 2, FILM_Y + yoff
        hw, hh = fw / 2 * sc, fh / 2 * sc
        g.rect(cx - hw, cy - hh, cx + hw, cy + hh, fill=(13, 16, 22), alpha=int(a))
        g.rect(cx - hw, cy - hh, cx + hw, cy + hh, outline=col, w=2.2,
               alpha=int(a * 0.9))
        if mood == GOLD:
            gl = f.glow(color=AMBER, blur=42, gain=0.26, down=4)
            gl.rect(cx - hw, cy - hh, cx + hw, cy + hh, fill=255, alpha=int(a * 0.42))
        _film_icon(g, kind, cx, cy, fh * 0.30 * sc, col, int(a * 0.95), t=t,
                   crack=clamp(seg(t, 2.0, 3.2)))
        mono(g, {"phone": "ARGUMENTS", "clock": "WAITING", "warn": "RED FLAGS",
                 "sun": "PEAK", "heart": "PEAK"}[kind], cx, cy + hh - 18,
             size=13, color=col, alpha=int(a * 0.55), tracking=2.6, align="center")

    # edit flash: each flaw is sliced out where it sits
    if c_flags < t < c_art - 0.6:
        a = int(180 * window(t, c_flags, c_art - 0.8, fade=0.3))
        mono(g, "EDIT  /  LIVE", 924, FILM_Y + fh / 2 + 62, size=17,
             color=CRIMSON, alpha=a, tracking=4.6, align="right")
        g.circle(946, FILM_Y + fh / 2 + 55, 4, fill=CRIMSON,
                 alpha=int(a * (0.6 + 0.4 * math.sin(t * 6))))
        for i, (kind, mood) in enumerate(FRAMES):
            if mood != DARK:
                continue
            p0 = _cut_time(i)
            cx = x_start + offsets[i] + drift + fw / 2
            if p0 <= t <= p0 + 0.45:
                q = seg(t, p0, p0 + 0.45)
                g.line([(cx, FILM_Y - fh / 2), (cx, FILM_Y + fh / 2)], w=2.6,
                       color=WHITE, alpha=int(230 * (1 - q)))
                g.circle(cx, FILM_Y, 20 + 200 * q, outline=CRIMSON, w=1.6,
                         alpha=int(150 * (1 - q)))
                rng = np.random.default_rng(i + 3)
                for k in range(9):
                    dy = (fh / 2 + 30) + q * rng.uniform(90, 260)
                    dx = rng.uniform(-90, 90) * q
                    g.rect(cx + dx, FILM_Y + dy, cx + dx + 8, FILM_Y + dy + 6,
                           fill=CRIMSON, alpha=int(210 * (1 - q)))

    # ---------------- the pedestal + artifact
    if merge > 0.01:
        py = lerp(1520, 1290, merge)
        alpha = int(255 * merge)
        g.poly([(410, py), (670, py), (688, py + 108), (392, py + 108)],
               fill=(14, 17, 24), alpha=alpha)
        g.poly([(410, py), (670, py), (688, py + 108), (392, py + 108)],
               outline=AMBER, w=1.8, alpha=int(alpha * 0.8))
        g.rect(382, py + 108, 698, py + 138, fill=(14, 17, 24), alpha=alpha)
        g.rect(382, py + 108, 698, py + 138, outline=AMBER, w=1.4,
               alpha=int(alpha * 0.55))
        # bust: head, neck, shoulders
        hx, hy = 540, py - 268
        bust = [(hx - 152, py), (hx - 140, py - 108), (hx - 86, py - 158),
                (hx - 40, py - 172), (hx + 40, py - 172), (hx + 86, py - 158),
                (hx + 140, py - 108), (hx + 152, py)]
        g.poly(bust, fill=(14, 17, 24), alpha=alpha)
        g.poly(bust, outline=AMBER, w=2.4, alpha=alpha)
        g.circle(hx, hy, 72, outline=AMBER, w=2.6, alpha=alpha)
        g.rect(hx - 27, hy + 62, hx + 27, py - 170, fill=(14, 17, 24), alpha=alpha)
        g.line([(hx - 27, hy + 62), (hx - 27, py - 172)], w=2.0, color=AMBER, alpha=alpha)
        g.line([(hx + 27, hy + 62), (hx + 27, py - 172)], w=2.0, color=AMBER, alpha=alpha)
        gl = f.glow(color=AMBER, blur=54, gain=0.34 * merge, down=4)
        gl.ellipse(hx, py - 150, 170, 230, fill=255, alpha=190)
        mono(g, "ARTIFACT  /  NO LIVING REFERENCE", hx, py + 196, size=18,
             color=AMBER, alpha=int(200 * merge), tracking=4.2, align="center")
        # glass case
        case = ease_out_cubic(seg(t, c_guard - 1.2, c_guard + 0.4))
        if case > 0.01:
            g.rect(300, py - 372, 780, py + 152, outline=(150, 176, 204), w=1.4,
                   alpha=int(110 * case))
            g.line([(300, py - 372), (780, py - 372)], w=3.0, color=(150, 176, 204),
                   alpha=int(150 * case))
            g.poly([(322, py - 362), (388, py - 362), (652, py + 142), (586, py + 142)],
                   fill=(180, 200, 220), alpha=int(14 * case))

    # ---------------- type
    ui_cam(g)
    Kinetic(lines=["EUPHORIC", "RECALL"], size=96, y=352, x=540, align="center",
            color=WHITE, t_in=c_recall - 0.3, tracking=-1.8, stagger=0.08,
            emphasis={1: "amber"}, t_out=c_flags - 1.5, out_dur=0.28).draw(g, t)
    if t > c_flags - 0.5:
        Kinetic(lines=["EDITED", "REALITY"], size=88, y=372, x=540, align="center",
                color=WHITE, t_in=c_flags - 0.5, tracking=-1.4, stagger=0.075,
                emphasis={1: "strike"}, t_out=c_art - 1.5, out_dur=0.28).draw(g, t)
    if t > c_art - 0.1:
        Kinetic(lines=["AN ARTIFACT."], size=88, y=396, x=540, align="center",
                color=AMBER, t_in=c_art - 0.1, tracking=-1.6, stagger=0.08,
                t_out=c_peak - 1.4, out_dur=0.28).draw(g, t)
    if t > c_peak - 0.2:
        Kinetic(lines=["AT THEIR PEAK."], size=84, y=396, x=540, align="center",
                color=WHITE, t_in=c_peak - 0.2, tracking=-1.6, stagger=0.075,
                emphasis={2: "amber"}).draw(g, t)

    chrome(f, g, s, t, accent=AMBER if t > c_recall else BLUE)
    if t > dur - 0.2:
        f.fade_to_black = ease_in_cubic(seg(t, dur - 0.2, dur))


# ================================================================== S5
def _small_figure(g, cx, base_y, h=150.0, color=BLUE, alpha=255, w=3.0, solid=True,
                 glow=None):
    """A very small standing person: circle head, tapered body, two legs."""
    hr = h * 0.16
    hy = base_y - h + hr
    body_top = hy + hr * 0.9
    body_bot = base_y - h * 0.42
    g.circle(cx, hy, hr, fill=color if solid else None,
             outline=None if solid else color, w=w, alpha=alpha)
    g.poly([(cx - hr * 0.95, body_top), (cx + hr * 0.95, body_top),
            (cx + hr * 1.35, body_bot), (cx - hr * 1.35, body_bot)],
           fill=color if solid else None, outline=None if solid else color, w=w,
           alpha=alpha)
    g.line([(cx - hr * 0.55, body_bot), (cx - hr * 0.7, base_y)], w=w * 2.2,
           color=color, alpha=alpha, cap=True)
    g.line([(cx + hr * 0.55, body_bot), (cx + hr * 0.7, base_y)], w=w * 2.2,
           color=color, alpha=alpha, cap=True)


def scene5(f, t, s):
    """THE DARK LEVERAGE - the phantom outweighs the real, then unlocks the vault."""
    c_disq = TL.cue("s5", "disqualify")
    c_present = TL.cue("s5", "partners")
    c_int = TL.cue("s5", "intensity")
    c_second = TL.cue("s5", "Second")
    c_key = TL.cue("s5", "key")
    c_bound = TL.cue("s5", "boundaries")
    c_unguard = TL.cue("s5", "unguarded")
    dur = s["dur"]
    part2 = c_second + 1.0

    # ---------------- part A: the scale
    if t < part2:
        f.set_cam(cam_keys(t, [(0, 1.02, 540, 1000), (6, 1.05, 540, 1010),
                               (c_int - 1.0, 1.10, 540, 1050),
                               (part2, 1.14, 540, 1060)]))
        g = f.surface()
        f.bg_gradient(top=(24, 30, 42), bottom=(5, 6, 9), cy=0.3)
        f.vignette = 0.56
        f.grain = 0.036
        for yy in range(260, HEIGHT, 68):
            g.line([(0, yy), (WIDTH, yy)], w=1.0, color=(110, 130, 160), alpha=8)

        tilt = 17.0 * EASE_SNAP(seg(t, c_disq - 0.4, c_disq + 2.6))
        piv = (540.0, 1006.0)
        L = 344.0
        a = math.radians(tilt)
        lx, ly = piv[0] - L * math.cos(a), piv[1] - L * math.sin(a)
        rx, ry = piv[0] + L * math.cos(a), piv[1] + L * math.sin(a)

        # stand + fulcrum
        g.poly([(piv[0] - 92, 1348), (piv[0] + 92, 1348), (piv[0], piv[1] + 8)],
               fill=(14, 17, 24), alpha=255)
        g.poly([(piv[0] - 92, 1348), (piv[0] + 92, 1348), (piv[0], piv[1] + 8)],
               outline=(120, 140, 170), w=2.0, alpha=170)
        g.line([(320, 1348), (760, 1348)], w=2.0, color=(120, 140, 170), alpha=120)
        sh = f.glow(color=(0, 0, 0), blur=40, gain=0.0, down=4)
        g.ellipse(540, 1356, 260, 26, fill=(3, 4, 6), alpha=200)
        # beam
        g.line([(lx, ly), (rx, ry)], w=16, color=(20, 25, 34), alpha=255, cap=True)
        g.line([(lx, ly), (rx, ry)], w=2.0, color=(150, 170, 198), alpha=190)
        g.circle(piv[0], piv[1], 16, fill=(24, 30, 40), alpha=255)
        g.circle(piv[0], piv[1], 16, outline=(150, 170, 198), w=2.0, alpha=180)

        def pan(px, py, color, alpha):
            top = py + 34
            g.line([(px, py), (px - 74, top)], w=2.0, color=color, alpha=alpha)
            g.line([(px, py), (px + 74, top)], w=2.0, color=color, alpha=alpha)
            g.arc(px, top, 92, 54, 8, 172, w=3.4, color=color, alpha=alpha)
            g.line([(px - 91, top + 12), (px + 91, top + 12)], w=1.4, color=color,
                   alpha=int(alpha * 0.45))

        pan(lx, ly, (140, 160, 190), 190)
        pan(rx, ry, AMBER, 210)

        # the real one: a solid figure on the rising pan, then dislodged
        slide = ease_in_cubic(seg(t, c_disq + 1.4, c_disq + 3.4))
        fig_x = lx + 46 * slide
        fig_base = ly + 34 + 12 + 26 * slide
        fa = int(255 * (1 - 0.55 * clamp(seg(t, c_disq + 2.0, c_disq + 3.6))))
        _small_figure(g, fig_x, fig_base, h=112 - 26 * slide, color=BLUE, alpha=fa,
                      w=3.2)
        mono(g, "REALITY / PRESENT", lx - 118, ly + 156, size=17, color=BLUE,
             alpha=int(200 * (1 - 0.4 * slide)), tracking=3.4)

        # the phantom: amber hologram on the heavy pan
        hx, hy = rx, ry + 34 + 12
        gl = f.glow(color=AMBER, blur=40, gain=0.45, down=4)
        gl.ellipse(hx, hy - 100, 110, 130, fill=255, alpha=170)
        _small_figure(g, hx, hy, h=128, color=AMBER, alpha=225, w=2.4, solid=False)
        for k in range(5):
            yy = hy - 118 + k * 26
            g.line([(hx - 92, yy), (hx + 92, yy)], w=1.0, color=AMBER,
                   alpha=int(70 + 30 * math.sin(t * 4 + k)))
        mono(g, "MEMORY / PERMANENT", rx + 118, ry + 196, size=17, color=AMBER,
             alpha=210, tracking=3.4, align="right")

        # ---------------- type
        ui_cam(g)
        if t > c_present - 1.2:
            Kinetic(lines=["NOBODY LIVING", "CAN COMPETE."], size=70, y=348,
                    x=540, align="center", color=WHITE, t_in=c_present - 1.2,
                    tracking=-1.0, stagger=0.07, t_out=c_int - 1.4,
                    out_dur=0.28).draw(g, t)
        if t > c_int - 0.3:
            Kinetic(lines=["INTENSITY", "IS NOT LOVE"], size=84, y=356, x=540,
                    align="center", color=WHITE, t_in=c_int - 0.3, tracking=-1.2,
                    stagger=0.08, emphasis={2: "crimson", 1: "grey"},
                    t_out=part2 - 0.3, out_dur=0.3).draw(g, t)
        chrome(f, g, s, t, accent=AMBER if tilt > 4 else BLUE)

    # ---------------- part B: the vault
    else:
        tt = t - part2
        f.set_cam(cam_keys(t, [(part2, 1.02, 540, 1000),
                               (c_key - 1.6, 1.14, 540, 1080),
                               (c_bound + 0.4, 1.30, 540, 1080, EASE_SNAP),
                               (dur, 1.12, 540, 1000)]))
        g = f.surface()
        f.bg_gradient(top=(22, 27, 38), bottom=(4, 5, 8), cy=0.3)
        f.vignette = 0.60
        f.grain = 0.036
        cx, cy, R = 540.0, 1020.0, 268.0

        opened = clamp(seg(t, c_bound - 0.1, c_bound + 1.5))
        # light behind the door
        if opened > 0:
            gl = f.glow(color=(255, 214, 160), blur=90, gain=0.55 * opened, down=4)
            gl.ellipse(cx, cy, R * 1.15, R * 1.15, fill=255, alpha=230)
        # frame
        g.circle(cx, cy, R + 34, fill=(12, 15, 21), alpha=255)
        g.circle(cx, cy, R + 34, outline=(120, 138, 164), w=3.0, alpha=180)
        for k in range(12):
            ang = k / 12 * 2 * math.pi
            bx, by = cx + math.cos(ang) * (R + 20), cy + math.sin(ang) * (R + 20)
            g.circle(bx, by, 7, fill=(70, 82, 100), alpha=235)

        # the door itself (squashes open to the left hinge)
        sy = 1.0
        sx = 1.0 - 0.88 * EASE_SNAP(opened)
        if sx > 0.05:
            g.ellipse(cx - R + R * sx, cy, R * sx, R, fill=(19, 23, 31), alpha=255)
            g.ellipse(cx - R + R * sx, cy, R * sx, R, outline=(140, 158, 186), w=3.0,
                      alpha=190)
            g.circle(cx - R + R * sx * 0.72, cy, R * 0.72 * sx, outline=(110, 126, 150),
                     w=2.0, alpha=140)
            g.circle(cx - R + R * sx * 0.45, cy, R * 0.45 * sx, outline=(110, 126, 150),
                     w=1.6, alpha=110)
            # wheel + spokes
            wh = (cx - R + R * sx, cy)
            turn = 90 * EASE_SNAP(seg(t, c_key + 1.5, c_bound - 0.4))
            for k in range(4):
                ang = math.radians(turn + k * 90)
                g.line([(wh[0] - math.cos(ang) * R * 0.40 * sx,
                         wh[1] - math.sin(ang) * R * 0.40),
                        (wh[0] + math.cos(ang) * R * 0.40 * sx,
                         wh[1] + math.sin(ang) * R * 0.40)],
                       w=5.0, color=(150, 168, 196), alpha=200, cap=True)
            g.circle(wh[0], wh[1], R * 0.13 * max(sx, 0.2), fill=(26, 31, 41), alpha=255)
            g.circle(wh[0], wh[1], R * 0.13 * max(sx, 0.2), outline=(160, 178, 206),
                     w=2.0, alpha=200)
            # keyhole
            kh = max(sx, 0.06)
            g.ellipse(wh[0], wh[1] - 26 * kh, 9 * kh, 12 * kh, fill=(4, 5, 8), alpha=235)
            g.poly([(wh[0] - 7 * kh, wh[1] - 18 * kh), (wh[0] + 7 * kh, wh[1] - 18 * kh),
                    (wh[0] + 3 * kh, wh[1] + 14 * kh), (wh[0] - 3 * kh, wh[1] + 14 * kh)],
                   fill=(4, 5, 8), alpha=235)

        # deadbolts: retract one by one
        for k in range(4):
            ang = math.radians(45 + k * 90)
            rb = R - 6
            bx, by = cx + math.cos(ang) * rb, cy + math.sin(ang) * rb
            pr = clamp(seg(t, c_key + 2.2 + k * 0.34, c_key + 2.9 + k * 0.34))
            pos = lerp(0, -26, EASE_SNAP(pr))
            g.rrect(bx - 15 + math.cos(ang) * pos, by - 15 + math.sin(ang) * pos,
                    bx + 15 + math.cos(ang) * pos, by + 15 + math.sin(ang) * pos, 3,
                    fill=(150, 168, 196), alpha=int(230 * (1 - opened * 0.6)))

        # the key: enters, turns
        kin = EASE_SNAP(seg(t, c_key - 0.9, c_key + 1.4))
        kx = lerp(1180, cx + 40, kin)
        ky = cy - 26
        ka = math.radians(lerp(0, 90, EASE_SNAP(seg(t, c_key + 1.5, c_bound - 0.5))))
        kv = int(240 * (1 - clamp(seg(t, c_bound + 0.1, c_bound + 0.9))))
        if kin > 0.01 and kv > 2:
            g.line([(kx, ky), (kx - 250, ky)], w=9, color=AMBER, alpha=kv, cap=True)
            g.circle(kx - 300, ky, 46, outline=AMBER, w=9, alpha=kv)
            g.circle(kx - 300, ky, 22, outline=AMBER, w=5, alpha=int(kv * 0.8))
            g.rect(kx - 250, ky + 2, kx - 214, ky + 44, fill=AMBER, alpha=kv)
            g.rect(kx - 158, ky + 2, kx - 132, ky + 30, fill=AMBER, alpha=kv)
            gl = f.glow(color=AMBER, blur=30, gain=0.8, down=4)
            gl.line([(kx, ky), (kx - 250, ky)], w=8, color=255, alpha=int(kv * 0.8))
            gl.circle(kx - 300, ky, 50, fill=255, alpha=int(kv * 0.7))

        # labels + type
        mono(g, "ADULT BOUNDARIES", cx, cy - R - 74, size=22, color=(170, 188, 212),
             alpha=int(210 * (1 - opened * 0.7)), tracking=5.0, align="center")
        ui_cam(g)
        if t > c_key - 0.5:
            Kinetic(lines=["SKELETON KEY"], size=80, y=392, x=540, align="center",
                    color=WHITE, t_in=c_key - 0.5, tracking=0.0, stagger=0.075,
                    emphasis={0: "amber"}, t_out=c_bound - 0.75, out_dur=0.26).draw(g, t)
        if t > c_bound - 0.1:
            Kinetic(lines=["BOUNDARIES", "DISSOLVED."], size=74, y=352, x=540,
                    align="center", color=WHITE, t_in=c_bound - 0.1, tracking=0.0,
                    stagger=0.075, emphasis={1: "crimson"}).draw(g, t)
        if t > c_unguard + 0.3:
            mono(g, "BACK TO THE UNGUARDED VERSION", 540, 1720, size=21,
                 color=CRIMSON, alpha=int(210 * seg(t, c_unguard + 0.3, c_unguard + 1.2)),
                 tracking=4.2, align="center")
        chrome(f, g, s, t, accent=AMBER if t > c_key else BLUE)

    if t > dur - 0.2:
        f.fade_to_black = ease_in_cubic(seg(t, dur - 0.2, dur))


# ================================================================== S6
def scene6(f, t, s):
    """CLOSE THE FILE - the same table, the same chair, nobody in it."""
    c_proto = TL.cue("s6", "prototype")
    c_close = TL.cue("s6", "close")
    c_seat = TL.cue("s6", "seat")
    c_sit = TL.cue("s6", "sit")
    dur = s["dur"]

    pull = smootherstep(seg(t, 0, dur))
    f.set_cam(Cam(lerp(1.16, 1.0, pull), lerp(660, 620, pull),
                  lerp(1120, 1030, pull)))
    g = f.surface()

    ghost = 1.0 - ease_in_cubic(seg(t, c_proto + 0.2, c_close + 1.4))
    warm = clamp(seg(t, c_close - 0.2, c_close + 3.0))
    cold = clamp(seg(t, c_proto, c_proto + 2.0)) * 0.5
    pov_room(f, g, t, ghost_alpha=max(0.0, ghost), ghost_progress=1.0 - ghost,
             ghost_glow=ghost * 0.8, cold=cold, warm=warm, hands=0.0,
             chair_rim=cold, table_rim=140)

    # the daylight that arrives across the table
    if warm > 0:
        f.glow(color=(255, 198, 138), blur=120, gain=0.20 * warm, down=4).ellipse(
            GHOST_CX, 1070, 300, 380, fill=255, alpha=170)
        f.tint = (255, 236, 208)
        f.grade_amt = 1.0
        g.poly([(GHOST_CX - 210, 1290), (GHOST_CX + 210, 1290),
                (GHOST_CX + 330, TABLE_NEAR), (GHOST_CX - 330, TABLE_NEAR)],
               fill=(255, 226, 186), alpha=int(16 * warm))

    # ---------------- type
    ui_cam(g)
    # ---------------- the file card (a UI tab in the corner of the room)
    close_p = EASE_SNAP(seg(t, c_close - 0.15, c_close + 0.55))
    card_a = int(255 * clamp(seg(t, 1.1, 1.9)) *
                 (1 - clamp(seg(t, c_close + 1.5, c_close + 2.6))))
    if card_a > 2:
        x0, x1 = 84.0, 486.0
        h = 124 * (1 - 0.92 * close_p)
        y0 = 286 + (124 - h) / 2
        g.rrect(x0 + 26, y0 - 24, x0 + 190, y0 + 2, 5, fill=(18, 22, 30), alpha=card_a)
        g.rrect(x0 + 26, y0 - 24, x0 + 190, y0 + 2, 5, outline=AMBER, w=1.2,
                alpha=int(card_a * 0.85))
        g.rrect(x0, y0, x1, y0 + h, 0, fill=(13, 17, 24), alpha=card_a)
        g.rrect(x0, y0, x1, y0 + h, 0, outline=AMBER, w=1.4, alpha=int(card_a * 0.9))
        if h > 46:
            ta = card_a * clamp(seg(t, 1.6, 2.2))
            mono(g, "FIRST LOVE", x0 + 24, y0 + 52, size=22, color=WHITE,
                 alpha=int(ta), tracking=4.0)
            mono(g, "PROTOTYPE", x0 + 24, y0 + 92, size=22, color=AMBER,
                 alpha=int(ta), tracking=4.0)
            mono(g, "01", x1 - 24, y0 + 52, size=20, color=GREY, alpha=int(ta * 0.55),
                 tracking=2.0, align="right")
            mono(g, "CLOSED" if close_p > 0.9 else "OPEN", x1 - 24, y0 + 92,
                 size=18, color=BLUE if close_p > 0.9 else CRIMSON,
                 alpha=int(ta * 0.95), tracking=3.2, align="right")
        if 0 < close_p < 0.45:
            g.line([(x0, y0 + h), (x1, y0 + h)], w=2.6, color=AMBER,
                   alpha=int(255 * (1 - close_p / 0.45)))

    if t > c_proto - 0.3:
        Kinetic(lines=["A PROTOTYPE."], size=92, y=1500, x=540, align="center",
                color=WHITE, t_in=c_proto - 0.3, tracking=-1.6, stagger=0.08,
                emphasis={1: "amber"}, t_out=c_close - 0.9, out_dur=0.28).draw(g, t)
    if t > c_close - 0.35:
        Kinetic(lines=["CLOSE THE FILE."], size=86, y=1500, x=540, align="center",
                color=WHITE, t_in=c_close - 0.35, tracking=-1.4, stagger=0.075,
                emphasis={2: "blue"}, t_out=c_sit - 1.5, out_dur=0.28).draw(g, t)
    if t > c_sit - 1.2:
        Kinetic(lines=["KEEP THE SEAT", "EMPTY."], size=62, y=1420, x=540,
                align="center", color=WHITE, t_in=c_sit - 1.2, tracking=0.0,
                stagger=0.07, emphasis={1: "blue"}, t_out=dur - 1.9,
                out_dur=0.4).draw(g, t)

    # ---------------- closing card
    end_t = TL.scene("s6")["lead"] + TL.scene("s6")["beat"]["dur"]
    tail = clamp(seg(t, end_t + 1.5, end_t + 2.6))
    if tail > 0:
        g.line([(360, 980), (720, 980)], w=1.4, color=BLUE, alpha=int(120 * tail))
        mono(g, "FILE CLOSED", 540, 1056, size=34, color=WHITE, alpha=int(235 * tail),
             tracking=9.0, align="center")
        mono(g, "NO ONE LIVING CAN COMPETE WITH A MEMORY", 540, 1108, size=18,
             color=GREY, alpha=int(160 * tail), tracking=4.0, align="center")

    f.tint = ((255, 226, 190), 0.05 * warm) if warm > 0 else None
    chrome(f, g, s, t, accent=BLUE)
    if t > dur - 1.6:
        f.fade_to_black = ease_in_cubic(seg(t, dur - 1.6, dur))


# ------------------------------------------------------------------ registry
def _stub(f, t, s):
    f.bg_gradient()
    g = f.surface()
    mono(g, f"{s['title']} (wip)", 540, 960, size=40, color=GREY, alpha=120,
         tracking=4, align="center")
    chrome(f, g, s, t)


SCENES = {
    "s1": scene1,
    "s2": scene2,
    "s3": scene3,
    "s4": scene4,
    "s5": scene5,
    "s6": scene6,
}
