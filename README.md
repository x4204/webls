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

- run tests
```
python -m tests -v
```

- run app
```
python -m webls --help
python -m webls
```

## TODO

- ?avoid using chdir
  - easier to test

- security
  - search for url attacks + symlink traversal; analyze; try to secure against
    these kinds of attacks (also see `bottle.static_file`)

- syntax highlighting for text files
  - https://pygments.org/

- build a demo docker image
  - different mime types (text (different programming languages), image, audio,
    video, pdf)
  - empty text files, big text files
  - different file types (dir, file, symlink, broken symlink, socket, etc)

- ?migrate to werkzeug
  - https://werkzeug.palletsprojects.com/en/3.0.x/

- ?support downloading a directory (with confirmation; zip)
