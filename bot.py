import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, ReplyKeyboardRemove

from config import BOT_TOKEN, ADMIN_IDS, WEBAPP_URL
from database import add_product
# Tepadagi utils.py dan funksiyani chaqiramiz
from utils import upload_image_to_telegraph 

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class ProductState(StatesGroup):
    photo = State()
    name = State()
    price = State()
    stock = State()

def is_admin(user_id):
    return user_id in ADMIN_IDS

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    if is_admin(user_id):
        # Admin uchun tugmalar
        kb = ReplyKeyboardMarkup(keyboard=[
            # BU YERDA LINK MUAMMOSINI OLDINI OLAMIZ
            [KeyboardButton(text="⚙️ Admin Panel", web_app=WebAppInfo(url=f"{WEBAPP_URL}/admin"))],
            [KeyboardButton(text="➕ Mahsulot qo'shish")]
        ], resize_keyboard=True)
        await message.answer("Admin panelga xush kelibsiz.", reply_markup=kb)
    else:
        # Oddiy user uchun
        kb = ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="🛍 Do'konni ochish", web_app=WebAppInfo(url=f"{WEBAPP_URL}"))]
        ], resize_keyboard=True)
        await message.answer("Assalomu alaykum! Do'konimizga xush kelibsiz.", reply_markup=kb)

# --- Mahsulot qo'shish (Chat orqali) ---
@dp.message(F.text == "➕ Mahsulot qo'shish", F.from_user.id.in_(ADMIN_IDS))
async def start_add(message: types.Message, state: FSMContext):
    await message.answer("Mahsulot rasmini yuboring:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(ProductState.photo)

@dp.message(ProductState.photo, F.photo)
async def process_photo(message: types.Message, state: FSMContext):
    msg = await message.answer("Rasm serverga yuklanmoqda... ⏳")
    
    # Rasmni URL ga aylantiramiz
    photo_id = message.photo[-1].file_id
    image_url = await upload_image_to_telegraph(bot, photo_id)
    
    await msg.delete()
    
    if not image_url:
        await message.answer("Xatolik! Rasmni yuklab bo'lmadi. Boshqatdan urinib ko'ring.")
        return

    # URLni saqlab qolamiz
    await state.update_data(image_url=image_url)
    await message.answer("Rasm qabul qilindi! ✅\nEndi mahsulot NOMINI yozing:")
    await state.set_state(ProductState.name)

@dp.message(ProductState.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("NARXINI yozing (faqat raqam):")
    await state.set_state(ProductState.price)

@dp.message(ProductState.price)
async def process_price(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Iltimos, faqat raqam yozing!")
        return
    await state.update_data(price=int(message.text))
    await message.answer("Omborda qancha bor? (SONI):")
    await state.set_state(ProductState.stock)

@dp.message(ProductState.stock)
async def process_stock(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Faqat raqam yozing!")
        return
    
    data = await state.get_data()
    
    # Bazaga yozish (URL bilan)
    await add_product(
        name=data['name'],
        price=data['price'],
        stock=int(message.text),
        file_id=data['image_url'], # Diqqat: Bu yerda file_id o'rniga URL ketmoqda
        description="Yangi mahsulot",
        tags=[],
        category="General"
    )
    
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="⚙️ Admin Panel", web_app=WebAppInfo(url=f"{WEBAPP_URL}/admin"))],
        [KeyboardButton(text="➕ Mahsulot qo'shish")]
    ], resize_keyboard=True)
    
    await message.answer("✅ Mahsulot bazaga muvaffaqiyatli qo'shildi!", reply_markup=kb)
    await state.clear()
