from dishka import make_async_container
from dishka.integrations import faststream as faststream_integration
from faststream import FastStream

from sentence_bert.src.config import Config
from sentence_bert.src.controllers.ampq import TasksController
from sentence_bert.src.infrastructure.broker import new_broker
from sentence_bert.src.ioc import AppProvider


config = Config()
container = make_async_container(AppProvider(), context={Config: config})


def get_faststream_app() -> FastStream:
    broker = new_broker(config.rabbitmq)
    app = FastStream(broker)
    faststream_integration.setup_dishka(container, app, auto_inject=True)
    broker.include_router(TasksController)
    return app

app = get_faststream_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)