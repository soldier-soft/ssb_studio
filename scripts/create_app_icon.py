"""Generate a high-resolution, ultra-crisp modern app icon (.ico and .png) for SSB Practice Studio."""

import math
from pathlib import Path
from PIL import Image, ImageDraw

assets_dir = Path(__file__).resolve().parent.parent / "assets"
assets_dir.mkdir(parents=True, exist_ok=True)

# Render at 1024x1024 supersampled canvas for high-DPI clarity
canvas_size = 1024
img_hi = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img_hi)

cx, cy = canvas_size // 2, canvas_size // 2

# Outer protective circular crest base with dark navy and glowing sapphire border
radius = 470
draw.ellipse(
    [cx - radius, cy - radius, cx + radius, cy + radius],
    fill=(11, 15, 25, 255),
    outline=(37, 99, 235, 255),
    width=26,
)

# Secondary inner sapphire / sky ring
in_radius = 420
draw.ellipse(
    [cx - in_radius, cy - in_radius, cx + in_radius, cy + in_radius],
    outline=(56, 189, 248, 200),
    width=8,
)

# Function to draw symmetric star crest
def draw_star(center_x, center_y, outer_r, inner_r, fill_col, outline_col, outline_width=6):
    points = []
    for i in range(10):
        angle = i * (math.pi / 5) - (math.pi / 2)
        r = outer_r if i % 2 == 0 else inner_r
        x = center_x + r * math.cos(angle)
        y = center_y + r * math.sin(angle)
        points.append((x, y))
    draw.polygon(points, fill=fill_col, outline=outline_col)


# Star drop shadow
draw_star(cx, cy - 30 + 10, 240, 105, (0, 0, 0, 140), None)

# Main golden commander star (SSB Gold)
draw_star(cx, cy - 35, 235, 102, (245, 158, 11, 255), (251, 191, 36, 255), 8)

# Mid-layer faceted star
draw_star(cx, cy - 35, 175, 75, (217, 119, 6, 255), (252, 211, 77, 255), 4)

# Inner luminous cyan star accent (representing mental clarity)
draw_star(cx, cy - 35, 120, 52, (56, 189, 248, 255), (224, 242, 254, 255), 4)

# Laurel Wing embellishments
draw.arc(
    [cx - 360, cy + 30, cx - 40, cy + 350],
    start=95,
    end=275,
    fill=(96, 165, 250, 255),
    width=18,
)
draw.arc(
    [cx + 40, cy + 30, cx + 360, cy + 350],
    start=265,
    end=85,
    fill=(96, 165, 250, 255),
    width=18,
)

# Lower banner pedestal with bevel outline
draw.rounded_rectangle(
    [cx - 310, cy + 250, cx + 310, cy + 365],
    radius=24,
    fill=(23, 37, 84, 255),
    outline=(96, 165, 250, 255),
    width=7,
)

# Inner pedestal highlight bar
draw.rounded_rectangle(
    [cx - 270, cy + 295, cx + 270, cy + 320],
    radius=8,
    fill=(59, 130, 246, 255),
)

# Downscale to 512x512 with Lanczos antialiasing for maximum sharpness
final_img = img_hi.resize((512, 512), Image.Resampling.LANCZOS)

# Save PNG
png_path = assets_dir / "app_icon.png"
final_img.save(png_path, "PNG", optimize=True)

# Save Windows multi-res ICO including all standard Windows icon sizes
ico_path = assets_dir / "app_icon.ico"
sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
final_img.save(ico_path, format="ICO", sizes=sizes)

print(f"Generated ultra-crisp icon assets in {assets_dir}:")
print(f" - PNG (512x512): {png_path} ({png_path.stat().st_size} bytes)")
print(f" - ICO (Multi-res): {ico_path} ({ico_path.stat().st_size} bytes)")
