from pydantic import BaseSettings, DirectoryPath, Field, FilePath


class Dsl(BaseSettings):
    dbname: str = Field(..., env='postgres_db')
    user: str = Field('app', env='postgres_user')
    password: str = Field(..., env='postgres_password')
    host: str = Field('127.0.0.1', env='db_host')
    port: str = Field(5432, env='db_port')


class EsBaseUrl(BaseSettings):
    es_host: str = Field(..., env='es_host')
    es_port: str = Field(9200, env='es_port')

    def get_url(self):
        return 'http://{}:{}'.format(self.es_host, self.es_port)


class BaseConfig(BaseSettings):
    bunch_extract: int = 100
    bunch_insert: int = 100
    bunch_es_load: int = 100
    sqlite3_path: FilePath = Field(..., env='sqlite3_path')
    es_schemas_dir: DirectoryPath = Field(..., env='es_schemas_dir')
    es_base_url: str = EsBaseUrl().get_url()
    dsl: dict = Dsl().dict()
