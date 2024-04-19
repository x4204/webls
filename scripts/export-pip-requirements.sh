set -xe

poetry export --only=production > requirements/production.txt
poetry export --only=test > requirements/test.txt
