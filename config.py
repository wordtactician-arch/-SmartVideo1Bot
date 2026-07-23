import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")

# Video settings
VIDEO_WIDTH = int(os.getenv("VIDEO_WIDTH", "1080"))
VIDEO_HEIGHT = int(os.getenv("VIDEO_HEIGHT", "1920"))  # default: vertical/shorts format
FPS = int(os.getenv("FPS", "30"))
MAX_SCENES = int(os.getenv("MAX_SCENES", "6"))
TTS_VOICE = os.getenv("TTS_VOICE", "en-US-GuyNeural")  # edge-tts voice

TMP_DIR = os.getenv("TMP_DIR", "/tmp/smartvideobot")

REQUIRED_VARS = {
    "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
    "OPENAI_API_KEY": OPENAI_API_KEY,
    "PEXELS_API_KEY": PEXELS_API_KEY,
}


def validate_config():
    missing = [k for k, v in REQUIRED_VARS.items() if not v]
    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Set them in your .env file locally or in Railway's Variables tab."
        )
