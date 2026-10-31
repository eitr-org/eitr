"""Source projections for contracts spanning explicit child components."""
from pathlib import Path
import re
import textwrap


def qml_block(source, marker):
    start = source.index(marker)
    opening = source.index('{', start)
    depth = 1
    cursor = opening + 1
    while depth:
        depth += (source[cursor] == '{') - (source[cursor] == '}')
        cursor += 1
    return source[start:cursor]


def control_center_source(directory):
    folder = Path(directory) / 'panels'
    source = (folder / 'ControlCenter.qml').read_text()
    for name in ('Connectivity', 'Sliders', 'Style', 'Settings', 'Tools', 'Power'):
        child = (folder / f'ControlCenter{name}.qml').read_text().split('Column {', 1)[1]
        child = 'Column {' + child
        child = child.replace('section.centerRef', 'center')
        child = re.sub(r'center\.(\w+)Ref', r'\1', child)
        source += '\n' + textwrap.indent(child, ' ' * 20)
    source += '\n' + (folder / 'ControlCenterNavigation.qml').read_text().replace('navigation.centerRef', 'center')
    return source
