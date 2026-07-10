import io
import os
import sys
import tempfile
import traceback
import wave

import numpy as np

sys.path.insert(0, r"c:\Users\ihtis\OneDrive\Desktop\Coding\pte-app-v2\pte-app-v2\backend")
import audio_utils
import forced_alignment

sr = 16000
samples = int(sr * 0.5)
t = np.linspace(0, 0.5, samples, endpoint=False)
x = (np.sin(2 * np.pi * 440 * t) * 0.3).astype(np.float32)
buf = io.BytesIO()
wf = wave.open(buf, 'wb')
wf.setnchannels(1)
wf.setsampwidth(2)
wf.setframerate(sr)
wf.writeframes((x * 32767).astype('int16').tobytes())
wf.close()

with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
    tmp.write(buf.getvalue())
    tmp_path = tmp.name
trimmed_path = tmp_path.replace('.wav', '_trimmed.wav')

try:
    out = audio_utils.trim_silence(tmp_path, trimmed_path)
    print('trimmed', out)
    result = forced_alignment.align(out, 'hello')
    print('alignment', result)
except Exception:
    traceback.print_exc()
finally:
    for p in [tmp_path, trimmed_path]:
        if p and os.path.exists(p):
            os.remove(p)
