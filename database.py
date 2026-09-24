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
        created_at TIMESTAMP NOT NULL)
        ''')
        await db.commit()
async def add_search(user_id: int, query: str, min_price: int = 0, max_price: int = 0):
    async with aiosqlite.connect(db_name) as db:
        await db.execute('''INSERT INTO search (user_id, query, min_price, max_price) VALUES (?, ?, ?, ?)''',
            (user_id, query, min_price, max_price)
        )

async def get_searches(user_id: int):
    async with aiosqlite.connect(db_name) as db:
        async with db.execute('''SELECT * FROM search WHERE user_id = ?''', (user_id,)
        ) as cursor: return await cursor.fetchall()
