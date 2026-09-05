from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import math
import random

W, H = 900, 185
CELL = 14
GAP = 4
COLS = 52
ROWS = 7
GRID_X, GRID_Y = 34, 46

OUT = Path(__file__).resolve().parents[1] / "assets" / "creeper-contribution.gif"

# GitHub-like contribution colors.
EMPTY = (22, 27, 34)
LEVELS = [
    (22, 27, 34),
    (14, 68, 41),
    (22, 101, 52),
    (45, 153, 63),
    (87, 199, 96),
]

random.seed(17)

# A pleasant, mostly-empty contribution history with stronger activity near the right.
grid = []
for r in range(ROWS):
    row = []
    for c in range(COLS):
        if c < 18:
            p = 0.08
        elif c < 34:
            p = 0.22
        else:
            p = 0.62
        x = random.random()
        level = 0 if x > p else random.choices([1, 2, 3, 4], [45, 30, 18, 7])[0]
        row.append(level)
    grid.append(row)

def draw_grid(draw):
    for r in range(ROWS):
        for c in range(COLS):
            x = GRID_X + c * (CELL + GAP)
            y = GRID_Y + r * (CELL + GAP)
            draw.rounded_rectangle(
                [x, y, x + CELL, y + CELL],
                radius=3,
                fill=LEVELS[grid[r][c]]
            )

def draw_creeper_realistic(draw, cx, cy, scale=2, leg_offset=0, flash_progress=0, flip_y=False):
    def blend(c1, c2, t):
        return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))
    
    g = blend((77, 184, 72), (255, 255, 255), flash_progress)
    d = blend((28, 86, 39), (255, 255, 255), flash_progress)
    b = blend((13, 38, 22), (255, 255, 255), flash_progress)

    def draw_rect(x1, y1, x2, y2, fill):
        if flip_y:
            y1_flip = cy + (cy - y2)
            y2_flip = cy + (cy - y1)
            y1, y2 = y1_flip, y2_flip
        draw.rectangle([x1, y1, x2, y2], fill=fill)

    # Body
    body_w = 8 * scale
    body_h = 12 * scale
    bx = cx - body_w / 2
    by = cy - 6 * scale - body_h
    
    draw_rect(bx, by, bx + body_w, by + body_h - 1, fill=g)
    for i in range(4):
        for j in range(6):
            if (i + j) % 3 == 0:
                draw_rect(bx + i * 2 * scale, by + j * 2 * scale, bx + (i + 1) * 2 * scale - 1, by + (j + 1) * 2 * scale - 1, fill=d)

    # Legs
    leg_w = 4 * scale
    leg_h = 6 * scale
    
    for i in [-1, 1]:
        lx = cx + i * (leg_w/2) - leg_w/2
        ly = cy - 6 * scale
        offset = -leg_offset if i == -1 else leg_offset
        draw_rect(lx + offset, ly, lx + offset + leg_w - 1, ly + leg_h - 1, fill=d)
        
    for i in [-1, 1]:
        lx = cx + i * (leg_w/2 + 2 * scale) - leg_w/2
        ly = cy - 6 * scale
        offset = leg_offset if i == -1 else -leg_offset
        draw_rect(lx + offset, ly, lx + offset + leg_w - 1, ly + leg_h - 1, fill=g)

    # Head
    head_w = 8 * scale
    head_h = 8 * scale
    hx = cx - head_w / 2
    hy = by - head_h
    draw_rect(hx, hy, hx + head_w - 1, hy + head_h - 1, fill=g)
    
    # Face
    eye_size = 2 * scale
    draw_rect(hx + scale, hy + 2 * scale, hx + scale + eye_size - 1, hy + 2 * scale + eye_size - 1, fill=b)
    draw_rect(hx + 5 * scale, hy + 2 * scale, hx + 5 * scale + eye_size - 1, hy + 2 * scale + eye_size - 1, fill=b)
    
    draw_rect(hx + 3 * scale, hy + 4 * scale, hx + 5 * scale - 1, hy + 7 * scale - 1, fill=b)
    draw_rect(hx + 2 * scale, hy + 5 * scale, hx + 3 * scale - 1, hy + 8 * scale - 1, fill=b)
    draw_rect(hx + 5 * scale, hy + 5 * scale, hx + 6 * scale - 1, hy + 8 * scale - 1, fill=b)

def draw_boom(draw, cx, cy, progress, rng, multiplier=1.0):
    if progress <= 0: return
    radius = 180 * math.pow(progress, 0.4) * multiplier
    
    if progress < 0.15:
        s = int(300 * (1 - progress / 0.15) * multiplier)
        draw.ellipse([cx - s, cy - s, cx + s, cy + s], fill=(255, 255, 255))
        return

    if progress < 0.6:
        width = max(1, int(15 * (1 - progress / 0.6)))
        draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], outline=(255, 200, 100), width=width)

    count = int(120 * multiplier)
    for i in range(count):
        ang = 2 * math.pi * i / count + rng.uniform(-0.2, 0.2)
        dist = radius * rng.uniform(0.05, 1.1) * (1 - progress * 0.2)
        px = cx + math.cos(ang) * dist
        py = cy + math.sin(ang) * dist
        
        size = rng.uniform(4, 20) * (1 - progress) * multiplier
        if size < 1: continue
        
        if progress < 0.3:
            col = random.choice([(255, 255, 200), (255, 150, 50), (200, 50, 0)])
        else:
            col = random.choice([(120, 120, 120), (80, 80, 80), (40, 40, 40)])
            
        draw.ellipse([px - size, py - size, px + size, py + size], fill=col)

def get_separate_creeper_state(frame, start_x, end_x, y, is_top=False):
    cx = start_x
    cy = y
    leg_offset = 0
    scale = 2 
    flash_progress = 0
    progress_boom = 0

    if frame < 70:
        if frame < 30:
            cx = start_x + ((end_x - start_x) * 0.35 / 30) * frame
            leg_offset = 3 * math.sin(frame * 1.5)
        elif frame < 45:
            t = (frame - 30) / 15
            dist = (end_x - start_x) * 0.5
            cx = start_x + (end_x - start_x) * 0.35 + dist * t
            jump_h = 30 * math.sin(t * math.pi)
            if is_top: cy = y + jump_h
            else: cy = y - jump_h
            leg_offset = -2
        else:
            t = (frame - 45) / 15
            dist = (end_x - start_x) * 0.15
            cx = start_x + (end_x - start_x) * 0.85 + dist * t
            leg_offset = 3 * math.sin(frame * 1.5) * (1 - t)

        if frame >= 60:
            charge_t = (frame - 60) / 10
            flash_progress = charge_t
            scale = 2 + charge_t * 0.5
            cx += random.randint(-2, 2)
            cy += random.randint(-2, 2)
            leg_offset = 0
    else:
        cx = end_x
        progress_boom = (frame - 70) / 20

    return cx, cy, scale, leg_offset, flash_progress, progress_boom


frames = []
rng = random.Random(42)
FPS = 15
TOTAL_FRAMES = 180 # 90 frames for high-five + 90 frames for separate explosions

ground_y_bottom = GRID_Y + ROWS * (CELL + GAP) - 4
ground_y_top = GRID_Y - 14
center_y = (ground_y_bottom + ground_y_top) / 2

for full_frame in range(TOTAL_FRAMES):
    img = Image.new("RGB", (W, H), (9, 13, 18))
    d = ImageDraw.Draw(img)
    
    draw_grid(d)

    if full_frame < 90:
        # --- PART 1: HIGH FIVE SEQUENCE (Frames 0-89) ---
        frame = full_frame
        
        scale_b = scale_t = 2
        flash_b = flash_t = 0
        boom = 0
        
        if frame < 30:
            t = frame / 30
            cx_b = 150 + (320 - 150) * t
            cy_b = ground_y_bottom
            leg_offset_b = 4 * math.sin(frame * 1.5)
            
            cx_t = 750 - (750 - 580) * t
            cy_t = ground_y_top
            leg_offset_t = 4 * math.sin(frame * 1.5)
            
        elif frame < 45:
            t = (frame - 30) / 15
            cx_b = 320 + (435 - 320) * t
            cy_b = ground_y_bottom - (ground_y_bottom - center_y - 12) * t - 30 * math.sin(t * math.pi)
            leg_offset_b = -3

            cx_t = 580 - (580 - 465) * t
            cy_t = ground_y_top + (center_y - 12 - ground_y_top) * t + 30 * math.sin(t * math.pi)
            leg_offset_t = -3

        elif frame < 70:
            cx_b = 435; cy_b = center_y + 12; leg_offset_b = 0
            cx_t = 465; cy_t = center_y - 12; leg_offset_t = 0
            
            if frame < 60:
                bounce = math.sin((frame - 45) / 15 * math.pi) * 3
                d.text((450 - 40, center_y - 30 - bounce), "HIGH FIVE!", fill=(255, 215, 0))
            else:
                charge_t = (frame - 60) / 10
                flash_b = flash_t = charge_t
                scale_b = scale_t = 2 + charge_t * 0.5
                cx_b += random.randint(-2, 2); cy_b += random.randint(-2, 2)
                cx_t += random.randint(-2, 2); cy_t += random.randint(-2, 2)
        else:
            boom = (frame - 70) / 20

        if frame < 70:
            draw_creeper_realistic(d, cx_b, cy_b, scale=scale_b, leg_offset=leg_offset_b, flash_progress=flash_b, flip_y=False)
            draw_creeper_realistic(d, cx_t, cy_t, scale=scale_t, leg_offset=leg_offset_t, flash_progress=flash_t, flip_y=True)
        else:
            draw_boom(d, 450, center_y, boom, rng, multiplier=1.5)

    else:
        # --- PART 2: SEPARATE BOOMS SEQUENCE (Frames 90-179) ---
        frame = full_frame - 90

        # Bottom Creeper
        cx_b, cy_b, scale_b, leg_offset_b, flash_b, boom_b = get_separate_creeper_state(
            frame, start_x=100, end_x=750, y=ground_y_bottom, is_top=False)
        if frame < 70:
            draw_creeper_realistic(d, cx_b, cy_b, scale=scale_b, leg_offset=leg_offset_b, flash_progress=flash_b, flip_y=False)
        else:
            draw_boom(d, cx_b, cy_b, boom_b, rng, multiplier=0.7)

        # Top Creeper
        cx_t, cy_t, scale_t, leg_offset_t, flash_t, boom_t = get_separate_creeper_state(
            frame, start_x=800, end_x=150, y=ground_y_top, is_top=True)
        if frame < 70:
            draw_creeper_realistic(d, cx_t, cy_t, scale=scale_t, leg_offset=leg_offset_t, flash_progress=flash_t, flip_y=True)
        else:
            draw_boom(d, cx_t, cy_t, boom_t, rng, multiplier=0.7)

    frames.append(img)

OUT.parent.mkdir(parents=True, exist_ok=True)
frames[0].save(
    OUT,
    save_all=True,
    append_images=frames[1:],
    duration=int(1000/FPS),
    loop=0,
    optimize=False,
)
print(f"Generated {OUT}")
