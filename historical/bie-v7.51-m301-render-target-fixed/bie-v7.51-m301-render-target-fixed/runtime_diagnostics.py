from pathlib import Path
import shutil, json

def detect_runtime():
    tools={}
    for name in ("node","npm","npx","ffmpeg","ffprobe","tesseract"):
        tools[name]=shutil.which(name)
    return tools

def can_execute_remotion():
    tools=detect_runtime()
    return bool(tools["node"] and tools["npm"] and tools["npx"])
