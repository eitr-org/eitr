"""Shared Bifröst palette and motion for terminal progress and generated splash assets."""
PALETTE = ((224, 92, 104), (232, 147, 90), (230, 195, 106),
           (127, 201, 143), (111, 168, 220), (169, 139, 214))
FRAME_SECONDS = 0.1
ADVANCE_NUMERATOR = 2
ADVANCE_DENOMINATOR = 3
LETTER_PHASE = 24
STOP_RESOLUTION = 256
PHASE_COUNT = len(PALETTE) * STOP_RESOLUTION // LETTER_PHASE


def phase_color(phase):
    position = (-phase * LETTER_PHASE) % (len(PALETTE) * STOP_RESOLUTION)
    stop, mix = divmod(position, STOP_RESOLUTION)
    first, second = PALETTE[stop], PALETTE[(stop + 1) % len(PALETTE)]
    return tuple(start + int((end - start) * mix / STOP_RESOLUTION)
                 for start, end in zip(first, second))


def frame_phase(frame):
    return (frame * ADVANCE_NUMERATOR // ADVANCE_DENOMINATOR) % PHASE_COUNT


if __name__ == '__main__':
    # Fixed numeric rows consumed by spinner.sh, never localized or evaluated.
    for channel in range(3):
        print(' '.join(str(color[channel]) for color in PALETTE))
    print(FRAME_SECONDS, ADVANCE_NUMERATOR, ADVANCE_DENOMINATOR, LETTER_PHASE,
          STOP_RESOLUTION, len(PALETTE))
