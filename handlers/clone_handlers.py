from pyrogram import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import logging
from database import Database
import re

logger = logging.getLogger(__name__)
db = Database()

async def handle_clone_callback(client: Client, callback_query):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Add Clone", callback_data="add_clone")],
        [InlineKeyboardButton("Back", callback_data="start")]
    ])
    
    await callback_query.message.edit_text(
        "✨ Manage Clone's\n\n"
        "You can now manage and create your very own identical clone bot, "
        "mirroring all my awesome features, using the given buttons.",
        reply_markup=keyboard
    )

async def handle_add_clone(client: Client, callback_query):
    await callback_query.message.edit_text(
        "To create your clone:\n\n"
        "1) Create a bot using @BotFather\n"
        "2) Then you will get a message with bot token\n"
        "3) Send that bot token to me",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Back", callback_data="clone")
        ]])
    )
    
    # Set user state to waiting for token
    await db.set_user_state(callback_query.from_user.id, {"clone_mode": "waiting_token"})

async def handle_bot_token(client: Client, message: Message):
    try:
        # Validate bot token format
        if not re.match(r"^\d+:[A-Za-z0-9_-]{35}$", message.text):
            await message.reply_text(
                "Invalid bot token format. Please send a valid bot token."
            )
            return

        # Create test client to validate token and get bot info
        async with Client(
            "test_bot",
            api_id=client.api_id,
            api_hash=client.api_hash,
            bot_token=message.text,
            in_memory=True
        ) as bot:
            bot_info = await bot.get_me()
            
        # Store clone information
        clone_data = await db.add_clone(
            user_id=message.from_user.id,
            username=message.from_user.username,
            bot_token=message.text,
            bot_username=bot_info.username,
            bot_id=bot_info.id
        )
        
        await message.reply_text(
            "✅ Your bot clone has been successfully created!\n\n"
            "⏳ Please wait 24 hours for the clone to be fully operational.\n"
            f"🤖 Your bot: @{bot_info.username}"
        )
        
        # Reset user state
        await db.reset_user_state(message.from_user.id)
        
    except Exception as e:
        logger.error(f"Error creating clone: {e}")
        await message.reply_text(
            "❌ Failed to create clone. Please try again with a valid bot token."
        )
        await db.reset_user_state(message.from_user.id)