import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup, default_state
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import BOT_TOKEN, ADMIN_IDS, CARD_NUMBER
from database import (add_product, get_all_products, get_product, delete_product, 
                      decrease_stock, set_product_stock, set_shop_info, get_shop_info)

# Loglarni yoqamiz
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

# Storage (Xotira) aniq belgilaymiz
storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)

# --- HOLATLAR (STATES) ---
class AdminState(StatesGroup):
    photo = State()
    name = State()
    price = State()
    desc = State()
    stock = State()
    edit_stock_qty = State()
    shop_address = State()

class UserState(StatesGroup):
    input_qty = State()
    phone = State()
    location = State()
    comment = State()
    check_photo = State()

# --- YORDAMCHILAR ---
def is_admin(user_id):
    return user_id in ADMIN_IDS

def main_menu_kb(user_id):
    kb = [
        [KeyboardButton(text="🛍 Do'kon"), KeyboardButton(text="🛒 Savat")],
        [KeyboardButton(text="ℹ️ Biz haqimizda")]
    ]
    if is_admin(user_id):
        kb.append([KeyboardButton(text="➕ Mahsulot qo'shish"), KeyboardButton(text="⚙️ Sozlamalar")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# --- START ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(f"Assalomu alaykum, {message.from_user.full_name}!", reply_markup=main_menu_kb(message.from_user.id))

# ================= ADMIN BO'LIMI =================

@dp.message(F.text == "➕ Mahsulot qo'shish")
async def admin_add(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id): 
        await message.answer("Siz admin emassiz.")
        return
    
    await state.set_state(AdminState.photo)
    await message.answer("📸 <b>Mahsulot rasmini yuboring:</b>", parse_mode="HTML", reply_markup=ReplyKeyboardRemove())

# ---------------------------------------------------------
#  MUAMMONI HAL QILUVCHI HANDLERLAR (KETMA-KETLIK MUHIM)
# ---------------------------------------------------------

# 1. TO'G'RI VARIANT: AdminState.photo holatida va RASM kelganda
@dp.message(StateFilter(AdminState.photo), F.photo)
async def adm_ph_success(m: types.Message, s: FSMContext):
    file_id = m.photo[-1].file_id
    await s.update_data(file_id=file_id)
    await m.answer("✅ Rasm qabul qilindi!\n\nEndi mahsulot <b>NOMINI</b> yozing:", parse_mode="HTML")
    await s.set_state(AdminState.name)

# 2. XATO VARIANT: AdminState.photo holatida, lekin FAYL yoki VIDEO kelganda
@dp.message(StateFilter(AdminState.photo))
async def adm_ph_fail(m: types.Message):
    await m.answer(f"⚠️ Men rasm kutyapman, siz esa <b>{m.content_type}</b> yubordingiz.\n\nIltimos, oddiy rasm yuboring.", parse_mode="HTML")

# 3. KRIZIS VARIANT: Hech qanday holat yo'q (State=None), lekin Rasm keldi
# Bu aynan sizdagi "Jim qolish" muammosini ushlaydi
@dp.message(StateFilter(default_state), F.photo)
async def ghost_photo(m: types.Message, s: FSMContext):
    # Agar admin bo'lsa, unga yordam beramiz
    if is_admin(m.from_user.id):
        await m.answer("⚠️ Bot qayta ishga tushgani sababli jarayon uzildi.\n\nIltimos, <b>➕ Mahsulot qo'shish</b> tugmasini qaytadan bosing va rasmni keyin yuboring.", parse_mode="HTML", reply_markup=main_menu_kb(m.from_user.id))
    else:
        # Oddiy user bo'lsa indamaymiz
        pass

# ---------------------------------------------------------

@dp.message(AdminState.name)
async def adm_nm(m: types.Message, s: FSMContext):
    await s.update_data(name=m.text)
    await m.answer("💰 Narxi (faqat raqam):")
    await s.set_state(AdminState.price)

@dp.message(AdminState.price)
async def adm_pr(m: types.Message, s: FSMContext):
    if not m.text.isdigit(): return await m.answer("⚠️ Iltimos, faqat raqam yozing (so'mda)!")
    await s.update_data(price=int(m.text))
    await m.answer("📝 Tavsif (Description):")
    await s.set_state(AdminState.desc)

@dp.message(AdminState.desc)
async def adm_ds(m: types.Message, s: FSMContext):
    await s.update_data(desc=m.text)
    await m.answer("📦 Omborda nechta bor? (Raqam yozing):")
    await s.set_state(AdminState.stock)

@dp.message(AdminState.stock)
async def adm_st(m: types.Message, s: FSMContext):
    if not m.text.isdigit(): return await m.answer("⚠️ Faqat raqam yozing!")
    data = await s.get_data()
    try:
        await add_product(data['name'], data['price'], int(m.text), data['file_id'], data['desc'])
        await m.answer("✅ Mahsulot muvaffaqiyatli qo'shildi!", reply_markup=main_menu_kb(m.from_user.id))
    except Exception as e:
        await m.answer(f"❌ Xatolik bo'ldi: {str(e)}")
    await s.clear()

# --- ADMIN SOZLAMALAR ---
@dp.message(F.text == "⚙️ Sozlamalar")
async def admin_settings(message: types.Message):
    if not is_admin(message.from_user.id): return
    builder = InlineKeyboardBuilder()
    builder.button(text="📍 Manzilni o'zgartirish", callback_data="adm_set_addr")
    builder.button(text="📦 Mahsulot sonini tahrirlash", callback_data="adm_edit_stock")
    builder.button(text="❌ Mahsulot o'chirish", callback_data="adm_del_prod")
    builder.adjust(1)
    await message.answer("Sozlamalar bo'limi:", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "adm_set_addr")
async def set_addr_start(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("Yangi manzilni yozing:")
    await state.set_state(AdminState.shop_address)
    await call.answer()

@dp.message(AdminState.shop_address)
async def save_addr(message: types.Message, state: FSMContext):
    await set_shop_info(message.text, "Admin")
    await message.answer("✅ Manzil saqlandi!", reply_markup=main_menu_kb(message.from_user.id))
    await state.clear()

@dp.callback_query(F.data == "adm_edit_stock")
async def edit_stock_list(call: types.CallbackQuery):
    products = await get_all_products()
    builder = InlineKeyboardBuilder()
    for p in products:
        builder.button(text=f"{p['name']} ({p['stock']} ta)", callback_data=f"editst_{p['_id']}")
    builder.adjust(1)
    await call.message.edit_text("Mahsulotni tanlang:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("editst_"))
async def edit_stock_ask(call: types.CallbackQuery, state: FSMContext):
    pid = call.data.split("_")[1]
    await state.update_data(edit_pid=pid)
    await call.message.answer("Yangi sonini yozing:")
    await state.set_state(AdminState.edit_stock_qty)
    await call.answer()

@dp.message(AdminState.edit_stock_qty)
async def save_new_stock(message: types.Message, state: FSMContext):
    if not message.text.isdigit(): return await message.answer("Raqam yozing!")
    data = await state.get_data()
    await set_product_stock(data['edit_pid'], int(message.text))
    await message.answer("✅ Soni yangilandi!", reply_markup=main_menu_kb(message.from_user.id))
    await state.clear()

@dp.callback_query(F.data == "adm_del_prod")
async def del_list(call: types.CallbackQuery):
    products = await get_all_products()
    builder = InlineKeyboardBuilder()
    for p in products:
        builder.button(text=f"❌ {p['name']}", callback_data=f"del_{p['_id']}")
    builder.adjust(1)
    await call.message.edit_text("O'chirish uchun tanlang:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("del_"))
async def del_item(call: types.CallbackQuery):
    await delete_product(call.data.split("_")[1])
    await call.answer("O'chirildi!")
    await call.message.delete()

# ================= MIJOZ TARAFI =================

@dp.message(F.text == "ℹ️ Biz haqimizda")
async def about_us(message: types.Message):
    info = await get_shop_info()
    await message.answer(f"📍 <b>Manzilimiz:</b>\n{info['address']}", parse_mode="HTML")

@dp.message(F.text == "🛍 Do'kon")
async def shop_list(message: types.Message):
    products = await get_all_products()
    if not products: return await message.answer("Hozircha mahsulotlar yo'q.")
    builder = InlineKeyboardBuilder()
    for p in products:
        if p.get('stock', 0) > 0:
            builder.button(text=f"{p['name']} - {p['price']} so'm", callback_data=f"view_{p['_id']}")
    builder.adjust(1)
    await message.answer("📦 Mahsulot tanlang:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("view_"))
async def view_prod(call: types.CallbackQuery):
    pid = call.data.split("_")[1]
    p = await get_product(pid)
    if not p: return await call.answer("Topilmadi")
    
    caption = f"📱 <b>{p['name']}</b>\n\n💰 {p['price']} so'm\n📄 {p['description']}\n📦 Omborda: {p['stock']} ta"
    kb = InlineKeyboardBuilder()
    kb.button(text="🛒 Savatga qo'shish", callback_data=f"askqty_{pid}")
    kb.button(text="🔙 Orqaga", callback_data="back_shop")
    
    try:
        await call.message.answer_photo(p['file_id'], caption=caption, parse_mode="HTML", reply_markup=kb.as_markup())
        await call.message.delete()
    except Exception as e:
        await call.message.answer("Rasmda xatolik. Balki rasm eski bazadan qolgan bo'lishi mumkin.")

@dp.callback_query(F.data == "back_shop")
async def back_shop(call: types.CallbackQuery):
    await call.message.delete()
    await call.message.answer("🛍 Do'kon", reply_markup=main_menu_kb(call.from_user.id))

@dp.callback_query(F.data.startswith("askqty_"))
async def ask_qty(call: types.CallbackQuery, state: FSMContext):
    pid = call.data.split("_")[1]
    await state.update_data(temp_pid=pid)
    await call.message.answer("🔢 Nechta xarid qilmoqchisiz? (Raqam yozing):", reply_markup=ReplyKeyboardRemove())
    await state.set_state(UserState.input_qty)
    await call.answer()

@dp.message(UserState.input_qty)
async def add_cart_logic(message: types.Message, state: FSMContext):
    if not message.text.isdigit(): return await message.answer("Iltimos, faqat raqam yozing.")
    qty = int(message.text)
    if qty <= 0: return await message.answer("Kamida 1 ta.")
    
    data = await state.get_data()
    pid = data.get('temp_pid')
    p = await get_product(pid)
    
    if qty > p['stock']:
        return await message.answer(f"Uzur, bizda faqat {p['stock']} ta qolgan.")
    
    user_data = await state.get_data()
    cart = user_data.get("cart", {})
    if pid in cart:
        cart[pid]['qty'] += qty
    else:
        cart[pid] = {'name': p['name'], 'price': p['price'], 'qty': qty}
    
    await state.update_data(cart=cart)
    await message.answer(f"✅ {qty} ta {p['name']} savatga qo'shildi!", reply_markup=main_menu_kb(message.from_user.id))
    await state.set_state(None)

@dp.message(F.text == "🛒 Savat")
async def show_cart(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cart = data.get("cart", {})
    if not cart: return await message.answer("Savat bo'sh.")
    
    text = "🛒 <b>Sizning Savatingiz:</b>\n\n"
    total = 0
    for pid, item in cart.items():
        summ = item['price'] * item['qty']
        total += summ
        text += f"▪️ {item['name']} x {item['qty']} = {summ}\n"
    text += f"\n<b>Jami: {total} so'm</b>"
    
    kb = InlineKeyboardBuilder()
    kb.button(text="🚖 Buyurtma berish", callback_data="checkout")
    kb.button(text="🗑 Tozalash", callback_data="clear_cart")
    await message.answer(text, parse_mode="HTML", reply_markup=kb.as_markup())

@dp.callback_query(F.data == "clear_cart")
async def clr(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(cart={})
    await call.message.edit_text("Savat tozalandi.")

@dp.callback_query(F.data == "checkout")
async def checkout_start(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📱 Raqamni yuborish", request_contact=True)]], resize_keyboard=True)
    await call.message.answer("Bog'lanish uchun raqam yuboring:", reply_markup=kb)
    await state.set_state(UserState.phone)

@dp.message(UserState.phone)
async def get_ph(message: types.Message, state: FSMContext):
    phone = message.contact.phone_number if message.contact else message.text
    await state.update_data(phone=phone)
    
    kb = InlineKeyboardBuilder()
    kb.button(text="🏃 O'zim olib ketaman", callback_data="dlv_pickup")
    kb.button(text="🚖 Yetkazib berish (Taksi)", callback_data="dlv_taxi")
    kb.adjust(1)
    await message.answer("Yetkazib berish turini tanlang:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("dlv_"))
async def dlv_type(call: types.CallbackQuery, state: FSMContext):
    dtype = call.data
    await state.update_data(delivery_type=dtype)
    
    if dtype == "dlv_taxi":
        kb = ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="📍 Lokatsiya yuborish", request_location=True)],
            [KeyboardButton(text="O'tkazib yuborish")]
        ], resize_keyboard=True)
        await call.message.answer("Lokatsiya yuboring:", reply_markup=kb)
        await state.set_state(UserState.location)
    else:
        await call.message.answer("Izohingiz bormi? (Yozing yoki 'Yoq')", reply_markup=ReplyKeyboardRemove())
        await state.set_state(UserState.comment)
    await call.answer()

@dp.message(UserState.location)
async def get_loc(message: types.Message, state: FSMContext):
    loc = f"http://googleusercontent.com/maps.google.com/?q={message.location.latitude},{message.location.longitude}" if message.location else message.text
    await state.update_data(location_link=loc)
    await message.answer("Izohingiz bormi?", reply_markup=ReplyKeyboardRemove())
    await state.set_state(UserState.comment)

@dp.message(UserState.comment)
async def get_comment(message: types.Message, state: FSMContext):
    await state.update_data(comment=message.text)
    
    data = await state.get_data()
    if data['delivery_type'] == "dlv_taxi":
        await message.answer(f"Karta: `{CARD_NUMBER}`\nChekni rasm yoki fayl qilib yuboring:")
        await state.set_state(UserState.check_photo)
    else:
        await finalize_order(message, state, "Naqd")

@dp.message(UserState.check_photo)
async def get_chk_universal(message: types.Message, state: FSMContext):
    file_id = None
    check_type = None

    if message.photo:
        file_id = message.photo[-1].file_id
        check_type = "photo"
    elif message.document:
        file_id = message.document.file_id
        check_type = "document"
    
    if file_id:
        await finalize_order(message, state, "Karta", file_id, check_type)
    else:
        await message.answer("Iltimos, rasm yoki pdf/doc yuboring.")

async def finalize_order(message, state, pay_method, check_id=None, check_type="photo"):
    data = await state.get_data()
    cart = data.get("cart", {})
    
    txt = f"🚨 <b>YANGI BUYURTMA</b>\n\n"
    txt += f"👤 {message.chat.full_name}\n📞 {data.get('phone')}\n"
    txt += f"📝 Izoh: {data.get('comment')}\n"
    if 'location_link' in data:
        txt += f"📍 Lokatsiya: {data['location_link']}\n"
    
    total = 0
    for pid, item in cart.items():
        summ = item['price'] * item['qty']
        total += summ
        txt += f"▫️ {item['name']} x {item['qty']} = {summ}\n"
        await decrease_stock(pid, item['qty'])
        
    txt += f"\n💰 Jami: {total} so'm ({pay_method})"
    
    for admin in ADMIN_IDS:
        try:
            if check_id:
                if check_type == "document":
                    await bot.send_document(admin, check_id, caption=txt, parse_mode="HTML")
                else:
                    await bot.send_photo(admin, check_id, caption=txt, parse_mode="HTML")
            else:
                await bot.send_message(admin, txt, parse_mode="HTML")
        except: pass
        
    await message.answer("✅ Buyurtma qabul qilindi!", reply_markup=main_menu_kb(message.from_user.id))
    await state.clear()

# --- ZOMBI HANDLER (OXIRGI CHORA) ---
@dp.message()
async def catch_all(message: types.Message):
    # Agar bot hech qanday buyruqni tushunmasa va hech narsa kutmayotgan bo'lsa
    # Lekin rasm kelsa, bu "Arvoh rasm" bo'ladi
    if message.photo and is_admin(message.from_user.id):
         await message.answer("⚠️ Bot qayta ishga tushgani uchun jarayon uzildi.\nIltimos, <b>➕ Mahsulot qo'shish</b> tugmasini bosib, qaytadan urinib ko'ring.", parse_mode="HTML", reply_markup=main_menu_kb(message.from_user.id))

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
