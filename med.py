import asyncio
import re
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# --- AYARLAR ---
API_ID = 36856573
API_HASH = '9045fafb55bc4aa6fa2aadafbb1f2e1e'
# Session String başına tırnakları ve boşlukları kontrol ederek tam yapıştır
SESSION_STRING = '1AZWarzcBu51WB3mMH821DzBiaozgnIzAzbsu1H6fqydatjnCYfcgl8dBFltBqWjWDTPI_NscQQ45chKjk5bnG824qjulAW2O8x4vIYQqb6ZAwWajQtgqSguIFZRkZQwJelriY3mhMtIWJHxITZPOEzHbFH9JHRAh6cYCaC1a7Z4isn6Z37vtjs2YICTcDdNF-WY5PYE_Qz0VnY6j9cp1wEHL5oOrprapTeIITZrzvixJ_IG01ULsTSHU0BNyXhEHvmKszN-oWXGkABtT2lqnWLOD0FQNkFClbI1Y3OUgZ1MtZGoP_ytkIg9Q3Tz_eaJ91QyVoK1nJRpPy_DH6brBsUxIfytfAss='

AUTHORIZED_IDS = [8343507331, 6534222591, 8256872080, 7727812432]
bot_mode = 0

# Session String ile istemciyi başlatıyoruz
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

@client.on(events.NewMessage(pattern=r'/(doeda|gayeda|stop)', from_users=AUTHORIZED_IDS))
async def command_handler(event):
    global bot_mode
    cmd = event.pattern_match.group(1)
    if cmd == 'doeda':
        bot_mode = 1
        await event.respond("🛡 **Doeda Modu Aktif!**")
    elif cmd == 'gayeda':
        bot_mode = 2
        await event.respond("🛡 **Gayeda Modu Aktif!**")
    elif cmd == 'stop':
        bot_mode = 0
        await event.respond("🛑 **Koruma Durduruldu.**")

@client.on(events.NewMessage)
async def protection_handler(event):
    global bot_mode
    if event.sender_id in AUTHORIZED_IDS or event.out:
        return

    # Telefon numarası filtresi
    if re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', event.raw_text):
        await event.delete()
        return

    if bot_mode == 1:
        await event.delete()
    elif bot_mode == 2:
        if event.media and not (event.voice or event.audio):
            await event.delete()

async def start_bot():
    print("Bot bağlanıyor...")
    # DİKKAT: client.start() yerine client.connect() kullanarak numara sormasını engelliyoruz
    await client.connect()
    
    if not await client.is_user_authorized():
        print("HATA: Session String geçersiz! Lütfen yeni bir session al.")
        return
        
    print("Bot başarıyla bağlandı!")
    await client.run_until_disconnected()

if __name__ == '__main__':
    try:
        asyncio.run(start_bot())
    except Exception as e:
        print(f"Bir hata oluştu: {e}")
