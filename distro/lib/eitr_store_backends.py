"""Store backend operation interface: installed, index, install, remove, update, apply, preview.

Plugin prepare/confirm and artwork/detail extend that interface for reviewed code.
"""
import json
from pathlib import Path
import subprocess
import tempfile

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
        target = cache('eitr/catalog-previews/index.json')
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode='w', dir=target.parent, delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(result, handle)
        temporary.replace(target)
        return {'items': result['themes']}
    if name == 'detail' and args.get('channel') == 'community':
        return community_detail(args['id'], backend)
    if name in {'preview', 'artwork'}:
        return artwork_preview(kind, args['id'], backend, args.get('path'), args.get('channel', 'official'), args.get('url'))
    if name == 'install':
        return {'result': backend.install(THEMES, args['ids'])}
    if name == 'check':
        return {'updates': backend.check()}
    if name == 'apply':
        subprocess.run(['bash', str(code_root() / 'walker/scripts/actions/style/apply.sh'), args['id']], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=90)
        return {}
    return {'result': getattr(backend, name)(args['id'])}


def plugins(name, args):
    from eitr_paths import cache
    kind = args['kind']
    if args.get('channel') == 'community' and name == 'index':
        return community(name, args)
    backend = plugin_backend()
    if name == 'installed':
        return {'items': installed_badges([dict(row, kind='builtin' if row.get('builtin') else 'official' if row['official'] else 'third-party') for row in backend.installed()], kind)}
    if name == 'check':
        return {'updates': backend.check_updates()}
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
    if name == 'install' and args.get('ids') == ['weather']:
        return {'result': backend.install_bundled('weather')}
    if name == 'prepare':
        if args.get('id') == 'weather' and not args.get('url') and not args.get('updating'):
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
            from eitr_community import validate_index
            from eitr_plugin_install import normalized_url
            record = backend.records()[item_id]
            try:
                index = validate_index(json.loads(cache('eitr/community-index.json').read_text()))
            except (OSError, ValueError):
                index = {'plugins': []}
            row = next((row for row in index['plugins'] if row['id'] == item_id and
                        normalized_url(record['url']) == normalized_url(row['repository']) and
                        record.get('path', '') == row['folder']), None)
            try:
                if row is not None:
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
    rows = backend.bundled_catalog() + [row for row in rows if row['id'] != 'weather']
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
    return BACKENDS[definition['backend']](name, args)
