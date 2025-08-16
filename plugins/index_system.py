from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import MongoClient
from info import DATABASE_URI, DATABASE_NAME, COLLECTION_NAME

# MongoDB setup
mongo_client = MongoClient(DATABASE_URI)
db = mongo_client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

# Track user modes
user_mode = {}  # user_id: "single" | "batch"


# -------------------- SINGLE INDEX MODE --------------------
@Client.on_message(filters.command("single") & filters.private)
async def single_index_mode(client: Client, message: Message):
    user_mode[message.from_user.id] = "single"
    await message.reply_text("✅ Single index mode ON\nAb ek file bhejo, woh DB me save ho jayegi.")


# -------------------- BATCH INDEX MODE --------------------
@Client.on_message(filters.command("batch") & filters.private)
async def batch_index_mode(client: Client, message: Message):
    user_mode[message.from_user.id] = "batch"
    await message.reply_text("✅ Batch index mode ON\nAb multiple files bhejo, sab DB me save ho jayengi.")


# -------------------- HANDLE FILE SAVING --------------------
@Client.on_message(filters.document | filters.video | filters.audio)
async def save_files(client: Client, message: Message):
    mode = user_mode.get(message.from_user.id)

    if not mode:
        return  # agar mode ON nahi hai to kuch mat karo

    file_id, file_name, file_size, mime_type = None, None, None, None

    if message.document:
        file_id = message.document.file_id
        file_name = message.document.file_name
        file_size = message.document.file_size
        mime_type = message.document.mime_type
    elif message.video:
        file_id = message.video.file_id
        file_name = message.video.file_name
        file_size = message.video.file_size
        mime_type = message.video.mime_type
    elif message.audio:
        file_id = message.audio.file_id
        file_name = message.audio.file_name
        file_size = message.audio.file_size
        mime_type = message.audio.mime_type

    if file_id:
        data = {
            "file_id": file_id,
            "file_name": file_name,
            "file_size": file_size,
            "mime_type": mime_type,
            "mode": mode,
            "indexed_by": message.from_user.id
        }

        # duplicate check
        if collection.find_one({"file_id": file_id}):
            await message.reply_text(f"⚠️ Already in DB:\n**{file_name}**")
            return

        collection.insert_one(data)
        await message.reply_text(f"✅ Saved in DB:\n**{file_name}**")


# -------------------- STOP INDEX MODE --------------------
@Client.on_message(filters.command("stopindex") & filters.private)
async def stop_index_mode(client: Client, message: Message):
    if message.from_user.id in user_mode:
        del user_mode[message.from_user.id]
        await message.reply_text("🛑 Index mode stopped.")
    else:
        await message.reply_text("❌ Aapne koi index mode start hi nahi kiya.")
