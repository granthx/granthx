"""Generate a seamless looping 3D ASCII Knight GIF with procedural cloth, parallax, and rain materialisation.

Matches the aesthetic of https://ascii-knight.vercel.app/ and index.html:
- Pure integer-phase periodic loop (6.0 seconds)
- Materialisation from the sky: falling glowing streak characters (| !) paint the warrior top-to-bottom
- Volumetric pseudo-3D relief map with parallax sway (+/- 15 deg) and directional light highlights
- Scarlet cloth ribbons (- = + * # % @) with traveling wave flutter and fold shading
- Deterministic ember particles (* : + ' ` .) breaking off cloth tail and drifting up/right
- Twinkling star characters in night sky and wind-swayed green grass (/ | \)
- Outputs an optimized, GitHub profile-friendly GIF (<8 MB) to assets/ascii-knight.gif
"""

import sys
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Output & Canvas Configuration
# ---------------------------------------------------------------------------
OUT = Path(__file__).resolve().parents[1] / "assets" / "ascii-knight.gif"
OUT.parent.mkdir(parents=True, exist_ok=True)

COLS, ROWS = 152, 119
CW, CH = 5, 8
FPS = 18
LOOP_SEC = 6.0
TOTAL_FRAMES = int(FPS * LOOP_SEC)
FRAME_DELAY_MS = int(1000 / FPS)

FONT_SIZE = 8
try:
    FONT = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", FONT_SIZE)
except OSError:
    try:
        FONT = ImageFont.truetype("consola.ttf", FONT_SIZE)
    except OSError:
        FONT = ImageFont.load_default()

RAMP = " .`'^,:;~-_+<>i!lI?/|()1{}[]rcvunxzjftLCJUYXZO0Qoahkbdpqwm*WMB8&%$#@"
CRAMP = "-=+*#%@"
PCH = "*:+'`."

# Extract BUILTIN_KNIGHT data
INDEX_HTML = Path(__file__).resolve().parents[1] / "index.html"
import re
import json

with open(INDEX_HTML, "r", encoding="utf-8") as f:
    content = f.read()
match = re.search(r"BUILTIN_KNIGHT\s*=\s*(\{.*?\});", content, re.DOTALL)
if not match:
    raise ValueError("Could not parse BUILTIN_KNIGHT data from index.html")
KNIGHT_DATA = json.loads(match.group(1))

KC = KNIGHT_DATA["cols"]
KR = KNIGHT_DATA["rows"]
OFF_X = (COLS - KC) // 2
OFF_Y = ROWS - KR

L = [0.0] * (COLS * ROWS)
MASK = [0] * (COLS * ROWS)

for r in range(KR):
    row_str = KNIGHT_DATA["data"][r]
    for c in range(KC):
        val = int(row_str[c], 16) / 15.0
        tx = c + OFF_X
        ty = r + OFF_Y
        if 0 <= tx < COLS and 0 <= ty < ROWS:
            idx = ty * COLS + tx
            L[idx] = val
            MASK[idx] = 1 if val > 0.05 else 0

def blur_map(a, rad=2, passes=2):
    res = list(a)
    temp = [0.0] * len(a)
    for _ in range(passes):
        # horizontal pass
        for y in range(ROWS):
            row_off = y * COLS
            for x in range(COLS):
                s, count = 0.0, 0
                for k in range(-rad, rad + 1):
                    xx = x + k
                    if 0 <= xx < COLS:
                        s += res[row_off + xx]
                        count += 1
                temp[row_off + x] = s / count
        # vertical pass
        for y in range(ROWS):
            row_off = y * COLS
            for x in range(COLS):
                s, count = 0.0, 0
                for k in range(-rad, rad + 1):
                    yy = y + k
                    if 0 <= yy < ROWS:
                        s += temp[yy * COLS + x]
                        count += 1
                res[row_off + x] = s / count
    return res

BLURRED_L = blur_map(L, rad=3, passes=2)
D = [0.0] * (COLS * ROWS)

for y in range(ROWS):
    for x in range(COLS):
        idx = y * COLS + x
        if MASK[idx]:
            cx = (x / COLS - 0.5) * 2.0
            curve = math.sqrt(max(0.0, 1.0 - cx * cx))
            vert = 1.0 - (y / ROWS) * 0.25
            D[idx] = min(1.0, max(0.0, 0.55 * BLURRED_L[idx] + 0.35 * curve * vert + 0.1))

D = blur_map(D, rad=2, passes=2)

ANCHOR_X = 0.42 * COLS
ANCHOR_Y = 0.30 * ROWS

def p_hash(x, y=0.0):
    h = math.sin(x * 127.1 + y * 311.7) * 43758.5453
    return h - math.floor(h)

def sstep(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3.0 - 2.0 * x)

# Stars
STARS = []
for i in range(80):
    STARS.append({
        "x": int(p_hash(i, 1.0) * COLS),
        "y": int(p_hash(i, 2.0) * ROWS * 0.48),
        "k": 1 + int(p_hash(i, 3.0) * 3.0),
        "ph": p_hash(i, 4.0) * math.tau,
        "ch": "." if p_hash(i, 5.0) > 0.4 else "*"
    })

RIBBONS = [
    {"dir": -0.22, "ph": 0.0, "th": 7.2, "len": 0.58, "m1": 3, "m2": 5},
    {"dir":  0.18, "ph": 1.8, "th": 6.2, "len": 0.52, "m1": 2, "m2": 4}
]

def ribbon_point(rb, s, w, scale):
    wave1 = math.sin(s * 8.0 - rb["m1"] * w + rb["ph"]) * s * 7.5
    wave2 = math.sin(s * 15.0 - rb["m2"] * w + rb["ph"] * 1.4) * s * 3.5
    return (
        ANCHOR_X + s * rb["len"] * COLS * scale,
        ANCHOR_Y + rb["dir"] * s * ROWS * 0.45 * scale + (wave1 + wave2) * scale
    )

def render_frame(phase):
    w = phase * math.tau
    r_mat = sstep(phase / 0.28) if phase < 0.82 else 1.0 - sstep((phase - 0.82) / 0.18)
    cloth_scale = sstep((r_mat - 0.55) / 0.45)

    img = Image.new("RGB", (COLS * CW, ROWS * CH), "#05060a")
    draw = ImageDraw.Draw(img)

    # 1. Stars
    for s in STARS:
        twinkle = 0.25 + 0.65 * (0.5 + 0.5 * math.sin(w * s["k"] + s["ph"]))
        col = (int(255 * twinkle), int(245 * twinkle), int(185 * twinkle))
        draw.text((s["x"] * CW, s["y"] * CH), s["ch"], fill=col, font=FONT)

    # 2. Glowing rain streaks
    rain_intensity = 1.0 - 0.8 * r_mat
    for x in range(0, COLS, 2):
        if p_hash(x * 9.1) > 0.42:
            continue
        cycles = 3 + int(p_hash(x) * 3.0)
        head = ((p_hash(x * 4.3) + phase * cycles) % 1.0) * (ROWS + 20) - 10
        for k in range(8):
            y = int(head - k)
            if 0 <= y < ROWS:
                alpha = rain_intensity * (1.0 - k / 8.0) * 0.75
                if alpha > 0.05:
                    if k == 0:
                        col = (int(200 * alpha * 1.3), int(235 * alpha * 1.3), int(255 * alpha * 1.3))
                        draw.text((x * CW, y * CH), "!", fill=col, font=FONT)
                    else:
                        col = (int(130 * alpha), int(180 * alpha), int(245 * alpha))
                        draw.text((x * CW, y * CH), "|", fill=col, font=FONT)

    # 3. Volumetric Knight & Grass
    sway_angle = math.sin(w) * 0.65 * 0.8
    paint_front_y = r_mat * (ROWS * 1.15) - 5
    dissolve_front_y = (1.0 - (phase - 0.82) / 0.18) * ROWS if phase >= 0.82 else 9999.0

    cloth_buf = [0.0] * (COLS * ROWS)
    if cloth_scale > 0.02:
        for rb in RIBBONS:
            N = 140
            for k in range(N):
                s = k / N
                px, py = ribbon_point(rb, s, w, cloth_scale)
                th = rb["th"] * (1.0 - s * 0.52) * cloth_scale
                shade = 0.5 + 0.5 * math.sin(s * 16.0 - rb["m1"] * w + rb["ph"])
                xi = round(px)
                if 0 <= xi < COLS:
                    y0 = max(0, math.floor(py - th * 0.5))
                    y1 = min(ROWS - 1, math.ceil(py + th * 0.5))
                    for yy in range(y0, y1 + 1):
                        edge = max(0.0, 1.0 - abs(yy - py) / (th * 0.5 + 0.01))
                        val = 0.28 + 0.72 * shade * edge
                        idx = yy * COLS + xi
                        if val > cloth_buf[idx]:
                            cloth_buf[idx] = val

    for y in range(ROWS):
        row_frac = y / ROWS
        for x in range(COLS):
            idx = y * COLS + x
            shift = round((D[idx] - 0.45) * sway_angle * 14.0)
            sx = min(COLS - 1, max(0, x - shift))
            s_idx = y * COLS + sx
            lum = L[s_idx]
            drawn = False

            if lum > 0.05 and y <= paint_front_y and y <= dissolve_front_y:
                dist_front = paint_front_y - y
                dist_diss = dissolve_front_y - y
                if dist_front < 3.5 or (phase >= 0.82 and dist_diss < 3.5):
                    draw.text((x * CW, y * CH), "!" if p_hash(x, y) > 0.45 else "|", fill=(190, 240, 255), font=FONT)
                else:
                    nx = D[min(COLS * ROWS - 1, max(0, y * COLS + sx + 1))] - D[min(COLS * ROWS - 1, max(0, y * COLS + sx - 1))]
                    highlight = min(1.35, max(0.75, 1.0 + nx * 2.8 * math.sin(w)))
                    lit_lum = min(1.0, max(0.0, lum * highlight))
                    r_idx = min(len(RAMP) - 1, int(lit_lum * (len(RAMP) - 1)))
                    # Cool grey tone
                    g_val = int(24 + lit_lum * 190)
                    draw.text((x * CW, y * CH), RAMP[r_idx], fill=(g_val - 8, g_val - 2, g_val + 14), font=FONT)
                drawn = True

            # 4. Swaying Grass
            if not drawn and row_frac > 0.76 and p_hash(x, y + 5) < 0.58 * ((row_frac - 0.76) * 4.2 + 0.15):
                grass_wind = math.sin(x * 0.28 + w * 2.0 + y * 0.35)
                g_char = "/" if grass_wind > 0.35 else ("\\" if grass_wind < -0.35 else "|")
                g_green = int(50 + (row_frac - 0.76) * 160 + (25 if grass_wind > 0.4 else 0))
                draw.text((x * CW, y * CH), g_char, fill=(int(g_green * 0.65), g_green, int(g_green * 0.4)), font=FONT)

    # 5. Cloth Ribbons
    for i in range(COLS * ROWS):
        v = cloth_buf[i]
        if v > 0:
            c_idx = min(len(CRAMP) - 1, int(v * len(CRAMP)))
            r_val = int(140 + v * 115)
            draw.text(((i % COLS) * CW, (i // COLS) * CH), CRAMP[c_idx], fill=(r_val, int(v * 20), int(v * 25)), font=FONT)

    # 6. Particles
    num_particles = 44
    part_life = 0.22
    for k in range(num_particles):
        birth = k / num_particles
        age = ((phase - birth) % 1.0 + 1.0) % 1.0
        if age < part_life and cloth_scale > 0.15:
            u = age / part_life
            rb = RIBBONS[k % len(RIBBONS)]
            spawn_phase = ((phase - age) % 1.0 + 1.0) % 1.0
            spawn_w = spawn_phase * math.tau
            sp_x, sp_y = ribbon_point(rb, 0.85 + (p_hash(k, 1.0) - 0.5) * 0.2, spawn_w, cloth_scale)
            vx = 9.0 + p_hash(k, 2.0) * 16.0
            vy = -3.5 - p_hash(k, 3.0) * 8.0
            px = round(sp_x + vx * u + math.sin(spawn_w * 2.0 + k) * 1.5)
            py = round(sp_y + vy * u - 2.5 * u * u)
            if 0 <= px < COLS and 0 <= py < ROWS:
                pch = PCH[min(len(PCH) - 1, int(u * len(PCH)))]
                r_col = int(255 - u * 60)
                g_col = int(180 * (1.0 - u) * (1.0 - u))
                b_col = int(30 * (1.0 - u))
                draw.text((px * CW, py * CH), pch, fill=(r_col, g_col, b_col), font=FONT)

    # Return crisp high-resolution frame (760x952 px) for big README display
    return img

def main():
    print(f"Generating {TOTAL_FRAMES} frames ({LOOP_SEC}s loop @ {FPS} fps)...")
    frames = []
    for i in range(TOTAL_FRAMES):
        phase = i / TOTAL_FRAMES
        frames.append(render_frame(phase))
        if (i + 1) % 18 == 0 or i == TOTAL_FRAMES - 1:
            print(f"Rendered frame {i + 1}/{TOTAL_FRAMES}")

    print("Quantizing and saving GIF...")
    # 48 colors gives sharp grays, reds, and greens while staying under 8 MB
    palette_frames = [f.convert("P", palette=Image.Palette.ADAPTIVE, colors=48) for f in frames]

    palette_frames[0].save(
        OUT,
        save_all=True,
        append_images=palette_frames[1:],
        duration=FRAME_DELAY_MS,
        loop=0,
        optimize=True
    )
    size_mb = OUT.stat().st_size / (1024 * 1024)
    print(f"Successfully generated {OUT} ({size_mb:.2f} MB)")

    # Also copy to granthx/assets if directory exists
    granthx_out = Path(__file__).resolve().parents[1] / "granthx" / "assets" / "ascii-knight.gif"
    if granthx_out.parent.exists():
        import shutil
        shutil.copy2(OUT, granthx_out)
        print(f"Copied to {granthx_out}")

if __name__ == "__main__":
    main()
