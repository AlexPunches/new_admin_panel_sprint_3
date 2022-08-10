FROM python:3.10-slim

WORKDIR /opt/app

COPY requirements.txt requirements.txt


RUN  pip install --no-cache-dir --upgrade pip \
     && apt-get -y update && apt-get -y install gcc libpq-dev python3-dev \
     && pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD [ "python3", "/opt/app/postgres_to_es/load_indexes.py" ]