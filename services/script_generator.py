import json
import logging
from openai import OpenAI
import config

logger = logging.getLogger(__name__)

_client = None


def get_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=config.OPENAI_API_KEY)
    return _client


SYSTEM_PROMPT = """You are a short-form video scriptwriter, similar to InVideo AI's script engine.
Given a topic, produce a JSON object with a "title" and a "scenes" array.
Each scene has:
- "narration": one or two spoken sentences (natural, punchy, no stage directions)
- "search_query": 2-4 words describing stock footage/imagery that visually matches the narration
- "duration": estimated seconds this scene should run (4-8 seconds)

Rules:
- Produce between 4 and {max_scenes} scenes.
- Total narration should read naturally as one continuous short video script.
- Return ONLY valid JSON, no markdown fences, no commentary.
"""


def generate_script(topic: str, max_scenes: int = None) -> dict:
    """Call OpenAI to turn a topic into a structured scene-by-scene script.

    Returns a dict: {"title": str, "scenes": [{"narration", "search_query", "duration"}, ...]}
    """
    max_scenes = max_scenes or config.MAX_SCENES
    client = get_client()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT.format(max_scenes=max_scenes)},
            {"role": "user", "content": f"Topic: {topic}"},
        ],
        temperature=0.8,
    )

    raw = response.choices[0].message.content.strip()

    # Defensive cleanup in case the model wraps output in a code fence
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse script JSON: %s\nRaw: %s", e, raw)
        raise ValueError("Script generation returned invalid JSON") from e

    if "scenes" not in data or not data["scenes"]:
        raise ValueError("Script generation returned no scenes")

    return data
