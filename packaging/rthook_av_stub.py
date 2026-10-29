# PyInstaller runtime hook. faster-whisper imports PyAV only for decode_audio(),
# which reads audio files; FreeFlow hands it raw microphone samples instead.
# A stub saves shipping ~125 MB of FFmpeg libraries.
import sys
import types

if "av" not in sys.modules:
    sys.modules["av"] = types.ModuleType("av")
