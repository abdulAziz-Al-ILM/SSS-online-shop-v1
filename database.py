from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URL

client = AsyncIOMotorClient(MONGO_URL)
db = client['online_store_db']

# Kolleksiyalar
products_col = db['products']
orders_col = db['orders']
settings_col = db['settings']

async def add_product(name, price, category, stock, file_id, description, tags):
    await products_col.insert_one({
        "name": name,
        "price": price,
        "category": category,
        "stock": stock,
        "file_id": file_id, # Rasmning telegramdagi IDsi
        "description": description,
        "tags": tags,
        "is_active": True
    })

async def get_all_products():
    return await products_col.find({"is_active": True}).to_list(length=100)

async def update_stock(product_id, quantity):
    # Mahsulot sonini o'zgartirish
    await products_col.update_one({"_id": product_id}, {"$inc": {"stock": quantity}})

# Do'kon sozlamalari (Logo, Video, Ranglar)
async def update_settings(key, value):
    await settings_col.update_one({"type": "general"}, {"$set": {key: value}}, upsert=True)
