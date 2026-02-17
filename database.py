from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URL
from bson import ObjectId

client = AsyncIOMotorClient(MONGO_URL)
db = client['simple_shop_db']
products_col = db['products']
settings_col = db['settings']

# --- MAHSULOTLAR ---
async def add_product(name, price, stock, file_id, description):
    await products_col.insert_one({
        "name": name,
        "price": price,
        "stock": stock,
        "file_id": file_id,
        "description": description
    })

async def get_all_products():
    return await products_col.find().to_list(length=100)

async def get_product(product_id):
    try:
        return await products_col.find_one({"_id": ObjectId(product_id)})
    except:
        return None

async def delete_product(product_id):
    await products_col.delete_one({"_id": ObjectId(product_id)})

# --- YANGI: OMBOR BILAN ISHLASH ---
async def decrease_stock(product_id, qty):
    """Sotilganda mahsulot sonini kamaytirish"""
    await products_col.update_one(
        {"_id": ObjectId(product_id)}, 
        {"$inc": {"stock": -qty}}
    )

async def set_product_stock(product_id, new_stock):
    """Admin mahsulot sonini tahrirlashi uchun"""
    await products_col.update_one(
        {"_id": ObjectId(product_id)},
        {"$set": {"stock": new_stock}}
    )

# --- YANGI: DO'KON SOZLAMALARI (MANZIL) ---
async def set_shop_info(address, contact):
    await settings_col.update_one(
        {"type": "info"}, 
        {"$set": {"address": address, "contact": contact}}, 
        upsert=True
    )

async def get_shop_info():
    info = await settings_col.find_one({"type": "info"})
    if not info:
        return {"address": "Manzil kiritilmagan", "contact": "Aloqa yo'q"}
    return info
