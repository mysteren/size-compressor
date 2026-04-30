import asyncio

from .container import AppContainer
from .infrastructure.config import BOT_TOKEN, DB_PATH


def main():

    app = AppContainer(BOT_TOKEN, DB_PATH)
    asyncio.run(app.db.connect())
    asyncio.run(app.max_bot_client.start())
    print("Привет! Я работаю из src-пакета!")


if __name__ == "__main__":
    main()
