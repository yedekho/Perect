from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
import logging
from database import Database
import re

logger = logging.getLogger(__name__)
db = Database()

async def check_channel_admin(client: Client, channel_id: int) -> bool:
    try:
        chat_member = await client.get_chat_member(channel_id, "me")
        return chat_member.privileges is not None
    except Exception:
        return False

async def handle_genlink(client: Client, message: Message):
    try:
        if not message.reply_to_message:
            await message.reply_text("Please reply to a file/message to generate a link.")
            return

        forwarded = await message.reply_to_message.forward(Config.DATABASE_CHANNEL)
        file_id = str(forwarded.id)
        await db.add_file(file_id, forwarded.id, message.from_user.id)
        
        share_link = f"https://t.me/{(await client.get_me()).username}?start=file_{file_id}"
        await message.reply_text(
            f"✅ File stored successfully!\n\n📎 Shareable Link: {share_link}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📎 Share Link", url=share_link)
            ]])
        )
    except Exception as e:
        logger.error(f"Error in genlink: {e}")
        await message.reply_text("Failed to generate link. Please try again.")

async def handle_batch(client: Client, message: Message):
    try:
        # Initial state
        user_data = await db.get_user_state(message.from_user.id)
        if not user_data.get("batch_mode"):
            await message.reply_text(
                "Forward The Batch First Message From your Batch Channel "
                "(With Forward Tag).. or Give Me Batch First Message link"
            )
            await db.set_user_state(message.from_user.id, {"batch_mode": "waiting_first"})
            return

        if user_data["batch_mode"] == "waiting_first":
            # Extract channel ID and message ID from forwarded message or link
            channel_id, start_id = await extract_message_info(client, message)
            if not channel_id:
                await message.reply_text("Invalid message or link. Please try again.")
                return

            # Check if bot is admin
            if not await check_channel_admin(client, channel_id):
                await message.reply_text("I am not admin in this channel. Please make me admin first.")
                await db.reset_user_state(message.from_user.id)
                return

            await db.set_user_state(message.from_user.id, {
                "batch_mode": "waiting_last",
                "channel_id": channel_id,
                "start_id": start_id
            })
            await message.reply_text(
                "Now Forward The Batch Last Message From Your Batch Channel "
                "(With Forward Tag).. or Give Me Batch last message link"
            )
            return

        if user_data["batch_mode"] == "waiting_last":
            channel_id, end_id = await extract_message_info(client, message)
            if channel_id != user_data["channel_id"]:
                await message.reply_text("Both messages must be from the same channel.")
                return

            status_msg = await message.reply_text("Processing batch... 0%")
            
            # Process messages in batches
            start_id = min(user_data["start_id"], end_id)
            end_id = max(user_data["start_id"], end_id)
            
            batch_files = []
            for msg_id in range(start_id, end_id + 1):
                try:
                    msg = await client.get_messages(channel_id, msg_id)
                    if msg.media:
                        forwarded = await msg.forward(Config.DATABASE_CHANNEL)
                        batch_files.append(str(forwarded.id))
                        
                        # Update progress
                        progress = ((msg_id - start_id + 1) / (end_id - start_id + 1)) * 100
                        await status_msg.edit_text(f"Processing batch... {progress:.1f}%")
                except Exception as e:
                    logger.error(f"Error processing message {msg_id}: {e}")

            # Create batch entry and generate link
            batch_id = await db.create_batch(message.from_user.id, batch_files)
            share_link = f"https://t.me/{(await client.get_me()).username}?start=batch_{batch_id}"
            
            await status_msg.edit_text(
                f"✅ Batch processed successfully!\n\n"
                f"📎 Total files: {len(batch_files)}\n"
                f"🔗 Batch Link: {share_link}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📎 Share Batch Link", url=share_link)
                ]])
            )
            
            await db.reset_user_state(message.from_user.id)

    except Exception as e:
        logger.error(f"Error in batch: {e}")
        await message.reply_text("An error occurred. Please try again.")
        await db.reset_user_state(message.from_user.id)

async def extract_message_info(client: Client, message: Message):
    if message.forward_from_chat:
        return message.forward_from_chat.id, message.forward_from_message_id
    
    # Try to extract from link
    if message.text:
        match = re.match(r"https?://t\.me/([^/]+)/(\d+)", message.text)
        if match:
            channel_username, msg_id = match.groups()
            try:
                chat = await client.get_chat(channel_username)
                return chat.id, int(msg_id)
            except Exception:
                pass
    return None, None