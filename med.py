import asyncio
import re
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# --- AYARLAR ---
API_ID = 36856573
API_HASH = '9045fafb55bc4aa6fa2aadafbb1f2e1e'
# Session String başına tırnakları ve boşlukları kontrol ederek tam yapıştır
SESSION_STRING = '1BJWap1sBuxwiAI-Ui9NBh4e3GGk2nNVsX0TUfv_FPskG_7H0PNuA0AsLLWW5sRIg2gH8J3z_LmyhUoLngHf3KYBdidK8__r29pO5xHRnv0v8N_eD6DhuFevv0NbWXyhEFU-kdY3xXLf3yKCCD-g_bU-hZEYGXsz98fdsAACrB8yNoMApZNkoK2OfQ7NNR9k5bZWthtrhY9zK6fSx--Jpoh_WhfGsw2r47zt8kz1ePHJmBnVrWQO6iB5amqgu0b9bcO4zHi8RQRMeFeHuWvj78r78haGOx4TZi8LpopZxYaBmQuXwJrEARHjSXkl8lOXkgt2wMDk-1qkLzXWT2VWaKZcqqZH9fyk='

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
