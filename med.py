import asyncio
import re
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# --- AYARLAR ---
API_ID = 9045fafb55bc4aa6fa2aadafbb1f2e1e
API_HASH = '36856573'
SESSION_STRING = '1AZWarzcBu51WB3mMH821DzBiaozgnIzAzbsu1H6fqydatjnCYfcgl8dBFltBqWjWDTPI_NscQQ45chKjk5bnG824qjulAW2O8x4vIYQqb6ZAwWajQtgqSguIFZRkZQwJelriY3mhMtIWJHxITZPOEzHbFH9JHRAh6cYCaC1a7Z4isn6Z37vtjs2YICTcDdNF-WY5PYE_Qz0VnY6j9cp1wEHL5oOrprapTeIITZrzvixJ_IG01ULsTSHU0BNyXhEHvmKszN-oWXGkABtT2lqnWLOD0FQNkFClbI1Y3OUgZ1MtZGoP_ytkIg9Q3Tz_eaJ91QyVoK1nJRpPy_DH6brBsUxIfytfAss='

# Yetkili ID Listesi
AUTHORIZED_IDS = [8343507331, 6534222591, 8256872080, 7727812432]

# Bot Durumu (0: Kapalı, 1: Doeda Modu, 2: Gayeda Modu)
bot_mode = 0

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

print("Bot başlatılıyor...")

# Komut Kontrolü (Sadece yetkililer için)
@client.on(events.NewMessage(pattern=r'/(doeda|gayeda|stop)', from_users=AUTHORIZED_IDS))
async def command_handler(event):
    global bot_mode
    cmd = event.pattern_match.group(1)
    
    if cmd == 'doeda':
        bot_mode = 1
        await event.respond("🛡 **Doeda Modu Aktif:** Her şey temizleniyor!")
    elif cmd == 'gayeda':
        bot_mode = 2
        await event.respond("🛡 **Gayeda Modu Aktif:** Metin ve Ses hariç her şey temizleniyor!")
    elif cmd == 'stop':
        bot_mode = 0
        await event.respond("🛑 **Koruma Durduruldu.**")

# Mesaj Filtreleme Mantığı
@client.on(events.NewMessage)
async def protection_handler(event):
    global bot_mode
    
    # Yetkili biriyse veya bot kendi mesajıysa dokunma
    if event.sender_id in AUTHORIZED_IDS or event.out:
        return

    # 1. Telefon Numarası Kontrolü (Her zaman aktif)
    phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    if re.search(phone_pattern, event.raw_text):
        await event.delete()
        return

    # 2. Modlara Göre Silme İşlemi
    if bot_mode == 1:
        # Doeda: Her şeyi sil
        await event.delete()
    
    elif bot_mode == 2:
        # Gayeda: Metin ve Ses hariç her şeyi sil
        # event.media kontrolü medya olup olmadığını söyler
        # event.voice ve event.audio ses dosyalarını temsil eder
        if event.media:
            if not (event.voice or event.audio):
                await event.delete()

async def main():
    await client.start()
    print("Bot başarıyla bağlandı ve çalışıyor!")
    await client.run_until_disconnected()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
