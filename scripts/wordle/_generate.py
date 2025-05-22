"""
Generates wordle icons
"""

from PIL import Image, ImageDraw, ImageFont

# import os
from pathlib import Path


def generate_wordle_icons(
    output_dir: str = "./wordle_icons",
    tile_px: int = 96,
    letters: str = "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
):
    colours = {
        "grey": (120, 124, 126),
        "green": (106, 170, 100),
        "black": (18, 18, 19),
        "orange": (201, 180, 88),
    }

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Pick a bold font; fall back to default if not found.
    bold_candidates = ["arialbd.ttf", "DejaVuSans-Bold.ttf"]
    font = None
    for f in bold_candidates:
        try:
            font = ImageFont.truetype(f, int(tile_px * 0.8))
            break
        except IOError:
            font = None
    if font is None:
        font = ImageFont.load_default()

    # … keep the imports, colours, font loading etc. …

    for letter in letters.upper():
        for name, colour in colours.items():
            img = Image.new("RGB", (tile_px, tile_px), colour)
            draw = ImageDraw.Draw(img)

            # bounding-box and true centre
            bbox = draw.textbbox((0, 0), letter, font=font)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            x = (tile_px - w) / 2 - bbox[0]  # bbox[0] fixes baseline shift
            y = (tile_px - h) / 2 - bbox[1]  # bbox[1] fixes ascent shift
            draw.text((x, y), letter, fill="white", font=font)

            img.save(f"{output_dir}/{name}_{letter.lower()}.png")


if __name__ == "__main__":
    generate_wordle_icons()
