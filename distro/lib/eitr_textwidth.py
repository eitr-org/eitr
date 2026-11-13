"""Terminal cell widths: Japanese, Chinese and Korean characters take two cells."""
import textwrap
import unicodedata


def cell_width(text):
    return sum(0 if unicodedata.combining(character) else 2 if unicodedata.east_asian_width(character) in "WF" else 1
               for character in text)


def clip(text, limit):
    """text within limit cells, ending in an ellipsis when it was shortened."""
    if cell_width(text) <= limit:
        return text
    kept, used = "", 0
    for character in text:
        size = cell_width(character)
        if used + size > limit - 1:
            break
        kept, used = kept + character, used + size
    return kept + "…" if limit > 0 else ""


def wrap_text(text, width):
    """Lines of at most width cells. Words wrap at spaces; text with wide
    characters, which have no spaces between words, breaks between characters."""
    if cell_width(text) == len(text):
        return textwrap.wrap(text, width)
    lines, line, used = [], "", 0
    for character in text:
        size = cell_width(character)
        if used + size > width and line:
            lines.append(line.rstrip())
            line, used = "", 0
        if line or not character.isspace():
            line, used = line + character, used + size
    return [*lines, line.rstrip()] if line.strip() else lines
