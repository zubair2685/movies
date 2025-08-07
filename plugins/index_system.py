from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import MongoClient
from info import DATABASE_URI, DATABASE_NAME, COLLECTION_NAME

# MongoDB Setup
mongo_client = MongoClient(DATABASE_URI)
db = mongo_client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

# Track user mode
user_mode = {}  # user_id: "single" or "batch"

@Client.on_message(filters.command("single") & filters.private)
async def start_single_index(client, message: Message):
    user_mode[message.from_user.id] = "single"
    await message.reply_text("✅ Single index mode activated.\nNow send the video/file you want to index.")

@Client.on_message(filters.command("batch") & filters.private)
async def start_batch_index(client, message: Message):
    user_mode[message.from_user.id] = "batch"
    await message.reply_text("✅ Batch index mode activated.\nNow send multiple files (one by one) to index.\nSend /done when finished.")

@Client.on_message(filters.command("done") & filters.private)
async def stop_batch_index(client, message: Message):
    user_mode.pop(message.from_user.id, None)
    await message.reply_text("❌ Batch indexing stopped.")

@Client.on_message(filters.private & filters.media)
async def handle_file(client, message: Message):
    user_id = message.from_user.id
    mode = user_mode.get(user_id)

    if mode not in ["single", "batch"]:
        return  # User has not activated indexing mode

    if not message.caption:
        await message.reply_text("⚠️ This file has no caption, skipping.")
        return

    file_data = {
        "file_id": message.id,
        "chat_id": message.chat.id,
        "caption": message.caption,
        "file_type": str(message.media),
    }

    collection.insert_one(file_data)
    await message.reply_text(f"✅ File indexed successfully in {mode} mode.")

    if mode == "single":
        user_mode.pop(user_id, None)
