import bottle
import functools
import mimetypes
import os
import stat

from bottle import Bottle, SimpleTemplate
from optparse import OptionParser
from pathlib import Path


class Templates:
    def __init__(self, *, path, fresh):
        self.path = path
        self.fresh = fresh

        self.cache = {}

    def build(self, name):
        return SimpleTemplate(
            lookup=[self.path],
            name=name,
        )

    def __getitem__(self, name):
        if self.fresh:
            return self.build(name)
        if name in self.cache:
            return self.cache[name]

        self.cache[name] = self.build(name)
        return self.cache[name]


class WrapPath:
    api = 2

    def apply(self, callback, route):
        @functools.wraps(callback)
        def wrapper(*args, **kwargs):
            if 'path' in kwargs:
                kwargs['path'] = Path(kwargs['path'])
            else:
                kwargs['path'] = Path('.')
            return callback(*args, **kwargs)

        return wrapper


def dir_entry_sort_key(path):
    path_str = str(path)

    dir_first = -1 if path.is_dir() else 1
    dot_first = -1 if path_str.startswith('.') else 1

    return (dir_first, dot_first, path_str)


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


def path_crumbs(app, path):
    crumbs = [path] + list(path.parents)

    crumbs.reverse()
    if len(crumbs) == 1:
        crumbs = [Path('.')]

    for idx, path in enumerate(crumbs):
        if path == Path('.'):
            name = '.'
        else:
            name = path.name

        crumbs[idx] = {
            'name': name,
            'url': app.get_url('fs', path=path),
            'link_class': 'is-file',
        }

        if path.is_dir():
            crumbs[idx]['link_class'] = 'is-dir'

    return crumbs


def dir_read_entries(app, path):
    entries = list(path.iterdir())

    entries.sort(key=dir_entry_sort_key)
    for idx, entry in enumerate(entries):
        entry_stat = entry.stat()
        entries[idx] = {
            'is_dir': False,
            'mode': stat.filemode(entry_stat.st_mode),
            'size_bytes': entry_stat.st_size,
            'size_pretty': size_pretty(entry_stat.st_size),
            'name': entry.name,
            'url': app.get_url('fs', path=entry),
            'dl_url': app.get_url('dl', path=entry),
            'link_class': 'is-file',
        }

        if entry.is_dir():
            entries[idx]['is_dir'] = True
            entries[idx]['name'] += '/'
            entries[idx]['url'] += '/'
            entries[idx]['link_class'] = 'is-dir'

    return entries


def dir_serve(app, path):
    return app.templates['dir.html'].render(
        path=path,
        crumbs=path_crumbs(app, path),
        entries=dir_read_entries(app, path),
    )


def file_serve(app, path):
    try:
        file_content = path.read_text()
        line_count = file_content.count('\n')
        can_display = True
        error_msg = None

        if len(file_content) == 0:
            can_display = False
            error_msg = 'file is empty'
            line_numbers = 0
        else:
            line_count += 1
            line_numbers = '\n'.join([
                f'{number}.'
                for number in range(1, line_count + 1)
            ])
    except UnicodeDecodeError:
        file_content = None
        line_numbers = None
        can_display = False
        error_msg = 'the contents of the file cannot be displayed'

    return app.templates['file.html'].render(
        path=path,
        crumbs=path_crumbs(app, path),
        dl_url=app.get_url('dl', path=path),
        can_display=can_display,
        error_msg=error_msg,
        line_numbers=line_numbers,
        file_content=file_content,
    )


def app_build(opts):
    app = Bottle()

    app.path = Path('.').absolute()
    app.templates = Templates(
        path=app.path.joinpath('templates/'),
        fresh=opts.development,
    )

    wrap_path = WrapPath()

    @app.error(404)
    def handler(error):
        req = bottle.request
        path = Path(req.path[4:])

        if req.path[:4] not in ['/fs/', '/dl/']:
            return f'not found: {req.method} {req.path}'
        else:
            return app.templates['not_found.html'].render(
                path=path,
                crumbs=path_crumbs(app, path),
                root_url=app.get_url('fs', path=''),
            )

    @app.route('/')
    @app.route('/fs')
    def handler():
        bottle.redirect(app.get_url('fs', path=''))

    @app.route('/fs/', apply=wrap_path)
    @app.route('/fs/<path:path>', name='fs', apply=wrap_path)
    def handler(path):
        if path.is_dir():
            return dir_serve(app, path)
        elif path.is_file():
            return file_serve(app, path)
        elif not path.exists():
            bottle.abort(404)
        else:
            raise NotImplementedError('unknown file type')

    @app.route('/dl/', apply=wrap_path)
    @app.route('/dl/<path:path>', name='dl', apply=wrap_path)
    def handler(path):
        mimetype, encoding = mimetypes.guess_type(path)
        interpret_as_octet_stream = (
            mimetype is None
            or mimetype[:5] == 'text/'
        )
        kwargs = {}

        if interpret_as_octet_stream:
            kwargs['mimetype'] = 'application/octet-stream'
            kwargs['download'] = True

        return bottle.static_file(str(path), root='.', **kwargs)

    return app


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


def app_chdir(opts):
    dev = opts.development
    child = bool(os.getenv('BOTTLE_CHILD'))

    if not dev or (dev and child):
        os.chdir(opts.root)


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
        help='run in development mode',
        dest='development',
        action='store_true',
        default=False,
    )
    option_parser.add_option(
        '--no-dev',
        help='run in production mode (default)',
        dest='development',
        action='store_false',
        default=False,
    )

    return option_parser


if __name__ == '__main__':
    option_parser = option_parser_build()
    opts, _ = option_parser.parse_args()

    app = app_build(opts)
    kwargs = run_kwargs(opts)

    app_chdir(opts)
    app.run(**kwargs)
