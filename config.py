import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    API_ID = int(os.getenv("API_ID"))
    API_HASH = os.getenv("API_HASH")
    ADMIN_IDS = [int(id) for id in os.getenv("ADMIN_ID").split()]
    MONGODB_URI = os.getenv("MONGODB_URI")
    DB_NAME = os.getenv("DB_NAME")
    DATABASE_CHANNEL = int(os.getenv("DATABASE_CHANNEL"))
    PORT = int(os.getenv("PORT", "8080"))