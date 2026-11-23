"""Render theme previews from the default wallpaper and palette."""
from io import BytesIO

from eitr_wallpapers import wallpapers

MAX_PREVIEW_BYTES = 2 * 1024 * 1024


def render_preview(directory, colors):
    from PIL import Image, ImageDraw, ImageOps
    picture = next(iter(wallpapers(directory / "backgrounds")), None)
    canvas = Image.new("RGB", (1280, 720), colors["background"])
    if picture is not None:
        with Image.open(picture) as source:
            canvas.paste(ImageOps.fit(ImageOps.exif_transpose(source).convert("RGB"), (1280, 720), Image.Resampling.LANCZOS))
    def swatches(image):
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 640, 1280, 720), fill=colors["background"])
        keys = ("accent", "foreground", *(f"color{index}" for index in range(1, 7)))
        for index, key in enumerate(keys):
            left = 24 + index * 154
            draw.rounded_rectangle((left, 656, left + 138, 704), radius=10, fill=colors[key])

    swatches(canvas)
    output = BytesIO()
    canvas.save(output, format="PNG", optimize=True)
    if output.tell() <= MAX_PREVIEW_BYTES:
        return output.getvalue()

    # Leave nine palette slots for the exact theme colors.
    reduced = Image.new("RGB", canvas.size)
    reduced.paste(canvas.crop((0, 0, 1280, 640)).quantize(colors=247).convert("RGB"))
    swatches(reduced)
    output = BytesIO()
    reduced.quantize(colors=256).save(output, format="PNG", optimize=True)
    if output.tell() > MAX_PREVIEW_BYTES:
        raise ValueError("Theme preview exceeds the Store size limit")
    return output.getvalue()


def write_preview(directory, colors):
    (directory / "preview.png").write_bytes(render_preview(directory, colors))
