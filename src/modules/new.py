from aiogram import Bot, Dispatcher, types
from aiogram.utils.executor import start_webhook
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.middlewares.logging import LoggingMiddleware

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text

from code_gen import qr_code_generator
from config import *
from bson.objectid import ObjectId
import datetime
import logging
import pymongo
import aiohttp
import os
import re


# ------------
# Classes part
# ------------
# Connect to database
class EventCon:
    def __init__(self):
        self.client = pymongo.MongoClient(host=['localhost:27017'], document_class=dict, tz_aware=False, connect=True)
        self.db = self.client['bot']
        self.collection = self.db['users']

    def add_event(self, arr):
        date = datetime.datetime.strptime(arr["date"], "%d.%m.%y %H:%M")
        arr["date"] = date
        _id = self.collection.insert_one(arr)
        return _id.inserted_id

    def add_qr_path(self, _id, file_path):
        self.collection.update_one({'_id': ObjectId(_id)}, {'$set': {"code_path": file_path}})

    def update_keyboard(self, _id, buttons):
        self.collection.update_one({'_id': ObjectId(_id)}, {'$set': {"keyboard": buttons}})

    def close(self):
        self.client.close()


class CreateEvent(StatesGroup):
    title = State()
    poster = State()
    date = State()
    keyboard = State()
    # button = State()
    edit_button = State()
    del_button = State()


bot = Bot(token=token)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())
et = EventCon()

logging.basicConfig(level=logging.INFO)


async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)
    # insert code here to run it after start
    async with aiohttp.ClientSession() as session:
        await session.get(f"https://api.telegram.org/bot{token}/setWebhook?url={WEBHOOK_URL}")


async def on_shutdown(dp):
    logging.warning('Shutting down..')

    # insert code here to run it before shutdown

    # Remove webhook (not acceptable in some cases)
    await bot.delete_webhook()

    # Close DB connection (if used)
    await dp.storage.close()
    await dp.storage.wait_closed()

    logging.warning('Bye!')


# ----------------------
#  Message Handlers part
# ----------------------
# New post command
@dp.message_handler(commands=['new'])
async def create_command(m: types.Message):
    await m.answer("Let's create new event! Enter your Event title and short Description:")
    await CreateEvent.title.set()


@dp.message_handler(state=CreateEvent.title)
async def enter_date(m: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['title'] = m.text

        if check_caption_len(len(m.text)):
            await CreateEvent.poster.set()
            await m.answer("Send us Poster for your event")
        else:
            await m.answer("Your text is too long, try again (now {} ch. - max 1024 ch.).".format(len(m.text)))
            await CreateEvent.title.set()


@dp.message_handler(state=CreateEvent.poster, content_types=['photo'])
async def set_price(m: types.Message, state: FSMContext):
    parent = os.path.dirname(os.getcwd())
    path = os.path.join(parent, "database/data/posters")
    filename = create_file_name(path, "jpg")
    if m.photo:
        await m.photo[-1].download(destination_file=filename[0])

    async with state.proxy() as data:
        data['poster'] = filename[1]

    # await m.answer("Please set your price")
    await m.answer("Now send date for your Event (eg. DD.MM.YY HH:MM)")
    await CreateEvent.date.set()

keyboard = []


@dp.message_handler(state=CreateEvent.date)
async def send_poster(m: types.Message, state: FSMContext):
    if not valid_date(m.text):
        await m.answer("Your date format is wrong, try again:")
        await CreateEvent.date.set()
    else:
        await state.update_data(date=m.text)

    await show_preview(m, state)
    await CreateEvent.keyboard.set()


@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    """
    Allow user to cancel any action
    """
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info('Cancelling state %r', current_state)
    # Cancel state and inform user about it
    await state.finish()
    # And remove keyboard (just in case)
    await message.reply('Successfully cancelled.', reply_markup=types.ReplyKeyboardRemove())


# -----------------
# Callback handlers
# -----------------
@dp.callback_query_handler(text='confirm', state=CreateEvent.keyboard)
async def confirm_button(c: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        res = {
            "title": data['title'],
            "date": data['date'],
            "poster": data['poster'],
            "creator": c.from_user.id,
            "keyboard": keyboard
        }

        _id = et.add_event(res)
        file_path = qr_code_generator(_id)
        et.add_qr_path(_id, file_path)

        caption = "New post created. That's your QRCode to invite people:"
        with open(file_path, 'rb') as photo:
            await bot.send_photo(c.from_user.id, photo, caption=caption)
    await state.finish()


@dp.callback_query_handler(text='add_link', state=CreateEvent.keyboard)
async def add_link_button(c: types.CallbackQuery):
    await bot.send_message(c.from_user.id,
                           "send link and short name if needed - eg. https://youtube.com/mychannel MyChannel")
    await CreateEvent.edit_button.set()


@dp.callback_query_handler(text='del_link', state=CreateEvent.keyboard)
async def delete_link_button(c: types.CallbackQuery):
    await bot.send_message(c.from_user.id, "Which one you want to delete.")
    await CreateEvent.del_button.set()


@dp.message_handler(state=CreateEvent.edit_button)
async def process_link_button(m: types.Message, state: FSMContext):
    s = m.text
    url = re.search("(?P<url>https?://[^\s]+)", s).group("url")
    text = s.replace(url + '', '')
    d = dict()
    d['name'] = text
    d['url'] = url
    keyboard.append(d)
    print(keyboard)
    await show_preview(m, state)


@dp.message_handler(state=CreateEvent.del_button)
async def process_delete_button(m: types.Message, state: FSMContext):
    b_name = m.text
    global keyboard
    res = keyboard

    keyboard = list(filter(lambda i: i['name'].strip() != b_name.strip(), res))

    # print(res)
    # print(keyboard)
    await show_preview(m, state)


# ---------------
# Functions part
# ---------------
def create_file_name(drc, ext):
    drc_list = os.listdir(drc)
    if drc_list:
        lastname = int(os.path.splitext(drc_list[-1])[0])
        file_id = lastname + 1
    else:
        file_id = 0
    filename = f"{drc}/{file_id}.{ext}"
    return filename, file_id


def valid_date(date_text):
    try:
        res = bool(datetime.datetime.strptime(date_text, "%d.%m.%y %H:%M"))
    except ValueError:
        res = False
    return res


def check_caption_len(cap_l):
    if cap_l > 700:
        return False
    else:
        return True


def generate_qr_code(res):
    et = EventCon()
    _id = et.add_event(res)
    file_path = qr_code_generator(_id)
    et.add_qr_path(_id, file_path)

    # caption = "New post created. That's your QRCode to invite people:"
    # with open(file_path, 'rb') as photo:
    #     await bot.send_photo(from_u_id, photo, caption=caption)


async def show_preview(m: types.Message, state: FSMContext):
    async with state.proxy() as data:

        inline_btn_1 = InlineKeyboardButton('Add link', callback_data='add_link')
        inline_btn_2 = InlineKeyboardButton('Delete link', callback_data='del_link')
        inline_btn_3 = InlineKeyboardButton('Confirm', callback_data='confirm')
        inline_kb1 = InlineKeyboardMarkup()
        if keyboard:
            for b in keyboard:
                inline_kb1.add(InlineKeyboardButton(b["name"], url=b["url"]))
            inline_kb1.row(inline_btn_1, inline_btn_2).add(inline_btn_3)
        else:
            inline_kb1.add(inline_btn_1).add(inline_btn_3)

        caption = "{}\n\n{}".format(data['title'], datetime.datetime.strptime(data['date'], "%d.%m.%y %H:%M")
                                    .strftime('%H:%M %d, %b %Y'))

        parent = os.path.dirname(os.getcwd())
        path = os.path.join(parent, "database/data/posters")
        poster_filename = f"{path}/{str(data['poster'])}.jpg"

        with open(poster_filename, 'rb') as photo:
            await bot.send_photo(m.from_user.id, photo, caption, reply_markup=inline_kb1)

    await CreateEvent.keyboard.set()

if __name__ == '__main__':
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )
