#!/usr/bin/env python3
"""
Podcast Transcription Engine using faster-whisper + pyannote speaker diarization.

Usage:
  python transcribe.py --input /path/to/audio.mp3
  python transcribe.py --input /path/to/audio.mp3 --diarize --hf-token TOKEN
  python transcribe.py --input /path/to/audio.mp3 --model large-v3 --language en

Output: JSON to stdout with segments, timestamps, and optional speaker labels.
"""

import argparse
import glob
import json
import os
import sys
import time
from pathlib import Path

# Ensure ffmpeg is on PATH (winget installs to a non-PATH location)
_FFMPEG_WINGET = glob.glob(
    os.path.expandvars(
        r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*\ffmpeg-*\bin"
    )
)
if _FFMPEG_WINGET:
    os.environ["PATH"] = _FFMPEG_WINGET[0] + os.pathsep + os.environ.get("PATH", "")


def check_faster_whisper():
    try:
        import faster_whisper
        return True
    except ImportError:
        return False


def check_pyannote():
    try:
        from pyannote.audio import Pipeline
        return True
    except ImportError:
        return False


def transcribe_audio(audio_path, model_size, compute_type, device, beam_size, language):
    from faster_whisper import WhisperModel

    sys.stderr.write(f"Loading model {model_size} ({compute_type} on {device})...\n")
    sys.stderr.flush()
    model = WhisperModel(model_size, device=device, compute_type=compute_type)

    sys.stderr.write(f"Transcribing {audio_path}...\n")
    sys.stderr.flush()
    start_time = time.time()

    segments_gen, info = model.transcribe(
        str(audio_path),
        beam_size=beam_size,
        language=language,
        vad_filter=True,
        vad_parameters=dict(
            min_silence_duration_ms=500,
            speech_pad_ms=200,
        ),
    )

    segments = []
    for seg in segments_gen:
        segments.append({
            "start": round(seg.start, 3),
            "end": round(seg.end, 3),
            "text": seg.text.strip(),
            "speaker": None,
        })

    elapsed = time.time() - start_time
    sys.stderr.write(f"Transcription complete in {elapsed:.1f}s\n")
    sys.stderr.flush()

    return segments, {
        "language": info.language,
        "language_probability": round(info.language_probability, 3),
        "duration_seconds": round(info.duration, 1),
        "transcription_seconds": round(elapsed, 1),
    }


def load_audio_waveform(audio_path):
    """Load audio as a waveform dict that pyannote can consume directly,
    bypassing torchcodec's need for ffmpeg shared libraries."""
    import torch
    import torchaudio

    waveform, sample_rate = torchaudio.load(str(audio_path))
    # pyannote expects mono; average channels if stereo
    if waveform.shape[0] > 1:
        waveform = waveform.mean(dim=0, keepdim=True)
    return {"waveform": waveform, "sample_rate": sample_rate}


def diarize_and_align(audio_path, segments, hf_token):
    """Run pyannote speaker diarization and align with whisper segments."""
    from pyannote.audio import Pipeline

    sys.stderr.write("Running speaker diarization...\n")
    sys.stderr.flush()
    start_time = time.time()

    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        use_auth_token=hf_token,
    )

    # Load audio as waveform to avoid torchcodec/ffmpeg DLL issues on Windows
    sys.stderr.write("Loading audio waveform...\n")
    sys.stderr.flush()
    audio_input = load_audio_waveform(audio_path)
    diarization = pipeline(audio_input)

    # Build a list of (start, end, speaker) from pyannote
    speaker_segments = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        speaker_segments.append({
            "start": turn.start,
            "end": turn.end,
            "speaker": speaker,
        })

    # Align whisper segments to speaker labels using midpoint overlap
    for seg in segments:
        seg_mid = (seg["start"] + seg["end"]) / 2
        best_speaker = None
        best_overlap = 0

        for sp in speaker_segments:
            # Calculate overlap between whisper segment and speaker segment
            overlap_start = max(seg["start"], sp["start"])
            overlap_end = min(seg["end"], sp["end"])
            overlap = max(0, overlap_end - overlap_start)

            if overlap > best_overlap:
                best_overlap = overlap
                best_speaker = sp["speaker"]

        # Fallback to midpoint if no overlap found
        if best_speaker is None:
            for sp in speaker_segments:
                if sp["start"] <= seg_mid <= sp["end"]:
                    best_speaker = sp["speaker"]
                    break

        seg["speaker"] = best_speaker

    elapsed = time.time() - start_time
    sys.stderr.write(f"Diarization complete in {elapsed:.1f}s\n")
    sys.stderr.flush()

    # Collect unique speakers
    speakers = sorted(set(s["speaker"] for s in segments if s["speaker"]))
    return segments, speakers


def merge_consecutive_speaker_segments(segments):
    """Merge consecutive segments from the same speaker into longer blocks."""
    if not segments:
        return segments

    merged = [segments[0].copy()]
    for seg in segments[1:]:
        prev = merged[-1]
        # Merge if same speaker and gap is < 2 seconds
        if (seg["speaker"] == prev["speaker"]
                and seg["speaker"] is not None
                and seg["start"] - prev["end"] < 2.0):
            prev["end"] = seg["end"]
            prev["text"] = prev["text"] + " " + seg["text"]
        else:
            merged.append(seg.copy())

    return merged


def format_timestamp(seconds):
    """Format seconds as HH:MM:SS."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def main():
    config_path = Path(__file__).parent / "config.json"
    config = {}
    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)

    parser = argparse.ArgumentParser(description="Transcribe podcast audio")
    parser.add_argument("--input", required=True, help="Path to audio file")
    parser.add_argument("--model", default=config.get("model_size", "large-v3"))
    parser.add_argument("--compute-type", default=config.get("compute_type", "int8"))
    parser.add_argument("--device", default=config.get("device", "cpu"))
    parser.add_argument("--beam-size", type=int, default=config.get("beam_size", 5))
    parser.add_argument("--language", default=config.get("language", "en"))
    parser.add_argument("--diarize", action="store_true", help="Enable speaker diarization")
    parser.add_argument("--hf-token", default=os.environ.get("HF_TOKEN"), help="HuggingFace token for pyannote")
    args = parser.parse_args()

    audio_path = Path(args.input)
    if not audio_path.exists():
        print(json.dumps({"status": "error", "message": f"File not found: {audio_path}"}))
        sys.exit(1)

    # Check dependencies
    if not check_faster_whisper():
        print(json.dumps({
            "status": "error",
            "message": "faster-whisper is not installed",
            "install": "pip install faster-whisper",
        }))
        sys.exit(1)

    if args.diarize and not args.hf_token:
        print(json.dumps({
            "status": "error",
            "message": "Speaker diarization requires a HuggingFace token. "
                       "Get one at https://huggingface.co/settings/tokens and accept "
                       "the pyannote terms at https://huggingface.co/pyannote/speaker-diarization-3.1",
            "install": "pip install pyannote.audio && set HF_TOKEN=your_token",
        }))
        sys.exit(1)

    if args.diarize and not check_pyannote():
        print(json.dumps({
            "status": "error",
            "message": "pyannote.audio is not installed (required for speaker diarization)",
            "install": "pip install pyannote.audio",
        }))
        sys.exit(1)

    # Transcribe
    segments, info = transcribe_audio(
        audio_path, args.model, args.compute_type, args.device, args.beam_size, args.language
    )

    speakers = []
    if args.diarize:
        segments, speakers = diarize_and_align(audio_path, segments, args.hf_token)
        segments = merge_consecutive_speaker_segments(segments)

    # Build full text
    full_text = " ".join(s["text"] for s in segments)

    output = {
        "status": "success",
        "input_file": audio_path.name,
        "model": args.model,
        "compute_type": args.compute_type,
        "device": args.device,
        "language": info["language"],
        "language_probability": info["language_probability"],
        "duration_seconds": info["duration_seconds"],
        "transcription_seconds": info["transcription_seconds"],
        "diarization": args.diarize,
        "speakers": speakers,
        "segment_count": len(segments),
        "word_count": len(full_text.split()),
        "segments": segments,
        "full_text": full_text,
    }

    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
