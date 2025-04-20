from os import environ as env
from pydantic import BaseModel, Field, field_validator


class BotConfig(BaseModel):
    token: str = Field(alias="BOT_TOKEN")
    parse_mode: str = Field(alias="BOT_PARSE_MODE")
    max_length: int = Field(alias="BOT_ANSWER_MAX_LENGTH")
    group_id: str = Field(alias="BOT_GROUP_CHAT_ID")
    allowed_users: list[int] = Field(alias="BOT_ALLOWED_USERS")

    @field_validator("allowed_users", mode="before")
    def split_allowed_users(cls, value):
        return [int(user.strip()) for user in value.split(",")] if isinstance(value, str) else value


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
    bot: BotConfig = Field(default_factory=lambda: BotConfig(**env))
    rabbitmq: RabbitMQConfig = Field(default_factory=lambda: RabbitMQConfig(**env))
    redis: RedisConfig = Field(default_factory=lambda: RedisConfig(**env))