import aiohttp
from io import BytesIO

async def upload_image_to_telegraph(bot, file_id):
    """
    Telegramdagi rasmni yuklab olib, uni Telegra.ph ga joylaydi va URL qaytaradi.
    """
    try:
        # 1. Telegram serveridan rasmni yuklab olish
        file = await bot.get_file(file_id)
        file_path = file.file_path
        
        # Rasmni bayt ko'rinishida olamiz
        downloaded_file = await bot.download_file(file_path)
        
        # 2. Telegra.ph ga yuklash (POST request)
        form = aiohttp.FormData()
        form.add_field('file', downloaded_file, filename='image.jpg', content_type='image/jpeg')
        
        async with aiohttp.ClientSession() as session:
            async with session.post('https://telegra.ph/upload', data=form) as response:
                result = await response.json()
                if isinstance(result, list) and 'src' in result[0]:
                    return 'https://telegra.ph' + result[0]['src']
    except Exception as e:
        print(f"Rasm yuklashda xatolik: {e}")
        return None
