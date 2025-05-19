from os import environ as env

from pydantic import BaseModel, Field


class BertConfig(BaseModel):
    base_path: str = Field(alias="BERT_BASE_PATH")
    model_name: str = Field(alias="BERT_MODEL_NAME")
    threshold: float = Field(alias="BERT_THRESHOLD")
    query_instruction: str = Field(alias="BERT_QUERY_INSTRUCTION")
    document_instruction: str = Field(alias="BERT_DOCUMENT_INSTRUCTION")


class RedisConfig(BaseModel):
    host: str = Field(alias="REDIS_HOST")
    port: int = Field(alias="REDIS_PORT")
    password: str = Field(alias="REDIS_PASSWORD")
    db: int = Field(alias="REDIS_DB")


class RabbitMQConfig(BaseModel):
    host: str = Field(alias='RABBITMQ_HOST')
    port: int = Field(alias='RABBITMQ_PORT')
    login: str = Field(alias='RABBITMQ_USER')
    password: str = Field(alias='RABBITMQ_PASSWORD')
    vhost: str = Field(alias='RABBITMQ_VHOST')


class Config(BaseModel):
    redis: RedisConfig = Field(default_factory=lambda: RedisConfig(**env))
    bert: BertConfig = Field(default_factory=lambda: BertConfig(**env))
    rabbitmq: RabbitMQConfig = Field(default_factory=lambda: RabbitMQConfig(**env))