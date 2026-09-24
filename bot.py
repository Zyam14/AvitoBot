import asyncio
from service import *
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from database import init_db,add_search, get_searches

bot = Bot(API)
dp = Dispatcher()
async def main():
    await init_db()
    print('Database Successfully Initialized!')
    await dp.start_polling(bot)

@dp.message (CommandStart())
async def cmd_start (message: Message):
    await message.answer("Привет! \nЯ твой бот для поиска новинок в Avito \n"
                         "/help - для помощи")

@dp.message (Command('help'))
async def cmd_help(message: Message):
    await message.answer("Возможные команды:\n"
                         "/add - добавить новый поиск\n"
                         "/show_my_searches - показать мои поиски")



class AddSearchGroup(StatesGroup):
    waiting_for_query = State()      # Шаг 1: Ждем название
    waiting_for_min_price = State()  # Шаг 2: Ждем мин. цену
    waiting_for_max_price = State()


@dp.message (Command('add'))
async def cmd_add(message: Message, state: FSMContext):
    await state.set_state(AddSearchGroup.waiting_for_query)
    await message.answer("Введите название товара")

@dp.message (AddSearchGroup.waiting_for_query)
async def process_query(message: Message, state: FSMContext):
    await state.update_data(query=message.text)
    await state.set_state(AddSearchGroup.waiting_for_min_price)
    await message.answer("Введите минимальную цену")

@dp.message (AddSearchGroup.waiting_for_min_price)
async def min_price(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введите число!")
        return
    if int(message.text) < 0:
        await message.answer("Сумма должна быть больше 0!")
        return
    await state.update_data(min_price=int(message.text))
    await state.set_state(AddSearchGroup.waiting_for_max_price)
    await message.answer("Введите максимальную цену или 0")

@dp.message (AddSearchGroup.waiting_for_max_price)
async def max_price(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введите число!")
        return
    max_price = int(message.text)
    if max_price < 0:
        await message.answer('Минимальная цена должна быть >= 0')
        return

    user_data = await state.get_data()
    min_price = user_data.get('min_price')

    if not max_price > min_price or max_price == 0:
        await message.answer(f"Максимальная цена должна быть больше минимальной! > ({min_price}) или =0")
        return

    query = user_data['query']
    min_price = user_data['min_price']
    user_id = message.from_user.id

    await add_search(user_id=user_id, query=query, min_price=min_price, max_price=max_price)

    await message.answer(
        f" Поиск успешно сохранен!\n\n"
        f"{query} ({min_price} - {max_price} руб.)" )
    await state.clear()

@dp.message (Command('show_my_searches'))
async def cmd_show_my_searches(message: Message):
    searches = await get_searches(message.from_user.id)

    if not searches:
        await message.answer('У тебя пока нет поисков')
        return

    text = 'Твои поиски:\n\n'
    for s in searches:
        searche_id, query, min_price, max_price = s
        text+= f"*{searche_id}* {query}  ({min_price}-{max_price})\n"
    await message.answer(text, pase_mode="Markdown")



if __name__ == '__main__':
    asyncio.run(main())