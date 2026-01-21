import json
import logging
from datetime import datetime
import pytz
import requests
from functools import lru_cache
import math
from telegram import InlineKeyboardButton

# =================== SETUP ===================
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Timezone WIB
WIB = pytz.timezone('Asia/Jakarta')

# Data storage
jadwal_data = {
    "harian": {"Senin":[],"Selasa":[],"Rabu":[],"Kamis":[],"Jumat":[],"Sabtu":[],"Minggu":[]},
    "upcoming": [],
    "channels": [],  # List channel/group untuk auto post bergiliran
    "post_time": "06:00",
    "auto_post_enabled": False,
    "telegraph_token": "",
    "telegraph_url": "",
    "rules_text": "",  # Rules text dengan support HTML
    "media_jadwal": {  # Media untuk setiap hari
        "Senin": {"type": "", "url": ""},
        "Selasa": {"type": "", "url": ""},
        "Rabu": {"type": "", "url": ""},
        "Kamis": {"type": "", "url": ""},
        "Jumat": {"type": "", "url": ""},
        "Sabtu": {"type": "", "url": ""},
        "Minggu": {"type": "", "url": ""}
    }
}

# =================== CACHE ===================
def get_today():
    """Selalu ambil hari terbaru berdasarkan timezone WIB"""
    now = datetime.now(WIB)
    days = {
        "Monday": "Senin",
        "Tuesday": "Selasa",
        "Wednesday": "Rabu",
        "Thursday": "Kamis",
        "Friday": "Jumat",
        "Saturday": "Sabtu",
        "Sunday": "Minggu"
    }
    english_day = now.strftime("%A")
    return days[english_day]

@lru_cache(maxsize=64)
def cached_format_time(hour, minute):
    """Cache format waktu"""
    return f"{hour:02d}:{minute:02d}"

# =================== TELEGRAPH FUNCTIONS ===================
def create_telegraph_account():
    """Buat akun Telegraph baru"""
    try:
        url = "https://api.telegra.ph/createAccount"
        data = {
            "short_name": "JadwalDonghua",
            "author_name": "Jadwal Donghua Bot",
            "author_url": "https://t.me/AnimeStreamingID"
        }
        response = requests.post(url, json=data, timeout=15)

        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                return result['result']['access_token']
    except Exception as e:
        logger.error(f"Telegraph account creation error: {e}")
    return None

def create_telegraph_page(token, title, content):
    """Buat/Update halaman Telegraph"""
    try:
        url = "https://api.telegra.ph/createPage"
        data = {
            "access_token": token,
            "title": title,
            "content": content,
            "return_content": False
        }
        response = requests.post(url, json=data, timeout=15)

        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                return result['result']['url']
    except Exception as e:
        logger.error(f"Telegraph page creation error: {e}")
    return None

def update_telegraph_page(token, path, title, content):
    """Update halaman Telegraph yang sudah ada"""
    try:
        url = f"https://api.telegra.ph/editPage/{path}"
        data = {
            "access_token": token,
            "title": title,
            "content": content,
            "return_content": False
        }
        response = requests.post(url, json=data, timeout=15)

        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                return result['result']['url']
    except Exception as e:
        logger.error(f"Telegraph page update error: {e}")
    return None

def generate_telegraph_content():
    """Generate konten Telegraph pakai HTML tags terstruktur"""
    now = datetime.now(WIB)
    today = get_today()

    bulan_indo = {
        1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
        7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember"
    }

    date = now.day
    month = bulan_indo[now.month]
    year = now.year
    update_time = now.strftime("%H:%M")

    content = []

    # Header dengan HTML br
    content.append({
        "tag": "p",
        "children": [f"Pembaruan pada {today}, {date} {month} {year} pukul {update_time} WIB"]
    })

    # BR tags untuk spasi
    content.append({"tag": "br"})
    content.append({"tag": "br"})

    for hari in ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]:
        if jadwal_data["harian"][hari]:
            # Nama hari
            content.append({
                "tag": "p",
                "children": [{"tag": "strong", "children": [hari]}]
            })

            # List anime
            for i, anime in enumerate(jadwal_data["harian"][hari], 1):
                if isinstance(anime, dict):
                    # Anime dengan link
                    content.append({
                        "tag": "p",
                        "children": [
                            f"   {i}. ",
                            {"tag": "a", "attrs": {"href": anime["link"]}, "children": [anime["judul"]]}
                        ]
                    })
                else:
                    # Anime tanpa link (string biasa)
                    content.append({
                        "tag": "p",
                        "children": [f"   {i}. {anime}"]
                    })

            # Spasi antar hari - double BR
            content.append({"tag": "br"})
            content.append({"tag": "br"})

    return content

def update_telegraph():
    """Update halaman Telegraph dengan jadwal terbaru"""
    if not jadwal_data.get("telegraph_token"):
        return False

    title = "Jadwal Donghua CA3D "
    content = generate_telegraph_content()

    if jadwal_data.get("telegraph_url"):
        # Update existing page
        try:
            path = jadwal_data["telegraph_url"].split("/")[-1]
            url = update_telegraph_page(jadwal_data["telegraph_token"], path, title, content)
            if url:
                jadwal_data["telegraph_url"] = url
                save_data()
                return True
        except Exception as e:
            logger.error(f"Telegraph update error: {e}")

    # Create new page jika update gagal
    url = create_telegraph_page(jadwal_data["telegraph_token"], title, content)
    if url:
        jadwal_data["telegraph_url"] = url
        save_data()
        return True

    return False

# =================== FUNGSI HELPER ===================
def save_data():
    try:
        with open("jadwal.json", "w", encoding="utf-8") as f:
            json.dump(jadwal_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Save data error: {e}")

def load_data():
    global jadwal_data
    try:
        with open("jadwal.json", "r", encoding="utf-8") as f:
            loaded = json.load(f)
            jadwal_data.update(loaded)
            # Migrate old channel_id to channels list
            if "channel_id" in jadwal_data and jadwal_data["channel_id"] and jadwal_data["channel_id"] not in jadwal_data.get("channels", []):
                if not jadwal_data.get("channels"):
                    jadwal_data["channels"] = []
                jadwal_data["channels"].append(jadwal_data["channel_id"])
                del jadwal_data["channel_id"]
                save_data()
            # Migrate old foto/video to media_jadwal
            if "jadwal_foto" in jadwal_data or "jadwal_video" in jadwal_data:
                if not jadwal_data.get("media_jadwal"):
                    jadwal_data["media_jadwal"] = {
                        "Senin": {"type": "", "url": ""},
                        "Selasa": {"type": "", "url": ""},
                        "Rabu": {"type": "", "url": ""},
                        "Kamis": {"type": "", "url": ""},
                        "Jumat": {"type": "", "url": ""},
                        "Sabtu": {"type": "", "url": ""},
                        "Minggu": {"type": "", "url": ""}
                    }
                # Hapus old fields
                if "jadwal_foto" in jadwal_data:
                    del jadwal_data["jadwal_foto"]
                if "jadwal_video" in jadwal_data:
                    del jadwal_data["jadwal_video"]
                save_data()
            # Ensure all fields exist
            if "rules_text" not in jadwal_data:
                jadwal_data["rules_text"] = ""
            if "media_jadwal" not in jadwal_data:
                jadwal_data["media_jadwal"] = {
                    "Senin": {"type": "", "url": ""},
                    "Selasa": {"type": "", "url": ""},
                    "Rabu": {"type": "", "url": ""},
                    "Kamis": {"type": "", "url": ""},
                    "Jumat": {"type": "", "url": ""},
                    "Sabtu": {"type": "", "url": ""},
                    "Minggu": {"type": "", "url": ""}
                }
            save_data()
    except Exception as e:
        logger.error(f"Load data error: {e}")
        save_data()

def get_media_for_today():
    """Ambil media untuk hari ini"""
    today = get_today()
    return jadwal_data.get("media_jadwal", {}).get(today, {"type": "", "url": ""})

def format_jadwal_hari_ini():
    """Format jadwal PERSIS seperti di foto contoh"""
    today = get_today()

    # Header dengan format persis seperti foto
    msg = f"<b>Jadwal Donghua Hari Ini :</b>\n"

    # Jadwal harian
    if jadwal_data["harian"][today]:
        for i, anime in enumerate(jadwal_data["harian"][today], 1):
            if isinstance(anime, dict):
                # Anime dengan link - tampilkan sebagai hyperlink
                msg += f"  {i}. <a href=\"{anime['link']}\">{anime['judul']}</a>\n"
            else:
                # Anime tanpa link
                msg += f"  {i}. {anime}\n"
    else:
        msg += "❌ <i>Tidak ada jadwal donghua hari ini dalam waktu dekat</i>\n"

    # Upcoming section dengan format blockquote seperti di foto
    msg += "\n<b>Upcoming Donghua :\n</b>"

    if jadwal_data["upcoming"]:
        for i, up in enumerate(jadwal_data["upcoming"], 1):
            # Format blockquote hijau seperti di foto dengan format yang diperbaiki
            msg += f'<blockquote>{i}. <b>{up["judul"]}</b>'
            if up.get("season"):
                msg += f'[Season {up["season"]}]'

            # Cek apakah ada link atau tidak
            if up.get("link"):
                msg += f'\n({up["hari"]}, {up["tanggal"]}) (<a href="{up["link"]}">PV</a>)</blockquote>\n'
            else:
                msg += f'\n({up["hari"]}, {up["tanggal"]})</blockquote>\n'
    else:
        msg += "<blockquote>Belum ada donghua dalam waktu dekat</blockquote>\n\n"

    # Footer dengan link Telegraph
    if jadwal_data.get("telegraph_url"):
        msg += f'<a href="{jadwal_data["telegraph_url"]}"><b>Jadwal Donghua Semua Hari</b></a>\n#botjadwal'
    else:
        msg += "<b>Jadwal Donghua Semua Hari</b>\n#botjadwal"

    return msg

def format_jadwal_lengkap():
    """Format jadwal lengkap untuk command /jadwal"""
    today = get_today()

    # Header
    msg = f"<b>Jadwal Donghua Hari Ini :</b>\n"

    # Jadwal hari ini
    if jadwal_data["harian"][today]:
        for i, anime in enumerate(jadwal_data["harian"][today], 1):
            if isinstance(anime, dict):
                # Anime dengan link - tampilkan sebagai hyperlink
                msg += f" {i}. <a href=\"{anime['link']}\">{anime['judul']}</a>\n"
            else:
                # Anime tanpa link
                msg += f" {i}. {anime}\n"
    else:
        msg += "Tidak ada jadwal hari ini\n"

    # Upcoming section
    msg += "\n<b>Upcoming Donghua :\n</b>"

    if jadwal_data["upcoming"]:
        for i, up in enumerate(jadwal_data["upcoming"], 1):
            msg += f'<blockquote>{i}. <b>{up["judul"]}</b>'
            if up.get("season"):
                msg += f'[Season {up["season"]}]'

            # Cek apakah ada link atau tidak
            if up.get("link"):
                msg += f'\n({up["hari"]}, {up["tanggal"]}) (<a href="{up["link"]}">PV</a>)</blockquote>\n'
            else:
                msg += f'\n({up["hari"]}, {up["tanggal"]})</blockquote>\n'
    else:
        msg += "<blockquote> Belum ada donghua dalam waktu dekat </blockquote>\n\n"

    # Footer dengan link Telegraph
    if jadwal_data.get("telegraph_url"):
        msg += f'<a href="{jadwal_data["telegraph_url"]}"><b>Jadwal Donghua Semua Hari</b></a>\n#botjadwal'
    else:
        msg += "<b>Jadwal Donghua Semua Hari</b>\n#botjadwal"

    return msg

def format_rules_message():
    """Format pesan rules dengan hashtag"""
    if not jadwal_data.get("rules_text"):
        return "❌ <i>Rules belum diset oleh admin</i>\n\n#rulesbot"

    return f"{jadwal_data['rules_text']}\n\n#rulesbot"

async def send_jadwal_with_media(chat_id, context, message_text):
    """Send jadwal dengan foto/video/GIF sesuai hari"""
    try:
        # Ambil media untuk hari ini
        today_media = get_media_for_today()

        if today_media["url"] and today_media["type"]:
            if today_media["type"] == "video":
                # Send as video/animation
                await context.bot.send_video(
                    chat_id=chat_id,
                    video=today_media["url"],
                    caption=message_text,
                    parse_mode='HTML',
                    has_spoiler=False
                )
            elif today_media["type"] == "photo":
                # Send as photo
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=today_media["url"],
                    caption=message_text,
                    parse_mode='HTML'
                )
        else:
            # Send as text only
            await context.bot.send_message(
                chat_id=chat_id,
                text=message_text,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
    except Exception as e:
        logger.error(f"Send media error: {e}")
        # Fallback to text
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=message_text,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
        except Exception as fallback_error:
            logger.error(f"Send text fallback error: {fallback_error}")

def get_all_schedule_items():
    """Dapatkan semua item jadwal (harian + upcoming) dengan indexing"""
    items = []

    # Jadwal harian
    for hari in ["Senin","Selasa","Rabu","Kamis","Jumat","Sabtu","Minggu"]:
        for anime in jadwal_data["harian"][hari]:
            if isinstance(anime, dict):
                display_text = f"{anime['judul']} ({hari})"
                items.append({
                    'type': 'harian',
                    'text': display_text,
                    'hari': hari,
                    'anime': anime,
                    'hash': hash(anime['judul']) % 1000
                })
            else:
                items.append({
                    'type': 'harian',
                    'text': f"{anime} ({hari})",
                    'hari': hari,
                    'anime': anime,
                    'hash': hash(anime) % 1000
                })

    # Upcoming
    for i, up in enumerate(jadwal_data["upcoming"]):
        items.append({
            'type': 'upcoming',
            'text': f"{up['judul']} (Upcoming)",
            'index': i,
            'data': up
        })

    return items

def generate_delete_keyboard(page=1, items_per_page=10):
    """Generate keyboard dengan pagination 2 kolom, 5 baris"""
    all_items = get_all_schedule_items()
    total_items = len(all_items)
    total_pages = math.ceil(total_items / items_per_page)

    if total_pages == 0:
        return [[InlineKeyboardButton("Belum ada jadwal", callback_data="back")], [InlineKeyboardButton("Kembali", callback_data="back")]]

    # Pastikan page dalam range
    page = max(1, min(page, total_pages))

    start_index = (page - 1) * items_per_page
    end_index = min(start_index + items_per_page, total_items)
    current_items = all_items[start_index:end_index]

    keyboard = []

    # Items dalam 2 kolom, maksimal 5 baris (10 items per halaman)
    for i in range(0, len(current_items), 2):
        row = []
        for j in range(2):
            if i + j < len(current_items):
                item = current_items[i + j]
                # Truncate text jika terlalu panjang
                display_text = item['text'][:20] + "..." if len(item['text']) > 20 else item['text']

                if item['type'] == 'harian':
                    callback_data = f"del_h_{item['hari']}_{item['hash']}"
                else:
                    callback_data = f"del_u_{item['index']}"

                row.append(InlineKeyboardButton(f"❌ {display_text}", callback_data=callback_data))

        if row:
            keyboard.append(row)

    # Pagination controls jika lebih dari 1 halaman
    if total_pages > 1:
        pagination_row = []

        # Previous button
        if page > 1:
            pagination_row.append(InlineKeyboardButton("◀️", callback_data=f"del_page_{page-1}"))

        # Page numbers (maksimal 5 angka)
        start_page = max(1, page - 2)
        end_page = min(total_pages, start_page + 4)

        # Adjust start_page jika end_page sudah maksimal
        if end_page - start_page < 4:
            start_page = max(1, end_page - 4)

        for p in range(start_page, end_page + 1):
            if p == page:
                pagination_row.append(InlineKeyboardButton(f"• {p} •", callback_data=f"del_page_{p}"))
            else:
                pagination_row.append(InlineKeyboardButton(str(p), callback_data=f"del_page_{p}"))

        # Next button
        if page < total_pages:
            pagination_row.append(InlineKeyboardButton("▶️", callback_data=f"del_page_{page+1}"))

        keyboard.append(pagination_row)

    # Kembali button
    keyboard.append([InlineKeyboardButton("Kembali", callback_data="back")])

    return keyboard
