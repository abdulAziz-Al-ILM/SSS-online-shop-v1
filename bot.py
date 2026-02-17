import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import BOT_TOKEN, ADMIN_IDS, CARD_NUMBER
from database import add_product, get_all_products, get_product, delete_product

# Logika
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- FSM (Holatlar) ---
class AdminState(StatesGroup):
    photo = State()
    name = State()
    price = State()
    desc = State()
    stock = State()

class UserState(StatesGroup):
    cart = State() # Savatni shu yerda ushlaymiz
    phone = State()
    check_photo = State()

# --- YORDAMCHI FUNKSIYALAR ---
def is_admin(user_id):
    return user_id in ADMIN_IDS

def main_menu_kb(user_id):
    kb = [
        [KeyboardButton(text="🛍 Do'kon"), KeyboardButton(text="🛒 Savat")],
        [KeyboardButton(text="📞 Aloqa")]
    ]
    if is_admin(user_id):
        kb.append([KeyboardButton(text="➕ Mahsulot qo'shish (Admin)")])
        kb.append([KeyboardButton(text="❌ Mahsulot o'chirish (Admin)")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# --- START ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(f"Xush kelibsiz, {message.from_user.full_name}!", 
                         reply_markup=main_menu_kb(message.from_user.id))

# ================= ADMIN TARAFI =================

@dp.message(F.text == "➕ Mahsulot qo'shish (Admin)")
async def admin_add(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    await message.answer("Mahsulot rasmini yuboring:")
    await state.set_state(AdminState.photo)

@dp.message(AdminState.photo, F.photo)
async def admin_photo(message: types.Message, state: FSMContext):
    await state.update_data(file_id=message.photo[-1].file_id)
    await message.answer("Nomini yozing:")
    await state.set_state(AdminState.name)

@dp.message(AdminState.name)
async def admin_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Narxini yozing (faqat raqam):")
    await state.set_state(AdminState.price)

@dp.message(AdminState.price)
async def admin_price(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Raqam yozing!")
        return
    await state.update_data(price=int(message.text))
    await message.answer("Tavsif (Description) yozing:")
    await state.set_state(AdminState.desc)

@dp.message(AdminState.desc)
async def admin_desc(message: types.Message, state: FSMContext):
    await state.update_data(desc=message.text)
    await message.answer("Soni (Stock):")
    await state.set_state(AdminState.stock)

@dp.message(AdminState.stock)
async def admin_stock(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await add_product(data['name'], data['price'], int(message.text), data['file_id'], data['desc'])
    await message.answer("✅ Mahsulot qo'shildi!")
    await state.clear()

@dp.message(F.text == "❌ Mahsulot o'chirish (Admin)")
async def admin_delete_list(message: types.Message):
    if not is_admin(message.from_user.id): return
    products = await get_all_products()
    if not products:
        await message.answer("Mahsulot yo'q.")
        return
    
    builder = InlineKeyboardBuilder()
    for p in products:
        builder.button(text=f"❌ {p['name']}", callback_data=f"del_{p['_id']}")
    builder.adjust(1)
    await message.answer("O'chirish uchun tanlang:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("del_"))
async def delete_callback(call: types.CallbackQuery):
    pid = call.data.split("_")[1]
    await delete_product(pid)
    await call.message.delete()
    await call.answer("O'chirildi!")

# ================= MIJOZ TARAFI =================

# 1. Do'kon (Ro'yxat)
@dp.message(F.text == "🛍 Do'kon")
async def show_shop(message: types.Message):
    products = await get_all_products()
    if not products:
        await message.answer("Hozircha mahsulot yo'q.")
        return
    
    builder = InlineKeyboardBuilder()
    for p in products:
        builder.button(text=f"{p['name']} - {p['price']} so'm", callback_data=f"view_{p['_id']}")
    builder.adjust(1)
    await message.answer("📦 Mahsulotni tanlang:", reply_markup=builder.as_markup())

# 2. Mahsulotni ko'rish
@dp.callback_query(F.data.startswith("view_"))
async def view_product(call: types.CallbackQuery):
    pid = call.data.split("_")[1]
    p = await get_product(pid)
    if not p:
        await call.answer("Topilmadi", show_alert=True)
        return

    caption = f"📱 <b>{p['name']}</b>\n\n💰 Narxi: {p['price']} so'm\n📄 {p['description']}\n📦 Omborda: {p['stock']} ta"
    
    builder = InlineKeyboardBuilder()
    # Savatga qo'shish tugmasi
    builder.button(text="🛒 Savatga qo'shish", callback_data=f"add_{pid}")
    builder.button(text="🔙 Orqaga", callback_data="back_shop")
    
    await call.message.answer_photo(photo=p['file_id'], caption=caption, parse_mode="HTML", reply_markup=builder.as_markup())
    await call.answer()

@dp.callback_query(F.data == "back_shop")
async def back_to_shop(call: types.CallbackQuery):
    await call.message.delete() # Rasm xabarini o'chirish
    # Qayta do'konni chiqarish (oddiyroq yo'l - user qayta bosishi kerak yoki shunchaki o'chirib qo'yamiz)
    await call.answer()

# 3. Savatga qo'shish
@dp.callback_query(F.data.startswith("add_"))
async def add_to_cart(call: types.CallbackQuery, state: FSMContext):
    pid = call.data.split("_")[1]
    p = await get_product(pid)
    
    data = await state.get_data()
    cart = data.get("cart", {}) # {pid: {'name':..., 'price':..., 'qty':...}}
    
    if pid in cart:
        cart[pid]['qty'] += 1
    else:
        cart[pid] = {'name': p['name'], 'price': p['price'], 'qty': 1}
    
    await state.update_data(cart=cart)
    await call.answer(f"{p['name']} savatga qo'shildi! ✅")

# 4. Savatni ko'rish
@dp.message(F.text == "🛒 Savat")
async def show_cart(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cart = data.get("cart", {})
    
    if not cart:
        await message.answer("Savatingiz bo'sh.")
        return
    
    text = "🛒 <b>Sizning Savatingiz:</b>\n\n"
    total = 0
    for pid, item in cart.items():
        summ = item['price'] * item['qty']
        total += summ
        text += f"▪️ {item['name']} x {item['qty']} = {summ} so'm\n"
    
    text += f"\n<b>Jami: {total} so'm</b>"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🚖 Buyurtma berish", callback_data="checkout")
    builder.button(text="🗑 Tozalash", callback_data="clear_cart")
    
    await message.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "clear_cart")
async def clear_cart(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(cart={})
    await call.message.edit_text("Savat tozalandi.")

# 5. Buyurtma (Checkout)
@dp.callback_query(F.data == "checkout")
async def checkout_start(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("📞 Siz bilan bog'lanishimiz uchun telefon raqamingizni yozing (yoki pastdagi tugmani bosing):", 
                              reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📱 Raqamni yuborish", request_contact=True)]], resize_keyboard=True, one_time_keyboard=True))
    await state.set_state(UserState.phone)
    await call.answer()

@dp.message(UserState.phone)
async def get_phone(message: types.Message, state: FSMContext):
    phone = message.contact.phone_number if message.contact else message.text
    await state.update_data(phone=phone)
    
    # Yetkazib berish va To'lov
    builder = InlineKeyboardBuilder()
    builder.button(text="O'zim olib ketaman (Naqd)", callback_data="type_pickup")
    builder.button(text="Taksi / Pochta (Karta)", callback_data="type_delivery")
    builder.adjust(1)
    
    await message.answer("Yetkazib berish turini tanlang:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("type_"))
async def order_type(call: types.CallbackQuery, state: FSMContext):
    otype = call.data
    await state.update_data(order_type=otype)
    
    if otype == "type_delivery":
        # Karta to'lovi
        await call.message.edit_text(f"💳 To'lov uchun karta: `{CARD_NUMBER}`\n\nIltimos, to'lov qilib chekni (skrinshotni) shu yerga yuboring.")
        await state.set_state(UserState.check_photo)
    else:
        # Naqd
        await finish_order(call.message, state, "Naqd (Joyida)")

@dp.message(UserState.check_photo, F.photo)
async def get_check(message: types.Message, state: FSMContext):
    await finish_order(message, state, "Karta orqali", check_file_id=message.photo[-1].file_id)

async def finish_order(message, state, payment_method, check_file_id=None):
    data = await state.get_data()
    cart = data.get("cart", {})
    phone = data.get("phone")
    
    # Admin uchun hisobot
    report = f"🚨 <b>YANGI BUYURTMA!</b>\n\n"
    report += f"👤 Mijoz: {message.chat.full_name} (@{message.chat.username})\n"
    report += f"📞 Tel: {phone}\n"
    report += f"💳 To'lov: {payment_method}\n\n"
    
    total = 0
    for pid, item in cart.items():
        summ = item['price'] * item['qty']
        total += summ
        report += f"▫️ {item['name']} x {item['qty']} = {summ}\n"
    report += f"\n<b>JAMI: {total} so'm</b>"
    
    # Adminlarga yuborish
    for admin_id in ADMIN_IDS:
        try:
            if check_file_id:
                await bot.send_photo(admin_id, photo=check_file_id, caption=report, parse_mode="HTML")
            else:
                await bot.send_message(admin_id, report, parse_mode="HTML")
        except:
            pass
            
    await message.answer("✅ Buyurtmangiz qabul qilindi! Tez orada aloqaga chiqamiz.", reply_markup=main_menu_kb(message.chat.id))
    await state.clear() # Cart tozalanadi

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
