# Greetings traveller

Собрать и запустить контейнеры
```bash
make build
make up
```

Собрать и накатить миграции
```bash
make makemigrations
make migrate
```

Запустить ETL из SQLite в Postgres
```bash
make load-data
```

Запустить ETL из Postgres в Elasticsearch
```bash
make load-es-movies
```

Тесты
```bash
make pytest
```

Остановить и удалить контейнеры
```bash
make down
```

# Режим разработки. 

Чтобы было удобно разрабатывать и дебажить, можно в postgres и elastic пробросить наружу порты,
и запускать load_indexes.py в локальном виртуальном окружении, в котором DB_HOST ES_HOST будет localhost