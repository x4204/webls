# `webls`

Simple file browser over HTTP

## Running

```
python -m webls
python -m webls --help
```

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

## TODO

- `templates/dir.html`/`templates/file.html`
  - split the "Contents of XXX" into path segments and then make links out of
    them so that you can navigate to a specific parent directory

- `templates/file.html`
  - scrollable `<pre>`
  - preview file (based on file extension)
    - syntax highlighting?

- general
  - better css design (both desktop and mobile)

- `webls.py`
  - handle other cases besides `is_dir()` and `is_file()`

- cover with tests

- security
  - search for url attacks + symlink traversal; analyze; try to secure agains
    these kinds of attacks (also see `bottle.static_file`)

- download
  - support downloading a directory (with confirmation; zip)
