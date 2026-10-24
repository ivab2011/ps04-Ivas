"""Narrate a text file with Chatterbox in my own voice (voice.wav), chunk by chunk.
Chatterbox works best on short passages, so the text is split into chunks of a few sentences,
each chunk is generated separately, and the pieces are joined with a short pause.
Usage (in .venv-tts): python production/tts.py production/out/narration_01.txt production/out/audio_01.wav"""
import re, sys, time
import torch, torchaudio
from chatterbox.tts import ChatterboxTTS

src, dst = sys.argv[1], sys.argv[2]
VOICE = "production/voice.wav"
MAX_CHARS = 280

device = "mps" if torch.backends.mps.is_available() else "cpu"
try:
    model = ChatterboxTTS.from_pretrained(device=device)
except Exception as err:                                   # fall back to CPU if MPS is not supported
    print(f"tts: {device} failed ({err}); using cpu", file=sys.stderr)
    device = "cpu"
    model = ChatterboxTTS.from_pretrained(device="cpu")
print(f"tts: device {device}", file=sys.stderr)

text = open(src, encoding="utf-8").read()
sentences = re.split(r"(?<=[.!?])\s+", " ".join(text.split()))
chunks, cur = [], ""
for s in sentences:
    if cur and len(cur) + len(s) + 1 > MAX_CHARS:
        chunks.append(cur)
        cur = s
    else:
        cur = (cur + " " + s).strip()
if cur:
    chunks.append(cur)

pause = torch.zeros(1, int(model.sr * 0.35))
parts, t0 = [], time.time()
for i, chunk in enumerate(chunks, 1):
    wav = model.generate(chunk, audio_prompt_path=VOICE)
    parts += [wav.cpu(), pause]
    print(f"tts: chunk {i}/{len(chunks)} done ({time.time() - t0:.0f}s)", file=sys.stderr)
audio = torch.cat(parts, dim=1)
torchaudio.save(dst, audio, model.sr)
print(f"tts: wrote {dst} ({audio.shape[1] / model.sr / 60:.1f} min)", file=sys.stderr)
