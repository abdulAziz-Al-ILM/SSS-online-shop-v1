# Python 3.10 versiyasini ishlatamiz (yengil versiya)
FROM python:3.10-slim

# Ishchi papkani belgilaymiz
WORKDIR /app

# Avval kutubxonalarni o'rnatamiz (keshlash uchun qulay)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Barcha kodlarni ko'chiramiz
COPY . .

# Portni ochamiz (Railway o'zi port beradi, lekin yozib qo'ygan yaxshi)
EXPOSE 8000

# Ilovani ishga tushirish buyrug'i
# $PORT - Railway tomonidan avtomatik beriladigan port
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
