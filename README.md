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

- do not display text file in the browser if too big (>1mb)

- handle directory names with special characters (`asd?`, `asd#`, etc.)
  - currently 404 is returned

- cover with tests

- check if it looks ok in other browsers

- security
  - search for url attacks + symlink traversal; analyze; try to secure against
    these kinds of attacks (also see `bottle.static_file`)

- support downloading a directory (with confirmation; zip)

- ?syntax highlighting for text files
