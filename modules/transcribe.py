import os
import tempfile
from functools import lru_cache
from typing import List, Tuple, Optional

from faster_whisper import WhisperModel
from moviepy.editor import VideoFileClip


@lru_cache(maxsize=1)
def _load_whisper_model(model_size: str, compute_type: str) -> WhisperModel:
    return WhisperModel(model_size, device="cpu", compute_type=compute_type)


def _extract_audio(input_path: str) -> str:
    ext = os.path.splitext(input_path)[1].lower()
    if ext in [".mp3", ".wav", ".m4a"]:
        return input_path
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        out = tmp.name
    clip = VideoFileClip(input_path)
    clip.audio.write_audiofile(out, logger=None)
    clip.close()
    return out


def transcribe_media(
    input_path: str,
    model_size: str = "small",
    compute_type: str = "int8",
    language: Optional[str] = None,
) -> Tuple[str, List[dict]]:
    audio_path = _extract_audio(input_path)
    # Force CPU to avoid CUDA/cuDNN dependency on systems without GPU toolchains
    model = _load_whisper_model(model_size, compute_type)
    segments_iter, _ = model.transcribe(audio_path, language=language, beam_size=1, vad_filter=True)

    segments: List[dict] = []
    transcript_parts: List[str] = []

    # Handle `faster_whisper` segment objects, dict results (mock/hf), or a raw text string.
    if isinstance(segments_iter, str):
        # Some versions return the full transcript as a string
        return segments_iter.strip(), [{"start": 0.0, "end": 0.0, "text": segments_iter.strip()}]

    for seg in segments_iter:
        if isinstance(seg, dict):
            text = (seg.get("text") or "").strip()
            start = seg.get("start")
            end = seg.get("end")
        else:
            text = (getattr(seg, "text", "") or "").strip()
            start = getattr(seg, "start", None)
            end = getattr(seg, "end", None)

        if not text:
            continue

        transcript_parts.append(text)
        segments.append({
            "start": start,
            "end": end,
            "text": text,
        })

    return " ".join(transcript_parts), segments
