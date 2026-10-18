import os
from openai import AsyncOpenAI

async def generate_draft(obj: str, tone: str, facts: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "❌ Ошибка: OPENAI_API_KEY не задан в переменных окружения. Генерация невозможна."

    client = AsyncOpenAI(api_key=api_key)
    prompt = (
        f"Напиши текст-отзыв на русском языке объемом от 600 до 900 знаков.\n"
        f"Объект: {obj}\n"
        f"Тон: {tone}\n"
        f"Ключевые факты/детали: {facts}\n"
        f"Текст должен выглядеть естественно, без маркдауна, без вводных слов вроде 'Вот ваш отзыв'."
    )

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ Ошибка генерации: {str(e)}"