import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, ReplyKeyboardRemove

from config import BOT_TOKEN, ADMIN_IDS, WEBAPP_URL
from database import add_product
from utils import upload_image_to_telegraph

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- Admin States (Qadamlar) ---
class ProductState(StatesGroup):
    photo = State()
    name = State()
    price = State()
    description = State()
    tags = State()
    stock = State()

def is_admin(user_id):
    return user_id in ADMIN_IDS

# --- Start ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if is_admin(message.from_user.id):
        kb = ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="🛍 Web Admin (Mini App)", web_app=WebAppInfo(url=f"{WEBAPP_URL}/admin"))],
            [KeyboardButton(text="➕ Yangi Mahsulot Qo'shish")]
        ], resize_keyboard=True)
        await message.answer("Admin panelga xush kelibsiz. Mahsulot qo'shamizmi?", reply_markup=kb)
    else:
        kb = ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="🛍 Do'konni ochish", web_app=WebAppInfo(url=f"{WEBAPP_URL}"))]
        ], resize_keyboard=True)
        await message.answer("Assalomu alaykum! SSS Online Shopga xush kelibsiz.", reply_markup=kb)

# --- Mahsulot Qo'shish Jarayoni ---

@dp.message(F.text == "➕ Yangi Mahsulot Qo'shish", F.from_user.id.in_(ADMIN_IDS))
async def start_add(message: types.Message, state: FSMContext):
    await message.answer("1. Mahsulot rasmini yuboring:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(ProductState.photo)

@dp.message(ProductState.photo, F.photo)
async def add_photo(message: types.Message, state: FSMContext):
    # Rasmni yuklab, URL olamiz
    wait_msg = await message.answer("Rasm serverga yuklanmoqda, kuting...")
    photo_id = message.photo[-1].file_id
    image_url = await upload_image_to_telegraph(bot, photo_id)
    
    await wait_msg.delete()
    
    if not image_url:
        await message.answer("Rasmni yuklashda xatolik bo'ldi. Boshqa rasm yuboring.")
        return

    await state.update_data(image_url=image_url)
    await message.answer("2. Mahsulot nomini yozing (Masalan: iPhone 15 Pro):")
    await state.set_state(ProductState.name)

@dp.message(ProductState.name)
async def add_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("3. Narxini yozing (faqat raqam, so'mda. Masalan: 1200000):")
    await state.set_state(ProductState.price)

@dp.message(ProductState.price)
async def add_price(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Iltimos, faqat raqam yozing!")
        return
    await state.update_data(price=int(message.text))
    await message.answer("4. Mahsulot haqida batafsil tavsif (Description) yozing:")
    await state.set_state(ProductState.description)

@dp.message(ProductState.description)
async def add_desc(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("5. Teglarni yozing (vergul bilan ajrating. Masalan: telefon, apple, yangi):")
    await state.set_state(ProductState.tags)

@dp.message(ProductState.tags)
async def add_tags(message: types.Message, state: FSMContext):
    tags = [t.strip() for t in message.text.split(',')]
    await state.update_data(tags=tags)
    await message.answer("6. Omborda qancha bor? (Soni, masalan: 10):")
    await state.set_state(ProductState.stock)

@dp.message(ProductState.stock)
async def add_stock(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Faqat raqam yozing!")
        return
    
    data = await state.get_data()
    stock = int(message.text)
    
    # Bazaga saqlash
    await add_product(
        name=data['name'],
        price=data['price'],
        stock=stock,
        image_url=data['image_url'],
        description=data['description'],
        tags=data['tags']
    )
    
    # Menyu qaytarish
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🛍 Web Admin (Mini App)", web_app=WebAppInfo(url=f"{WEBAPP_URL}/admin"))],
        [KeyboardButton(text="➕ Yangi Mahsulot Qo'shish")]
    ], resize_keyboard=True)
    
    await message.answer("✅ Mahsulot muvaffaqiyatli qo'shildi!", reply_markup=kb)
    await state.clear()
