"""Generate the authentic Creeper Contribution GIF with crater destruction.

Reverts to the exact original 171-frame two-act Creeper animation:
- Act 1 (Frames 0-92): Two Creepers meet in the center, High-Five, and explode together.
  -> In that explosion, all green contribution cells in the blast zone are REMOVED and turned blank/black (22, 27, 34).
- Act 2 (Frames 93-170): Two Creepers stalk and explode separately on the top-left and bottom-right.
  -> In those explosions, the green contribution cells in both separate blast zones are REMOVED and turned blank/black.
- Fireball, smoke puffs, creeper sprites, and 'HIGH FIVE!' text are 100% preserved.

Output:
    assets/creeper-contribution.gif
"""

import math
from pathlib import Path
from PIL import Image

ORIG = Path(__file__).resolve().parents[1] / "assets" / "creeper-contribution-orig.gif"
OUT = Path(__file__).resolve().parents[1] / "assets" / "creeper-contribution.gif"
OUT_GRANTHX = Path(__file__).resolve().parents[1] / "granthx" / "assets" / "creeper-contribution.gif"

EMPTY_CELL = (22, 27, 34)

# Grid Layout
GRID_X = 34
GRID_Y = 46
CELL_SIZE = 14
CELL_PITCH = 18
COLS = 47
ROWS = 7

def main():
    if not ORIG.exists():
        raise FileNotFoundError(f"Original backup GIF not found at {ORIG}")

    im_orig = Image.open(ORIG)
    n_frames = im_orig.n_frames
    duration = im_orig.info.get("duration", 60)
    print(f"Loaded original GIF: {n_frames} frames, {duration}ms per frame")

    # Step 1: Detect baseline green contribution cells from frame 0
    im_orig.seek(0)
    f0 = im_orig.convert("RGB")
    green_cells = set()
    for r in range(ROWS):
        for c in range(COLS):
            x0 = GRID_X + c * CELL_PITCH
            y0 = GRID_Y + r * CELL_PITCH
            xc = x0 + 7
            yc = y0 + 7
            col = f0.getpixel((xc, yc))
            # Green check: significantly more green than red/blue
            if col[1] > col[0] + 15 and col[1] > 45:
                green_cells.add((r, c))

    print(f"Total baseline green contribution cells: {len(green_cells)}")

    # Step 2: Define blast zones
    # Act 1 Explosion: Center (449.0, 85.0), radius ~80px
    act1_destroyed = set()
    for (r, c) in green_cells:
        xc = GRID_X + c * CELL_PITCH + 7
        yc = GRID_Y + r * CELL_PITCH + 7
        if math.hypot(xc - 449.0, yc - 85.0) <= 80.0:
            act1_destroyed.add((r, c))

    # Act 2 Explosions:
    # Top-Left: (149.5, 49.0), radius ~75px
    # Bottom-Right: (749.5, 142.5), radius ~78px
    act2_destroyed = set()
    for (r, c) in green_cells:
        xc = GRID_X + c * CELL_PITCH + 7
        yc = GRID_Y + r * CELL_PITCH + 7
        d_left = math.hypot(xc - 149.5, yc - 49.0)
        d_right = math.hypot(xc - 749.5, yc - 142.5)
        if d_left <= 75.0 or d_right <= 78.0:
            act2_destroyed.add((r, c))

    print(f"Act 1 crater destroyed green cells: {len(act1_destroyed)}")
    print(f"Act 2 craters destroyed green cells: {len(act2_destroyed)}")

    processed_frames = []

    for f in range(n_frames):
        im_orig.seek(f)
        frame_rgb = im_orig.convert("RGB")

        # Determine which cells are destroyed at frame f:
        # Act 1 explosion triggers at frame 62 and persists
        # Act 2 separate explosions trigger at frame 152 and persist
        active_destroyed = set()
        if 62 <= f < 93:
            active_destroyed = act1_destroyed
        elif f >= 93:
            # During Act 2, Act 1 crater remains destroyed, and at f >= 152 Act 2 craters also get destroyed
            active_destroyed = set(act1_destroyed)
            if f >= 152:
                active_destroyed.update(act2_destroyed)

        if active_destroyed:
            pix = frame_rgb.load()
            for (r, c) in active_destroyed:
                x0 = GRID_X + c * CELL_PITCH
                y0 = GRID_Y + r * CELL_PITCH
                for yy in range(y0, y0 + CELL_SIZE + 1):
                    for xx in range(x0, x0 + CELL_SIZE + 1):
                        color = pix[xx, yy]
                        # Check if pixel is a green contribution pixel:
                        # (Leave fireballs, explosion rings, smoke, and creeper sprites intact)
                        is_green_pixel = (
                            color[1] > color[0] + 12 and
                            color[1] > color[2] + 10 and
                            color[0] < 120 and
                            color[2] < 120
                        )
                        if is_green_pixel:
                            pix[xx, yy] = EMPTY_CELL

        processed_frames.append(frame_rgb)

    print("Quantizing and saving GIF...")
    # Quantize to adaptive palette with transparency/loop preservation
    palette_frames = [f.convert("P", palette=Image.Palette.ADAPTIVE, colors=64) for f in processed_frames]

    palette_frames[0].save(
        OUT,
        save_all=True,
        append_images=palette_frames[1:],
        duration=duration,
        loop=0,
        optimize=True
    )
    size_mb = OUT.stat().st_size / (1024 * 1024)
    print(f"Successfully generated {OUT} ({size_mb:.2f} MB)")

    if OUT_GRANTHX.parent.exists():
        import shutil
        shutil.copy2(OUT, OUT_GRANTHX)
        print(f"Copied to {OUT_GRANTHX}")

if __name__ == "__main__":
    main()
