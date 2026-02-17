import uvicorn
import asyncio
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from aiogram import types, Dispatcher, Bot
from contextlib import asynccontextmanager

from config import BOT_TOKEN, WEBAPP_URL, MONGO_URL
from database import products_col
from bot import dp, bot

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(dp.start_polling(bot))
    yield
    await bot.session.close()

app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- ASOSIY YO'LLAR ---

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# MANA SHU YO'L BO'LISHI SHART
@app.get("/admin")
async def admin_panel(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

# --- API ---
@app.get("/api/products")
async def get_products():
    products = await products_col.find({"is_active": True}).to_list(length=100)
    for p in products:
        p["_id"] = str(p["_id"])
        # Agar eski mahsulotlarda URL yo'q bo'lsa, xatolik bermasligi uchun:
        if "image_url" not in p and "file_id" in p:
             p["image_url"] = p["file_id"] # Vaqtinchalik yechim
    return products

if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
