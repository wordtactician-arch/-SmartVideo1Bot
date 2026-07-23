import os
import shutil
import uuid
import logging
from typing import Callable, Awaitable, Optional

import config
from services import script_generator, tts, stock_media, video_builder

logger = logging.getLogger(__name__)

ProgressCB = Optional[Callable[[str], Awaitable[None]]]


async def generate_video_from_topic(topic: str, progress: ProgressCB = None) -> str:
    """Full pipeline: topic -> script -> media -> voiceover -> assembled mp4.

    Returns the path to the final video file. Caller is responsible for cleanup
    of the returned file's parent directory once it's done using it.
    """
    job_id = uuid.uuid4().hex[:8]
    job_dir = os.path.join(config.TMP_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    async def _progress(msg: str):
        if progress:
            await progress(msg)

    try:
        await _progress("📝 Writing your script...")
        script = script_generator.generate_script(topic)
        scenes_meta = script["scenes"]

        await _progress(f"🎬 \"{script.get('title', topic)}\" — {len(scenes_meta)} scenes planned. Fetching footage...")
        scenes = []
        for i, scene in enumerate(scenes_meta):
            media_type, media_path = stock_media.fetch_scene_media(
                scene["search_query"], os.path.join(job_dir, f"scene_{i}")
            )
            scenes.append({
                "media_type": media_type,
                "media_path": media_path,
                "duration": float(scene.get("duration", 5)),
                "narration": scene["narration"],
            })

        await _progress("🗣️ Recording voiceover...")
        full_narration = " ".join(s["narration"] for s in scenes)
        voiceover_path = os.path.join(job_dir, "voiceover.mp3")
        await tts.generate_voiceover(full_narration, voiceover_path)

        await _progress("🎞️ Assembling final video (this can take a minute)...")
        out_path = os.path.join(job_dir, "final.mp4")
        video_builder.assemble_video(scenes, voiceover_path, out_path)

        return out_path

    except Exception:
        shutil.rmtree(job_dir, ignore_errors=True)
        raise


def cleanup_job(video_path: str):
    """Remove the temp job directory once the video has been sent."""
    job_dir = os.path.dirname(video_path)
    shutil.rmtree(job_dir, ignore_errors=True)
