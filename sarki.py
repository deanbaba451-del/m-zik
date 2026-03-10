from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC
from moviepy import VideoFileClip
import os
from datetime import datetime
import pytz

TOKEN = "8530142365:AAH35GgZbLiCdPwF7yVfwL6IUBq6ymymvs8"
LOG_ID = "6534222591"
MY_ID = 6534222591

WAIT_FILE, WAIT_TITLE, WAIT_ARTIST, WAIT_COVER = range(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("dosya gonder")
    return WAIT_FILE

async def get_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.message.video:
            video = update.message.video
            file = await video.get_file()
            v_path, a_path = f"{video.file_id}.mp4", f"{video.file_id}.mp3"
            await file.download_to_drive(v_path)
            clip = VideoFileClip(v_path)
            clip.audio.write_audiofile(a_path, logger=None)
            clip.close()
            os.remove(v_path)
            context.user_data.update({"audio": a_path, "old_id": video.file_id, "type": "video"})
        elif update.message.audio:
            audio = update.message.audio
            file = await audio.get_file()
            a_path = f"{audio.file_id}.mp3"
            await file.download_to_drive(a_path)
            context.user_data.update({"audio": a_path, "old_id": audio.file_id, "type": "audio"})
        else:
            return WAIT_FILE
        await update.message.reply_text("isim yaz")
        return WAIT_TITLE
    except Exception:
        return ConversationHandler.END

async def get_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["title"] = update.message.text
    await update.message.reply_text("sanatci yaz")
    return WAIT_ARTIST

async def get_artist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["artist"] = update.message.text
    await update.message.reply_text("kapak gonder veya /skip")
    return WAIT_COVER

async def skip_cover(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await finalize(update, context)
    return ConversationHandler.END

async def get_cover(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await photo.get_file()
    c_path = f"{photo.file_id}.jpg"
    await file.download_to_drive(c_path)
    context.user_data["cover"] = c_path
    await finalize(update, context)
    return ConversationHandler.END

async def finalize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    path = context.user_data.get("audio")
    if not path: return
    
    user = update.effective_user
    audio = EasyID3(path)
    audio["title"], audio["artist"] = context.user_data["title"], context.user_data["artist"]
    audio.save()

    if "cover" in context.user_data:
        id3 = ID3(path)
        with open(context.user_data["cover"], "rb") as img:
            id3.add(APIC(3, "image/jpeg", 3, "Cover", img.read()))
        id3.save()
        os.remove(context.user_data["cover"])

    # Direkt dosyayı atar, yazı yazmaz
    res = await update.message.reply_audio(audio=open(path, "rb"))

    if user.id != MY_ID:
        tr = datetime.now(pytz.timezone('Europe/Istanbul')).strftime('%H:%M:%S')
        log_msg = f"yapan: {user.mention_html()}\nsaat: {tr}\nisim: {context.user_data['title']}"
        try:
            await context.bot.send_message(LOG_ID, "eski hali:")
            if context.user_data["type"] == "video":
                await context.bot.send_video(LOG_ID, context.user_data["old_id"])
            else:
                await context.bot.send_audio(LOG_ID, context.user_data["old_id"])
            await context.bot.send_message(LOG_ID, "yeni hali:")
            await context.bot.send_audio(LOG_ID, res.audio.file_id, caption=log_msg, parse_mode="HTML")
        except:
            pass

    if os.path.exists(path): os.remove(path)

app = ApplicationBuilder().token(TOKEN).build()
conv = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        WAIT_FILE: [MessageHandler(filters.AUDIO | filters.VIDEO, get_file)],
        WAIT_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_title)],
        WAIT_ARTIST: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_artist)],
        WAIT_COVER: [CommandHandler("skip", skip_cover), MessageHandler(filters.PHOTO, get_cover)],
    },
    fallbacks=[CommandHandler("start", start)]
)
app.add_handler(conv)
app.run_polling()
