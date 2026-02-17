
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URL
from bson import ObjectId

client = AsyncIOMotorClient(MONGO_URL)
db = client['online_store_db']

products_col = db['products']
orders_col = db['orders']
settings_col = db['settings']
temp_codes = db['temp_codes'] # Login kodlari uchun

async def add_product(name, price, stock, image_url, description, tags, category="General"):
    await products_col.insert_one({
        "name": name,
        "price": price,
        "stock": stock,
        "image_url": image_url, # URL saqlaymiz!
        "description": description,
        "tags": tags, # List ko'rinishida: ["arzon", "yangi"]
        "category": category,
        "is_active": True
    })

async def get_product_by_id(pid):
    try:
        return await products_col.find_one({"_id": ObjectId(pid)})
    except:
        return None
