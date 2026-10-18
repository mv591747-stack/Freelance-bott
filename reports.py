from db import get_stats

def generate_report_text() -> str:
    stats = get_stats()
    text = "📊 <b>Ежедневный отчет</b>\n\n"
    text += f"Сегодня выполнено: {stats['today'][0]} шт.\n"
    text += f"Заработано сегодня: {stats['today'][1]:.2f} ₽\n\n"

    text += "<b>Разбивка по площадкам (всего):</b>\n"
    if stats['platforms']:
        for platform, count, amount in stats['platforms']:
            text += f"- {platform}: {count} шт. на {amount:.2f} ₽\n"
    else:
        text += "Нет выполненных заданий."
    return text