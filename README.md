# `webls`

Simple file browser over HTTP

## Development

- setup virtual environment
```
virtualenv .venv --python $(which python3.12)
```

- enter virtual environment
```
. .venv/bin/activate
```

- install dependencies
```
pip install -r requirements.txt
```

## Running

```
python -m webls
```

## TODO

- `templates/dir.html`/`templates/file.html`
  - split the "Contents of XXX" into path segments and then make links out of
    them so that you can navigate to a specific parent directory

- `templates/file.html`
  - scrollable `<pre>` (both desktop and mobile)
  - preview file (based on file extension)
    - syntax highlighting?

- general: support command line arguments
  - `--host HOST` (default: `127.0.0.1`)
  - `--port PORT` (default: `8080`)
  - `--root DIR` (default: `.`)
  - `--dev/--no-dev` (default: `--dev`)

- general
  - better css design

- `webls.py`
  - handle other cases besides `is_dir()` and `is_file()`

- security
  - search for url attacks + symlink traversal; analyze; try to secure agains
    these kinds of attacks (also see `bottle.static_file`)

- download
  - support downloading a directory (with confirmation; zip)
