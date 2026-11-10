"""Machine-local placements of plugin desktop widgets and bar items.

A widget can be placed any number of times; each copy has its own `instance` id, display,
geometry, rotation and options. Bar items are on or off per plugin item.
"""
import hashlib
import json
import re
import secrets

from eitr_paths import config
from eitr_plugin_manifest import identifier, object_keys, string, unique_object


VERSION = 3
INSTANCE = re.compile(r'[0-9a-f]{8}\Z')
WIDGET_FIELDS = ('plugin', 'id', 'monitor', 'x', 'y', 'width', 'height')
LIMIT = 256


def instance_id(value):
    if not isinstance(value, str) or not INSTANCE.fullmatch(value):
        raise ValueError('Invalid widget copy id')
    return value


def monitor_instance(monitor):
    """Before version 3 a widget was unique per display, so its display names the copy."""
    return hashlib.sha256(monitor.encode()).hexdigest()[:8]


def rotation_value(value):
    if type(value) is not int or not 0 <= value <= 359:
        raise ValueError('Widget rotation must be a whole number from 0 to 359')
    return value


def geometry_value(geometry):
    object_keys(geometry, ('x', 'y', 'width', 'height'))
    for number in geometry.values():
        if type(number) is not int or not 0 <= number <= 65536:
            raise ValueError('Invalid widget geometry')
    if geometry['width'] < 24 or geometry['height'] < 24:
        raise ValueError('Widget geometry must be at least 24 pixels')
    return geometry


def validate_widget(placement, version):
    newer = ('instance', 'rotation') if version >= 3 else ()
    object_keys(placement, WIDGET_FIELDS + (('instance',) if version >= 3 else ()), ('aboveWindows', 'surface') + newer)
    if 'aboveWindows' in placement and (version == 1 or type(placement['aboveWindows']) is not bool):
        raise ValueError('Invalid widget layer')
    if 'surface' in placement and placement['surface'] not in ('panel', 'none'):
        raise ValueError('Invalid widget surface')
    if 'rotation' in placement:
        rotation_value(placement['rotation'])
    string(placement['monitor'])
    for field in ('x', 'y', 'width', 'height'):
        if type(placement[field]) is not int or not 0 <= placement[field] <= 65536 or (field in ('width', 'height') and placement[field] < 24):
            raise ValueError('Invalid widget geometry')
    placement.setdefault('aboveWindows', False)
    placement['instance'] = instance_id(placement['instance']) if version >= 3 else monitor_instance(placement['monitor'])


class PluginPlacements:
    def placements(self):
        """Versions 1 and 2 are read as version 3 and written in that form on the next change."""
        try:
            value = json.loads(config('eitr/plugin-placements.json').read_text(), object_pairs_hook=unique_object)
        except FileNotFoundError:
            return dict(version=VERSION, widgets=[], barItems=[])
        object_keys(value, ('version', 'widgets', 'barItems'))
        if type(value['version']) is not int or value['version'] not in (1, 2, 3):
            raise ValueError('Invalid plugin placement version')
        seen = set()
        for kind in ('widgets', 'barItems'):
            if not isinstance(value[kind], list) or len(value[kind]) > LIMIT:
                raise ValueError('Invalid plugin placements')
            for placement in value[kind]:
                if kind == 'widgets':
                    validate_widget(placement, value['version'])
                else:
                    object_keys(placement, ('plugin', 'id'))
                identifier(placement['plugin'])
                identifier(placement['id'])
                key = (kind, placement['plugin'], placement['id'], placement.get('instance'))
                if key in seen:
                    raise ValueError('Duplicate plugin placement')
                seen.add(key)
        value['version'] = VERSION
        return value

    def place(self, plugin_id, entry_id, monitor=None, *, instance=None, new=False, remove=False, geometry=None,
              toggle_layer=False, surface=None, rotation=None, duplicate=False):
        """Change one placement; returns the widget copy's instance id.

        A widget copy is named by `instance`. `new` adds another copy on `monitor`, and
        `duplicate` copies `instance`. Without either, `monitor` names the display's
        first copy, as a bar started before version 3 still asks.
        """
        identifier(plugin_id)
        identifier(entry_id)
        if instance is not None:
            instance_id(instance)
        if surface is not None and surface not in ('panel', 'none'):
            raise ValueError('Invalid widget surface')
        if rotation is not None:
            rotation_value(rotation)
        if geometry is not None:
            geometry_value(geometry)
        with self.lock():
            values = self.placements()
            entry = next((entry for entry in self.ui() if entry['plugin'] == plugin_id and entry['id'] == entry_id and entry['kind'] in ('widgets', 'barItems')), None)
            if not entry and not remove:
                raise ValueError('Unknown plugin visual')
            kind = entry['kind'] if entry else ('widgets' if monitor is not None or instance is not None else 'barItems')
            result = None
            if kind == 'barItems':
                if instance or new or duplicate or geometry or toggle_layer or surface or rotation is not None:
                    raise ValueError('Bar items have no widget settings')
                values[kind] = [placement for placement in values[kind] if placement['plugin'] != plugin_id or placement['id'] != entry_id]
                if not remove:
                    values[kind].append(dict(plugin=plugin_id, id=entry_id))
            else:
                result = self._change_widget(values['widgets'], entry, plugin_id, entry_id, monitor, instance, new, remove,
                                             geometry, toggle_layer, surface, rotation, duplicate)
            if len(values[kind]) > LIMIT:
                raise ValueError('Too many plugin placements')
            path = config('eitr/plugin-placements.json')
            path.parent.mkdir(parents=True, exist_ok=True)
            self.write(path, values)
            return result

    def _change_widget(self, widgets, entry, plugin_id, entry_id, monitor, instance, new, remove,
                       geometry, toggle_layer, surface, rotation, duplicate):
        copies = [placement for placement in widgets if placement['plugin'] == plugin_id and placement['id'] == entry_id]
        if instance is not None:
            target = next((placement for placement in copies if placement['instance'] == instance), None)
            if target is None and not remove:
                raise ValueError('Unknown widget copy')
        elif new:
            target = None
        else:
            string(monitor)
            target = next((placement for placement in copies if placement['monitor'] == monitor), None)
        if remove:
            if target is not None:
                widgets.remove(target)
            return instance
        if (toggle_layer or duplicate) and target is None:
            raise ValueError('Widget must be placed first')
        if target is None or duplicate:
            if target is None:
                target = dict(plugin=plugin_id, id=entry_id, monitor=string(monitor), aboveWindows=False, x=24, y=24,
                              width=entry.get('defaultWidth', 192), height=entry.get('defaultHeight', 192))
            else:
                target = dict(target, x=target['x'] + 24, y=target['y'] + 24)
            target['instance'] = self._new_instance(widgets)
            widgets.append(target)
        if monitor is not None:
            target['monitor'] = string(monitor)
        if surface is not None:
            target['surface'] = surface
        if toggle_layer:
            target['aboveWindows'] = not target['aboveWindows']
        if geometry is not None:
            target.update(geometry)
        if rotation is not None:
            target['rotation'] = rotation
        if not target.get('rotation'):
            target.pop('rotation', None)
        return target['instance']

    @staticmethod
    def _new_instance(widgets):
        taken = {placement['instance'] for placement in widgets}
        while True:
            candidate = secrets.token_hex(4)
            if candidate not in taken:
                return candidate
