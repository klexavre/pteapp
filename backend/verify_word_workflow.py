import urllib.request
import uuid
from pathlib import Path

base = 'http://127.0.0.1:8000'
audio_path = Path('test_audio.wav')
audio_bytes = audio_path.read_bytes()

boundary = '----WebKitFormBoundary' + uuid.uuid4().hex
body = b''
body += f'--{boundary}\r\n'.encode()
body += b'Content-Disposition: form-data; name="word"\r\n\r\n'
body += b'centuries\r\n'
body += f'--{boundary}\r\n'.encode()
body += b'Content-Disposition: form-data; name="audio"; filename="test_audio.wav"\r\n'
body += b'Content-Type: audio/wav\r\n\r\n'
body += audio_bytes + b'\r\n'
body += f'--{boundary}--\r\n'.encode()

req = urllib.request.Request(
    base + '/api/words/score',
    data=body,
    headers={'Content-Type': f'multipart/form-data; boundary={boundary}'},
    method='POST',
)
with urllib.request.urlopen(req, timeout=120) as resp:
    print('word-score ->', resp.status)
    print(resp.read().decode('utf-8', 'ignore')[:1200])
