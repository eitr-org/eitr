"""Adapt the frame dependencies to the existing isolated geometry stand-ins."""
from pathlib import Path
import re
import textwrap

from qml_source import qml_block


def frame_source(directory):
    source = (Path(directory) / "bar/BarWindow.qml").read_text()
    for name in ('BarVerticalPlacement', 'BarHorizontalPlacement', 'BarIslands',
                 'BarCenteredOutline', 'BarPanels', 'BarTabs', 'BarInputMask'):
        child = (Path(directory) / 'bar' / (name + '.qml')).read_text()
        child = child.split('\n\n', 1)[1].strip()
        exports = dict(re.findall(r'readonly property alias (\w+): (\w+(?:\.\w+)?)', child))
        instance_id = name[0].lower() + name[1:]
        for alias, target in exports.items():
            source = source.replace(instance_id + '.' + alias, target)
        child = re.sub(r'^    (?:required property var|readonly property alias) .*\n', '', child, flags=re.M)
        child = child.replace('barHost.stripItem', 'barContents').replace('barHost.autoHideRef', 'autoHide')
        child = child.replace('host: verticalSurface.host', 'host: bar.host').replace('host: surface.host', 'host: bar.host')
        child = child.replace('barHost: verticalSurface.barHost', 'barHost: bar').replace('barHost: surface.barHost', 'barHost: bar')
        child = child.replace('barHost.', 'bar.')
        child = re.sub(r'\bbarHost\b(?!\s*:)', 'bar', child)
        for identifier in ('networkServiceRef', 'notificationsRef', 'remoteServiceRef'):
            child = child.replace('bar.' + identifier, identifier)
        # Frame aliases become lexical IDs in the isolated projection.
        child = re.sub(r'\bbar\.(' + '|'.join(re.findall(r'property alias (\w+):', source.split('    required property var host', 1)[0])) + r')\b', r'\1', child)
        for identifier in ('edgeSensor', 'tabStrip', 'barContents', 'leadingTab', 'notchTab', 'trailingTab'):
            child = child.replace(identifier + 'Ref', identifier)
        if name == 'BarTabs':
            child = child[child.index('    Item {'):child.rfind('}')]
            child = textwrap.dedent(child)
        if name == 'BarPanels':
            child = textwrap.dedent(child[child.index('    NotificationPopups {'):child.rfind('}')])
            for method in ('openPluginPanel', 'showControlCenter', 'toggleControlCenter', 'showKind', 'inspectPanels'):
                wrapper = qml_block(source, '    function ' + method + '(')
                source = source.replace(wrapper, '')
        if name == 'BarIslands':
            component = qml_block(child, '    component IslandSurface:')
            child = child.replace(component, '') + '\n' + component
        match = re.search(r'^([ \t]*)' + name + r' \{', source, re.M)
        child = child.replace('{\n\n    id:', '{\n    id:')
        if name == 'BarIslands':
            child = child.replace('    component IslandSurface:', 'component IslandSurface:')
        instance = qml_block(source, match[0])
        indentation = len(match[1])
        source = source.replace(instance, textwrap.indent(child, ' ' * indentation))
    names = {
        'host': 'shell',
        'networkServiceRef': 'networkOwner',
        'notificationsRef': 'notificationsService',
        'remoteServiceRef': 'remoteAccessService',
        'dockClientsRef': 'dockClients',
        'idleLockProcessRef': 'toggleIdleLock',
    }
    source = source.replace("host: bar.host", "host: shell")
    return textwrap.indent(re.sub(r"\b(" + "|".join(names) + r")\b(?!\s*:)", lambda match: names[match[0]], source), " " * 12)
