import whisper_timestamped as whisper

audio = whisper.load_audio("./alice.mp3")

model = whisper.load_model("tiny", device="cpu")

result = whisper.transcribe(model, audio, language="en")

import json
print(json.dumps(result, indent = 2, ensure_ascii = False))