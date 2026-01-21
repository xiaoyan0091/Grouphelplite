import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Required configurations (loaded from environment variables)
API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
JADWALBOT_TOKEN = os.getenv("JADWALBOT_TOKEN", "")

# MongoDB Configuration - coba beberapa nama variabel yang umum
MONGO_URI = os.getenv(
    "MONGO_URI", 
    os.getenv("MONGODB_URI", "mongodb://localhost:27017")  # fallback
)
DB_NAME = os.getenv("DB_NAME", "Cluster0")

# Debug: Print MongoDB URI untuk memastikan
print(f"🔍 MongoDB URI: {MONGO_URI}")

# Owner and bot details
OWNER_ID = int(os.getenv("OWNER_ID", 0))
BOT_USERNAME = os.getenv("BOT_USERNAME", "NomadeHelpBot")

# Links and visuals
SUPPORT_GROUP = os.getenv("SUPPORT_GROUP", "https://t.me/LearningBotsCommunity")
UPDATE_CHANNEL = os.getenv("UPDATE_CHANNEL", "https://t.me/Learning_Bots")
START_IMAGE = os.getenv("START_IMAGE", "https://files.catbox.moe/j2yhce.jpg")
