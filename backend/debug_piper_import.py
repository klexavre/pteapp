import os, sys, traceback
sys.path.insert(0, os.getcwd())
try:
    import piper
    print('piper module import ok')
    print('module', piper)
    model = piper.PiperVoice.load(r'C:\Users\ihtis\OneDrive\Desktop\Coding\pte-app-v1 - (RS+WD+RA)\pte-app-v2\backend\voices\en_US-lessac-low.onnx')
    print('loaded model', model)
    chunks = list(model.synthesize('hello world'))
    print('chunk count', len(chunks))
    print('first chunk type', type(chunks[0]).__name__)
    print('sample', getattr(chunks[0], 'audio_float_array', None)[:3])
except Exception as exc:
    print('import/load failed', repr(exc))
    traceback.print_exc()
