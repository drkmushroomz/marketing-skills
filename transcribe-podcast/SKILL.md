---
name: transcribe-podcast
description: Transcribe podcast audio files from Google Drive with speaker diarization using faster-whisper
disable-model-invocation: true
---

# Transcribe Podcast

Transcribe podcast audio files from Google Drive using faster-whisper (large-v3) with optional speaker diarization via pyannote. Saves transcripts back to the same Drive folder as Google Docs.

## Arguments

The user may specify:
- A Google Drive folder URL or ID (default: use `default_folder_id` from config)
- A specific file name to transcribe (default: list all audio files and ask)
- `--no-diarize` to skip speaker labeling (diarization is ON by default)
- `--language XX` to override language detection (default: `en`)
- `--model` to override model size (default: `large-v3`)

## Steps

1. **Load identity and settings:**
   - Read `.claude/me.md` for user email. If missing, STOP and tell user to run `./setup.sh`.
   - Read `.claude/ops/transcribe-podcast/config.json` for defaults.

2. **Parse the folder ID:**
   - If the user provides a Google Drive URL, extract the folder ID from it.
   - If no folder specified, use `default_folder_id` from config.

3. **Check prerequisites (first run only):**

   a. Test ffmpeg:
   ```bash
   ffmpeg -version
   ```
   If missing, install it:
   ```bash
   winget install Gyan.FFmpeg --accept-package-agreements --accept-source-agreements
   ```
   After install, tell the user: "ffmpeg installed. You may need to restart your terminal for it to be on PATH."

   b. Test faster-whisper:
   ```bash
   python -c "import faster_whisper; print(faster_whisper.__version__)"
   ```
   If missing:
   ```bash
   pip install faster-whisper
   ```

   c. If diarization is requested, test pyannote:
   ```bash
   python -c "from pyannote.audio import Pipeline; print('ok')"
   ```
   If missing:
   ```bash
   pip install pyannote.audio
   ```
   Also check for HuggingFace token:
   - Check `HF_TOKEN` environment variable
   - If not set, ask the user for their token. They need to:
     1. Create a token at https://huggingface.co/settings/tokens
     2. Accept the pyannote model terms at https://huggingface.co/pyannote/speaker-diarization-3.1
     3. Accept the segmentation model terms at https://huggingface.co/pyannote/segmentation-3.0
   - Pass the token via `--hf-token` to the script

4. **List audio files in Google Drive folder:**
   - Use `mcp__google-workspace__list_drive_items` with the folder ID.
   - Filter for audio file extensions: `.mp3`, `.wav`, `.m4a`, `.flac`, `.ogg`, `.wma`, `.aac`, `.mp4` (some podcasts are video).
   - Present the list to the user with file sizes.
   - Ask which file(s) to transcribe, or confirm "all" if user already specified.
   - Also check for existing transcript docs (names containing "Transcript") to avoid re-transcribing.

5. **Download audio file(s):**
   - For each file, use `mcp__google-workspace__get_drive_file_download_url` to download to local disk.
   - Note the returned local file path.

6. **Run transcription:**

   **Important: CPU speed warning.** Before starting, warn the user:
   > "This machine uses CPU transcription (no NVIDIA GPU). Estimated time: ~30-60 min per hour of audio with large-v3. For faster results, you can use `--model medium` (~3x faster) or `--model small` (~6x faster)."

   Run the script:
   ```bash
   python .claude/ops/transcribe-podcast/transcribe.py --input "{local_path}" --diarize --hf-token "{token}"
   ```

   Without diarization:
   ```bash
   python .claude/ops/transcribe-podcast/transcribe.py --input "{local_path}"
   ```

   The script outputs JSON to stdout. Parse it. If `status` is `error`, show the error message and any install instructions, then stop.

   **Timeout:** Set a generous timeout (600000ms / 10 minutes). For very long files, warn the user it may take a while and run in the background if possible.

7. **Format transcript as Markdown:**

   Convert the JSON output into a readable Markdown document.

   **With speaker diarization:**
   ```markdown
   # Transcript: {filename}

   **Date transcribed:** {today's date}
   **Duration:** {duration formatted as H:MM:SS}
   **Speakers:** {count} identified
   **Words:** {word_count}
   **Model:** faster-whisper {model}

   ---

   **Speaker 1** [00:00:00]
   Welcome to the show. Today we're going to talk about...

   **Speaker 2** [00:00:15]
   Thanks for having me. I'm really excited to be here.

   **Speaker 1** [00:01:02]
   Let's dive right in. Tell us about your background.
   ```

   **Without speaker diarization:**
   ```markdown
   # Transcript: {filename}

   **Date transcribed:** {today's date}
   **Duration:** {duration}
   **Words:** {word_count}
   **Model:** faster-whisper {model}

   ---

   [00:00:00] Welcome to the show. Today we're going to talk about...

   [00:00:15] Thanks for having me. I'm really excited to be here.

   [00:01:02] Let's dive right in. Tell us about your background.
   ```

   **Formatting rules:**
   - Group text by speaker turns (if diarized) or by natural paragraph breaks (~30s chunks if not)
   - One blank line between speaker turns
   - Timestamps at the start of each turn, not every sentence
   - Clean up obvious whisper artifacts (repeated words, hallucinated text at silence)

8. **Upload transcript to Google Drive:**
   - Use `mcp__google-workspace__import_to_google_doc` with:
     - `file_name`: `"{original_filename} — Transcript"`
     - `content`: the formatted Markdown
     - `source_format`: `"md"`
     - `folder_id`: the same folder ID the audio came from
     - `user_google_email`: from me.md
   - Save the returned Google Doc link.

9. **Clean up temp files:**
   - Delete the downloaded audio file from local disk after successful upload.

10. **Present results:**

    For a single file:
    ```
    ## Transcription Complete

    | Detail | Value |
    |--------|-------|
    | File | {filename} |
    | Duration | {H:MM:SS} |
    | Words | {word_count} |
    | Speakers | {count or "N/A"} |
    | Processing time | {transcription_seconds}s |
    | Transcript | [Google Doc link] |
    ```

    For multiple files, show a summary table with all files.

    Then ask:
    - "Want me to transcribe more files from this folder?"
    - "Want me to identify the speakers by name?" (if diarized — user can tell you who Speaker 1, Speaker 2 are, and you can find-and-replace in the Google Doc)

## Notes
- The first run will download the large-v3 model (~3GB). This is cached for future runs.
- CPU transcription with large-v3 int8 uses ~3GB RAM.
- For podcasts longer than 2 hours, consider using `--model medium` for speed.
- pyannote diarization adds ~30-50% more processing time on top of transcription.
- Google Docs has a ~1M character limit. A 1-hour podcast is typically ~9,000 words / ~50,000 characters — well within limits.
- If transcription quality is poor, try without `--language` to let Whisper auto-detect, or try a different model size.
