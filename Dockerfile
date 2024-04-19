FROM python:3.12-alpine

ARG UID
ARG GID

RUN \
  set -xe \
  && addgroup -g $GID webls \
  && adduser -D -u $UID -G webls webls

WORKDIR /home/webls/
USER webls

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python", "-m", "webls", "--host", "0.0.0.0", "--root", "storage"]
