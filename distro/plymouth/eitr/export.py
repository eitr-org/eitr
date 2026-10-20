#!/usr/bin/env python3
"""Export the Eitr boot splash images (wordmark, Futhark ring, passphrase field)
and the background colour in eitr.script, from the approved wordmark and the
Norse palette. Requires Pillow and the
JetBrainsMono Nerd Font package:

  uv run --with pillow distro/plymouth/eitr/export.py
"""
from pathlib import Path
import re
import tomllib
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
WORDMARK = ROOT / "branding/png/eitr-wordmark-white-1024.png"
FONT = Path("/usr/share/fonts/TTF/JetBrainsMonoNerdFont-Regular.ttf")
SCALE = 4  # draw large, then downsample for smooth rounded edges


def rgb(value, alpha=255):
    return tuple(int(value[offset:offset + 2], 16) for offset in (1, 3, 5)) + (alpha,)


def rounded(size, color):
    width, height = size
    image = Image.new("RGBA", (width * SCALE, height * SCALE))
    ImageDraw.Draw(image).rounded_rectangle((0, 0, width * SCALE - 1, height * SCALE - 1),
                                            radius=height * SCALE // 2, fill=color)
    return image.resize(size, Image.Resampling.LANCZOS)


FUTHARK = "ᚠᚢᚦᚨᚱᚲᚷᚹᚺᚾᛁᛃᛇᛈᛉᛊᛏᛒᛖᛗᛚᛜᛞᛟ"
RUNIC_FONT = Path("/usr/share/fonts/noto/NotoSansRunic-Regular.ttf")


def runes(accent):
    """rune-00.png to rune-23.png: the Elder Futhark ring around the wordmark, in the accent with a soft glow."""
    font = ImageFont.truetype(str(RUNIC_FONT), 32 * SCALE)
    size = 52 * SCALE
    for index, rune in enumerate(FUTHARK):
        glyph = Image.new("RGBA", (size, size))
        left, top, right, bottom = font.getbbox(rune)
        position = ((size - (right - left)) / 2 - left, (size - (bottom - top)) / 2 - top)
        ImageDraw.Draw(glyph).text(position, rune, font=font, fill=rgb(accent))
        glow = glyph.filter(ImageFilter.GaussianBlur(5 * SCALE))
        image = Image.alpha_composite(glow, glyph)
        image.resize((size // SCALE, size // SCALE), Image.Resampling.LANCZOS).save(HERE / f"rune-{index:02d}.png")


def main():
    palette = tomllib.loads((ROOT / "themes/norse/colors.toml").read_text())
    accent = palette["accent"]
    script = HERE / "eitr.script"
    shade = ", ".join(f"{channel / 255:.3f}" for channel in rgb(palette["background"])[:3])
    script.write_text(re.sub(r"(Window\.SetBackground(?:Top|Bottom)Color)\([^)]*\)", rf"\1({shade})",
                             script.read_text()))
    source = Image.open(WORDMARK).convert("RGBA")
    width = 360
    alpha = source.getchannel("A").resize((width, round(width * source.height / source.width)),
                                          Image.Resampling.LANCZOS)
    wordmark = Image.new("RGBA", alpha.size, rgb(accent))
    wordmark.putalpha(alpha)
    wordmark.save(HERE / "wordmark.png")
    runes(accent)
    # The passphrase prompt uses the accent too: one colour from power-on to the desktop.
    rounded((10, 10), rgb(accent)).save(HERE / "bullet.png")
    rounded((320, 40), rgb(accent, 28)).save(HERE / "field.png")
    font = ImageFont.truetype(str(FONT), 15 * SCALE)
    text = "Enter the disk passphrase"
    left, top, right, bottom = font.getbbox(text)
    label = Image.new("RGBA", (right - left + 8 * SCALE, bottom - top + 8 * SCALE))
    ImageDraw.Draw(label).text((4 * SCALE - left, 4 * SCALE - top), text, font=font, fill=rgb(accent, 235))
    label.resize((label.width // SCALE, label.height // SCALE), Image.Resampling.LANCZOS).save(HERE / "passphrase.png")


if __name__ == "__main__":
    main()
