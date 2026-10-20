#!/usr/bin/env python3
"""Export the desktop's Fenrir sprite from the website's original artwork.

The source is two 887 × 887 frames side by side (snarling, then open jaws);
the desktop shows each frame at most 640 px, so it ships 640 px frames.
"""
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[3] / "website/assets/ragnarok/fenrir-bite.png"
FRAME = 640

with Image.open(SOURCE) as sprite:
    sprite.resize((FRAME * 2, FRAME), Image.LANCZOS).save(HERE / "fenrir-bite.png", optimize=True)
print(HERE / "fenrir-bite.png")
