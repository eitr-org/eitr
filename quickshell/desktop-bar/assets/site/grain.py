#!/usr/bin/env python3
"""Regenerate grain.png, the tileable film grain the library windows share with the website."""
from pathlib import Path

from PIL import Image, ImageFilter

SIZE = 160
noise = Image.effect_noise((SIZE, SIZE), 64).filter(ImageFilter.GaussianBlur(0.4))
grain = Image.new('LA', (SIZE, SIZE))
grain.putdata([(value, 255) for value in noise.get_flattened_data()])
grain.save(Path(__file__).with_name('grain.png'), optimize=True)
