from pyrogram import Client, filters
from pyrogram.types import Message
from datetime import datetime
from pymongo import MongoClient
from config import DATABASE_URI, DATABASE_NAME, COLLECTION_NAME

# Connect to your MongoDB database
mongo_client = MongoClient(DATABASE_URI)
db = mongo_client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

@Client.on_message(filters.command("single") & filters.private)
async def single_index(client: Client, message: Message):
    if not message.reply_to_message or not message.reply_to_message.document:
        return await message.reply("❌ Please reply to a single file to index it.")

    file_msg = message.reply_to_message
    file_id = file_msg.document.file_id
    file_name = file_msg.document.file_name
    chat_id = file_msg.chat.id
    msg_id = file_msg.id

    # Check if file is already indexed
    if collection.find_one({"file_id": file_id}):
        return await message.reply("⚠️ This file is already indexed.")

    collection.insert_one({
        "file_id": file_id,
        "file_name": file_name,
        "chat_id": chat_id,
        "msg_id": msg_id,
        "indexed_by": message.from_user.id,
        "timestamp": datetime.utcnow()
    })

    await message.reply(f"✅ Indexed **{file_name}** from channel `{chat_id}`")

@Client.on_message(filters.command("batch") & filters.private)
async def batch_index(client: Client, message: Message):
    if not message.reply_to_message or not message.reply_to_message.media_group_id:
        return await message.reply("❌ Reply to a grouped message (album) to batch index.")

    chat_id = message.reply_to_message.chat.id
    media_group_id = message.reply_to_message.media_group_id
    indexed = 0

    async for msg in client.get_chat_history(chat_id, limit=100):
        if msg.media_group_id != media_group_id:
            continue
        if msg.document:
            file_id = msg.document.file_id
            file_name = msg.document.file_name

            if not collection.find_one({"file_id": file_id}):
                collection.insert_one({
                    "file_id": file_id,
                    "file_name": file_name,
                    "chat_id": chat_id,
                    "msg_id": msg.id,
                    "indexed_by": message.from_user.id,
                    "timestamp": datetime.utcnow()
                })
                indexed += 1

    await message.reply(f"✅ Indexed `{indexed}` new files from batch.")
