from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.executor import start_webhook
from aiogram import Bot, types

from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext, Dispatcher

# from config import token
from auth import Auth
import logging
import os

TOKEN = os.getenv('TOKEN')
# TOKEN = token
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
au = Auth()

# webhook settings
WEBHOOK_PATH = ""
WEBHOOK_URL = "https://epicentr-tg.vercel.app/"

# webserver settings
WEBAPP_HOST = 'localhost'  # or ip
WEBAPP_PORT = 8000

logging.basicConfig(level=logging.INFO)


async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)
    # insert code here to run it after start


async def on_shutdown(dp):
    logging.warning('Shutting down..')

    # insert code here to run it before shutdown

    # Remove webhook (not acceptable in some cases)
    await bot.delete_webhook()

    # Close DB connection (if used)
    await dp.storage.close()
    await dp.storage.wait_closed()

    logging.warning('Bye!')


class PhoneReq(StatesGroup):
    get_num = State()


@dp.message_handler(commands=["start"])
async def start_command(m: types.Message):
    share_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    share_button = types.KeyboardButton(text="Send", request_contact=True)
    share_keyboard.add(share_button)

    u_id = m.from_user.id
    res = au.check_user_exist(u_id)

    if res is None:
        await m.answer("To continue send us your phone number:", reply_markup=share_keyboard)
        await PhoneReq.get_num.set()
    else:
        await m.answer("Hi, welcome to 'Collapse'!")


@dp.message_handler(state=PhoneReq.get_num, content_types=types.ContentTypes.CONTACT)
async def get_phone(m: types.Message, state: FSMContext):
    await m.answer("Thanks", reply_markup=types.ReplyKeyboardRemove())

    ph_num = m.contact.phone_number
    u_name = m.from_user.username
    u_id = m.from_user.id
    info = {
        "name": u_name,
        "user_id": u_id,
        "phone_n": ph_num,
        "tickets": [],
        "confirm_tickets": [],
        "follows": [],
    }

    au.create_document(info)
    await state.finish()


@dp.message_handler(commands=['test'])
async def test_command(m: types.Message):
    await m.answer('Successfully')


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
