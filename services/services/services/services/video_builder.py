import os
import logging
from moviepy.editor import (
    VideoFileClip,
    ImageClip,
    AudioFileClip,
    CompositeVideoClip,
    TextClip,
    concatenate_videoclips,
)
import config

logger = logging.getLogger(__name__)


def _fit_to_frame(clip, w, h):
    """Resize/crop a clip to fill the target frame (center-crop), like a mobile-first video editor."""
    clip_ratio = clip.w / clip.h
    target_ratio = w / h

    if clip_ratio > target_ratio:
        clip = clip.resize(height=h)
        clip = clip.crop(x_center=clip.w / 2, width=w)
    else:
        clip = clip.resize(width=w)
        clip = clip.crop(y_center=clip.h / 2, height=h)
    return clip


def _caption_clip(text: str, duration: float, w: int, h: int):
    txt = TextClip(
        text,
        fontsize=54,
        color="white",
        font="DejaVu-Sans-Bold",
        method="caption",
        size=(int(w * 0.85), None),
        stroke_color="black",
        stroke_width=2,
    ).set_duration(duration)
    txt = txt.set_position(("center", h * 0.78))
    return txt


def build_scene_clip(media_type: str, media_path: str, duration: float, caption: str):
    w, h = config.VIDEO_WIDTH, config.VIDEO_HEIGHT

    if media_type == "video":
        base = VideoFileClip(media_path)
        if base.duration < duration:
            # loop short clips by freezing the last frame for the remainder
            base = base.loop(duration=duration)
        base = base.subclip(0, duration)
    else:
        base = ImageClip(media_path).set_duration(duration)
        # subtle Ken Burns zoom for stills
        base = base.resize(lambda t: 1 + 0.04 * (t / duration))

    base = _fit_to_frame(base, w, h).set_position("center")
    caption_clip = _caption_clip(caption, duration, w, h)

    return CompositeVideoClip([base, caption_clip], size=(w, h)).set_duration(duration)


def assemble_video(scenes: list[dict], voiceover_path: str, out_path: str) -> str:
    """scenes: list of {"media_type", "media_path", "duration", "narration"}"""
    w, h = config.VIDEO_WIDTH, config.VIDEO_HEIGHT

    clips = [
        build_scene_clip(s["media_type"], s["media_path"], s["duration"], s["narration"])
        for s in scenes
    ]

    final = concatenate_videoclips(clips, method="compose")

    audio = AudioFileClip(voiceover_path)
    # Match video length to audio length (voiceover is the source of truth for pacing)
    if audio.duration < final.duration:
        final = final.subclip(0, audio.duration)
    final = final.set_audio(audio)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    final.write_videofile(
        out_path,
        fps=config.FPS,
        codec="libx264",
        audio_codec="aac",
        threads=4,
        preset="veryfast",
        logger=None,
    )

    for c in clips:
        c.close()
    final.close()
    audio.close()

    return out_path
