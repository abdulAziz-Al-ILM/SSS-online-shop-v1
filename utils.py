import aiohttp

async def upload_image_to_telegraph(bot, file_id):
    try:
        # 1. Telegramdan faylni topamiz
        file_info = await bot.get_file(file_id)
        file_path = file_info.file_path
        
        # 2. Faylni yuklab olamiz (download)
        file = await bot.download_file(file_path)
        
        # 3. Telegra.ph ga yuklaymiz
        form = aiohttp.FormData()
        form.add_field('file', file, filename='image.jpg', content_type='image/jpeg')
        
        async with aiohttp.ClientSession() as session:
            async with session.post('https://telegra.ph/upload', data=form) as response:
                result = await response.json()
                if isinstance(result, list) and 'src' in result[0]:
                    # Tayyor linkni qaytaramiz
                    return 'https://telegra.ph' + result[0]['src']
    except Exception as e:
        print(f"Rasm yuklashda xatolik: {e}")
    return None
