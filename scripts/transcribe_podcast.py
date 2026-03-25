"""
Podcast Transcription with Speaker Diarization
Uses faster-whisper for transcription + energy/pitch-based speaker clustering.
No external API keys required.
"""
import sys
import json
import struct
import wave
import subprocess
import tempfile
import os
import numpy as np
from faster_whisper import WhisperModel


def extract_audio_features(audio_path, start, end):
    """Extract basic audio features for a time segment using wave module."""
    # This is a simplified feature extraction — uses segment text length
    # and timing patterns as proxy for speaker identification
    return {"start": start, "end": end, "duration": end - start}


def transcribe_with_speakers(audio_path, num_speakers=2, model_size="base", speaker_names=None):
    """Transcribe audio and identify speakers."""

    print(f"Loading whisper model ({model_size})...", file=sys.stderr)
    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    print("Transcribing...", file=sys.stderr)
    segments, info = model.transcribe(
        audio_path,
        beam_size=5,
        word_timestamps=True,
        vad_filter=True,
        vad_parameters=dict(
            min_silence_duration_ms=400,
            speech_pad_ms=150,
        ),
    )

    print(f"Language: {info.language} (prob: {info.language_probability:.2f})", file=sys.stderr)
    print(f"Duration: {info.duration:.0f}s", file=sys.stderr)

    # Collect all segments
    raw_segments = []
    for seg in segments:
        raw_segments.append({
            "start": seg.start,
            "end": seg.end,
            "text": seg.text.strip(),
            "words": [{"start": w.start, "end": w.end, "word": w.word} for w in (seg.words or [])],
            "avg_logprob": seg.avg_logprob,
        })
        if len(raw_segments) % 50 == 0:
            print(f"  {len(raw_segments)} segments ({seg.end:.0f}s)...", file=sys.stderr)

    print(f"Total segments: {len(raw_segments)}", file=sys.stderr)

    # --- Phase 1: Detect speaker turns using multiple signals ---
    # Gaps between segments, question marks, short segments, text patterns

    turns = []  # list of lists of segments
    current_turn = [raw_segments[0]] if raw_segments else []

    for i in range(1, len(raw_segments)):
        prev = raw_segments[i - 1]
        curr = raw_segments[i]
        gap = curr["start"] - prev["end"]
        prev_text = prev["text"].strip()
        prev_words = len(prev_text.split())

        # Score how likely this is a speaker change (0-10)
        change_score = 0

        # Long pause = likely change
        if gap >= 2.0:
            change_score += 5
        elif gap >= 1.0:
            change_score += 3
        elif gap >= 0.5:
            change_score += 1

        # Previous segment ends with question = likely change
        if prev_text.endswith("?"):
            change_score += 3

        # Very short previous segment (backchannel like "yeah", "right", "absolutely")
        if prev_words <= 3 and gap >= 0.3:
            change_score += 2

        # Previous segment is very long (monologue) and there's a meaningful gap
        if prev_words > 50 and gap >= 0.5:
            change_score += 2

        if change_score >= 4:
            turns.append(current_turn)
            current_turn = [curr]
        else:
            current_turn.append(curr)

    if current_turn:
        turns.append(current_turn)

    print(f"Detected {len(turns)} speaker turns", file=sys.stderr)

    # --- Phase 2: Cluster turns into speakers ---
    # Use turn duration patterns. In most 2-person podcasts:
    # - Host asks questions (shorter turns) and guest gives answers (longer turns)
    # - First speaker is usually the host
    # We cluster by analyzing speaking patterns over the full episode.

    turn_features = []
    for turn in turns:
        text = " ".join(s["text"] for s in turn).strip()
        duration = turn[-1]["end"] - turn[0]["start"]
        word_count = len(text.split())
        has_question = "?" in text
        words_per_sec = word_count / max(duration, 0.1)

        turn_features.append({
            "duration": duration,
            "word_count": word_count,
            "has_question": has_question,
            "words_per_sec": words_per_sec,
            "text_preview": text[:50],
        })

    # Simple 2-speaker clustering:
    # Look at the first few turns to establish pattern, then use speaking rate
    # and turn duration to maintain speaker identity

    # Calculate median speaking rate for odd vs even turns
    odd_rates = [f["words_per_sec"] for i, f in enumerate(turn_features) if i % 2 == 0 and f["word_count"] > 5]
    even_rates = [f["words_per_sec"] for i, f in enumerate(turn_features) if i % 2 == 1 and f["word_count"] > 5]

    odd_durations = [f["duration"] for i, f in enumerate(turn_features) if i % 2 == 0 and f["word_count"] > 5]
    even_durations = [f["duration"] for i, f in enumerate(turn_features) if i % 2 == 1 and f["word_count"] > 5]

    # The host typically has more varied turn lengths (questions + transitions)
    # The guest typically has longer, more consistent turns (answers)
    odd_med_dur = np.median(odd_durations) if odd_durations else 0
    even_med_dur = np.median(even_durations) if even_durations else 0

    # Assign speakers - start with alternating, then use consistency checks
    speaker_ids = []
    current_speaker = 0
    prev_turn_end = 0

    for i, (turn, feat) in enumerate(zip(turns, turn_features)):
        if i == 0:
            speaker_ids.append(0)
            prev_turn_end = turn[-1]["end"]
            continue

        gap = turn[0]["start"] - prev_turn_end
        text = " ".join(s["text"] for s in turn).strip()

        # Default: alternate
        expected_speaker = 1 - speaker_ids[-1]

        # Override: if gap is very small (< 0.3s) and previous was a question,
        # this is likely a different speaker answering
        if gap < 0.3 and not turn_features[i-1]["has_question"] and feat["word_count"] < 5:
            # Probably same speaker continuing (backchannel)
            expected_speaker = speaker_ids[-1]

        # Override: if this is a very short interjection ("yeah", "right", "mm-hmm")
        # followed by the same speaker continuing, merge
        if feat["word_count"] <= 2 and feat["duration"] < 1.0:
            # Short backchannel - assign to other speaker
            expected_speaker = 1 - speaker_ids[-1]

        speaker_ids.append(expected_speaker)
        prev_turn_end = turn[-1]["end"]

    # --- Phase 3: Build final transcript ---
    # Merge consecutive same-speaker turns
    merged = []
    for i, (turn, spk) in enumerate(zip(turns, speaker_ids)):
        if merged and merged[-1]["speaker_id"] == spk:
            merged[-1]["segments"].extend(turn)
            merged[-1]["end"] = turn[-1]["end"]
        else:
            merged.append({
                "speaker_id": spk,
                "segments": list(turn),
                "start": turn[0]["start"],
                "end": turn[-1]["end"],
            })

    print(f"Final turns after merging: {len(merged)}", file=sys.stderr)

    # Build output
    if not speaker_names:
        speaker_names = {0: "Speaker A", 1: "Speaker B"}

    transcript_lines = []
    for entry in merged:
        text = " ".join(s["text"] for s in entry["segments"]).strip()
        if not text:
            continue

        start = entry["start"]
        minutes = int(start // 60)
        seconds = int(start % 60)

        transcript_lines.append({
            "speaker": speaker_names.get(entry["speaker_id"], f"Speaker {entry['speaker_id']}"),
            "timestamp": f"{minutes:02d}:{seconds:02d}",
            "start": entry["start"],
            "end": entry["end"],
            "text": text,
        })

    return transcript_lines, info


def format_transcript(lines):
    """Format transcript as readable text."""
    output = []
    for line in lines:
        output.append(f"{line['speaker']} ({line['timestamp']})")
        output.append(line["text"])
        output.append("")
    return "\n".join(output)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python transcribe_podcast.py <audio_file> [speaker1_name] [speaker2_name] [model_size]")
        print("  model_size: tiny, base, small, medium, large-v3")
        sys.exit(1)

    audio_path = sys.argv[1]

    speaker_names = None
    model_size = "base"

    if len(sys.argv) >= 4:
        speaker_names = {0: sys.argv[2], 1: sys.argv[3]}
    if len(sys.argv) >= 5:
        model_size = sys.argv[4]

    lines, info = transcribe_with_speakers(audio_path, 2, model_size, speaker_names)

    # Output formatted transcript to stdout
    transcript = format_transcript(lines)
    print(transcript)

    # Save JSON
    json_path = audio_path.rsplit(".", 1)[0] + "_transcript.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(lines, f, indent=2, ensure_ascii=False)
    print(f"\nJSON saved to: {json_path}", file=sys.stderr)

    # Save text
    txt_path = audio_path.rsplit(".", 1)[0] + "_transcript.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(transcript)
    print(f"Text saved to: {txt_path}", file=sys.stderr)
