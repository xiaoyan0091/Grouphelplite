import motor.motor_asyncio
import datetime  # <-- TAMBAHKAN INI
from config import MONGO_URI, DB_NAME
import logging

# setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s - %(message)s'
)

# Inisialisasi variabel
db = None
client = None

try:
    logging.info(f"🔄 Connecting to MongoDB: {MONGO_URI}")
    
    # Gunakan timeout yang lebih pendek untuk testing
    client = motor.motor_asyncio.AsyncIOMotorClient(
        MONGO_URI,
        serverSelectionTimeoutMS=10000,  # 10 detik timeout
        connectTimeoutMS=10000
    )
    
    # Test koneksi
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Ping database untuk test koneksi
    loop.run_until_complete(client.admin.command('ping'))
    
    db = client[DB_NAME]
    logging.info(f"✅ MongoDB connected successfully to database: {DB_NAME}")
    
except Exception as e:
    logging.error(f"❌ Failed to connect to MongoDB: {e}")
    logging.warning("⚠️  Creating dummy database objects")
    # Buat objek dummy jika koneksi gagal
    db = None
    client = None

# ==========================================================
# 🟢 WELCOME MESSAGE SYSTEM
# ==========================================================

async def set_welcome_message(chat_id, text: str):
    if db is None:
        return
    try:
        await db.welcome.update_one(
            {"chat_id": chat_id},
            {"$set": {"message": text}},
            upsert=True
        )
    except Exception as e:
        logging.error(f"Error setting welcome message: {e}")

async def get_welcome_message(chat_id):
    if db is None:
        return None
    try:
        data = await db.welcome.find_one({"chat_id": chat_id})
        return data.get("message") if data else None
    except:
        return None

async def set_welcome_status(chat_id, status: bool):
    if db is None:
        return
    try:
        await db.welcome.update_one(
            {"chat_id": chat_id},
            {"$set": {"enabled": status}},
            upsert=True
        )
    except Exception as e:
        logging.error(f"Error setting welcome status: {e}")

async def get_welcome_status(chat_id) -> bool:
    if db is None:
        return True
    try:
        data = await db.welcome.find_one({"chat_id": chat_id})
        if not data:  # default ON
            return True
        return bool(data.get("enabled", True))
    except:
        return True

# ==========================================================
# 🔒 LOCK SYSTEM
# ==========================================================

async def set_lock(chat_id, lock_type, status: bool):
    if db is None:
        return
    try:
        await db.locks.update_one(
            {"chat_id": chat_id},
            {"$set": {f"locks.{lock_type}": status}},
            upsert=True
        )
    except Exception as e:
        logging.error(f"Error setting lock: {e}")

async def get_locks(chat_id):
    if db is None:
        return {}
    try:
        data = await db.locks.find_one({"chat_id": chat_id})
        return data.get("locks", {}) if data else {}
    except:
        return {}

# ==========================================================
# ⚠️ WARN SYSTEM
# ==========================================================

async def add_warn(chat_id: int, user_id: int) -> int:
    if db is None:
        return 0
    try:
        data = await db.warns.find_one({"chat_id": chat_id, "user_id": user_id})
        warns = data.get("count", 0) + 1 if data else 1
        await db.warns.update_one(
            {"chat_id": chat_id, "user_id": user_id},
            {"$set": {"count": warns}},
            upsert=True
        )
        return warns
    except Exception as e:
        logging.error(f"Error adding warn: {e}")
        return 0

async def get_warns(chat_id: int, user_id: int) -> int:
    if db is None:
        return 0
    try:
        data = await db.warns.find_one({"chat_id": chat_id, "user_id": user_id})
        return data.get("count", 0) if data else 0
    except:
        return 0

async def reset_warns(chat_id: int, user_id: int):
    if db is None:
        return
    try:
        await db.warns.update_one(
            {"chat_id": chat_id, "user_id": user_id},
            {"$set": {"count": 0}},
            upsert=True
        )
    except Exception as e:
        logging.error(f"Error resetting warns: {e}")

# ==========================================================
# 👤 USER SYSTEM (for broadcast)
# ==========================================================

async def add_user(user_id, first_name):
    if db is None:
        logging.info(f"📝 Would save user {user_id} ({first_name}) but db is not connected")
        return
    try:
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"first_name": first_name, "added_at": datetime.datetime.now()}},
            upsert=True
        )
        logging.info(f"✅ User saved to database: {user_id}")
    except Exception as e:
        logging.error(f"❌ Error adding user: {e}")

async def get_all_users():
    if db is None:
        return []
    try:
        cursor = db.users.find({}, {"_id": 0, "user_id": 1})
        users = []
        async for document in cursor:
            if "user_id" in document:
                users.append(document["user_id"])
        return users
    except:
        return []

# ==========================================================
# 🧹 CLEANUP UTILS (Optional)
# ==========================================================

async def clear_group_data(chat_id: int):
    if db is None:
        return
    try:
        await db.welcome.delete_one({"chat_id": chat_id})
        await db.locks.delete_one({"chat_id": chat_id})
        await db.warns.delete_many({"chat_id": chat_id})
    except Exception as e:
        logging.error(f"Error clearing group data: {e}")

# ==========================================================
# EKSPOR VARIABEL
# ==========================================================
__all__ = ['db', 'client']
