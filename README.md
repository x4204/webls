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

- have better not found page
  - file `xxx` not found
  - link to root

- `templates/file.html`
  - scrollable `<pre>`
  - ?line numbers

- general
  - better css design (both desktop and mobile)

- `webls.py`
  - handle other cases besides `is_dir()` and `is_file()`

- cover with tests

- security
  - search for url attacks + symlink traversal; analyze; try to secure agains
    these kinds of attacks (also see `bottle.static_file`)

- file syntax highlighting (based on file extension)

- download
  - support downloading a directory (with confirmation; zip)
