import asyncio
import re
import os
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from aiohttp import web

# --- AYARLAR ---
API_ID = 36856573
API_HASH = '9045fafb55bc4aa6fa2aadafbb1f2e1e'
SESSION_STRING = '1BJWap1sBu4GSAP5620LpBYu4P_PQhCkZTG8NQOxrjjItv_xLMF6liSCqVcDSOm6BzfW4Gvtco-POckMRBFyi17DItKbUA4bpbNPIbv-QCCQ61WkfvwODGiW2TifaShCb7qZPr3D7sr4FS0De5FUO9CPsuGFPr2n0KiyWun4PRBU9ixwlU6JNTbt1ki6cUr123bZ3db3QVrt6Ao5iZl6nVIcVw_KhfBZJL9LQiIVeBOQcLovEab1z6aIEAhej4uDRx7Mlu-5CtxkcP6X7BdeSLV5LOwiHo7tv-Iqpd0ZxQ58cYB9ywAt4VfXAyQvR7PXNO5RPgjAj8vLxpxs1G8lvtNevxyn-UX8='

# SADECE BU GRUPTA ÇALIŞIR
TARGET_GROUP_ID = -1003626403225 

# Komut yetkisi olan kişiler
AUTHORIZED_IDS = [8343507331, 6534222591, 8256872080, 7727812432]
bot_mode = 0 

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# --- RENDER WEB SUNUCUSU ---
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

# --- SESSİZ YANIT SİSTEMİ ---
async def silent_response(event, text):
    # Senin yazdığın komutu (/doeda vb.) anında siler
    await event.delete()
    # Botun verdiği yanıtı 4 saniye sonra siler
    msg = await event.respond(text)
    await asyncio.sleep(4)
    await msg.delete()

# --- BOT KOMUTLARI ---
@client.on(events.NewMessage(pattern=r'/(doeda|gayeda|stop)', from_users=AUTHORIZED_IDS))
async def command_handler(event):
    # Başka gruptaysa hiçbir şey yapma
    if event.chat_id != TARGET_GROUP_ID:
        return 

    global bot_mode
    cmd = event.pattern_match.group(1)

    if cmd == 'doeda':
        bot_mode = 1
        await silent_response(event, "🛡 **Doeda Modu Aktif.**")
    elif cmd == 'gayeda':
        bot_mode = 2
        await silent_response(event, "🛡 **Gayeda Modu Aktif.**")
    elif cmd == 'stop':
        bot_mode = 0
        await silent_response(event, "🛑 **Koruma Durduruldu.**")

# --- KORUMA VE NUMARA FİLTRESİ ---
@client.on(events.NewMessage)
async def protection_handler(event):
    global bot_mode
    
    # Sadece hedef grupta çalış ve yetkilileri/kendini atla
    if event.chat_id != TARGET_GROUP_ID or event.sender_id in AUTHORIZED_IDS or event.out:
        return

    # 1. ÖNCELİK: NUMARA SİLME (Her zaman aktif)
    if re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', event.raw_text):
        await event.delete()
        return

    # 2. MODLARA GÖRE SİLME
    if bot_mode == 1:
        await event.delete()
    elif bot_mode == 2:
        if event.media and not (event.voice or event.audio):
            await event.delete()

async def main():
    await run_web_server()
    await client.connect()
    if not await client.is_user_authorized():
        print("HATA: Session Geçersiz!")
        return
    print("✅ Bot Belirlenen Grupta Hazır!")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
