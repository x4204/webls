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

- `templates/dir.html`
  - display as table
    - file type (icon)
    - file permissions
    - file name (with color)
    - file size
    - download link
      - use a unicode character?; same for other download links?
      - https://symbl.cc/en/21AF/

- general
  - better css design

- download
  - support downloading a directory (with confirmation; zip)

- `webls.py`
  - handle other cases besides `is_dir()` and `is_file()`

- `templates/dir.html`/`templates/file.html`
  - split the "Contents of XXX" into path segments and then make links out of
    them so that you can navigate to a specific parent directory

- `templates/file.html`
  - scrollable `<pre>` (both desktop and mobile)
  - preview file (based on file extension)
    - syntax highlighting?

- security
  - search for url attacks + symlink traversal; analyze; try to secure agains
    these kinds of attacks (also see `bottle.static_file`)
