import json
import urllib.request
import uuid
from pathlib import Path

base = 'http://127.0.0.1:8000'
audio_path = Path('test_audio.wav')
with audio_path.open('rb') as fh:
    audio_bytes = fh.read()

boundary = '----WebKitFormBoundary' + uuid.uuid4().hex
body = b''
body += f'--{boundary}\r\n'.encode()
body += b'Content-Disposition: form-data; name="question_id"\r\n\r\n'
body += b'RS_0001\r\n'
body += f'--{boundary}\r\n'.encode()
body += b'Content-Disposition: form-data; name="audio"; filename="test_audio.wav"\r\n'
body += b'Content-Type: audio/wav\r\n\r\n'
body += audio_bytes + b'\r\n'
body += f'--{boundary}--\r\n'.encode()

req = urllib.request.Request(
    base + '/api/score',
    data=body,
    headers={'Content-Type': f'multipart/form-data; boundary={boundary}'},
    method='POST',
)
with urllib.request.urlopen(req, timeout=120) as resp:
    print('score ->', resp.status)
    print(resp.read().decode('utf-8', 'ignore')[:1200])
