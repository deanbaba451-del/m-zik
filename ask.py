import os
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from openai import OpenAI

# Render panelinden (Environment Variables) gelen bilgiler
tg_token = os.getenv("TG_TOKEN")
openai_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=openai_key)

user_pairs = {}

async def gpt_soru_uret():
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "sen bir oyun botusun. sevgililer için 'yapar misin yapmaz misin' formatinda kisa, eğlenceli ve romantik sorular üret. asla büyük harf kullanma. asla emoji kullanma. sadece soruyu gönder."}],
            max_tokens=50
        )
        return response.choices[0].message.content.lower().strip()
    except:
        return "hata olustu ama soruyorum: benimle her gün konusur musun?"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    args = context.args
    
    if not args:
        bot_info = await context.bot.get_me()
        link = f"https://t.me/{bot_info.username}?start={user_id}"
        await update.message.reply_text(f"bu linki sevgiline gönder: {link}")
    else:
        partner_id = int(args[0])
        user_pairs[user_id] = partner_id
        user_pairs[partner_id] = user_id
        await update.message.reply_text("eslesme tamamlandi. ilk soru geliyor.")
        await yeni_soru_gonder(context, user_id, partner_id)

async def yeni_soru_gonder(context, u1, u2):
    soru = await gpt_soru_uret()
    keyboard = [[
        InlineKeyboardButton("yaparim", callback_data="evet"),
        InlineKeyboardButton("yapmam", callback_data="hayir")
    ]]
    markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(chat_id=u1, text=soru, reply_markup=markup)
    await context.bot.send_message(chat_id=u2, text=soru, reply_markup=markup)

async def button_tap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    partner_id = user_pairs.get(user_id)
    
    if not partner_id: 
        return
    
    cevap = "yaparim" if query.data == "evet" else "yapmam"
    
    await context.bot.send_message(chat_id=partner_id, text=f"sevgilin bu soruya '{cevap}' dedi.")
    await query.answer()
    
    await asyncio.sleep(3)
    await yeni_soru_gonder(context, user_id, partner_id)

def main():
    app = Application.builder().token(tg_token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_tap))
    
    print("bot baslatildi...")
    app.run_polling()

if __name__ == "__main__":
    main()
