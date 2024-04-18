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

- setup demo directory
```
sudo bash setupdemo.sh
```

- run tests
```
python -m tests -v
```

- run app
```
python -m webls --help
python -m webls
```

## Docker

- build image
```
docker build -t webls:local .
```

- run container
```
docker run --rm --network=host webls:local
```

## TODO

- syntax highlighting for text files
  - https://pygments.org/

- security
  - search for url attacks + symlink traversal; analyze; try to secure against
    these kinds of attacks (also see `bottle.static_file`)

- ?migrate to werkzeug
  - https://werkzeug.palletsprojects.com/en/3.0.x/

- ?support downloading a directory (with confirmation; zip)
