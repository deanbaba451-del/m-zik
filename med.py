import asyncio
import re
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# --- AYARLAR ---
API_ID = 36856573
API_HASH = '9045fafb55bc4aa6fa2aadafbb1f2e1e'
SESSION_STRING = '1AZWarzcBu51WB3mMH821DzBiaozgnIzAzbsu1H6fqydatjnCYfcgl8dBFltBqWjWDTPI_NscQQ45chKjk5bnG824qjulAW2O8x4vIYQqb6ZAwWajQtgqSguIFZRkZQwJelriY3mhMtIWJHxITZPOEzHbFH9JHRAh6cYCaC1a7Z4isn6Z37vtjs2YICTcDdNF-WY5PYE_Qz0VnY6j9cp1wEHL5oOrprapTeIITZrzvixJ_IG01ULsTSHU0BNyXhEHvmKszN-oWXGkABtT2lqnWLOD0FQNkFClbI1Y3OUgZ1MtZGoP_ytkIg9Q3Tz_eaJ91QyVoK1nJRpPy_DH6brBsUxIfytfAss='

# Yetkili ID'ler (Komutları kullanabilen ve silinmeyen kişiler)
AUTHORIZED_IDS = [8343507331, 6534222591, 8256872080, 7727812432]
bot_mode = 0  # 0: Kapalı, 1: Doeda (Her şeyi sil), 2: Gayeda (Medya sil)

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# --- RENDER PORT HATASINI ENGELLEMEK İÇİN SUNUCU ---
class WebServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Bot is active and running!")

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), WebServer)
    print(f"Web sunucusu {port} portunda calisiyor.")
    server.serve_forever()

# --- BOT KOMUTLARI ---
@client.on(events.NewMessage(pattern=r'/(doeda|gayeda|stop)', from_users=AUTHORIZED_IDS))
async def command_handler(event):
    global bot_mode
    cmd = event.pattern_match.group(1)
    
    if cmd == 'doeda':
        bot_mode = 1
        await event.respond("🛡 **Doeda Modu Aktif:** Grup tamamen kilitlendi, her şey silinecek!")
    elif cmd == 'gayeda':
        bot_mode = 2
        await event.respond("🛡 **Gayeda Modu Aktif:** Sadece Metin ve Seslere izin var, medya silinecek!")
    elif cmd == 'stop':
        bot_mode = 0
        await event.respond("🛑 **Koruma Durduruldu.** Sadece numara takibi aktif.")

# --- KORUMA VE NUMARA FİLTRESİ ---
@client.on(events.NewMessage)
async def protection_handler(event):
    global bot_mode
    
    # Yetkiliyse veya botun kendi mesajıysa işlem yapma
    if event.sender_id in AUTHORIZED_IDS or event.out:
        return

    # 1. ÖNCELİK: NUMARA SİLME (Komutlardan bağımsız her zaman çalışır)
    # Bu regex farklı formatlardaki telefon numaralarını yakalar
    phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    if re.search(phone_pattern, event.raw_text):
        await event.delete()
        print(f"Numara paylasimi engellendi: {event.sender_id}")
        return # Numara bulduysa ve sildiyse alt tarafa bakmasına gerek yok

    # 2. MODLARA GÖRE SİLME
    if bot_mode == 1:
        # Doeda: Her şeyi sil
        await event.delete()
    
    elif bot_mode == 2:
        # Gayeda: Metin (text) ve Ses (voice/audio) hariç her şeyi sil
        if event.media:
            if not (event.voice or event.audio):
                await event.delete()

async def start_bot():
    print("Bot baglaniyor...")
    await client.connect()
    if not await client.is_user_authorized():
        print("HATA: Session String gecersiz!")
        return
    print("Bot basariyla baglandi!")
    await client.run_until_disconnected()

if __name__ == '__main__':
    # Web sunucusunu başlat (Render kapanmasın diye)
    threading.Thread(target=run_http_server, daemon=True).start()
    
    # Botu başlat
    try:
        asyncio.run(start_bot())
    except (KeyboardInterrupt, SystemExit):
        pass