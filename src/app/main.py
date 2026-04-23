from .container import AppContainer


def main():

    app_container = AppContainer()
    app_container.BotClient.start()

    print("Привет! Я работаю из src-пакета!")


if __name__ == "__main__":
    main()
