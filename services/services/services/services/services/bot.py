import logging
import os

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

import config
from services.pipeline import generate_video_from_topic, cleanup_job

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 I'm SmartVideoBot.\n\n"
        "Send me a topic or short description and I'll write a script, "
        "grab matching footage, record a voiceover, and send you back a finished short video.\n\n"
        "Example: \"5 tips for staying focused while working from home\""
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Just send me any topic as a normal message and I'll turn it into a video.\n"
        "Generation usually takes 1-3 minutes depending on length."
    )


async def handle_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    topic = update.message.text.strip()
    if not topic:
        return

    status_msg = await update.message.reply_text("🚀 Starting video generation...")

    async def progress(text: str):
        try:
            await status_msg.edit_text(text)
        except Exception:
            pass  # ignore "message not modified" or rate-limit edge cases

    video_path = None
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_VIDEO)
        video_path = await generate_video_from_topic(topic, progress=progress)

        await status_msg.edit_text("📤 Uploading your video...")
        with open(video_path, "rb") as f:
            await update.message.reply_video(video=f, caption=f"✅ Here's your video on: {topic}")
        await status_msg.delete()

    except Exception as e:
        logger.exception("Video generation failed")
        await status_msg.edit_text(
            "❌ Something went wrong generating that video. "
            "Try a different/simpler topic, or try again in a moment.\n\n"
            f"Details: {e}"
        )
    finally:
        if video_path:
            cleanup_job(video_path)


def main():
    config.validate_config()
    os.makedirs(config.TMP_DIR, exist_ok=True)

    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_topic))

    logger.info("SmartVideoBot starting (polling mode)...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
