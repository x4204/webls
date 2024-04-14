from bottle import Bottle, SimpleTemplate, run, abort, static_file, redirect
from pathlib import Path


def dir_entry_sort_key(path):
    path_str = str(path)

    dir_first = -1 if path.is_dir() else 1
    dot_first = -1 if path_str.startswith('.') else 1

    return (dir_first, dot_first, path)


def dir_read_entries(path):
    entries = [
        entry
        for entry in path.iterdir()
    ]

    entries.sort(key=dir_entry_sort_key)
    for idx, entry in enumerate(entries):
        entries[idx] = {
            'name': str(entry.name),
            'url': f'/fs/{entry}',
        }

        if entry.is_dir():
            entries[idx]['name'] += '/'
            entries[idx]['url'] += '/'

    return entries


def dir_serve(web_path, fs_path):
    template = SimpleTemplate(
        lookup=['templates/'],
        name='dir.html',
    )

    return template.render(
        web_path=web_path,
        entries=dir_read_entries(fs_path),
    )


def file_serve(web_path, fs_path):
    template = SimpleTemplate(
        lookup=['templates/'],
        name='file.html',
    )

    dl_url = f'/dl/{fs_path}'
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


def app_build():
    app = Bottle()

    @app.error(404)
    def handler(error):
        return 'not found'

    @app.route('/')
    def handler():
        redirect('/fs/')

    @app.route('/fs<web_path:path>')
    def handler(web_path):
        fs_path = Path(web_path.lstrip('/'))

        if fs_path.is_dir():
            return dir_serve(web_path, fs_path)
        elif fs_path.is_file():
            return file_serve(web_path, fs_path)
        elif not fs_path.exists():
            abort(404)
        else:
            raise NotImplementedError('unknown file type')

    @app.route('/dl<web_path:path>')
    def handler(web_path):
        return static_file(web_path, root='.')

    return app


if __name__ == '__main__':
    run(
        app=app_build(),
        host='127.0.0.1',
        port=8080,
        reloader=True,
        interval=0.2,
        # debug=True,
    )
