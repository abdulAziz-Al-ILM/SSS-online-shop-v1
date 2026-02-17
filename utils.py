# utils.py
import aiohttp

async def upload_image_to_telegraph(file_path):
    url = 'https://telegra.ph/upload'
    async with aiohttp.ClientSession() as session:
        with open(file_path, 'rb') as f:
            data = {'file': f}
            async with session.post(url, data=data) as response:
                result = await response.json()
                if isinstance(result, list) and 'src' in result[0]:
                    return 'https://telegra.ph' + result[0]['src']
    return None
