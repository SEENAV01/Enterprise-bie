import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
from runtime_diagnostics import detect_runtime

def test_diagnostic_returns_all_required_tools():
    d=detect_runtime()
    for name in ("node","npm","npx","ffmpeg","ffprobe","tesseract"):
        assert name in d
