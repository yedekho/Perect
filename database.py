from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from config import Config
from bson import ObjectId

class Database:
    def __init__(self):
        self.client = AsyncIOMotorClient(Config.MONGODB_URI)
        self.db = self.client[Config.DB_NAME]
        self.users = self.db.users
        self.clones = self.db.clones
        self.files = self.db.files
        self.batches = self.db.batches
        self.states = self.db.states

    async def add_user(self, user_id: int, username: str):
        await self.users.update_one(
            {'user_id': user_id},
            {
                '$set': {
                    'username': username,
                    'last_active': datetime.utcnow(),
                    'banned': False
                },
                '$setOnInsert': {
                    'joined_date': datetime.utcnow()
                }
            },
            upsert=True
        )

    async def add_clone(self, user_id: int, username: str, bot_token: str, bot_username: str, bot_id: int):
        return await self.clones.insert_one({
            'user_id': user_id,
            'username': username,
            'bot_token': bot_token,
            'bot_username': bot_username,
            'bot_id': bot_id,
            'created_at': datetime.utcnow(),
            'status': 'pending'
        })

    async def add_file(self, file_id: str, message_id: int, user_id: int):
        return await self.files.insert_one({
            'file_id': file_id,
            'message_id': message_id,
            'user_id': user_id,
            'created_at': datetime.utcnow(),
            'access_count': 0
        })

    async def create_batch(self, user_id: int, file_ids: list):
        result = await self.batches.insert_one({
            'user_id': user_id,
            'file_ids': file_ids,
            'created_at': datetime.utcnow(),
            'access_count': 0
        })
        return str(result.inserted_id)

    async def get_batch(self, batch_id: str):
        return await self.batches.find_one({'_id': ObjectId(batch_id)})

    async def get_user_state(self, user_id: int):
        state = await self.states.find_one({'user_id': user_id})
        return state if state else {}

    async def set_user_state(self, user_id: int, state: dict):
        await self.states.update_one(
            {'user_id': user_id},
            {'$set': {**state, 'updated_at': datetime.utcnow()}},
            upsert=True
        )

    async def reset_user_state(self, user_id: int):
        await self.states.delete_one({'user_id': user_id})

    async def ban_user(self, user_id: int):
        await self.users.update_one(
            {'user_id': user_id},
            {'$set': {'banned': True}}
        )

    async def unban_user(self, user_id: int):
        await self.users.update_one(
            {'user_id': user_id},
            {'$set': {'banned': False}}
        )

    async def get_all_users(self):
        return self.users.find({'banned': False})