import asyncio
import aiohttp
import sqlite3
import io
import re
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery

id_app = 33077604 
hash_app = "119992704d1dd27a6ebf9d3327189204"
token_bot = "8479533926:AAG1HB9BkZd6rR1775kQyItM7zMKuEXUQfY"

owners = [6534222591, 8656150458]
sight_user = "1340231497"
sight_key = "yhhqoZzzN6rtdpjQKkvvd6tCvspMW2Vb"

def lol_db_init():
    conn = sqlite3.connect("data.db")
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS grps (
        id INTEGER PRIMARY KEY, 
        t_lkt INTEGER DEFAULT 0, t_val TEXT, 
        p_lkt INTEGER DEFAULT 0, p_id TEXT, 
        c_lkt INTEGER DEFAULT 0, 
        n_lkt INTEGER DEFAULT 0, n_thr REAL DEFAULT 0.60, n_txt TEXT, 
        l_ch INTEGER DEFAULT 0, 
        r_lkt INTEGER DEFAULT 0, 
        w_lkt INTEGER DEFAULT 0, w_txt TEXT, w_med TEXT)""")
    conn.commit()
    conn.close()

def lol_get(cid):
    conn = sqlite3.connect("data.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM grps WHERE id = ?", (cid,))
    res = cur.fetchone()
    conn.close()
    return dict(res) if res else None

def lol_upd(cid, k, v):
    conn = sqlite3.connect("data.db")
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO grps (id, n_txt, w_txt) VALUES (?, ?, ?)", 
               (cid, "{mention} yasak.", "hoÅ geldin {mention}"))
    cur.execute(f"UPDATE grps SET {k} = ? WHERE id = ?", (v, cid))
    conn.commit()
    conn.close()

app = Client("engine", api_id=id_app, api_hash=hash_app, bot_token=token_bot)

async def lol_scan(bits):
    url = "https://api.sightengine.com/1.0/check.json"
    form = aiohttp.FormData()
    form.add_field('models', 'nudity-2.0,wad,drugs')
    form.add_field('api_user', sight_user)
    form.add_field('api_secret', sight_key)
    form.add_field('media', bits, filename='c.jpg')
    async with aiohttp.ClientSession() as sess:
        try:
            async with sess.post(url, data=form) as r:
                res = await r.json()
                if res.get("status") != "success": return 0
                nude = res.get("nudity", {})
                v = max(nude.get("sexual_activity", 0), nude.get("sexual_display", 0), nude.get("erotica", 0))
                return max(v, res.get("weapon", 0), res.get("drugs", 0))
        except: return 0

@app.on_message(filters.command("start") & filters.private)
async def lol_start(cl, m):
    if m.from_user.id not in owners:
        return await m.reply("yetki yok.")
    
    conn = sqlite3.connect("data.db")
    cur = conn.cursor()
    cur.execute("SELECT id FROM grps")
    rows = cur.fetchall()
    conn.close()

    btns = []
    for r in rows:
        try:
            chat = await cl.get_chat(r[0])
            btns.append([InlineKeyboardButton(chat.title, callback_data=f"p_{chat.id}")])
        except: continue

    if not btns:
        return await m.reply("kayÄ±tlÄ± grup yok. grupta bir mesaj yazÄ±n.")
        
    await m.reply("grup:", reply_markup=InlineKeyboardMarkup(btns))

@app.on_callback_query(filters.regex("^p_"))
async def lol_panel(cl, cq):
    cid = int(cq.data.split("_")[1])
    d = lol_get(cid) or {"c_lkt": 0, "n_lkt": 0, "r_lkt": 0, "w_lkt": 0}
    t = f"id: {cid}\n\ns: {d.get('c_lkt')}\nai: {d.get('n_lkt')}\nr: {d.get('r_lkt')}\nk: {d.get('w_lkt')}"
    mk = InlineKeyboardMarkup([
        [InlineKeyboardButton("s", callback_data=f"t_c_lkt_{cid}"), InlineKeyboardButton("r", callback_data=f"t_r_lkt_{cid}")],
        [InlineKeyboardButton("ai", callback_data=f"t_n_lkt_{cid}"), InlineKeyboardButton("k", callback_data=f"t_w_lkt_{cid}")],
        [InlineKeyboardButton("geri", callback_data="back")]
    ])
    await cq.edit_message_text(t, reply_markup=mk)

@app.on_callback_query(filters.regex("^t_"))
async def lol_toggle(cl, cq):
    _, k, cid = cq.data.split("_", 2)
    cid = int(cid)
    d = lol_get(cid) or {k: 0}
    nv = 0 if d.get(k) else 1
    lol_upd(cid, k, nv)
    await lol_panel(cl, cq)

@app.on_callback_query(filters.regex("^back"))
async def lol_back(cl, cq):
    await lol_start(cl, cq.message)

@app.on_message(filters.group)
async def lol_core(cl, m):
    cid = m.chat.id
    d = lol_get(cid)
    if not d:
        lol_upd(cid, "id", cid)
        d = lol_get(cid)

    uid = m.from_user.id if m.from_user else 0

    if not m.service:
        if d.get("c_lkt") and uid not in owners:
            try: return await m.delete()
            except: pass

        if d.get("r_lkt") and uid not in owners:
            raw = (m.text or m.caption or "").lower()
            if any(x in raw for x in ["http", "t.me/", ".com", ".net", ".org", "bot"]):
                return await m.delete()
            if "@" in raw:
                men = re.findall(r"@(\w+)", raw)
                for u in men:
                    try:
                        f = await cl.get_users(u) if not u.isdigit() else None
                        if not f: f = await cl.get_chat(u)
                        if f: return await m.delete()
                    except: pass

        if d.get("n_lkt") and uid not in owners and (m.photo or m.video):
            try:
                f_d = await cl.download_media(m, in_memory=True)
                s = await lol_scan(f_d.getbuffer())
                if s >= d["n_thr"]:
                    await m.delete()
                    await cl.send_message(cid, d["n_txt"].format(mention=m.from_user.mention))
                    if d["l_ch"]:
                        f_d.seek(0)
                        await cl.send_photo(d["l_ch"], photo=f_d, caption=f"id: {uid}\ns: {s}")
            except: pass
    else:
        if m.new_chat_title and d.get("t_lkt"):
            if m.new_chat_title != d["t_val"]:
                try: await cl.set_chat_title(cid, d["t_val"])
                except: pass
        if (m.new_chat_photo or m.delete_chat_photo) and d.get("p_lkt"):
            if d["p_id"]:
                try: await cl.set_chat_photo(cid, photo=d["p_id"])
                except: pass

@app.on_message(filters.group & filters.new_chat_members)
async def lol_wel(cl, m):
    cid = m.chat.id
    d = lol_get(cid)
    if not d or not d["w_lkt"]: return
    for u in m.new_chat_members:
        tx = d["w_txt"].format(mention=u.mention, title=m.chat.title, id=u.id)
        try:
            if d["w_med"]: await cl.send_cached_media(cid, d["w_med"], caption=tx)
            else: await cl.send_message(cid, tx)
        except: await cl.send_message(cid, tx)

if __name__ == "__main__":
    lol_db_init()
    app.run()