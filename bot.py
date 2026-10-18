import os
import logging
from datetime import time
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

import db
import ai
import reports
from keep_alive import keep_alive

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

# Состояния для добавления задачи
(ADD_PLATFORM, ADD_TYPE, ADD_DESC, ADD_AMOUNT, ADD_STATUS) = range(5)
# Состояния для генерации
(AI_OBJ, AI_TONE, AI_FACTS) = range(5, 8)

def owner_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id != OWNER_ID:
            if update.message:
                await update.message.reply_text("⛔ У вас нет доступа к этому боту.")
            elif update.callback_query:
                await update.callback_query.answer("⛔ Доступ запрещен.", show_alert=True)
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("➕ Добавить задание", callback_data="add_task")],
        [InlineKeyboardButton("✍️ Сгенерировать черновик", callback_data="ai_draft")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton("📄 Отчёт", callback_data="report")],
        [InlineKeyboardButton("🗂 Мои задания", callback_data="my_tasks")]
    ]
    return InlineKeyboardMarkup(keyboard)

@owner_only
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "👋 Добро пожаловать в <b>Freelance Assistant</b>!\n\n"
    text += "Этот бот помогает вести учет мелких задач и генерировать черновики текстов.\n\n"
    text += "Выберите действие:"
    if update.message:
        await update.message.reply_text(text, reply_markup=get_main_menu(), parse_mode="HTML")
    else:
        await update.callback_query.edit_message_text(text, reply_markup=get_main_menu(), parse_mode="HTML")

@owner_only
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data

    if action == "stats":
        s = db.get_stats()
        text = "📊 <b>Статистика</b>\n\n"
        text += f"<b>Сегодня:</b> {s['today'][0]} задач, {s['today'][1]:.2f} ₽\n"
        text += f"<b>За неделю:</b> {s['week'][0]} задач, {s['week'][1]:.2f} ₽\n"
        text += f"<b>За всё время:</b> {s['all'][0]} задач, {s['all'][1]:.2f} ₽\n\n"
        text += "<b>По площадкам (всего):</b>\n"
        if s['platforms']:
            for p, c, a in s['platforms']:
                text += f"— {p}: {c} шт. на {a:.2f} ₽\n"
        else:
            text += "Нет данных."
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=get_main_menu())

    elif action == "report":
        text = reports.generate_report_text()
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=get_main_menu())

    elif action == "my_tasks":
        tasks = db.get_last_tasks(10)
        if not tasks:
            await query.edit_message_text("🗂 Список пуст.", reply_markup=get_main_menu())
            return
        await query.edit_message_text("🗂 <b>Последние 10 задач:</b>", parse_mode="HTML")
        for t in tasks:
            tid, p, ttype, desc, amt, status, dt = t
            status_icon = "✅" if status == "выполнено" else "🕒"
            text = f"{status_icon} <b>#{tid}</b> | {p} | {ttype}\n"
            text += f"📝 {desc[:50]}...\n"
            text += f"💰 {amt:.2f} ₽ | {status}\n"
            keyboard = [[
                InlineKeyboardButton("✅ Выполнено", callback_data=f"done_{tid}"),
                InlineKeyboardButton("🗑 Удалить", callback_data=f"del_{tid}")
            ]]
            await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    elif action.startswith("done_"):
        tid = int(action.split("_")[1])
        db.update_task_status(tid, "выполнено")
        await query.edit_message_text(f"✅ Задача #{tid} отмечена как выполненная.", reply_markup=get_main_menu())

    elif action.startswith("del_"):
        tid = int(action.split("_")[1])
        db.delete_task(tid)
        await query.edit_message_text(f"🗑 Задача #{tid} удалена.", reply_markup=get_main_menu())

# --- ДОБАВЛЕНИЕ ЗАДАЧИ ---

@owner_only
async def add_task_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🏷 Введите название площадки (например: Яндекс.Карты, Отзовик):")
    return ADD_PLATFORM

async def add_platform(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['platform'] = update.message.text
    await update.message.reply_text("📌 Введите тип задания (например: отзыв, описание):")
    return ADD_TYPE

async def add_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['type'] = update.message.text
    await update.message.reply_text("📝 Кратко опишите объект (что оцениваем):")
    return ADD_DESC

async def add_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['desc'] = update.message.text
    await update.message.reply_text("💰 Введите сумму оплаты в рублях (только число):")
    return ADD_AMOUNT

async def add_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text.replace(',', '.'))
        context.user_data['amount'] = amount
    except ValueError:
        await update.message.reply_text("❌ Ошибка: введите корректное число (например: 500 или 150.50).")
        return ADD_AMOUNT

    keyboard = [[
        InlineKeyboardButton("✅ Выполнено", callback_data="status_done"),
        InlineKeyboardButton("🕒 В работе", callback_data="status_pending")
    ]]
    await update.message.reply_text("Выберите статус задания:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ADD_STATUS

async def add_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    status = "выполнено" if query.data == "status_done" else "в работе"

    db.add_task(
        context.user_data['platform'],
        context.user_data['type'],
        context.user_data['desc'],
        context.user_data['amount'],
        status
    )

    await query.edit_message_text(f"✅ Задание успешно добавлено!\nСтатус: {status}", reply_markup=get_main_menu())
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Действие отменено.", reply_markup=get_main_menu())
    return ConversationHandler.END

# --- ГЕНЕРАЦИЯ ТЕКСТА ---

@owner_only
async def ai_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("✍️ Введите название объекта (что оцениваем/описываем):")
    return AI_OBJ

async def ai_obj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ai_obj'] = update.message.text
    keyboard = [[
        InlineKeyboardButton("Нейтральный", callback_data="tone_neutral"),
        InlineKeyboardButton("Восторженный", callback_data="tone_enthusiastic"),
        InlineKeyboardButton("Сдержанный", callback_data="tone_reserved")
    ]]
    await update.message.reply_text("Выберите тон текста:", reply_markup=InlineKeyboardMarkup(keyboard))
    return AI_TONE

async def ai_tone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tone_map = {
        "tone_neutral": "нейтральный",
        "tone_enthusiastic": "восторженный",
        "tone_reserved": "сдержанный"
    }
    context.user_data['ai_tone'] = tone_map.get(query.data, "нейтральный")
    await query.edit_message_text("📝 Введите 2-3 ключевых факта о объекте (через запятую):")
    return AI_FACTS

async def ai_facts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    facts = update.message.text
    obj = context.user_data['ai_obj']
    tone = context.user_data['ai_tone']

    await update.message.reply_text("⏳ Генерирую черновик, подождите...")

    draft = await ai.generate_draft(obj, tone, facts)

    if draft.startswith("❌"):
        await update.message.reply_text(draft, reply_markup=get_main_menu())
    else:
        await update.message.reply_text(f"📄 <b>Ваш черновик:</b>\n\n{draft}", parse_mode="HTML", reply_markup=get_main_menu())

    return ConversationHandler.END

# --- ЕЖЕДНЕВНЫЙ ОТЧЕТ ---

async def daily_report(context: ContextTypes.DEFAULT_TYPE):
    text = reports.generate_report_text()
    try:
        await context.bot.send_message(chat_id=OWNER_ID, text=text, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Ошибка отправки ежедневного отчета: {e}")

# --- ЗАПУСК ---

def main():
    if not BOT_TOKEN or not OWNER_ID:
        logging.error("❌ BOT_TOKEN или OWNER_ID не заданы!")
        return

    db.init_db()
    keep_alive()  # Запуск Flask для Render

    app = Application.builder().token(BOT_TOKEN).build()

    # Диалог добавления задачи
    add_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_task_start, pattern="^add_task$")],
        states={
            ADD_PLATFORM: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_platform)],
            ADD_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_type)],
            ADD_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_desc)],
            ADD_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_amount)],
            ADD_STATUS: [CallbackQueryHandler(add_status, pattern="^status_")],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    # Диалог генерации
    ai_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(ai_start, pattern="^ai_draft$")],
        states={
            AI_OBJ: [MessageHandler(filters.TEXT & ~filters.COMMAND, ai_obj)],
            AI_TONE: [CallbackQueryHandler(ai_tone, pattern="^tone_")],
            AI_FACTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ai_facts)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(add_conv)
    app.add_handler(ai_conv)
    app.add_handler(CallbackQueryHandler(menu_handler))

    # Ежедневный отчет в 21:00
    job_queue = app.job_queue
    job_queue.run_daily(daily_report, time=time(hour=21, minute=0))

    logging.info("🚀 Бот запущен!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()