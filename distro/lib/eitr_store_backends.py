"""Store backend operation interface: installed, index, install, remove, update, apply, preview.

Plugin prepare/confirm and artwork/detail extend that interface for reviewed code.
"""
import json
from pathlib import Path
import subprocess
import tempfile

from eitr_store_previews import discover_result, publish_json, repository_path, theme_previews

from eitr_plugin_bundled import BUNDLED_DEFAULTS
from eitr_store_content import community, community_detail, installed_badges, artwork_preview

THEMES = 'https://github.com/eitr-org/eitr-themes'
PLUGINS = 'https://github.com/eitr-org/eitr-plugins'

_PLUGIN_BACKEND = None
_THEME_BACKEND = None


def plugin_backend():
    global _PLUGIN_BACKEND
    if _PLUGIN_BACKEND is None:
        from eitr_plugins import Plugins
        _PLUGIN_BACKEND = Plugins()
        _PLUGIN_BACKEND.ensure_bundled()
    return _PLUGIN_BACKEND


def save_plugin_rows(rows, channel='official'):
    from eitr_paths import cache
    target = cache('eitr/catalog-previews/plugins' + ('-community' if channel == 'community' else '') + '.json')
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', dir=target.parent, delete=False) as handle:
        temporary = Path(handle.name)
        json.dump(rows, handle)
    temporary.replace(target)


def themes(name, args):
    from eitr_paths import code_root, cache
    from eitr_theme_packages import Themes
    kind = args['kind']
    if args.get('channel') == 'community' and name in {'index', 'install'}:
        return community(name, args)
    global _THEME_BACKEND
    if _THEME_BACKEND is None:
        _THEME_BACKEND = Themes()
    backend = _THEME_BACKEND
    if name == 'discard':
        backend.discard_reviews()
        return {}
    if name == 'prepare':
        return {'review': backend.prepare_review(args['url'], theme_id=args.get('id'), theme_ids=args.get('ids'))}
    if name == 'confirm':
        return {'result': backend.confirm_review(args['token'])}
    if name == 'installed':
        return {'items': installed_badges(backend.installed(), kind)}
    if name == 'index':
        result = backend.index(THEMES)
        publish_json(cache('eitr/catalog-previews/index.json'), result)
        rows = result['themes']
        with backend.lock():
            try:
                theme_previews(repository_path(backend, THEMES), result['commit'], THEMES, rows,
                               allow_file=backend.allow_file)
            except (OSError, ValueError, subprocess.SubprocessError):
                pass  # Keep the listing available if the preview fetch fails.
        return discover_result('official', rows)
    if name == 'detail' and args.get('channel') == 'community':
        return community_detail(args['id'], backend)
    if name in {'preview', 'artwork'}:
        return artwork_preview(kind, args['id'], backend, args.get('path'), args.get('channel', 'official'), args.get('url'))
    if name == 'install':
        return {'result': backend.install(THEMES, args['ids'])}
    if name == 'check':
        return {'updates': backend.check(preview=True)}
    if name == 'changes':
        from eitr_store_changes import theme_changes
        return theme_changes(backend, args['id'])
    if name == 'apply':
        subprocess.run(['bash', str(code_root() / 'walker/scripts/actions/style/apply.sh'), args['id']], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=90)
        return {}
    return {'result': getattr(backend, name)(args['id'])}


def community_plugins():
    from eitr_community import validate_index
    from eitr_paths import cache
    from eitr_plugin_install import normalized_url, read_state
    from eitr_store_changes import STATE_LIMIT
    try:
        rows = validate_index(read_state(cache('eitr/community-index.json'), STATE_LIMIT))['plugins']
    except (OSError, ValueError):
        rows = []
    return {(row['id'], normalized_url(row['repository']), row['folder']): row for row in rows}


def matching_plugin(index, plugin_id, record):
    from eitr_plugin_install import normalized_url
    return index.get((plugin_id, normalized_url(record['url']), record.get('path', '')), {})


def plugins(name, args):
    from eitr_paths import cache
    kind = args['kind']
    if args.get('channel') == 'community' and name == 'index':
        return community(name, args)
    if name == 'changes':
        from eitr_plugins import Plugins
        from eitr_store_changes import plugin_changes
        return plugin_changes(_PLUGIN_BACKEND or Plugins(), args['id'])
    backend = plugin_backend()
    if name == 'installed':
        return {'items': installed_badges([dict(row, kind='builtin' if row.get('builtin') else 'official' if row['official'] else 'third-party') for row in backend.installed()], kind)}
    if name == 'check':
        index = community_plugins()
        return {'updates': backend.check_updates(
            revision_for=lambda plugin_id, record: matching_plugin(index, plugin_id, record).get('commit'))}
    if name == 'remove':
        return {'result': backend.remove(args['id'], lambda record: True,
                                           lambda packages: [name for name in packages if name in args.get('removePackages', [])])}
    if name == 'discard':
        backend.discard_reviews()
        return {}
    if name == 'confirm':
        return {'result': backend.confirm_review(args['token'])}
    if name == 'advice':
        return {'answer': backend.review_advice(args['token'])}
    if name == 'source':
        return backend.review_source(args['token'], args.get('path'), args.get('offset', 0))
    if name == 'install':
        ids = args.get('ids') or []
        if len(ids) == 1 and ids[0] in BUNDLED_DEFAULTS:
            return {'result': backend.install_bundled(ids[0])}
    if name == 'prepare':
        if args.get('id') in BUNDLED_DEFAULTS and not args.get('url') and not args.get('updating'):
            return {'bundled': True}
        if args.get('url'):
            review = backend.prepare_review(args['url'], plugin_id=args.get('id'))
            if 'choices' in review:
                import hashlib
                from eitr_plugin_install import normalized_url
                # Cards need artwork paths: list the repository's plugins without
                # fetching code or media, and keep the rows for artwork requests.
                offered = {choice['id'] for choice in review['choices']}
                rows = [row for row in backend.catalog(review['url']) if row['id'] in offered]
                listing = cache('eitr/catalog-previews') / ('plugins-git-' + hashlib.sha256(normalized_url(review['url']).encode()).hexdigest() + '.json')
                listing.parent.mkdir(parents=True, exist_ok=True)
                listing.write_text(json.dumps(dict(url=review['url'], plugins=rows)))
                review['choices'] = rows
            return {'review': review}
        item_id = args['id']
        if args.get('updating'):
            record = backend.records()[item_id]
            row = matching_plugin(community_plugins(), item_id, record)
            try:
                if row:
                    review = backend.prepare_review(plugin_id=item_id, folder=row['folder'], revision=row['commit'], updating=True)
                    return {'review': dict(review, license=row['license'], maintainer=row['maintainer'])}
                if args.get('channel') == 'community':
                    raise ValueError('Community source differs from installed plugin')
                return {'review': backend.prepare_review(plugin_id=item_id, updating=True)}
            except ValueError as error:
                # Nothing newer than the installed commit: not an error, just up to date.
                if str(error) == 'No plugin changes to review':
                    return {'upToDate': True}
                raise
        channel = args.get('channel', 'official')
        rows = json.loads(cache('eitr/catalog-previews/plugins' + ('-community' if channel == 'community' else '') + '.json').read_text())
        row = next(row for row in rows if row['id'] == item_id)
        review = backend.prepare_review(row['repository'], plugin_id=item_id, folder=row['folder'],
                                        revision=row['commit'] if channel == 'community' else None)
        return {'review': dict(review, license=row.get('license', ''), maintainer=row.get('maintainer', ''))}
    if name in {'preview', 'artwork'}:
        return artwork_preview(kind, args['id'], backend, args.get('path'), args.get('channel', 'official'), args.get('url'))
    if name == 'detail':
        rows = json.loads(cache('eitr/catalog-previews/plugins' + ('-community' if args.get('channel') == 'community' else '') + '.json').read_text())
        return {'item': next(row for row in rows if row['id'] == args['id'])}
    try:
        rows = backend.catalog(PLUGINS)
    except (OSError, ValueError, subprocess.SubprocessError):
        rows = []
    rows = backend.bundled_catalog() + [row for row in rows if row['id'] not in BUNDLED_DEFAULTS]
    save_plugin_rows(rows)
    return {'items': rows}




def lockscreens(name, args):
    from eitr_lockscreen_packages import listing, root, select
    if name in {'installed', 'index'}:
        return {'items': listing(installed_only=name == 'installed')}
    if name == 'apply':
        select(args.get('id'))
        return {}
    root(name, args['ids'] if name == 'install' else [args['id']])
    return {'result': True}


def wallpapers(name, args):
    from eitr_store_wallpapers import dispatch
    return dispatch(name, args)


BACKENDS = dict(themes=themes, plugins=plugins, lockscreens=lockscreens, wallpapers=wallpapers)


def dispatch(name, args):
    from eitr_store_kinds import registry
    definition = registry()[args['kind']]
    if name == 'changes' and not definition['capabilities']['update']:
        from eitr_store_changes import versions
        return dict(**versions('', ''), commits=[], more=0)
    return BACKENDS[definition['backend']](name, args)
