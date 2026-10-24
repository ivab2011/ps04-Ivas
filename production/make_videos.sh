#!/usr/bin/env bash
# Build the three audience videos from the APPROVED package: narration text -> TTS audio -> slide + audio -> mp4.
# Usage (in .venv-tts): bash production/make_videos.sh runs/replay-20261018T205452Z [01 02 03]
set -euo pipefail
cd "$(dirname "$0")/.."
RUN="${1:?usage: make_videos.sh RUN_DIR [piece ...]}"; shift || true
PIECES="${*:-01 02 03}"
mkdir -p production/out
[ -f production/voice.wav ] || { echo "missing production/voice.wav (10-second recording of your voice)" >&2; exit 2; }
for p in $PIECES; do
  SCRIPT="$RUN/package/video_scripts/$p.md"
  TITLE=$(head -1 "$SCRIPT" | sed 's/^# *//')
  python production/narration.py "$SCRIPT" > "production/out/narration_$p.txt"
  echo "== $p: $(wc -w < production/out/narration_$p.txt | tr -d ' ') words: $TITLE"
  [ -f "production/out/audio_$p.wav" ] || python production/tts.py "production/out/narration_$p.txt" "production/out/audio_$p.wav"
  python production/slide.py "Part $((10#$p)) of 3" "$TITLE" "production/out/slide_$p.png"
  ffmpeg -nostdin -y -loglevel error -loop 1 -i "production/out/slide_$p.png" -i "production/out/audio_$p.wav" \
    -c:v libx264 -tune stillimage -pix_fmt yuv420p -c:a aac -b:a 160k -shortest "production/out/video_$p.mp4"
  echo "== $p: production/out/video_$p.mp4 ($(ffprobe -v error -show_entries format=duration -of csv=p=0 production/out/video_$p.mp4 | cut -d. -f1) s)"
done
