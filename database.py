from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URL
from bson import ObjectId

client = AsyncIOMotorClient(MONGO_URL)
db = client['simple_shop_db']
products_col = db['products']

async def add_product(name, price, stock, file_id, description):
    await products_col.insert_one({
        "name": name,
        "price": price,
        "stock": stock,
        "file_id": file_id, # Telegram file_id
        "description": description
    })

async def get_all_products():
    return await products_col.find().to_list(length=100)

async def get_product(product_id):
    return await products_col.find_one({"_id": ObjectId(product_id)})

async def delete_product(product_id):
    await products_col.delete_one({"_id": ObjectId(product_id)})
