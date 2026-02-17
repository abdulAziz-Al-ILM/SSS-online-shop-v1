# main.py
import uvicorn
import asyncio
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from aiogram import types, Dispatcher, Bot
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from contextlib import asynccontextmanager

from config import BOT_TOKEN, WEBAPP_URL, MONGO_URL
from database import db, products_col, orders_col
from bot import dp, bot  # bot.py dan import qilamiz

# --- FastAPI Sozlamalari ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ilova ishga tushganda botni webhook yoki pollingini sozlash mumkin
    # Railwayda polling oddiyroq, lekin webhook barqarorroq.
    # Hozircha oddiy polling variantini fonda yurgizamiz:
    asyncio.create_task(dp.start_polling(bot))
    yield
    # Yopilganda
    await bot.session.close()

app = FastAPI(lifespan=lifespan)

# Statik fayllar (css, js, images)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- Web App Routes (Frontend) ---

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/admin")
async def admin_panel(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

# --- API Routes (Ma'lumotlar almashinuvi) ---

@app.get("/api/products")
async def get_products():
    # Mahsulotlarni bazadan olib frontendga beramiz
    products = await products_col.find({"is_active": True}).to_list(length=100)
    # ObjectId ni stringga o'tkazamiz
    for p in products:
        p["_id"] = str(p["_id"])
    return products

@app.post("/api/login-verify")
async def verify_login_code(data: dict):
    # 20 soniyalik kodni tekshirish
    code = data.get("code")
    temp_code = await db.temp_codes.find_one({"code": code})
    if temp_code:
        # Kod to'g'ri bo'lsa, o'chirib tashlaymiz (bir martalik)
        await db.temp_codes.delete_one({"_id": temp_code["_id"]})
        return {"success": True, "role": temp_code["role"]}
    return {"success": False}

@app.post("/api/create-order")
async def create_order(request: Request):
    data = await request.json()
    # Buyurtmani bazaga yozish va Bot orqali Adminga xabar berish
    # Bu yerda logika yoziladi...
    return {"success": True, "message": "Buyurtma qabul qilindi"}

if __name__ == "__main__":
    # Railwayda host 0.0.0.0 va port environmentdan olinadi
    import os
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
