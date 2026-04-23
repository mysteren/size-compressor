from .container import AppContainer
from .infrastructure.config import BOT_TOKEN


def main():

    app_container = AppContainer(BOT_TOKEN)
    app_container.BotClient.start()

    print("Привет! Я работаю из src-пакета!")


if __name__ == "__main__":
    main()
