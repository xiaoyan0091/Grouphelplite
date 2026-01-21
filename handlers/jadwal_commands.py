import asyncio
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from utils.jadwal_utils import (
    format_jadwal_lengkap,
    format_rules_message,
    send_jadwal_with_media,
    WIB
)
from config import OWNER_ID
import logging

logger = logging.getLogger(__name__)

user_cooldown = {}
last_jadwal_time = None
last_rules_time = None

# =================== COMMAND HANDLERS ===================
async def jadwal_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_jadwal_time
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    now = datetime.now(WIB)

    # Hanya OWNER yang bisa di PM bot
    if chat_id > 0 and user_id != OWNER_ID:  # chat_id > 0 = private chat
        return

    # Owner tidak perlu anti spam
    if user_id != OWNER_ID:
        # Cek anti spam 20 menit
        if last_jadwal_time:
            time_diff = now - last_jadwal_time
            if time_diff < timedelta(minutes=20):
                minutes_ago = int(time_diff.total_seconds() / 60)
                minutes_left = 20 - minutes_ago

                anti_spam_msg = f"""Anti Spam!
Command Jadwal dapat diakses {minutes_left} menit lagi. Jadwal sudah pernah dikirim {minutes_ago} menit yang lalu, tekan hashtag
#botjadwal"""

                # Tunggu 2 detik lalu hapus pesan command
                await asyncio.sleep(2)
                try:
                    await update.message.delete()
                except Exception as e:
                    logger.warning(f"Delete message error: {e}")

                # Kirim pesan anti spam
                spam_msg = await update.effective_chat.send_message(anti_spam_msg)

                # Hapus pesan anti spam setelah 5 detik
                await asyncio.sleep(5)
                try:
                    await spam_msg.delete()
                except Exception as e:
                    logger.warning(f"Delete spam message error: {e}")

                return

    # Rate limit 5 per menit
    if user_id in user_cooldown:
        if len([t for t in user_cooldown[user_id] if (now-t).seconds < 60]) >= 5:
            return
        user_cooldown[user_id].append(now)
    else:
        user_cooldown[user_id] = [now]

    # Tunggu 2 detik lalu hapus pesan command (hanya di group)
    if chat_id < 0:  # Group chat
        await asyncio.sleep(2)
        try:
            await update.message.delete()
        except Exception as e:
            logger.warning(f"Delete message error: {e}")

    # Update waktu terakhir jadwal dikirim
    last_jadwal_time = now

    # Kirim jadwal dengan foto/video
    try:
        message_text = format_jadwal_lengkap()
        await send_jadwal_with_media(chat_id, context, message_text)
    except Exception as e:
        logger.error(f"Send jadwal error: {e}")

async def rules_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_rules_time
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    now = datetime.now(WIB)

    # Hanya OWNER yang bisa di PM bot
    if chat_id > 0 and user_id != OWNER_ID:  # chat_id > 0 = private chat
        return

    # Owner tidak perlu anti spam
    if user_id != OWNER_ID:
        # Cek anti spam 20 menit
        if last_rules_time:
            time_diff = now - last_rules_time
            if time_diff < timedelta(minutes=20):
                minutes_ago = int(time_diff.total_seconds() / 60)
                minutes_left = 20 - minutes_ago

                anti_spam_msg = f"""Anti Spam!
Command Rules dapat diakses {minutes_left} menit lagi. Rules sudah pernah dikirim {minutes_ago} menit yang lalu, tekan hashtag
#rulesbot"""

                # Tunggu 2 detik lalu hapus pesan command
                await asyncio.sleep(2)
                try:
                    await update.message.delete()
                except Exception as e:
                    logger.warning(f"Delete message error: {e}")

                # Kirim pesan anti spam
                spam_msg = await update.effective_chat.send_message(anti_spam_msg)

                # Hapus pesan anti spam setelah 5 detik
                await asyncio.sleep(5)
                try:
                    await spam_msg.delete()
                except Exception as e:
                    logger.warning(f"Delete spam message error: {e}")

                return

    # Rate limit 5 per menit
    if user_id in user_cooldown:
        if len([t for t in user_cooldown[user_id] if (now-t).seconds < 60]) >= 5:
            return
        user_cooldown[user_id].append(now)
    else:
        user_cooldown[user_id] = [now]

    # Tunggu 2 detik lalu hapus pesan command (hanya di group)
    if chat_id < 0:  # Group chat
        await asyncio.sleep(2)
        try:
            await update.message.delete()
        except Exception as e:
            logger.warning(f"Delete message error: {e}")

    # Update waktu terakhir rules dikirim
    last_rules_time = now

    # Kirim rules
    try:
        rules_msg = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=format_rules_message(),
            parse_mode='HTML',
            disable_web_page_preview=True
        )

        # Hapus pesan rules setelah 10 detik (hanya di group)
        if chat_id < 0:  # Group chat
            await asyncio.sleep(10)
            try:
                await rules_msg.delete()
            except Exception as e:
                logger.warning(f"Delete rules message error: {e}")

    except Exception as e:
        logger.error(f"Send rules message error: {e}")
