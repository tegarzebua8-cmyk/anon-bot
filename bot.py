import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
logging.basicConfig(level=logging.INFO)

waiting_user = None
active_chats = {}

def get_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 Cari Partner", callback_data="search")]
    ])

def get_chat_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏭️ Next Partner", callback_data="next")],
        [InlineKeyboardButton("🛑 Stop Chat", callback_data="stop")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Halo!\n\n"
        "Ngobrol anonim sama orang random!\n"
        "Bisa kirim Foto, Sticker, VN, Video!\n\n"
        "Pencet tombol di bawah untuk mulai 👇",
        reply_markup=get_main_keyboard()
    )

async def search_logic(user_id, context):
    global waiting_user
    if user_id in active_chats:
        await context.bot.send_message(chat_id=user_id, text="Kamu lagi ngobrol! Pencet Next dulu.", reply_markup=get_chat_keyboard())
        return

    if waiting_user is None:
        waiting_user = user_id
        await context.bot.send_message(
            chat_id=user_id,
            text="🔍 Mencari partner...\nTunggu sebentar ya...",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Batal Cari", callback_data="stop")]])
        )
    else:
        if waiting_user == user_id:
            return
        partner_id = waiting_user
        waiting_user = None
        active_chats[user_id] = partner_id
        active_chats[partner_id] = user_id
        text = "✅ Partner ditemukan! Mulai ngobrol anonim! /stop untuk berhenti."
        await context.bot.send_message(chat_id=user_id, text=text, reply_markup=get_chat_keyboard())
        await context.bot.send_message(chat_id=partner_id, text=text, reply_markup=get_chat_keyboard())

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await search_logic(update.effective_user.id, context)

async def stop_logic(user_id, context):
    global waiting_user
    if waiting_user == user_id:
        waiting_user = None
        await context.bot.send_message(chat_id=user_id, text="❌ Pencarian dibatalkan.", reply_markup=get_main_keyboard())
        return
    if user_id in active_chats:
        partner_id = active_chats[user_id]
        del active_chats[user_id]
        if partner_id in active_chats:
            del active_chats[partner_id]
        await context.bot.send_message(chat_id=user_id, text="🛑 Obrolan dihentikan.", reply_markup=get_main_keyboard())
        try:
            await context.bot.send_message(chat_id=partner_id, text="🛑 Partner memutuskan obrolan.", reply_markup=get_main_keyboard())
        except:
            pass
    else:
        await context.bot.send_message(chat_id=user_id, text="Kamu belum ngobrol.", reply_markup=get_main_keyboard())

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await stop_logic(update.effective_user.id, context)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if query.data == "search":
        await search_logic(user_id, context)
    elif query.data == "next":
        await stop_logic(user_id, context)
        await search_logic(user_id, context)
    elif query.data == "stop":
        await stop_logic(user_id, context)

async def relay_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in active_chats:
        await update.message.reply_text("Kamu belum terhubung. Pencet tombol di bawah:", reply_markup=get_main_keyboard())
        return
    partner_id = active_chats[user_id]
    try:
        await context.bot.copy_message(chat_id=partner_id, from_chat_id=user_id, message_id=update.message.message_id)
    except Exception as e:
        print(f"Gagal relay: {e}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("search", search))
    app.add_handler(CommandHandler("next", search))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, relay_message))
    print("Bot FINAL berjalan... tanpa nama & tanpa status bot")
    app.run_polling()

if __name__ == "__main__":
    main()