import io
import os
import sys
import tempfile
import wave

import numpy as np

sys.path.insert(0, r"c:\Users\ihtis\OneDrive\Desktop\Coding\pte-app-v2\pte-app-v2\backend")
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

try:
    print(forced_alignment.align(tmp_path, 'hello'))
finally:
    if os.path.exists(tmp_path):
        os.remove(tmp_path)
