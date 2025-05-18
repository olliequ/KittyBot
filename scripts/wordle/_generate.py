"""
Generates wordle icons
"""

from PIL import Image, ImageDraw, ImageFont

# import os
from pathlib import Path


def generate_wordle_icons(
    output_dir: str = "assets/appemoji",
    tile_px: int = 96,
    letters: str = "ABCDEFGHIJKLMNOPQRSTUVWXYZ ",
):
    colours = {
        "grey": ((230, 228, 232), "black"),
        "green": ((120, 178, 90), "white"),
        "black": ((49, 54, 61), "white"),
        "orange": ((252, 201, 89), "white"),
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

    for name, (bg, fg) in colours.items():
        for letter in letters.upper():
            img = Image.new("RGB", (tile_px, tile_px), bg)
            draw = ImageDraw.Draw(img)

            # bounding-box and true centre
            bbox = draw.textbbox((0, 0), letter, font=font)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            x = (tile_px - w) / 2 - bbox[0]  # bbox[0] fixes baseline shift
            y = (tile_px - h) / 2 - bbox[1]  # bbox[1] fixes ascent shift
            draw.text((x, y), letter, fill=fg, font=font)

            if letter == " ":
                letter = "sp"
            img.save(f"{output_dir}/{name}_{letter.lower()}.png")


if __name__ == "__main__":
    generate_wordle_icons()
