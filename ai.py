import os
import aiohttp

async def generate_draft(obj: str, tone: str, facts: str) -> str:
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        return "❌ Ошибка: MISTRAL_API_KEY не задан."

    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    prompt = (
        f"Напиши текст-отзыв на русском языке объемом от 600 до 900 знаков.\n"
        f"Объект: {obj}\n"
        f"Тон: {tone}\n"
        f"Ключевые факты/детали: {facts}\n"
        f"Текст должен выглядеть естественно, без маркдауна, без вводных слов."
    )
    
    payload = {
        "model": "open-mistral-7b",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                if resp.status != 200:
                    return f"❌ Ошибка Mistral: {resp.status} - {await resp.text()}"
                data = await resp.json()
                return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"❌ Ошибка генерации: {str(e)}"
