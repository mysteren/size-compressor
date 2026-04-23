import os

from dotenv import load_dotenv

# Загружаем переменные из файла .env в окружение (os.environ)
# Если .env отсутствует, функция ничего не сделает (ошибки не будет)
_ = load_dotenv()

# Читаем нужные переменные
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Хорошая практика: проверять, загрузилась ли обязательная переменная
if not BOT_TOKEN:
    raise ValueError(
        "❌ Переменная окружения BOT_TOKEN не найдена! Укажи её в .env файле."
    )
