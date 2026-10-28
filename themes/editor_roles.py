"""Shared, contrast-corrected editor roles derived from a theme palette."""
import colorsys


def blend(front, back, amount):
    return '#' + ''.join(f'{round(int(front[index:index+2], 16) * amount + int(back[index:index+2], 16) * (1-amount)):02x}' for index in (1, 3, 5))


def luminance(color):
    channels = [int(color[index:index+2], 16) / 255 for index in (1, 3, 5)]
    return sum(weight * (channel / 12.92 if channel <= .04045 else ((channel + .055) / 1.055) ** 2.4) for weight, channel in zip((.2126, .7152, .0722), channels))


def contrast(first, second):
    high, low = sorted((luminance(first), luminance(second)), reverse=True)
    return (high + .05) / (low + .05)


def readable(color, background, target=4.5):
    hue, lightness, saturation = colorsys.rgb_to_hls(*(int(color[index:index+2], 16)/255 for index in (1, 3, 5)))
    toward = 1 if luminance(background) < .5 else 0
    for step in range(101):
        candidate = '#' + ''.join(f'{round(channel*255):02x}' for channel in colorsys.hls_to_rgb(hue, lightness + (toward-lightness)*step/100, saturation))
        if contrast(candidate, background) >= target:
            return candidate
    return candidate


def roles(palette):
    background = palette['background']
    sources = dict(fg=palette['foreground'], accent=palette['accent'], second=palette.get('second', palette['color6']),
                   alert=palette.get('alert', palette['color1']), muted=palette.get('muted', palette['color8']))
    sources.update({name: palette[f'color{index}'] for index, name in enumerate(('red', 'green', 'yellow', 'blue', 'magenta', 'cyan'), 1)})
    result = {name: readable(value, background) for name, value in sources.items()}
    result.update(bg=background, keyword=result['accent'], function=result['second'], type=result['yellow'],
                  string=result['green'], number=result['magenta'], constant=result['alert'], builtin=result['cyan'],
                  property=result['blue'], parameter=result['second'], comment=readable(blend(result['second'], result['muted'], .3), background))
    for name, amount in (('surface', .08), ('raised', .16), ('line', .12), ('visual', .25), ('search', .32)):
        result[name] = blend(result['accent'], background, amount)
    result['selection_text'] = readable(result['fg'], result['search'])
    return result
