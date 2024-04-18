import bottle
import functools
import mimetypes
import os
import stat

from bottle import Bottle, SimpleTemplate, request as req
from optparse import OptionParser
from pathlib import Path
from urllib.parse import quote


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

    def __init__(self, *, fs_root):
        self.fs_root = fs_root

    def apply(self, callback, route):
        @functools.wraps(callback)
        def wrapper(*args, **kwargs):
            if 'url_path' in kwargs:
                kwargs['url_path'] = './' + kwargs['url_path']
                kwargs['fs_path'] = self.fs_root.joinpath(kwargs['url_path'])
            else:
                kwargs['url_path'] = './'
                kwargs['fs_path'] = self.fs_root.joinpath('.')
            return callback(*args, **kwargs)

        return wrapper


class CheckPath:
    api = 2

    def __init__(self, *, fs_root):
        self.fs_root = fs_root

    def apply(self, callback, route):

        @functools.wraps(callback)
        def wrapper(*args, **kwargs):
            url_path = kwargs['url_path']
            fs_path = kwargs['fs_path']

            if self.dir_trailing_slash(url_path, fs_path):
                bottle.abort(404)

            if self.is_forbidden(self.fs_root, fs_path):
                bottle.abort(403)

            return callback(*args, **kwargs)

        return wrapper

    def dir_trailing_slash(self, url_path, fs_path):
        has_trailing_slash = url_path.endswith('/')
        is_dir = fs_path.is_dir()

        return (
            (has_trailing_slash and not is_dir)
            or (not has_trailing_slash and is_dir)
        )

    def is_forbidden(self, root, path):
        is_outside_root = (
            path.is_symlink()
            and not path.resolve().is_relative_to(root)
        )

        return (
            is_outside_root
            or path.is_socket()
            or path.is_fifo()
            or path.is_char_device()
            or path.is_block_device()
        )


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


def get_url(app, name, url_path):
    path = quote(str(url_path))

    return app.get_url(name, url_path=url_path)


def url_path_crumbs(app, url_path):
    assert isinstance(url_path, str)

    path = Path(url_path)
    crumbs = [path] + list(path.parents)

    crumbs.reverse()
    if len(crumbs) == 1:
        crumbs = [Path('.')]

    for idx, crumb_path in enumerate(crumbs):
        fs_path = app.fs_root.joinpath(crumb_path)
        is_root = crumb_path == Path('.')

        crumbs[idx] = {
            'name': crumb_path.name,
            'url': get_url(app, 'fs', crumb_path),
            'link_class': 'is-file',
        }

        if fs_path.is_dir():
            if not is_root:
                crumbs[idx]['url'] += '/'
            crumbs[idx]['link_class'] = 'is-dir'

        if is_root:
            crumbs[idx]['name'] = '.'

    return crumbs


def dir_read_entries(app, fs_path):
    try:
        entries = list(fs_path.iterdir())
    except PermissionError:
        entries = []

    entries.sort(key=dir_entry_sort_key)
    for idx, entry in enumerate(entries):
        url_path = entry.relative_to(app.fs_root)
        entry_stat = entry.stat(follow_symlinks=False)
        entries[idx] = {
            'is_dir': False,
            'is_symlink': False,
            'mode': stat.filemode(entry_stat.st_mode),
            'size_bytes': entry_stat.st_size,
            'size_pretty': size_pretty(entry_stat.st_size),
            'name': entry.name,
            'url': get_url(app, 'fs', url_path),
            'dl_url': get_url(app, 'dl', url_path),
            'entry_class': 'is-file',
            'symlink_path': None,
            'symlink_class': 'is-file',
        }

        if entry.is_dir():
            entries[idx]['is_dir'] = True
            entries[idx]['name'] += '/'
            entries[idx]['url'] += '/'
            entries[idx]['entry_class'] = 'is-dir'
            entries[idx]['symlink_class'] = 'is-dir'
        elif entry.is_socket():
            entries[idx]['entry_class'] = 'is-socket'
        elif entry.is_fifo():
            entries[idx]['entry_class'] = 'is-fifo'
        elif entry.is_char_device():
            entries[idx]['entry_class'] = 'is-char-device'
        elif entry.is_block_device():
            entries[idx]['entry_class'] = 'is-block-device'

        if entry.is_symlink():
            entries[idx]['is_symlink'] = True
            entries[idx]['symlink_path'] = entry.readlink()
            if entry.exists():
                entries[idx]['entry_class'] = 'is-symlink'
            else:
                entries[idx]['entry_class'] = 'is-symlink-broken'

    return entries


def dir_serve(app, url_path, fs_path):
    return app.templates['dir.html'].render(
        path=url_path,
        crumbs=url_path_crumbs(app, url_path),
        entries=dir_read_entries(app, fs_path),
    )


def file_guess_display_type(path):
    MIMETYPES_TEXT = [
        'application/json',
        'application/manifest+json',
        'application/n-quads',
        'application/n-triples',
        'application/postscript',
        'application/rtf',
        'application/trig',
        'application/vnd.google-earth.kml+xml',
        'application/x-csh',
        'application/x-latex',
        'application/x-sh',
        'application/x-shar',
        'application/x-tcl',
        'application/x-tex',
        'application/x-texinfo',
        'application/x-troff',
        'application/xml',
        'message/rfc822',
    ]

    if path.is_symlink():
        path = path.readlink()

    mimetype, encoding = mimetypes.guess_type(path, strict=False)

    if not mimetype:
        return 'text'
    elif encoding:
        return 'binary'
    elif mimetype[:5] == 'text/' or mimetype in MIMETYPES_TEXT:
        return 'text'
    elif mimetype[:6] in 'image/':
        return 'image'
    elif mimetype[:6] == 'audio/':
        return 'audio'
    elif mimetype[:6] == 'video/':
        return 'video'
    elif mimetype == 'application/pdf':
        return 'pdf'
    else:
        return 'binary'


def file_serve_text_kwargs(kwargs):
    ONE_MIB = 1 << 20

    file_size = kwargs['fs_path'].stat().st_size
    file_size_pretty = size_pretty(file_size)

    if file_size > ONE_MIB:
        kwargs['warning_message'] = f'file is too large ({file_size_pretty})'
        return

    try:
        file_content = kwargs['fs_path'].read_text()
    except UnicodeDecodeError:
        return

    if file_size == 0:
        kwargs['warning_message'] = 'file is empty'
        return

    line_count = file_content.count('\n') + 1
    line_numbers = '\n'.join([
        f'{number}.'
        for number in range(1, line_count + 1)
    ])

    kwargs['can_display'] = True
    kwargs['warning_message'] = None
    kwargs['display_kwargs']['file_content'] = file_content
    kwargs['display_kwargs']['line_numbers'] = line_numbers


def file_serve_other_kwargs(app, kwargs):
    kwargs['can_display'] = True
    kwargs['warning_message'] = None
    kwargs['display_kwargs']['url'] = get_url(app, 'dl', kwargs['path'])


def file_serve(app, url_path, fs_path):
    kwargs = {
        'path': url_path,
        'fs_path': fs_path,
        'crumbs': url_path_crumbs(app, url_path),
        'dl_url': get_url(app, 'dl', url_path),
        'can_display': False,
        'warning_message': 'the contents cannot be displayed',
        'display_type': file_guess_display_type(fs_path),
        'display_kwargs': {},
    }

    if kwargs['display_type'] == 'binary':
        pass
    elif kwargs['display_type'] == 'text':
        file_serve_text_kwargs(kwargs)
    elif kwargs['display_type'] in ['image', 'audio', 'video', 'pdf']:
        file_serve_other_kwargs(app, kwargs)
    else:
        raise NotImplementedError(kwargs['display_type'])

    return app.templates['file.html'].render(**kwargs)


def error_serve(app, template_name, message):
    if req.path[:4] != '/fs/':
        return f'{message}: {req.method} {req.path}'

    url_path = './' + req.path[4:]
    fs_path = Path(url_path)

    return app.templates[template_name].render(
        path=url_path,
        crumbs=url_path_crumbs(app, url_path),
        root_url=get_url(app, 'fs', ''),
    )


def static_file_kwargs(fs_path):
    mimetype, encoding = mimetypes.guess_type(fs_path)
    interpret_as_octet_stream = (
        mimetype is None
        or mimetype[:5] == 'text/'
    )

    if not interpret_as_octet_stream:
        return {}

    return {
        'mimetype': 'application/octet-stream',
        'download': True,
    }


def app_build(*, development, root, fs_root):
    app = Bottle()

    app.root = root
    app.fs_root = fs_root

    app.templates = Templates(
        path=app.root.joinpath('templates/'),
        fresh=development,
    )

    wrap_path = WrapPath(fs_root=app.fs_root)
    check_path = CheckPath(fs_root=app.fs_root)

    @app.error(403)
    def handler(error):
        return error_serve(app, 'forbidden.html', 'forbidden')

    @app.error(404)
    def handler(error):
        return error_serve(app, 'not_found.html', 'not found')

    @app.route('/')
    @app.route('/fs')
    def handler():
        bottle.redirect(get_url(app, 'fs', ''))

    @app.route('/fs/', apply=[wrap_path, check_path])
    @app.route('/fs/<url_path:path>', name='fs', apply=[wrap_path, check_path])
    def handler(url_path, fs_path):
        if fs_path.is_dir():
            return dir_serve(app, url_path, fs_path)
        elif fs_path.exists():
            return file_serve(app, url_path, fs_path)
        else:
            bottle.abort(404)

    @app.route('/dl/', apply=[wrap_path, check_path])
    @app.route('/dl/<url_path:path>', name='dl', apply=[wrap_path, check_path])
    def handler(url_path, fs_path):
        path = str(fs_path.relative_to(app.fs_root))
        kwargs = static_file_kwargs(fs_path)

        return bottle.static_file(path,root=app.fs_root, **kwargs)

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


def main():
    option_parser = option_parser_build()
    opts, _ = option_parser.parse_args()

    app = app_build(
        development=opts.development,
        root=Path('.').absolute(),
        fs_root=Path(opts.root).absolute(),
    )
    kwargs = run_kwargs(opts)

    app.run(**kwargs)


if __name__ == '__main__':
    main()
