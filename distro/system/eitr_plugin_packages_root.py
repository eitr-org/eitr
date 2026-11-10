"""Root package transaction: accept names only and isolate repository selection."""
import json
import os
from pathlib import Path
import subprocess
import tempfile

from eitr_plugin_packages import REPOSITORIES, names, removable, repository, query


def dispatch(action, stream):
    if os.geteuid() != 0:
        raise ValueError('Package management requires root')
    packages = names(json.loads(stream.read(8193)))
    if not packages:
        return
    approved = {name: repository(name) for name in packages}
    if action == 'remove':
        if removable(packages) != packages:
            raise ValueError('Only orphaned dependency packages may be removed')
        subprocess.run(['/usr/bin/pacman', '-R', '--noconfirm', '--', *packages], check=True)
        return
    if action != 'install':
        raise ValueError('Invalid package action')
    targets = [approved[name] + '/' + name for name in packages if query('-Q', name).returncode != 0]
    if not targets:
        return
    # pacman-conf expands Include directives; omit all non-approved sync repositories,
    # including for dependency resolution. Do not refresh databases or partially upgrade.
    config = subprocess.check_output(['/usr/bin/pacman-conf'], text=True, timeout=30)
    lines, allowed = [], False
    for line in config.splitlines():
        if line.startswith('[') and line.endswith(']'):
            allowed = line[1:-1] in REPOSITORIES | {'options'}
        if allowed:
            lines.append(line)
    if not lines or '[options]' not in lines:
        raise ValueError('Invalid pacman configuration')
    with tempfile.TemporaryDirectory(prefix='eitr-packages-') as temporary:
        path = Path(temporary) / 'pacman.conf'
        path.write_text('\n'.join(lines) + '\n')
        subprocess.run(['/usr/bin/pacman', '--config', str(path), '-S', '--needed', '--asdeps',
                        '--noconfirm', '--', *targets], check=True)
