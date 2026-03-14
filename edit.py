import telebot

TOKEN = "8690542685:AAGAB5grLaJ78rGay-7R7hh6VGpgKQy_hNo"
bot = telebot.TeleBot(TOKEN)

@bot.edited_message_handler(func=lambda message: True)
def lol(message):
    try:
        if message.edit_date is not None:
            chat_id = message.chat.id
            message_id = message.message_id
            user_id = message.from_user.id
            user_name = message.from_user.first_name

            bot.delete_message(chat_id, message_id)

            response_text = f"[{user_name}](tg://user?id={user_id}), it is forbidden to edit messages."
            bot.send_message(chat_id, response_text, parse_mode="Markdown")

    except Exception:
        pass

if __name__ == "__main__":
    bot.infinity_polling()