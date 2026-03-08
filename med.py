import asyncio
import re
import os
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from aiohttp import web

# --- AYARLAR ---
API_ID = 36856573
API_HASH = '9045fafb55bc4aa6fa2aadafbb1f2e1e'
# Yeni verdiğin session string:
SESSION_STRING = '1BJWap1sBu4GSAP5620LpBYu4P_PQhCkZTG8NQOxrjjItv_xLMF6liSCqVcDSOm6BzfW4Gvtco-POckMRBFyi17DItKbUA4bpbNPIbv-QCCQ61WkfvwODGiW2TifaShCb7qZPr3D7sr4FS0De5FUO9CPsuGFPr2n0KiyWun4PRBU9ixwlU6JNTbt1ki6cUr123bZ3db3QVrt6Ao5iZl6nVIcVw_KhfBZJL9LQiIVeBOQcLovEab1z6aIEAhej4uDRx7Mlu-5CtxkcP6X7BdeSLV5LOwiHo7tv-Iqpd0ZxQ58cYB9ywAt4VfXAyQvR7PXNO5RPgjAj8vLxpxs1G8lvtNevxyn-UX8='

# Yetkili ID'ler
AUTHORIZED_IDS = [8343507331, 6534222591, 8256872080, 7727812432]
bot_mode = 0  # 0: Kapalı, 1: Doeda, 2: Gayeda

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# --- WEB SUNUCUSU (Render Kapanmasın Diye) ---
async def hello(request):
    return web.Response(text="Bot is running!")

async def run_web_server():
    app = web.Application()
    app.router.add_get('/', hello)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Web sunucusu {port} portunda aktif edildi.")

# --- BOT KOMUTLARI ---
@client.on(events.NewMessage(pattern=r'/(doeda|gayeda|stop)', from_users=AUTHORIZED_IDS))
async def command_handler(event):
    global bot_mode
    cmd = event.pattern_match.group(1)
    if cmd == 'doeda':
        bot_mode = 1
        await event.respond("🛡 **Doeda Modu Aktif!** Grup tamamen kilitlendi.")
    elif cmd == 'gayeda':
        bot_mode = 2
        await event.respond("🛡 **Gayeda Modu Aktif!** Sadece Metin ve Seslere izin var.")
    elif cmd == 'stop':
        bot_mode = 0
        await event.respond("🛑 **Koruma Durduruldu.** Sadece numara avcısı aktif.")

# --- KORUMA VE NUMARA FİLTRESİ ---
@client.on(events.NewMessage)
async def protection_handler(event):
    global bot_mode
    if event.sender_id in AUTHORIZED_IDS or event.out:
        return

    # Telefon Numarası Avcısı (Komutlardan bağımsız her zaman çalışır)
    phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    if re.search(phone_pattern, event.raw_text):
        await event.delete()
        return

    if bot_mode == 1:
        await event.delete()
    elif bot_mode == 2:
        if event.media and not (event.voice or event.audio):
            await event.delete()

async def main():
    print("Bot bağlanıyor...")
    await run_web_server()
    await client.connect()
    
    if not await client.is_user_authorized():
        print("HATA: Session hala geçersiz! Yeni bir session almalısın.")
        return
        
    print("✅ Bot hazır ve aktif!")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())