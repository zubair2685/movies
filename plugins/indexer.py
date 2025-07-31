from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import MongoClient
from info import DATABASE_URI, DATABASE_NAME, COLLECTION_NAME

client = MongoClient(DATABASE_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

@Client.on_message(filters.command("single") & filters.private)
async def index_single_file(bot, message: Message):
    if not message.reply_to_message or not message.reply_to_message.document:
        return await message.reply("Reply to a file with `/single` command.", quote=True)

    doc = message.reply_to_message.document
    file_name = doc.file_name
    file_id = doc.file_id
    file_size = doc.file_size

    data = {
        "file_name": file_name,
        "file_id": file_id,
        "file_size": file_size
    }
    collection.insert_one(data)
    await message.reply(f"✅ Indexed: `{file_name}`")

@Client.on_message(filters.command("batch") & filters.private)
async def index_batch_files(bot, message: Message):
    if not message.reply_to_message or not message.reply_to_message.media_group_id:
        return await message.reply("Reply to an album with `/batch` command.", quote=True)

    media_group_id = message.reply_to_message.media_group_id
    async for msg in bot.search_messages(chat_id=message.chat.id, filter="document"):
        if msg.media_group_id == media_group_id:
            doc = msg.document
            file_name = doc.file_name
            file_id = doc.file_id
            file_size = doc.file_size

            data = {
                "file_name": file_name,
                "file_id": file_id,
                "file_size": file_size
            }
            collection.insert_one(data)

    await message.reply("✅ All files in the batch have been indexed.")
