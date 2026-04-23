from app.adapters.max_bot.client import MaxBotClient


class AppContainer:
    def __init__(self):
        self.BotClient = MaxBotClient()
