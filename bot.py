import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

from config import BOT_TOKEN, ADMIN_IDS, WEBAPP_URL
from database import add_product, update_settings

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- Admin States ---
class AdminState(StatesGroup):
    waiting_for_product_photo = State()
    waiting_for_product_details = State()
    waiting_for_logo = State()

# --- Admin Tekshiruvi ---
def is_admin(user_id):
    return user_id in ADMIN_IDS

# --- Start Komandasi ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    
    # Agar Admin bo'lsa
    if is_admin(user_id):
        kb = ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="⚙️ Admin Panel (Mini App)", web_app=WebAppInfo(url=f"{WEBAPP_URL}/admin"))],
            [KeyboardButton(text="➕ Mahsulot qo'shish (Chat orqali)"), KeyboardButton(text="🖼 Logo o'zgartirish")]
        ], resize_keyboard=True)
        await message.answer(f"Salom Admin! Xush kelibsiz. Do'kon boshqaruvi panelidasiz.", reply_markup=kb)
    else:
        # Oddiy foydalanuvchi
        kb = ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="🛍 Do'konni ochish", web_app=WebAppInfo(url=f"{WEBAPP_URL}"))],
            [KeyboardButton(text="📦 Buyurtmalarim"), KeyboardButton(text="📞 Aloqa")]
        ], resize_keyboard=True)
        await message.answer(f"Assalomu alaykum! {message.from_user.full_name}, do'konimizga xush kelibsiz.", reply_markup=kb)

# --- Admin: Rasm ID sini olish va Mahsulot qo'shish (Chat varianti) ---
@dp.message(F.text == "➕ Mahsulot qo'shish (Chat orqali)", F.from_user.id.in_(ADMIN_IDS))
async def admin_add_prod(message: types.Message, state: FSMContext):
    await message.answer("Mahsulot rasmini yuboring (Men sizga uning ID sini bazaga saqlayman):")
    await state.set_state(AdminState.waiting_for_product_photo)

@dp.message(AdminState.waiting_for_product_photo, F.photo)
async def process_photo(message: types.Message, state: FSMContext):
    # Mana shu yerda eng muhim qism: Rasm ID sini olamiz
    photo_id = message.photo[-1].file_id
    await state.update_data(photo_id=photo_id)
    await message.answer(f"Rasm qabul qilindi! ID: {photo_id[:10]}...\nEndi nomini, narxini va sonini yozing (Masalan: iPhone 15, 1200, 5):")
    await state.set_state(AdminState.waiting_for_product_details)

@dp.message(AdminState.waiting_for_product_details)
async def process_details(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photo_id = data.get('photo_id')
    try:
        text = message.text.split(',')
        name = text[0].strip()
        price = float(text[1].strip())
        stock = int(text[2].strip())
        
        # Bazaga yozamiz
        await add_product(name, price, "General", stock, photo_id, "Tavsif yo'q", ["new"])
        await message.answer("✅ Mahsulot bazaga qo'shildi!")
        await state.clear()
    except:
        await message.answer("Xatolik! Format: Nom, Narx, Son (Vergul bilan ajrating)")

# --- Asosiy run funksiyasi ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
