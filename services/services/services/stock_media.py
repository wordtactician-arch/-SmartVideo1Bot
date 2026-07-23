import os
import logging
import requests
import config

logger = logging.getLogger(__name__)

PEXELS_VIDEO_SEARCH = "https://api.pexels.com/videos/search"
PEXELS_PHOTO_SEARCH = "https://api.pexels.com/v1/search"


def _headers():
    return {"Authorization": config.PEXELS_API_KEY}


def search_video(query: str) -> str | None:
    """Search Pexels for a vertical-friendly stock video. Returns a direct download URL or None."""
    params = {"query": query, "per_page": 5, "orientation": "portrait"}
    r = requests.get(PEXELS_VIDEO_SEARCH, headers=_headers(), params=params, timeout=15)
    r.raise_for_status()
    data = r.json()

    for video in data.get("videos", []):
        # Prefer a moderate-resolution file to keep downloads/processing fast
        files = sorted(video.get("video_files", []), key=lambda f: f.get("width", 0))
        for f in files:
            if f.get("width", 0) >= 720 and f.get("file_type") == "video/mp4":
                return f["link"]
        if files:
            return files[-1]["link"]
    return None


def search_photo(query: str) -> str | None:
    """Fallback: search Pexels for a still photo. Returns an image URL or None."""
    params = {"query": query, "per_page": 5, "orientation": "portrait"}
    r = requests.get(PEXELS_PHOTO_SEARCH, headers=_headers(), params=params, timeout=15)
    r.raise_for_status()
    data = r.json()

    photos = data.get("photos", [])
    if photos:
        return photos[0]["src"]["large2x"]
    return None


def download_file(url: str, out_path: str) -> str:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    r = requests.get(url, stream=True, timeout=30)
    r.raise_for_status()
    with open(out_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=1 << 16):
            f.write(chunk)
    return out_path


def fetch_scene_media(query: str, out_path_no_ext: str) -> tuple[str, str]:
    """Fetch either a video or a fallback photo for a scene.

    Returns (media_type, file_path) where media_type is 'video' or 'image'.
    """
    video_url = search_video(query)
    if video_url:
        path = download_file(video_url, out_path_no_ext + ".mp4")
        return "video", path

    photo_url = search_photo(query)
    if photo_url:
        path = download_file(photo_url, out_path_no_ext + ".jpg")
        return "image", path

    logger.warning("No stock media found for query: %s", query)
    raise LookupError(f"No stock footage or photo found for '{query}'")
