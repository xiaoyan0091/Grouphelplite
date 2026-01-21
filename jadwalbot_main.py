from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from handlers.jadwal_commands import jadwal_cmd, rules_cmd
from handlers.jadwal_panel import panel_cmd, handle_callbacks, handle_text, handle_media
from utils.jadwal_utils import load_data, jadwal_data, scheduled_daily_post, WIB
from config import JADWALBOT_TOKEN
import logging
from datetime import time

# =================== SETUP ===================
logging.basicConfig(level=logging.INFO)

def main():
    load_data()

    app = Application.builder().token(JADWALBOT_TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("jadwal", jadwal_cmd))
    app.add_handler(CommandHandler("rules", rules_cmd))
    app.add_handler(CommandHandler("panel", panel_cmd))
    app.add_handler(CallbackQueryHandler(handle_callbacks))
    app.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.ANIMATION, handle_media))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Setup jobs with timezone WIB that is defined in jadwal_utils
    if jadwal_data["auto_post_enabled"] and jadwal_data["channels"]:
        try:
            hour, minute = map(int, jadwal_data["post_time"].split(":"))
            # Schedule job for each channel with interval 1 minute
            for i, channel in enumerate(jadwal_data["channels"]):
                post_minute = (minute + i) % 60
                post_hour = hour + (minute + i) // 60
                if post_hour >= 24:
                    post_hour = post_hour % 24

                wib_time = time(post_hour, post_minute, tzinfo=WIB)
                app.job_queue.run_daily(
                    scheduled_daily_post,
                    time=wib_time,
                    name=f'daily_auto_post_{i}',
                    data={'channel': channel, 'index': i}
                )

            print(f"⏰ Jadwalbot auto post jobs scheduled for {len(jadwal_data['channels'])} channels starting at {jadwal_data['post_time']} WIB")

        except Exception as e:
            logging.error(f"Jadwalbot job scheduling error: {e}")
            print(f"❌ Jadwalbot error scheduling jobs: {e}")

    print("🚀 Jadwal Donghua Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
