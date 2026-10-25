"""Generate a continuously blinking ASCII code matrix eye for the GitHub profile README.

The animation mimics a live terminal running an AI vision stream:
- Monospace character grid filled with real AI & Python code tokens.
- Live code shimmer: code characters cycle across the grid.
- Eye geometry: almond eyelids, sclera, luminous iris, jet-black pupil, and bright specular glint.
- Smooth blinking dynamics: natural single blink, gaze shifts, quick double blink, and pause.
- Built using Python and Pillow only (no external sprite or heavy dependencies).

Usage:
    python scripts/generate_blinking_eye.py                # Defaults to reference video theme (amber)
    python scripts/generate_blinking_eye.py --theme cyan   # Futuristic cyber-cyan AI theme
    python scripts/generate_blinking_eye.py --theme amber  # Amber/copper theme matching video

Output:
    assets/blinking-eye.gif
"""
import sys
import math
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Output and Canvas Configuration
# ---------------------------------------------------------------------------
OUT = Path(__file__).resolve().parents[1] / "assets" / "blinking-eye.gif"

CW, CH = 6, 11            # Monospace cell width & height (pixels)
COLS, ROWS = 100, 26      # Grid resolution: 100x26 characters
TOP_BAR = 24              # Terminal header height
BOTTOM_BAR = 20           # Terminal status bar height
GRID_W = COLS * CW        # 600 px
GRID_H = ROWS * CH        # 286 px
W = GRID_W                # 600 px
H = TOP_BAR + GRID_H + BOTTOM_BAR  # 330 px

# ---------------------------------------------------------------------------
# Monospace & UI Fonts
# ---------------------------------------------------------------------------
def load_font(size):
    font_candidates = [
        "consolab.ttf",
        "C:/Windows/Fonts/consolab.ttf",
        "consola.ttf",
        "C:/Windows/Fonts/consola.ttf",
        "DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "Menlo.ttc",
    ]
    for fn in font_candidates:
        try:
            return ImageFont.truetype(fn, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()

FONT = load_font(10)
UI_FONT = load_font(10)

# Character density tiers for rendering shading
DENSE_CHARS = list("@#MW8%B&Q0OZmwqpdbkhao*#")
MID_CHARS   = list("XYUJCLtrcjvxznu123456789")
LIGHT_CHARS = list("+=-_~:;.,`'\"/\\|()[]{}<>!?")

# AI / Python code snippets for matrix stream
CODE_SNIPPETS = [
    "def forward(self, x, mask=None): q, k, v = self.proj(x).chunk(3, dim=-1)",
    "attn = torch.softmax(q @ k.transpose(-2, -1) / math.sqrt(d_k), dim=-1)",
    "output = self.dropout(attn @ v) + residual; return self.norm(output)",
    "class NeuralVisionBackbone(nn.Module): def __init__(self, channels=64):",
    "    self.conv1 = nn.Conv2d(3, 64, kernel_size=7, stride=2, padding=3)",
    "    self.layer1 = self._make_layer(block, 64, layers[0], stride=1)",
    "latent_z = encoder.sample_latent(mu, log_var); eps = torch.randn_like(std)",
    "gaze_vector = np.array([cos(theta), sin(phi)], dtype=np.float32) * scale",
    "pupil_mask = torch.exp(-((grid_x - cx)**2 + (grid_y - cy)**2) / radius**2)",
    "eyelid_upper = cy - amp_u * (1.0 - t**2)**0.78 * openness_factor",
    "eyelid_lower = cy + amp_l * (1.0 - t**2)**0.95 * lerp(0.72, 1.0, openness)",
    "iris_radiance = base_color * (0.85 + 0.15 * math.sin(angle * 16.0))",
    "specular = np.clip(1.0 - dist_glint / glint_radius, 0.0, 1.0) ** 4",
    "loss = criterion(pred_gaze, target_gaze) + 0.01 * kl_divergence",
    "optimizer.zero_grad(); loss.backward(); optimizer.step(); scheduler.step()",
    "weights = torch.load('checkpoints/vision_eye_latest.pt', map_location='cuda')",
    "cv2.imshow('Eye - Space', cv2.cvtColor(ascii_canvas, cv2.COLOR_RGB2BGR))",
    "while stream.isOpened(): ok, frame = stream.read(); tensor = transform(frame)",
    "feature_map = model.extract_features(tensor); bbox = detector(feature_map)",
    "theta, phi = kalman_filter.update(raw_gaze); render_ascii_matrix(theta, phi)",
    "shimmer_noise = np.random.uniform(0.0, 1.0, size=(ROWS, COLS)) < 0.18",
    "lut_palette = generate_cyber_palette(colors=96, theme='neural_matrix')",
    "export_gif_animation(frames, duration=durations, loop=0, optimize=True)",
    "for epoch in range(100): train_loss = train_step(loader, model, criterion)",
    "precision, recall, f1 = evaluate_metrics(val_loader, model, threshold=0.5)",
    "return {'openness': float(lid_state), 'gaze': gaze_coords, 'fps': 30.0}",
]

# ---------------------------------------------------------------------------
# Eye Model Geometry (relative to character grid)
# ---------------------------------------------------------------------------
CX = GRID_W / 2
CY = GRID_H / 2 + 1
HALF_W = 195.0
UPPER_AMP = 72.0
LOWER_AMP = 55.0
CLOSED_AT = 0.70
IRIS_R = 52.0
PUPIL_R = 18.0
IRIS_DY = 4.0
GAZE_X = 48.0

def lerp(a, b, t): return a + (b - a) * t
def clamp(v, lo=0.0, hi=1.0): return max(lo, min(hi, v))
def smooth(t): t = clamp(t); return t * t * (3 - 2 * t)
def mix(c1, c2, t): return tuple(int(round(lerp(a, b, t))) for a, b in zip(c1, c2))
def scale(c, k): return tuple(max(0, min(255, int(round(v * k)))) for v in c)

# ---------------------------------------------------------------------------
# Color Themes
# ---------------------------------------------------------------------------
PALETTES = {
    # Theme matching the user's reference video (warm amber/copper glow)
    "amber": {
        "bg": (10, 8, 8),
        "chrome": (18, 14, 14),
        "border": (42, 28, 26),
        "text_ambient": (45, 28, 24),
        "text_skin": (88, 48, 38),
        "lid_rim": (225, 120, 75),
        "sclera": (185, 140, 125),
        "iris_outer": (155, 55, 20),
        "iris_mid": (250, 145, 30),
        "iris_inner": (255, 220, 120),
        "specular": (255, 255, 245),
        "pupil": (8, 4, 4),
        "accent": (255, 150, 40),
        "title": "eye_stream.py  —  Vision Matrix (Code Stream)",
    },
    # Cyber-cyan futuristic AI theme
    "cyan": {
        "bg": (8, 12, 16),
        "chrome": (13, 17, 23),
        "border": (28, 38, 48),
        "text_ambient": (24, 38, 48),
        "text_skin": (42, 70, 84),
        "lid_rim": (70, 185, 220),
        "sclera": (145, 195, 215),
        "iris_outer": (0, 115, 155),
        "iris_mid": (15, 220, 245),
        "iris_inner": (140, 248, 255),
        "specular": (255, 255, 255),
        "pupil": (4, 8, 12),
        "accent": (20, 225, 245),
        "title": "eye_stream.py  —  Vision Matrix (Cyber AI Stream)",
    }
}

def get_sample(x, y, openness, gaze, pal):
    """Computes luminance, color, and region classification for coordinates (x, y)."""
    t = (x - CX) / HALF_W
    if abs(t) >= 1.0:
        in_eye = False
        yu = yl = CY
    else:
        base = max(0.0, 1.0 - t * t)
        fu = base ** 0.78
        fl = base ** 0.95
        meet = LOWER_AMP * CLOSED_AT
        yu = CY + lerp(meet * fl, -UPPER_AMP * fu, openness)
        yl = CY + LOWER_AMP * fl * lerp(CLOSED_AT, 1.0, openness)
        in_eye = (yu < y < yl) and (openness > 0.02)

    edge_x = smooth(min(x, GRID_W - x) / 100.0)
    edge_y = smooth(min(y, GRID_H - y) / 45.0)
    edge = edge_x * edge_y

    if in_eye:
        ix = CX + gaze * GAZE_X
        iy = CY + IRIS_DY
        dx = x - ix
        dy = y - iy
        dist = math.hypot(dx, dy)

        # Specular glint: bright reflection
        hx = (dx + 0.32 * IRIS_R) / (0.22 * IRIS_R)
        hy = (dy + 0.36 * IRIS_R) / (0.18 * IRIS_R)
        if hx * hx + hy * hy < 1.0:
            return 1.0, pal["specular"], "specular"

        # Pupil: dark central void
        if dist < PUPIL_R:
            return 0.0, pal["pupil"], "pupil"

        # Iris: radiant fiber ring
        if dist < IRIS_R:
            tr = (dist - PUPIL_R) / (IRIS_R - PUPIL_R)
            angle = math.atan2(dy, dx)
            striation = 0.16 * math.sin(angle * 18 + 2.0 * math.sin(angle * 6)) + 0.09 * math.sin(angle * 36)
            b = 0.70 + striation
            collarette = math.exp(-((tr - 0.28) / 0.14) ** 2) * 0.28
            b += collarette
            limbal = smooth((1.0 - tr) / 0.20)
            b *= (0.45 + 0.55 * limbal)
            b = clamp(b, 0.25, 1.0)

            # Eyelid shadow across upper iris
            s_lid = (y - yu) / max(1.0, yl - yu)
            b *= (0.40 + 0.60 * smooth(s_lid / 0.35))

            if tr < 0.45:
                col = mix(pal["iris_mid"], pal["iris_inner"], (0.45 - tr) / 0.45)
            else:
                col = mix(pal["iris_outer"], pal["iris_mid"], (1.0 - tr) / 0.55)
            col = scale(col, 0.7 + 0.3 * b)
            return b, col, "iris"

        # Sclera (eye white)
        s_lid = (y - yu) / max(1.0, yl - yu)
        shadow = 0.35 + 0.65 * smooth(s_lid / 0.32)
        corner_shadow = 1.0 - 0.55 * (abs(t) ** 2.2)
        b = clamp(0.70 * shadow * corner_shadow, 0.15, 0.85)
        col = scale(pal["sclera"], 0.45 + 0.55 * b)
        return b, col, "sclera"

    # Eyelid and facial contours
    d_upper = abs(y - yu) if abs(t) < 1.0 else 999.0
    d_lower = abs(y - yl) if abs(t) < 1.0 else 999.0
    d_lid = min(d_upper, d_lower)

    crease_y = CY - (UPPER_AMP + 26) * max(0.0, 1.0 - abs(t) ** 1.8)
    d_crease = abs(y - crease_y)

    if d_lid < 3.2 and abs(t) < 0.98:
        # Crisp eyelid rim
        b = 0.75 + 0.25 * (1.0 - d_lid / 3.2)
        col = mix(pal["text_skin"], pal["lid_rim"], 0.80)
        return b * edge, col, "lid"
    elif y < yu and d_lid < 16.0 and abs(t) < 0.95:
        # Upper eyelid shelf
        k = 1.0 - (d_lid / 16.0)
        b = 0.28 + 0.35 * (k ** 1.4)
        col = mix(pal["text_skin"], pal["lid_rim"], 0.35 * k)
        return b * edge, col, "skin"
    elif d_crease < 5.0 and abs(t) < 0.85:
        # Eyelid crease
        b = 0.36 * (1.0 - d_crease / 5.0)
        return b * edge, pal["text_skin"], "skin"
    else:
        # Ambient background code
        b = 0.18 * edge
        return b, pal["text_ambient"], "ambient"

# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------
def generate_blinking_eye(theme_name="amber", output_file=OUT):
    if theme_name not in PALETTES:
        theme_name = "amber"
    pal = PALETTES[theme_name]

    # Pre-generate base code grid
    rng = random.Random(42)
    current_grid = []
    for r in range(ROWS):
        line = ""
        while len(line) < COLS + 60:
            line += rng.choice(CODE_SNIPPETS) + "   "
        current_grid.append(list(line[:COLS]))

    # Construct the timeline of eye actions
    timeline = []
    def add(o, g, ms): timeline.append((o, g, ms))
    def hold(count, g=0.0, ms=100):
        for _ in range(count): add(1.0, g, ms)
    def glance(g0, g1, steps=3, ms=60):
        for i in range(1, steps + 1):
            t = i / steps
            ease = t * t * (3 - 2 * t)
            add(1.0, lerp(g0, g1, ease), ms)

    # Seamless looping sequence:
    hold(10)                       # Initial gaze, code streaming (~1.0s)
    # Blink 1
    add(0.50, 0.0, 50)
    add(0.00, 0.0, 60)
    add(0.40, 0.0, 50)
    add(0.85, 0.0, 60)
    hold(8)                        # Rest (~0.8s)
    # Gaze shift: right
    glance(0.0, 1.0, steps=3, ms=55)
    hold(6, g=1.0)                 # Hold right gaze (~0.6s)
    glance(1.0, 0.0, steps=3, ms=55)
    hold(5)                        # Pause
    # Quick double blink
    add(0.45, 0.0, 45)
    add(0.00, 0.0, 55)
    add(0.65, 0.0, 50)             # Reopen partially
    add(0.15, 0.0, 45)             # Immediate second closure
    add(0.00, 0.0, 50)
    add(0.40, 0.0, 50)
    add(0.85, 0.0, 60)
    hold(12)                       # Long natural pause after double blink (~1.2s)
    # Gaze shift: left
    glance(0.0, -0.85, steps=3, ms=55)
    hold(5, g=-0.85)
    # Small blink during glance
    add(0.20, -0.85, 50)
    add(0.00, -0.85, 55)
    add(0.70, -0.85, 55)
    glance(-0.85, 0.0, steps=3, ms=55)
    hold(4)                        # Settle to center for seamless loop

    raw_frames = []
    durations = []
    frame_rng = random.Random(1337)

    for f_idx, (openness, gaze, ms) in enumerate(timeline):
        # Shimmer update: only 8% of ambient characters re-roll per frame
        # (keeps file size under 1MB while maintaining continuous live streaming code)
        for r in range(ROWS):
            for c in range(COLS):
                if frame_rng.random() < 0.08:
                    current_grid[r][c] = frame_rng.choice(MID_CHARS if frame_rng.random() < 0.3 else LIGHT_CHARS)

        img = Image.new("RGB", (W, H), pal["bg"])
        d = ImageDraw.Draw(img)

        # Terminal Title Bar
        d.rectangle([0, 0, W, TOP_BAR], fill=pal["chrome"])
        d.line([(0, TOP_BAR), (W, TOP_BAR)], fill=pal["border"])
        for i, dot_col in enumerate([(255, 95, 87), (254, 188, 46), (40, 201, 64)]):
            x = 12 + i * 16
            d.ellipse([x, 7, x + 9, 16], fill=scale(dot_col, 0.85))
        d.text((W / 2, TOP_BAR / 2), pal["title"], font=UI_FONT, fill=pal["accent"], anchor="mm")

        # Character Matrix
        for r in range(ROWS):
            y = TOP_BAR + r * CH
            for c in range(COLS):
                x = c * CW
                center_x = x + CW / 2
                center_y = y + CH / 2

                b, col, region = get_sample(center_x, center_y - TOP_BAR, openness, gaze, pal)
                base_ch = current_grid[r][c]

                if region == "pupil":
                    ch = " "
                elif region == "specular":
                    ch = frame_rng.choice(["*", "@", "#", "8"])
                elif region == "iris":
                    ch = frame_rng.choice(DENSE_CHARS) if frame_rng.random() < 0.70 else base_ch
                elif region == "lid":
                    ch = frame_rng.choice(MID_CHARS) if frame_rng.random() < 0.40 else base_ch
                elif region == "sclera":
                    ch = base_ch if base_ch in LIGHT_CHARS or base_ch in MID_CHARS else frame_rng.choice(LIGHT_CHARS)
                else:
                    ch = base_ch

                if ch != " ":
                    d.text((x, y), ch, font=FONT, fill=col)

        # Terminal Status Bar
        d.rectangle([0, H - BOTTOM_BAR, W, H], fill=pal["chrome"])
        d.line([(0, H - BOTTOM_BAR), (W, H - BOTTOM_BAR)], fill=pal["border"])
        status_left = f"> VISION_MATRIX: active | lid: {openness:0.2f} | gaze: {gaze:+0.2f} | frame: {f_idx:03d}"
        d.text((12, H - BOTTOM_BAR / 2), status_left, font=UI_FONT, fill=mix(pal["text_ambient"], (200, 200, 200), 0.6), anchor="lm")
        status_right = "● LIVE STREAM [CODE MATRIX]"
        d.text((W - 12, H - BOTTOM_BAR / 2), status_right, font=UI_FONT, fill=pal["accent"], anchor="rm")

        raw_frames.append(img)
        durations.append(ms)

    # Quantize with a single shared global palette to avoid any frame flicker
    sample_sheet = Image.new("RGB", (W, H * 6))
    for k, idx in enumerate(range(0, len(raw_frames), max(1, len(raw_frames) // 6))[:6]):
        sample_sheet.paste(raw_frames[idx], (0, k * H))
    global_palette = sample_sheet.quantize(colors=96, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    p_frames = [f.quantize(palette=global_palette, dither=Image.Dither.NONE) for f in raw_frames]

    output_file.parent.mkdir(parents=True, exist_ok=True)
    p_frames[0].save(
        output_file,
        save_all=True,
        append_images=p_frames[1:],
        duration=durations,
        loop=0,
        optimize=True
    )
    print(f"Generated {output_file} ({len(p_frames)} frames, {sum(durations)/1000:.1f}s loop, {output_file.stat().st_size / 1024:.0f} KB)")

if __name__ == "__main__":
    theme = "amber"
    for arg in sys.argv[1:]:
        if arg.startswith("--theme="):
            theme = arg.split("=", 1)[1]
        elif arg in ("cyan", "amber"):
            theme = arg
        elif arg == "--theme" and sys.argv.index(arg) + 1 < len(sys.argv):
            theme = sys.argv[sys.argv.index(arg) + 1]
    generate_blinking_eye(theme_name=theme)
