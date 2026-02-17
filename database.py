from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URL

client = AsyncIOMotorClient(MONGO_URL)
db = client['online_store_db']

products_col = db['products']
orders_col = db['orders']
settings_col = db['settings']

# file_id nomini image_url deb tushuning, yoki kodda shunday qoldirib, 
# ichiga URL yozamiz (bot.py da shunday qildik).
async def add_product(name, price, category, stock, file_id, description, tags):
    await products_col.insert_one({
        "name": name,
        "price": price,
        "category": category,
        "stock": stock,
        "image_url": file_id, # Bazaga 'image_url' nomi bilan yozamiz
        "description": description,
        "tags": tags,
        "is_active": True
    })
