"""Classification and runtime staging shared by packaging and user adoption."""
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


class Layout:
    def __init__(self, root, manifest_path=None):
        self.root = Path(root)
        manifest = json.loads(Path(manifest_path or self.root / 'distro/layout-manifest.json').read_text())
        if manifest.get('version') != 1:
            raise ValueError('Unsupported layout manifest')
        self.rules = manifest['rules']

    def classify(self, relative):
        # **/ also matches zero subdirectories, as it does in path globbing.
        for rule in self.rules:
            patterns = [rule['pattern']]
            while any('**/' in pattern for pattern in patterns):
                expanded = [pattern.replace('**/', '', 1) for pattern in patterns if '**/' in pattern]
                if all(pattern in patterns for pattern in expanded):
                    break
                patterns.extend(pattern for pattern in expanded if pattern not in patterns)
            if any(fnmatch.fnmatchcase(str(relative), pattern) for pattern in patterns):
                return rule
        raise ValueError(f'Unclassified repository path: {relative}')

    def files(self):
        if (self.root / '.git').exists():
            result = subprocess.run(['git', '-C', str(self.root), 'ls-files', '-z'],
                                    check=True, capture_output=True).stdout.decode()
            return [path for path in result.split('\0') if path and (self.root / path).exists()]
        return [str(path.relative_to(self.root)) for path in self.root.rglob('*')
                if (path.is_file() or path.is_symlink()) and '__pycache__' not in path.parts]

    def stage(self, destination):
        destination = Path(destination)
        for relative in self.files():
            rule = self.classify(relative)
            if not rule['runtime']:
                continue
            source = self.root / relative
            if relative.startswith('distro/lib/'):
                installed = Path('lib') / relative.removeprefix('distro/lib/')
            elif relative.startswith('distro/migrations/'):
                installed = Path('migrations') / relative.removeprefix('distro/migrations/')
            elif relative.startswith('distro/defaults/'):
                installed = Path('defaults') / relative.removeprefix('distro/defaults/')
            elif relative.startswith('HOME_FILES/'):
                installed = Path('home') / relative.removeprefix('HOME_FILES/')
            else:
                installed = Path(relative)
            target = destination / installed
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.is_symlink():
                # Both sides resolved: makepkg stages from a relative root (--repo .).
                if source.resolve() == (self.root / 'distro/lib/eitr_bootstrap.py').resolve():
                    target.symlink_to(os.path.relpath(destination / 'lib/eitr_bootstrap.py', target.parent))
                # Native integration links are built by packaging, never ship a
                # source link pointing back into an old home code directory.
                continue
            shutil.copy2(source, target)
        shutil.copy2(self.root / 'distro/layout-manifest.json', destination / 'layout-manifest.json')
        shutil.copy2(self.root / 'distro/legacy-layout.json', destination / 'legacy-layout.json')

    def legacy_manifest(self, revision):
        """Capture reviewed repository defaults, never any live configuration."""
        result = subprocess.check_output(['git', '-C', str(self.root), 'ls-tree', '-rz', revision])
        roots = {'HOME_FILES', 'Kvantum', 'elephant', 'fastfetch', 'hypr', 'kitty',
                 'nvim', 'quickshell', 'swayosd', 'themes', 'walker',
                 'xdg-desktop-portal', 'dolphinrc', 'filetypesrc', 'mimeapps.list'}
        files = {}
        for line in result.split(b'\0'):
            if not line:
                continue
            metadata, relative = line.decode().split('\t', 1)
            mode, _, object_id = metadata.split()
            if relative.split('/')[0] not in roots:
                continue
            content = subprocess.check_output(['git', '-C', str(self.root), 'cat-file', 'blob', object_id])
            files[relative] = {'class': self.classify(relative)['class'],
                               'digest': ('link:' if mode == '120000' else 'file:') + hashlib.sha256(content).hexdigest(),
                               'mode': 0o777 if mode == '120000' else int(mode[-3:], 8)}
        return {'version': 1, 'revision': revision, 'files': files}
