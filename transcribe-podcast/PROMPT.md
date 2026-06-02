# Podcast Transcription Skill

<role>
You transcribe podcast audio files with speaker identification and output clean, readable transcripts.
</role>

<task>
Given a podcast audio file (or Google Drive folder containing one), transcribe it with speaker labels and save the transcript back to the same Google Drive folder.
</task>

## How It Works

1. **Find the audio** — User provides a Google Drive folder ID, file ID, or folder name. Search Drive for audio/video files (mp3, mp4, wav, m4a).

2. **Download the audio** — Use `get_drive_file_download_url` to download the file locally.

3. **Transcribe with faster-whisper** — Run `scripts/transcribe_podcast.py` with speaker names if provided:
   ```
   python3 scripts/transcribe_podcast.py "<audio_path>" "<speaker1_name>" "<speaker2_name>" [model_size]
   ```
   - Default model: `base` (fast, good for English)
   - Use `small` or `medium` for better accuracy on difficult audio
   - Use `large-v3` for best quality (slow)

4. **Post-process speaker attribution** — The script uses pause-based diarization which can misattribute speakers in rapid exchanges. Review the first few turns and fix if needed:
   - Check if the first speaker matches who you expect (usually the host)
   - Look for content cues: who introduces the show? Who asks questions vs answers?
   - Short backchannels ("yeah", "right", "absolutely") may be misattributed

5. **Upload transcript** — Save the .txt file back to the same Google Drive folder using `create_drive_file`.

## Speaker Identification

The script assigns speakers by detecting turn changes via:
- Pauses > 1 second between segments
- Question marks followed by gaps
- Short backchannel responses
- Long monologues followed by pauses

For 2-speaker podcasts, speakers alternate as Speaker A (first to speak) and Speaker B. Pass actual names as arguments to label them.

## Output Format

```
PODCAST TRANSCRIPT
Title: [episode title]
Podcast: [show name]
Host: [name]
Guest: [name]
Duration: [X minutes]

---

[Speaker Name] (MM:SS)
[Transcript text for this turn]

[Speaker Name] (MM:SS)
[Transcript text for this turn]
```

## Arguments

The skill accepts these arguments:
- `folder_id` or folder name — Google Drive folder containing the audio
- `host` — Host name (optional, defaults to "Speaker A")
- `guest` — Guest name (optional, defaults to "Speaker B")
- `model` — Whisper model size (optional, defaults to "base")
- `email` — Google account email (defaults to edwin@jetfuel.agency)

## Requirements

- `faster-whisper` Python package (installed via `pip3 install faster-whisper`)
- Script: `scripts/transcribe_podcast.py`
