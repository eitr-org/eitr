"""Package-owned plugins: local installation, one-time defaults and Store metadata."""
import hashlib
import json
from eitr_paths import ROOT

from eitr_paths import state
from eitr_plugin_manifest import identifier, manifest

BUNDLED = ROOT / 'distro/plugins/bundled'
BUNDLED_DEFAULTS = ('weather', 'ai-usage', 'hardware')
BUNDLED_URL = 'https://github.com/eitr-org/eitr'


def bundled_root(plugin_id):
    return BUNDLED / identifier(plugin_id)


def bundled_revision(root):
    digest = hashlib.sha256()
    for path in sorted(root.rglob('*')):
        if path.is_file():
            digest.update(str(path.relative_to(root)).encode() + b'\0' + path.read_bytes())
    return digest.hexdigest()


def is_bundled(root):
    return root.parent == BUNDLED and root.name in BUNDLED_DEFAULTS


class BundledPlugins:
    def ensure_bundled(self):
        """Runs at host startup, never re-adds a removed or disabled default."""
        from eitr_plugin_install import official
        marker = state('eitr/bundled-plugins.json')
        with self.lock():
            records = self.records()
            version = json.loads(marker.read_text())['version'] if marker.exists() else 0
            replaced_external = False
            for plugin_id in BUNDLED_DEFAULTS:
                record = records.get(plugin_id)
                if record and not record.get('bundled') and official(record.get('url', '')):
                    if not self.refusal(BUNDLED_URL, plugin_id=plugin_id):
                        self._install_bundled(records, plugin_id, enabled=record.get('enabled'))
                        replaced_external = True
            for plugin_id in BUNDLED_DEFAULTS[version:]:
                if plugin_id not in records and not self.refusal(BUNDLED_URL, plugin_id=plugin_id):
                    self._install_bundled(records, plugin_id)
            if replaced_external:
                self.clean_snapshots()
            if version < len(BUNDLED_DEFAULTS):
                self.write(marker, {'version': len(BUNDLED_DEFAULTS)})
            for plugin_id, record in records.items():
                if record.get('bundled'):
                    revision = bundled_revision(bundled_root(plugin_id))
                    if record['commit'] != revision:
                        record['commit'] = revision
                        self.save(records)

    def _install_bundled(self, records, plugin_id, *, enabled=None):
        import datetime
        root = bundled_root(plugin_id)
        if not is_bundled(root):
            raise ValueError('Unknown bundled plugin')
        self.check(BUNDLED_URL, plugin_id=plugin_id)
        spec = manifest(root)
        record = dict(id=plugin_id, url=BUNDLED_URL, commit=bundled_revision(root),
                      installed=datetime.datetime.now(datetime.timezone.utc).isoformat(), bundled=True)
        if enabled is False:
            record['enabled'] = False
        records[plugin_id] = record
        # Keep existing placements, including a previously chosen slot.
        placements = self.placements()
        for entry in spec.get('ui', {}).get('barItems', []):
            if not any(placement['plugin'] == plugin_id and placement['id'] == entry['id'] for placement in placements['barItems']):
                placements['barItems'].append(dict(plugin=plugin_id, id=entry['id']))
        from eitr_paths import config
        target = config('eitr/plugin-placements.json')
        target.parent.mkdir(parents=True, exist_ok=True)
        self.write(target, placements)
        self.save(records)

    def install_bundled(self, plugin_id):
        with self.lock():
            records = self.records()
            if plugin_id in records:
                raise ValueError('Plugin is already installed')
            self._install_bundled(records, plugin_id)
        return True

    def bundled_catalog(self):
        return [self._bundled_catalog_entry(plugin_id) for plugin_id in BUNDLED_DEFAULTS]

    def _bundled_catalog_entry(self, plugin_id):
        root = bundled_root(plugin_id)
        spec = manifest(root)
        return dict(id=spec['id'], name=spec['name'], description=spec['description'], author=spec['author'],
                    components={key: spec[key] for key in ('rows', 'ui', 'service', 'packages') if key in spec},
                    version=spec['version'], kind='builtin', builtin=True, official=True, repository=BUNDLED_URL,
                    previewUrl=(root / spec['icon']).as_uri(),
                    folder=f'plugins/bundled/{plugin_id}', commit=bundled_revision(root))
