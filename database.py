import sqlite3

import aiosqlite

db_name = 'database.db'

async def init_db():
    async with aiosqlite.connect(db_name) as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS search (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                query TEXT NOT NULL,
                min_price INTEGER DEFAULT 0,
                max_price INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1)
        ''')
        await db.execute('''CREATE TABLE IF NOT EXISTS seenitems (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
        ''')
        await db.commit()
async def add_search(user_id: int, query: str, min_price: int = 0, max_price: int = 0):
    async with aiosqlite.connect(db_name) as db:
        await db.execute('''INSERT INTO search (user_id, query, min_price, max_price) VALUES (?, ?, ?, ?)''',
            (user_id, query, min_price, max_price)
        )
        await db.commit()

async def get_searches(user_id: int):
    async with aiosqlite.connect(db_name) as db:
        #print("Connected with db")
        async with db.execute('''SELECT id, query, min_price, max_price FROM search WHERE user_id = ?''', (user_id,)) as cursor:
            return await cursor.fetchall()

async def db_delete_searches(search_id: int, user_id: int):
    async with aiosqlite.connect(db_name) as db:
        async with db.execute('''DELETE FROM search WHERE id = ? and user_id = ?''', (search_id, user_id)) as cursor:
            await db.commit()