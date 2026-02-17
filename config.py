import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",")]
MONGO_URL = os.getenv("MONGO_URL")
# Railway variablesga CARD_NUMBER deb qo'shasan
CARD_NUMBER = os.getenv("CARD_NUMBER", "Karta kiritilmagan")
