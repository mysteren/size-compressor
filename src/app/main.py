import asyncio

from .container import AppContainer
from .infrastructure.config import BOT_TOKEN, DB_PATH


def main():

    app_container = AppContainer(BOT_TOKEN, DB_PATH)
    asyncio.run(app_container.db.connect())
    asyncio.run(app_container.BotClient.start())
    print("Привет! Я работаю из src-пакета!")


if __name__ == "__main__":
    main()
