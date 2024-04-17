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

- cover with tests
  - https://bottlepy.org/docs/dev/recipes.html#unit-testing-bottle-applications

- security
  - search for url attacks + symlink traversal; analyze; try to secure against
    these kinds of attacks (also see `bottle.static_file`)

- support downloading a directory (with confirmation; zip)

- ?syntax highlighting for text files
