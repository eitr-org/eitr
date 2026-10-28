#!/usr/bin/env python3
"""Export the Eitr boot splash images (wordmark, Futhark ring, passphrase field)
and the background colour in eitr.script, from the approved wordmark, measured
runestone gold and the shared Bifröst progress palette. Requires Pillow and the
JetBrainsMono Nerd Font package:

  uv run --with pillow distro/plymouth/eitr/export.py
"""
import argparse
import math
import sys
import tempfile
from pathlib import Path
import re
import tomllib
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "distro/lib"))
from eitr_bifrost import (ADVANCE_NUMERATOR, ADVANCE_DENOMINATOR, FRAME_SECONDS,
                         PHASE_COUNT, frame_phase, phase_color)

# Dominant gold in the central runestone emblem: RGB (196, 145, 79).
RUNE_GOLD = "#c4914f"
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
    result = Image.new("RGBA", size, color)
    result.putalpha(image.getchannel("A").resize(size, Image.Resampling.LANCZOS))
    return result


FUTHARK = "ᚠᚢᚦᚨᚱᚲᚷᚹᚺᚾᛁᛃᛇᛈᛉᛊᛏᛒᛖᛗᛚᛜᛞᛟ"
RUNIC_FONT = Path("/usr/share/fonts/noto/NotoSansRunic-Regular.ttf")


def runes(accent, output):
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
        result = Image.new("RGBA", (size // SCALE, size // SCALE), rgb(accent))
        result.putalpha(image.getchannel("A").resize(result.size, Image.Resampling.LANCZOS))
        result.save(output / f"rune-{index:02d}.png")


def export(output):
    output.mkdir(parents=True, exist_ok=True)
    palette = tomllib.loads((ROOT / "themes/norse/colors.toml").read_text())
    accent = RUNE_GOLD
    foreground = palette["foreground"]
    script = output / "eitr.script"
    shade = ", ".join(f"{channel / 255:.3f}" for channel in rgb(palette["background"])[:3])
    script.write_text(re.sub(r"(Window\.SetBackground(?:Top|Bottom)Color)\([^)]*\)", rf"\1({shade})",
                             (HERE / "eitr.script").read_text()))
    source = Image.open(WORDMARK).convert("RGBA")
    width = 360
    alpha = source.getchannel("A").resize((width, round(width * source.height / source.width)),
                                          Image.Resampling.LANCZOS)
    wordmark = Image.new("RGBA", alpha.size, rgb(accent))
    wordmark.putalpha(alpha)
    wordmark.save(output / "wordmark.png")
    for phase in range(PHASE_COUNT):
        frame = Image.new("RGBA", alpha.size, phase_color(phase) + (255,))
        frame.putalpha(alpha)
        frame.save(output / f"wordmark-{phase:02d}.png")
    text = script.read_text()
    constants = (f"wordmark.phase_count = {PHASE_COUNT};\n"
                 f"wordmark.ticks_per_frame = {FRAME_SECONDS * 50:g};\n"
                 f"wordmark.advance_numerator = {ADVANCE_NUMERATOR};\n"
                 f"wordmark.advance_denominator = {ADVANCE_DENOMINATOR};")
    text = re.sub(r"wordmark.phase_count = .*?wordmark.advance_denominator = [^;]+;", constants, text, flags=re.S)
    script.write_text(text)
    runes(accent, output)
    # A neutral prompt and gold field stay readable while the wordmark changes colour.
    rounded((10, 10), rgb(accent)).save(output / "bullet.png")
    rounded((320, 40), rgb(accent, 28)).save(output / "field.png")
    font = ImageFont.truetype(str(FONT), 15 * SCALE)
    text = "Enter the disk passphrase"
    left, top, right, bottom = font.getbbox(text)
    label = Image.new("RGBA", (right - left + 8 * SCALE, bottom - top + 8 * SCALE))
    ImageDraw.Draw(label).text((4 * SCALE - left, 4 * SCALE - top), text, font=font, fill=rgb(foreground, 255))
    prompt = Image.new("RGBA", (label.width // SCALE, label.height // SCALE), rgb(foreground))
    prompt.putalpha(label.getchannel("A").resize(prompt.size, Image.Resampling.LANCZOS))
    prompt.save(output / "passphrase.png")


def previews(output, destination):
    destination.mkdir(parents=True, exist_ok=True)
    for name, frame, password in (("boot-frame-24", 24, False), ("boot-frame-48", 48, False),
                                  ("shutdown", 72, False), ("disk-passphrase", 0, True)):
        canvas = Image.new("RGBA", (1280, 720), rgb("#0a0b12"))
        logo = Image.open(output / f"wordmark-{frame_phase(frame):02d}.png").convert("RGBA")
        center_x, center_y = 640, 320
        canvas.alpha_composite(logo, (center_x - logo.width // 2, center_y - logo.height // 2))
        for index in range(24):
            rune = Image.open(output / f"rune-{index:02d}.png").convert("RGBA")
            angle = index / 24 * 2 * math.pi - math.pi / 2
            distance = abs(index - (frame / 40 % 1) * 24)
            distance = min(distance, 24 - distance)
            light = max(.75 if index + 1 <= .45 * 24 else .18, 1 - distance * .27 if distance < 3 else .18)
            rune.putalpha(rune.getchannel("A").point(lambda alpha: round(alpha * light)))
            canvas.alpha_composite(rune, (round(center_x + math.cos(angle) * 270 - 26),
                                           round(center_y + math.sin(angle) * (logo.height / 2 + 90) - 26)))
        if password:
            below = center_y + logo.height / 2 + 90 + 40
            label = Image.open(output / "passphrase.png").convert("RGBA")
            field = Image.open(output / "field.png").convert("RGBA")
            canvas.alpha_composite(label, (center_x - label.width // 2, round(below - 8)))
            field_y = round(below + label.height + 4)
            canvas.alpha_composite(field, (center_x - field.width // 2, field_y))
            bullet = Image.open(output / "bullet.png").convert("RGBA")
            for index in range(10):
                canvas.alpha_composite(bullet, (center_x - 77 + index * 16, field_y + 15))
        canvas.convert("RGB").save(destination / f"plymouth-{name}.png")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--preview-dir", type=Path)
    arguments = parser.parse_args()
    if arguments.check:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            export(output)
            stale = [path.name for path in output.iterdir()
                     if not (HERE / path.name).is_file() or path.read_bytes() != (HERE / path.name).read_bytes()]
            if stale:
                print("Stale Plymouth exports: " + ", ".join(sorted(stale)), file=sys.stderr)
                return 1
    else:
        export(HERE)
        if arguments.preview_dir:
            previews(HERE, arguments.preview_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
