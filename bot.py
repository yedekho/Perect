import asyncio
import logging
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from database import Database
from handlers.file_handlers import handle_genlink, handle_batch
from handlers.admin_handlers import handle_broadcast, handle_ban, handle_unban
from handlers.clone_handlers import handle_clone_callback, handle_add_clone, handle_bot_token

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class FileStoreBot:
    def __init__(self):
        self.app = Client(
            "FileStoreBot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN
        )
        self.db = Database()
        self.setup_handlers()

    def setup_handlers(self):
        # Command handlers
        self.app.on_message(filters.command("start"))(self.start_command)
        self.app.on_message(filters.command("genlink"))(handle_genlink)
        self.app.on_message(filters.command("batch"))(handle_batch)
        self.app.on_message(filters.command("broadcast"))(handle_broadcast)
        self.app.on_message(filters.command("ban"))(handle_ban)
        self.app.on_message(filters.command("unban"))(handle_unban)
        
        # Callback handlers
        self.app.on_callback_query(filters.regex("help"))(self.help_callback)
        self.app.on_callback_query(filters.regex("about"))(self.about_callback)
        self.app.on_callback_query(filters.regex("clone"))(handle_clone_callback)
        self.app.on_callback_query(filters.regex("add_clone"))(handle_add_clone)
        self.app.on_callback_query(filters.regex("start"))(self.start_callback)
        
        # State handlers
        self.app.on_message(filters.private & filters.text)(self.handle_states)

    async def start_command(self, client, message):
        try:
            await self.db.add_user(message.from_user.id, message.from_user.username)
            
            if len(message.command) > 1:
                arg = message.command[1]
                if arg.startswith("file_"):
                    file_id = arg.split("_")[1]
                    msg = await client.get_messages(Config.DATABASE_CHANNEL, int(file_id))
                    await msg.copy(message.chat.id)
                    await self.db.increment_file_access(file_id)
                    return
                elif arg.startswith("batch_"):
                    batch_id = arg.split("_")[1]
                    batch = await self.db.get_batch(batch_id)
                    if batch:
                        for file_id in batch["file_ids"]:
                            msg = await client.get_messages(Config.DATABASE_CHANNEL, int(file_id))
                            await msg.copy(message.chat.id)
                    return

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Help", callback_data="help"),
                 InlineKeyboardButton("About", callback_data="about")],
                [InlineKeyboardButton("CREATE MY OWN CLONE", callback_data="clone")],
                [InlineKeyboardButton("Update Channel", url="https://t.me/your_channel")]
            ])

            await message.reply_text(
                "🚀 Build Your Own File Store Bot with @juststoreitbot\n\n"
                "No coding needed! Get a powerful, feature-packed bot to store, "
                "share, and manage your files with ease. From custom access controls "
                "and batch uploads to real-time stats and 24/7 availability—this bot has it all.\n\n"
                "Need more? You can even request additional features to make it truly your own!\n\n"
                "👉 Click here to read the full list of features and get started!",
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            await message.reply_text("An error occurred. Please try again later.")

    async def help_callback(self, client, callback_query):
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("Back", callback_data="start")
        ]])
        
        help_text = """✨ Help Menu

I am a permanent file store bot. You can store files from your public channel without me being admin in there. If your channel or group is private, first make me admin in there. Then you can store your files using the commands below and access stored files using the shareable link I provide.

📚 Available Commands:
➛ /start - Check if I am alive.
➛ /genlink - To store a single message or file.
➛ /batch - To store multiple messages from a channel.
➛ /custom_batch - To store multiple random messages.
➛ /shortener - To shorten any shareable links.
➛ /settings - Customize your settings as needed.
➛ /broadcast - Broadcast messages to users (moderators only).
➛ /ban - Ban a user (moderators only).
➛ /unban - Unban a user (moderators only)."""

        await callback_query.message.edit_text(help_text, reply_markup=keyboard)

    async def about_callback(self, client, callback_query):
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("Back", callback_data="start")
        ]])
        
        about_text = """✨ ᴀʙᴏᴜᴛ ᴍᴇ

✰ ᴍʏ ɴᴀᴍᴇ: ꜰɪʟᴇ sᴛᴏʀᴇ ʙᴏᴛ
✰ ᴍʏ ᴏᴡɴᴇʀ: Crazy Developer
✰ ᴜᴘᴅᴀᴛᴇs: Crazy
✰ sᴜᴘᴘᴏʀᴛ: Crazy
✰ ᴠᴇʀsɪᴏɴ: 0.7.9"""

        await callback_query.message.edit_text(about_text, reply_markup=keyboard)

    async def start_callback(self, client, callback_query):
        await self.start_command(client, callback_query.message)

    async def handle_states(self, client, message):
        user_state = await self.db.get_user_state(message.from_user.id)
        
        if user_state.get("clone_mode") == "waiting_token":
            await handle_bot_token(client, message)
            return

    async def start(self):
        try:
            await self.app.start()
            logger.info("Bot started successfully!")
            await self.app.idle()
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
        finally:
            await self.app.stop()

    def run(self):
        asyncio.run(self.start())

if __name__ == "__main__":
    try:
        logger.info("Starting File Store Bot...")
        bot = FileStoreBot()
        bot.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise e