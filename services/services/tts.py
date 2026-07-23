import os
import edge_tts
import config


async def generate_voiceover(text: str, out_path: str, voice: str = None) -> str:
    """Generate an mp3 voiceover for the given text using edge-tts (free, no API key).

    Returns the path to the generated mp3 file.
    """
    voice = voice or config.TTS_VOICE
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(out_path)
    return out_path
