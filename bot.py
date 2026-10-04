import asyncio
from service import *
from aiogram import Bot, Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup
from database import init_db,add_search, get_searches, db_delete_searches

bot = Bot(API)
dp = Dispatcher()
async def main():
    await init_db()
    print('Database Successfully Initialized!')
    await dp.start_polling(bot)


main_keyboard= ReplyKeyboardMarkup(
    keyboard=[
        [#KeyboardButton(text="📍 Добавить адрес"),
         KeyboardButton(text='🔍 Мои поиски'),
         KeyboardButton(text="⚙️ Настройки"),
        ]
    ],
    resize_keyboard= True
)

cancel_keyboard= ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="❌ Отмена")]],
    resize_keyboard= True,
)



@dp.message (CommandStart())
async def cmd_start (message: Message):
    await message.answer("Привет! \nЯ твой бот для поиска новинок в Avito \n", reply_markup=main_keyboard)

@dp.message (F.text == '🛟 Помощь')
async def cmd_help(message: Message):
    await message.answer("Возможные команды:\n"
                         "/add - добавить новый поиск\n"
                         "/show_my_searches - показать мои поиски")



class AddSearchGroup(StatesGroup):
    waiting_for_query = State()      # Шаг 1: Ждем название
    waiting_for_min_price = State()  # Шаг 2: Ждем мин. цену
    waiting_for_max_price = State()



@dp.message(F.text=="❌ Отмена" )
async def cancel(message: Message, state:FSMContext):
    await state.clear()
    await message.answer("Действие отменено успешно!", reply_markup=main_keyboard)

@dp.callback_query (F.data == 'add')
async def cmd_add(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddSearchGroup.waiting_for_query)
    await callback.message.answer("Введите название товара",reply_markup=cancel_keyboard)

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
        f"{query} ({min_price} - {max_price} руб.)\n"
         ,reply_markup=main_keyboard)
    await state.clear()


editing_keyboard= InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text='➕ Добавить поиск', callback_data='add')],
                        [InlineKeyboardButton(text='➖ Удалить', callback_data='edit')]
                     ]
)

class EditSearchGroup(StatesGroup):
    editing = State()

@dp.message (F.text == '🔍 Мои поиски')
async def cmd_show_my_searches(message: Message):
    searches = await get_searches(message.chat.id)

    if not searches:
        text = 'У тебя пока нет поисков\n'
    else:
        text = 'Твои поиски:\n\n'
    i = 1
    for s in searches:
        searche_id, query, min_price, max_price = s
        text+= f"**{i}**.  {query} ({min_price} - {max_price}) \n"
        i+=1
    await message.answer(text,reply_markup=editing_keyboard, parse_mode="Markdown")

def get_searches_keyboard(searches)-> InlineKeyboardMarkup:
    builder=InlineKeyboardBuilder()
    i=1
    for s in searches:
        searche_id, query, min_price, max_price = s
        builder.button(text=f'{i}. {query}  ({min_price}-{max_price})', callback_data=f'del:{searche_id}')
        i+=1
        builder.adjust(1)
    builder.button(text="❌ Отмена", callback_data="cancel_edit")
    builder.adjust(1)
    return builder.as_markup()

@dp.callback_query (F.data == "edit")
async def callback_query(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EditSearchGroup.editing)
    searches = await get_searches(callback.from_user.id)
    if len(searches) <1:
        await state.clear()
        await cmd_show_my_searches(callback.message)
        return
    editkb=get_searches_keyboard(searches)

    await callback.message.edit_text(
        text="Нажмите для удаления",
        reply_markup=editkb,
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query (F.data.startswith('del:'))
async def delete_searches(callback: CallbackQuery, state: FSMContext):
    search_id=int(callback.data.split(':')[1])
    await db_delete_searches(search_id,callback.message.chat.id)
    await callback_query(callback, state)

@dp.callback_query(F.data=="cancel_edit" )# ❌
async def cancel(callback: CallbackQuery, state:FSMContext):
    await state.clear()
    await callback.message.delete()
    await cmd_show_my_searches(callback.message)


if __name__ == '__main__':
    asyncio.run(main())