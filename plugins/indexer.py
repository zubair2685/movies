from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import MongoClient
from info import DATABASE_URI, DATABASE_NAME, COLLECTION_NAME

# MongoDB setup
mongo_client = MongoClient(DATABASE_URI)
db = mongo_client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

# Track user modes (only private chat)
user_mode = {}  # user_id: "single" | "batch" | None

# ------------------------
# Save File (No Duplicate Check)
# ------------------------
def save_file(media):
    """Media ko MongoDB me bina duplicate check ke insert karega"""
    file_info = {
        "file_id": media.file_id,
        "file_name": media.file_name,
        "file_size": media.file_size,
        "mime_type": media.mime_type,
    }
    collection.insert_one(file_info)   # direct insert
    return f"✅ Saved: {media.file_name}"

# ------------------------
# /single command
# ------------------------
@Client.on_message(filters.command("single") & filters.private)
async def single_mode(bot, message: Message):
    user_mode[message.from_user.id] = "single"
    await message.reply("📌 Single Index Mode ON\nAb ek file bhejo.")

# ------------------------
# /batch command
# ------------------------
@Client.on_message(filters.command("batch") & filters.private)
async def batch_mode(bot, message: Message):
    user_mode[message.from_user.id] = "batch"
    await message.reply("📌 Batch Index Mode ON\nMultiple files bhejte raho.")

# ------------------------
# /off command
# ------------------------
@Client.on_message(filters.command("off") & filters.private)
async def off_mode(bot, message: Message):
    user_mode[message.from_user.id] = None
    await message.reply("❌ Index Mode OFF")

# ------------------------
# File handler (manual index)
# ------------------------
@Client.on_message((filters.document | filters.video | filters.audio) & filters.private)
async def index_file(bot, message: Message):
    user_id = message.from_user.id
    mode = user_mode.get(user_id)

    if not mode:  # Mode OFF
        return

    media = message.document or message.video or message.audio
    if not media:
        return

    if mode == "single":
        result = save_file(media)
        await message.reply(result)
        user_mode[user_id] = None  # reset after 1 file

    elif mode == "batch":
        result = save_file(media)
        await message.reply(result)
