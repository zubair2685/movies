from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import MongoClient
from info import DATABASE_URI, DATABASE_NAME, COLLECTION_NAME

# MongoDB setup
mongo_client = MongoClient(DATABASE_URI)
db = mongo_client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

# Track user modes
index_mode = {}  # user_id: "single" or "batch"

@Client.on_message(filters.command("single") & filters.private)
async def start_single_mode(bot, message: Message):
    user_id = message.from_user.id
    index_mode[user_id] = "single"
    await message.reply("📥 Now send **1 file** to index.\nSend /cancel to stop.")

@Client.on_message(filters.command("batch") & filters.private)
async def start_batch_mode(bot, message: Message):
    user_id = message.from_user.id
    index_mode[user_id] = "batch"
    await message.reply("📥 Batch mode started.\nSend multiple files one-by-one.\nSend /cancel to stop.")

@Client.on_message(filters.command("cancel") & filters.private)
async def cancel_mode(bot, message: Message):
    user_id = message.from_user.id
    if user_id in index_mode:
        del index_mode[user_id]
        await message.reply("❌ Indexing cancelled.")
    else:
        await message.reply("⚠️ You are not in indexing mode.")

@Client.on_message(filters.private & (filters.document | filters.video | filters.audio))
async def handle_file(bot, message: Message):
    user_id = message.from_user.id
    if user_id not in index_mode:
        return  # Not in indexing mode

    media = message.document or message.video or message.audio
    if not media:
        return await message.reply("❌ Unsupported media type.")

    file_name = media.file_name or "Unnamed File"
    file_id = media.file_id
    file_size = media.file_size

    data = {
        "file_name": file_name,
        "file_id": file_id,
        "file_size": file_size
    }
    collection.insert_one(data)
    await message.reply(f"✅ Indexed: `{file_name}`")

    # If single mode, exit after 1 file
    if index_mode[user_id] == "single":
        del index_mode[user_id]
        await message.reply("ℹ️ Single file indexing done. Send /single again to index another.")
