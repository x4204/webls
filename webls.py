import bottle
import mimetypes
import os
import stat

from bottle import Bottle, SimpleTemplate
from optparse import OptionParser
from pathlib import Path


def dir_entry_sort_key(path):
    path_str = str(path)

    dir_first = -1 if path.is_dir() else 1
    dot_first = -1 if path_str.startswith('.') else 1

    return (dir_first, dot_first, path)


def size_pretty(size):
    units = ['B', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y']
    idx = 0

    while size > 1024:
        size /= 1024
        idx += 1

    if idx == 0:
        return f'{size:d}{units[idx]}'
    else:
        return f'{size:.1f}{units[idx]}'


def dir_read_entries(fs_root, fs_path):
    entries = list(fs_path.iterdir())

    entries.sort(key=dir_entry_sort_key)
    for idx, entry in enumerate(entries):
        entry_stat = entry.stat()
        entry_path = entry.relative_to(fs_root)
        entries[idx] = {
            'is_dir': False,
            'mode': stat.filemode(entry_stat.st_mode),
            'size_bytes': entry_stat.st_size,
            'size_pretty': size_pretty(entry_stat.st_size),
            'name': entry.name,
            'url': f'/fs/{entry_path}',
            'dl_url': f'/dl/{entry_path}',
            'link_class': 'entry-file',
        }

        if entry.is_dir():
            entries[idx]['is_dir'] = True
            entries[idx]['name'] += '/'
            entries[idx]['url'] += '/'
            entries[idx]['link_class'] = 'entry-dir'

    return entries


def dir_serve(app_root, fs_root, web_path, fs_path):
    template = SimpleTemplate(
        lookup=[app_root.joinpath('templates/')],
        name='dir.html',
    )

    return template.render(
        web_path=web_path,
        entries=dir_read_entries(fs_root, fs_path),
    )


def file_serve(app_root, fs_root, web_path, fs_path):
    template = SimpleTemplate(
        lookup=[app_root.joinpath('templates/')],
        name='file.html',
    )
    entry_path = fs_path.relative_to(fs_root)

    dl_url = f'/dl/{entry_path}'
    try:
        file_content = fs_path.read_text()
        can_display = True
    except UnicodeDecodeError:
        file_content = None
        can_display = False

    return template.render(
        web_path=web_path,
        dl_url=dl_url,
        can_display=can_display,
        file_content=file_content,
    )


def app_build(config):
    app = Bottle()

    app.config.update(config)

    @app.error(404)
    def handler(error):
        return 'not found'

    @app.route('/')
    def handler():
        bottle.redirect('/fs/')

    @app.route('/fs<web_path:path>')
    def handler(web_path):
        app_root = app.config['webls.app_root']
        fs_root = app.config['webls.fs_root']
        fs_path = fs_root.joinpath(web_path.lstrip('/'))

        if fs_path.is_dir():
            return dir_serve(app_root, fs_root, web_path, fs_path)
        elif fs_path.is_file():
            return file_serve(app_root, fs_root, web_path, fs_path)
        elif not fs_path.exists():
            bottle.abort(404)
        else:
            raise NotImplementedError('unknown file type')

    @app.route('/dl<web_path:path>')
    def handler(web_path):
        fs_root = app.config['webls.fs_root']
        fs_path = fs_root.joinpath(web_path.lstrip('/'))
        kwargs = {}

        mimetype, encoding = mimetypes.guess_type(fs_path)
        interpret_as_octet_stream = (
            mimetype is None
            or mimetype[:5] == 'text/'
        )

        if interpret_as_octet_stream:
            kwargs['mimetype'] = 'application/octet-stream'
            kwargs['download'] = True

        return bottle.static_file(web_path, root=fs_root, **kwargs)

    return app


def option_parser_build():
    option_parser = OptionParser()

    option_parser.add_option(
        '--host',
        help='bind to this host (default: 127.0.0.1)',
        dest='host',
        type='string',
        default='127.0.0.1',
    )
    option_parser.add_option(
        '--port',
        help='bind to this port (default: 8080)',
        dest='port',
        type='int',
        default=8080,
    )
    option_parser.add_option(
        '--root',
        help='serve this directory (default: .)',
        dest='root',
        type='string',
        default='.',
    )
    option_parser.add_option(
        '--dev',
        help='run in development mode (default)',
        dest='development',
        action='store_true',
        default=True,
    )
    option_parser.add_option(
        '--no-dev',
        help='run in production mode',
        dest='development',
        action='store_false',
        default=True,
    )

    return option_parser


def app_config(opts):
    return {
        'webls.app_root': Path('.').absolute(),
        'webls.fs_root': Path(opts.root),
    }


def run_kwargs(opts):
    kwargs = {
        'host': opts.host,
        'port': opts.port,
    }

    if opts.development:
        kwargs['reloader'] = True
        kwargs['interval'] = 0.2
        kwargs['debug'] = True

    return kwargs


if __name__ == '__main__':
    option_parser = option_parser_build()
    opts, _ = option_parser.parse_args()

    config = app_config(opts)
    kwargs = run_kwargs(opts)

    app_build(config).run(**kwargs)
