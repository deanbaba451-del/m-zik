import telebot
from telebot import types
import music_tag
import os
import time
import threading
from flask import Flask

# --- RENDER PORT HATASI ÇÖZÜMÜ (FLASK) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot 7/24 Aktif!"

def run_flask():
    # Render'ın verdiği portu kullan, yoksa 8080
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# Flask'ı ayrı bir kanalda (thread) başlatıyoruz
threading.Thread(target=run_flask, daemon=True).start()
# ----------------------------------------

API_TOKEN = '8587842228:AAGnzowivP9sqGQ9mnfs4nAFbv7DBqnHj8w'
bot = telebot.TeleBot(API_TOKEN, threaded=True, num_threads=30)

ADMIN_IDS = [8256872080, 6534222591, 7727812432]
BOT_USERNAME = "@mussiceditbot"

user_sessions = {}

def get_user_mention(user):
    first_name = user.first_name if user.first_name else "Kullanıcı"
    return f"[{first_name}](tg://user?id={user.id})"

def send_log_with_file(file_path, caption, exclude_id=None):
    def log_worker(admin_id):
        if admin_id != exclude_id:
            try:
                with open(file_path, 'rb') as f:
                    bot.send_audio(admin_id, f, caption=caption, parse_mode="Markdown", timeout=60)
            except Exception as e:
                print(f"Log gönderim hatası (Admin {admin_id}): {e}")

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
                bot.send_message(chat_id, "⚠️ **Oturum Zaman Aşımı:** 10 dakika boyunca işlem yapılmadığı için dosya silindi.", parse_mode="Markdown")
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
        types.InlineKeyboardButton("🎵 İsim", callback_data="set_title"),
        types.InlineKeyboardButton("👤 Sanatçı", callback_data="set_artist"),
        types.InlineKeyboardButton("💿 Albüm", callback_data="set_album"),
        types.InlineKeyboardButton("🖼️ Kapak", callback_data="set_cover"),
        types.InlineKeyboardButton("🚀 Müziği Hazırla ve Gönder", callback_data="finalize_file")
    ]
    markup.add(buttons[0], buttons[1])
    markup.add(buttons[2], buttons[3])
    markup.add(buttons[4])
    return markup

@bot.message_handler(commands=['start'])
def welcome(message):
    welcome_text = (
        "Selam!**.\n\n"
        "Müziklerinin ismini, sanatçısını veya kapak fotoğrafını saniyeler içinde düzeltebilirim.\n\n"
        "👇 **Başlamak için herhangi bir müzik yolla!**"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown")

@bot.message_handler(content_types=['audio', 'document'])
def handle_music(message):
    chat_id = message.chat.id
    file_id = None
    ext = ".mp3"

    if message.content_type == 'audio':
        file_id = message.audio.file_id
        mime = message.audio.mime_type
        if 'wav' in mime: ext = ".wav"
        elif 'flac' in mime: ext = ".flac"
        elif 'm4a' in mime or 'mp4' in mime: ext = ".m4a"
    elif message.content_type == 'document':
        if message.document.file_name.lower().endswith(('.mp3', '.wav', '.flac', '.m4a', '.ogg')):
            file_id = message.document.file_id
            ext = os.path.splitext(message.document.file_name)[1]
        else:
            return

    status_msg = bot.reply_to(message, "⚡ **Dosya alınıyor...**", parse_mode="Markdown")
    
    try:
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        unique_name = f"tmp_{chat_id}_{int(time.time())}{ext}"
        file_path = unique_name
        
        with open(file_path, 'wb') as f:
            f.write(downloaded_file)

        f_tag = music_tag.load_file(file_path)
        
        user_sessions[chat_id] = {
            'file_path': file_path,
            'title': str(f_tag['title'] or "Bilinmiyor"),
            'artist': str(f_tag['artist'] or "Bilinmiyor"),
            'album': str(f_tag['album'] or "Bilinmiyor"),
            'panel_id': status_msg.message_id,
            'log': [],
            'timer': start_timeout_timer(chat_id)
        }

        refresh_panel(chat_id)
        
        mention = get_user_mention(message.from_user)
        log_caption = f"📩 **Yeni Müzik Geldi!**\n👤 Kullanıcı: {mention}"
        send_log_with_file(file_path, log_caption, exclude_id=chat_id if chat_id in ADMIN_IDS else None)

    except Exception as e:
        bot.edit_message_text(f"❌ Dosya işlenirken hata oluştu: {e}", chat_id, status_msg.message_id)

def refresh_panel(chat_id):
    if chat_id not in user_sessions: return
    data = user_sessions[chat_id]
    
    log_text = "\n".join([f"• {l}" for l in data['log']]) if data['log'] else "Henüz bir değişiklik yapılmadı."
    
    panel_text = (
        "🛠 **Düzenleme Paneli**\n\n"
        f"🎵 İsim: `{data['title']}`\n"
        f"👤 Sanatçı: `{data['artist']}`\n"
        f"💿 Albüm: `{data['album']}`\n\n"
        "📝 **İşlem Geçmişi:**\n"
        f"_{log_text}_\n\n"
        "Değiştirmek istediğin alanı seç:"
    )
    
    try:
        bot.edit_message_text(panel_text, chat_id, data['panel_id'], reply_markup=get_main_keyboard(), parse_mode="Markdown")
    except: pass

@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    chat_id = call.message.chat.id
    if chat_id not in user_sessions:
        bot.answer_callback_query(call.id, "❌ Oturum kapandı.")
        return

    user_sessions[chat_id]['timer'].cancel()
    user_sessions[chat_id]['timer'] = start_timeout_timer(chat_id)

    if call.data == "set_title":
        msg = bot.send_message(chat_id, "🖊 **Yeni şarkı ismini yaz:**")
        bot.register_next_step_handler(msg, update_meta, "title")
    elif call.data == "set_artist":
        msg = bot.send_message(chat_id, "👤 **Yeni sanatçı ismini yaz:**")
        bot.register_next_step_handler(msg, update_meta, "artist")
    elif call.data == "set_album":
        msg = bot.send_message(chat_id, "💿 **Yeni albüm ismini yaz:**")
        bot.register_next_step_handler(msg, update_meta, "album")
    elif call.data == "set_cover":
        msg = bot.send_message(chat_id, "🖼 **Yeni kapak fotoğrafını yolla:**")
        bot.register_next_step_handler(msg, update_cover)
    elif call.data == "finalize_file":
        finalize(chat_id)

def update_meta(message, key):
    chat_id = message.chat.id
    new_val = message.text
    if chat_id in user_sessions and new_val:
        data = user_sessions[chat_id]
        old_val = data[key]
        try:
            f = music_tag.load_file(data['file_path'])
            f[key] = new_val
            f.save()
            
            data[key] = new_val
            labels = {"title": "İsim", "artist": "Sanatçı", "album": "Albüm"}
            data['log'].append(f"{labels[key]} değişti ({old_val} -> {new_val})")
            
            bot.delete_message(chat_id, message.message_id)
            refresh_panel(chat_id)
        except Exception as e:
            bot.send_message(chat_id, f"❌ Kayıt hatası: {e}")

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
            
            data['log'].append("Kapak fotoğrafı güncellendi")
            bot.delete_message(chat_id, message.message_id)
            refresh_panel(chat_id)
        except Exception as e:
            bot.send_message(chat_id, f"❌ Kapak hatası: {e}")

def finalize(chat_id):
    if chat_id not in user_sessions: return
    data = user_sessions[chat_id]
    bot.edit_message_text("🚀 **Müzik hazırlanıyor...**", chat_id, data['panel_id'])
    
    def run():
        try:
            with open(data['file_path'], 'rb') as audio:
                bot.send_audio(
                    chat_id, audio,
                    title=data['title'],
                    performer=data['artist'],
                    caption=f"🎵 **{data['title']}**\n👤 **{data['artist']}**\n\n✅ {BOT_USERNAME}",
                    parse_mode="Markdown",
                    timeout=60
                )
                
            mention = get_user_mention(bot.get_chat(chat_id))
            log_caption = f"✅ **Müzik Düzenlendi!**\n👤 Kullanıcı: {mention}\n🎵 Son Hali: `{data['artist']} - {data['title']}`"
            send_log_with_file(data['file_path'], log_caption, exclude_id=chat_id if chat_id in ADMIN_IDS else None)
            
            if os.path.exists(data['file_path']):
                try: os.remove(data['file_path'])
                except: pass
            user_sessions[chat_id]['timer'].cancel()
            del user_sessions[chat_id]
            bot.send_message(chat_id, "✨ **İşlem başarıyla tamamlandı.**")
        except Exception as e:
            bot.send_message(chat_id, f"❌ Gönderim sırasında bir hata oluştu: {e}")

    threading.Thread(target=run).start()

if __name__ == "__main__":
    print("Father Music Tag Editor Başlatıldı...")
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
