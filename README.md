# `webls`

Simple file browser over HTTP

## Setup

- create virtual environment
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
python -m webls --help
```

## TODO

- scrollable table in `dir.html`

- file preview:
  - based on mimetype (pdf, png, jpg, etc.)

- cover with tests

- security
  - search for url attacks + symlink traversal; analyze; try to secure agains
    these kinds of attacks (also see `bottle.static_file`)

- `webls.py`
  - handle other cases besides `is_dir()` and `is_file()`

- syntax highlighting

- download
  - support downloading a directory (with confirmation; zip)
