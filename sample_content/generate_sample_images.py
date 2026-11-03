"""Generate clean sample practice images for TAT module testing."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

dest_dir = Path(__file__).parent / "sample_tat_images"
dest_dir.mkdir(parents=True, exist_ok=True)

scenarios = [
    ("pic_01.jpg", "A young officer studying a map under lamplight at night with two comrades.", (24, 32, 48), (70, 130, 180)),
    ("pic_02.jpg", "Villagers gathered near a breached embankment pointing towards rising floodwaters.", (35, 45, 35), (100, 149, 110)),
    ("pic_03.jpg", "An engineer examining blueprint machinery in a bustling industrial plant.", (48, 30, 25), (180, 120, 80)),
    ("pic_04.jpg", "A group of mountaineers ascending a ridge amidst gathering storm clouds.", (20, 20, 35), (120, 140, 180)),
]

for filename, text, bg_col, accent_col in scenarios:
    img = Image.new("RGB", (960, 640), color=bg_col)
    draw = ImageDraw.Draw(img)

    # Decorative gradient-like geometric silhouettes
    draw.rectangle([60, 60, 900, 580], outline=accent_col, width=3)
    draw.rectangle([70, 70, 890, 570], outline=(60, 70, 90), width=1)

    # Abstract silhouettes representing human figures in setting
    draw.ellipse([300, 200, 420, 320], fill=accent_col)
    draw.rectangle([260, 330, 460, 520], fill=accent_col)

    draw.ellipse([540, 240, 640, 340], fill=(accent_col[0] - 20, accent_col[1] - 20, accent_col[2] - 20))
    draw.rectangle([500, 350, 680, 520], fill=(accent_col[0] - 20, accent_col[1] - 20, accent_col[2] - 20))

    # Title caption
    caption = f"TAT PRACTICE SCENE — {Path(filename).stem.upper()}\n{text}"
    draw.text((100, 100), caption, fill=(240, 245, 255))

    img.save(dest_dir / filename, "JPEG", quality=92)

print(f"Generated {len(scenarios)} sample TAT images in {dest_dir}")
