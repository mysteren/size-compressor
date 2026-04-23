from .adapters.max_bot.client import MaxBotClient


class AppContainer:
    def __init__(self, bot_token: str):
        self.BotClient: MaxBotClient = MaxBotClient(bot_token)
