FROM python:3.12-alpine

WORKDIR /app/

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

RUN sh setupstorage.sh

EXPOSE 8080

CMD ["python", "-m", "webls", "--host", "0.0.0.0", "--root", "storage"]
