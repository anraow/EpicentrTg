from bson.objectid import ObjectId
from aiogram.utils.executor import start_webhook
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext

from code_enc import qr_code_decoder
from config import *
import logging
import aiohttp
import tempfile
import pymongo
import datetime
import os


class GetCode(StatesGroup):
    get = State()


class EventInfo:
    def __init__(self):
        self.client = pymongo.MongoClient(host=['localhost:27017'], document_class=dict, tz_aware=False, connect=True)
        self.db = self.client['bot']
        self.collection = self.db['users']

    def get_event_info(self, e_id):
        res = self.collection.find_one({"_id":  ObjectId(e_id)})
        return res

    def close(self):
        self.client.close()


bot = Bot(token=token)
dp = Dispatcher(bot, storage=MemoryStorage())
ei = EventInfo()

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


@dp.message_handler(commands=['find'])
async def find_event(m: types.Message):
    await m.answer("Send your inviting QRCode:")
    await GetCode.get.set()


@dp.message_handler(state=GetCode.get, content_types=['photo'])
async def get_code(m: types.Message, state: FSMContext):
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as fp:
        file_id = m.photo[-1].file_id
        file = await bot.get_file(file_id)

        if m.photo:
            await file.download(
                destination_file=fp.name,
            )
        e_id = qr_code_decoder(fp.name)
        arr = ei.get_event_info(e_id)
        keyboard = arr['keyboard']
        inline_kb1 = InlineKeyboardMarkup()
        if keyboard:
            for b in keyboard:
                inline_kb1.add(InlineKeyboardButton(b["name"], url=b["url"]))

        caption = "{}\n\n{}".format(arr['title'], datetime.datetime.strftime(arr['date'], "%d.%m.%y %H:%M"))

        parent = os.path.dirname(os.getcwd())
        path = os.path.join(parent, "database/data/posters")
        poster_filename = f"{path}/{str(arr['poster'])}.jpg"

        with open(poster_filename, 'rb') as photo:
            await bot.send_photo(m.from_user.id, photo, caption, reply_markup=inline_kb1)

    await state.finish()

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
