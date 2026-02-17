import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",")] # "12345,67890" kabi kiritiladi
MONGO_URL = os.getenv("MONGO_URL") # Railwaydagi MongoDB URL
WEBAPP_URL = os.getenv("WEBAPP_URL") # Railway domen
