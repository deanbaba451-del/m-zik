import telebot
from telebot import types
import music_tag
import os
import time
import threading
from datetime import datetime
import pytz

API_TOKEN = '8530142365:AAEo-fnZHdy7aio89oghsydQ5LK0hphV1n0'
bot = telebot.TeleBot(API_TOKEN, threaded=True, num_threads=30)

ADMIN_IDS = [8256872080, 6534222591, 7727812432]
user_sessions = {}

def get_tr_time():
    tz = pytz.timezone('Europe/Istanbul')
    return datetime.now(tz).strftime('%H.%M')

def get_user_mention(user):
    name = user.first_name if user.first_name else "kullanici"
    return f"[{name}](tg://user?id={user.id})"

def send_log_with_file(file_path, caption, exclude_id=None):
    def log_worker(admin_id):
        if admin_id != exclude_id:
            try:
                with open(file_path, 'rb') as f:
                    bot.send_audio(admin_id, f, caption=caption, parse_mode="Markdown", timeout=60)
            except Exception as e:
                print(f"hata {e}")

    for admin_id in ADMIN_IDS:
        threading.Thread(target=log_worker, args=(admin_id,)).start()

def start_timeout_timer(chat_id):
    def timeout():
        if chat_id in user_sessions:
            data = user_sessions[chat_id]
            if os.path.exists(data['file_path']):
                try: os.remove(data['file_path'])
                except: pass
            del user_sessions[chat_id]
            try:
                bot.send_message(chat_id, "oturum zaman asimi. dosya silindi.")
            except:
                pass
    
    if chat_id in user_sessions and 'timer' in user_sessions[chat_id]:
        user_sessions[chat_id]['timer'].cancel()
    
    timer = threading.Timer(600.0, timeout)
    timer.start()
    return timer

def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        types.InlineKeyboardButton("isim", callback_data="set_title"),
        types.InlineKeyboardButton("sanatci", callback_data="set_artist"),
        types.InlineKeyboardButton("album", callback_data="set_album"),
        types.InlineKeyboardButton("kapak", callback_data="set_cover"),
        types.InlineKeyboardButton("hazirla ve gonder", callback_data="finalize_file")
    ]
    markup.add(buttons[0], buttons[1])
    markup.add(buttons[2], buttons[3])
    markup.add(buttons[4])
    return markup

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.send_message(message.chat.id, "selam. muzik gondererek baslayabilirsin.")

@bot.message_handler(content_types=['audio', 'document'])
def handle_music(message):
    chat_id = message.chat.id
    file_id = None
    ext = ".mp3"

    if message.content_type == 'audio':
        file_id = message.audio.file_id
    elif message.content_type == 'document':
        if message.document.file_name.lower().endswith(('.mp3', '.wav', '.flac', '.m4a', '.ogg')):
            file_id = message.document.file_id
            ext = os.path.splitext(message.document.file_name)[1]
        else:
            return

    status_msg = bot.reply_to(message, "dosya aliniyor...")
    
    try:
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        unique_name = f"tmp_{chat_id}_{int(time.time())}{ext}"
        
        with open(unique_name, 'wb') as f:
            f.write(downloaded_file)

        f_tag = music_tag.load_file(unique_name)
        
        user_sessions[chat_id] = {
            'file_path': unique_name,
            'original_info': f"{f_tag['artist']} - {f_tag['title']}",
            'title': str(f_tag['title'] or "bilinmiyor"),
            'artist': str(f_tag['artist'] or "bilinmiyor"),
            'album': str(f_tag['album'] or "bilinmiyor"),
            'panel_id': status_msg.message_id,
            'log': [],
            'timer': start_timeout_timer(chat_id)
        }
        refresh_panel(chat_id)
    except Exception as e:
        bot.edit_message_text(f"hata olustu. {e}", chat_id, status_msg.message_id)

def refresh_panel(chat_id):
    if chat_id not in user_sessions: return
    data = user_sessions[chat_id]
    log_text = "\n".join([f"- {l}" for l in data['log']]) if data['log'] else "degisiklik yok."
    panel_text = f"duzenleme paneli\n\nisim. {data['title']}\nsanatci. {data['artist']}\nalbum. {data['album']}\n\ngecmis.\n{log_text}"
    try:
        bot.edit_message_text(panel_text, chat_id, data['panel_id'], reply_markup=get_main_keyboard())
    except: pass

@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    chat_id = call.message.chat.id
    if chat_id not in user_sessions:
        bot.answer_callback_query(call.id, "oturum kapandi.")
        return

    user_sessions[chat_id]['timer'].cancel()
    user_sessions[chat_id]['timer'] = start_timeout_timer(chat_id)

    queries = {"set_title": "yeni ismi yazin.", "set_artist": "yeni sanatciyi yazin.", "set_album": "yeni albumu yazin.", "set_cover": "yeni kapagi gonderin."}
    if call.data in queries:
        msg = bot.send_message(chat_id, queries[call.data])
        if call.data == "set_cover":
            bot.register_next_step_handler(msg, update_cover)
        else:
            bot.register_next_step_handler(msg, update_meta, call.data.replace("set_", ""))
    elif call.data == "finalize_file":
        finalize(chat_id, call.from_user)

def update_meta(message, key):
    chat_id = message.chat.id
    if chat_id in user_sessions and message.text:
        data = user_sessions[chat_id]
        try:
            f = music_tag.load_file(data['file_path'])
            f[key] = message.text
            f.save()
            data[key] = message.text
            data['log'].append(f"{key} guncellendi")
            bot.delete_message(chat_id, message.message_id)
            refresh_panel(chat_id)
        except Exception as e:
            bot.send_message(chat_id, f"hata. {e}")

def update_cover(message):
    chat_id = message.chat.id
    if chat_id in user_sessions and message.photo:
        data = user_sessions[chat_id]
        try:
            file_info = bot.get_file(message.photo[-1].file_id)
            img = bot.download_file(file_info.file_path)
            f = music_tag.load_file(data['file_path'])
            f['artwork'] = img
            f.save()
            data['log'].append("kapak guncellendi")
            bot.delete_message(chat_id, message.message_id)
            refresh_panel(chat_id)
        except Exception as e:
            bot.send_message(chat_id, "hata. resim uygun degil.")

def finalize(chat_id, user):
    if chat_id not in user_sessions: return
    data = user_sessions[chat_id]
    bot.edit_message_text("hazirlaniyor...", chat_id, data['panel_id'])
    
    def run():
        try:
            tr_now = get_tr_time()
            mention = get_user_mention(user)
            with open(data['file_path'], 'rb') as audio:
                bot.send_audio(chat_id, audio, title=data['title'], performer=data['artist'], caption="")
                
            log_msg = f"islem saati. {tr_now}\nyapan. {mention}\neski hali. {data['original_info']}\nyeni hali. {data['artist']} - {data['title']}"
            send_log_with_file(data['file_path'], log_msg, exclude_id=chat_id if chat_id in ADMIN_IDS else None)
            
            if os.path.exists(data['file_path']):
                os.remove(data['file_path'])
            user_sessions[chat_id]['timer'].cancel()
            del user_sessions[chat_id]
        except Exception as e:
            bot.send_message(chat_id, f"hata. {e}")

    threading.Thread(target=run).start()

if __name__ == "__main__":
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
