from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
import logging
from database import Database

logger = logging.getLogger(__name__)
db = Database()

def is_admin(func):
    async def wrapper(client: Client, message: Message):
        if message.from_user.id not in Config.ADMIN_IDS:
            await message.reply_text("⚠️ This command is only for administrators.")
            return
        await func(client, message)
    return wrapper

@is_admin
async def handle_broadcast(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("Please provide the message to broadcast.")
        return

    broadcast_message = " ".join(message.command[1:])
    users = await db.get_all_users()
    
    success = 0
    failed = 0
    
    progress_msg = await message.reply_text("Broadcasting message...")
    
    async for user in users:
        try:
            await client.send_message(user["user_id"], broadcast_message)
            success += 1
        except Exception as e:
            logger.error(f"Failed to broadcast to {user['user_id']}: {e}")
            failed += 1
            
        if (success + failed) % 20 == 0:
            await progress_msg.edit_text(
                f"Broadcasting...\n\n"
                f"✅ Success: {success}\n"
                f"❌ Failed: {failed}"
            )
    
    await progress_msg.edit_text(
        f"Broadcast completed!\n\n"
        f"✅ Successfully sent: {success}\n"
        f"❌ Failed: {failed}"
    )

@is_admin
async def handle_ban(client: Client, message: Message):
    if len(message.command) != 2:
        await message.reply_text("Please provide a user ID to ban.")
        return
    
    try:
        user_id = int(message.command[1])
        await db.ban_user(user_id)
        await message.reply_text(f"User {user_id} has been banned.")
    except ValueError:
        await message.reply_text("Invalid user ID.")
    except Exception as e:
        logger.error(f"Error banning user: {e}")
        await message.reply_text("Failed to ban user.")

@is_admin
async def handle_unban(client: Client, message: Message):
    if len(message.command) != 2:
        await message.reply_text("Please provide a user ID to unban.")
        return
    
    try:
        user_id = int(message.command[1])
        await db.unban_user(user_id)
        await message.reply_text(f"User {user_id} has been unbanned.")
    except ValueError:
        await message.reply_text("Invalid user ID.")
    except Exception as e:
        logger.error(f"Error unbanning user: {e}")
        await message.reply_text("Failed to unban user.")