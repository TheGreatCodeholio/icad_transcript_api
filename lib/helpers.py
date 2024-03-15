import io
import json
from os.path import splitext

from pydub import AudioSegment


def load_json_data(file):
    try:
        return json.loads(file.read()), None
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON data: {e}"


def update_config(default_config, user_config):
    def update(d, u):
        for k, v in u.items():
            if isinstance(v, dict):
                d[k] = update(d.get(k, {}), v)
            else:
                d[k] = v
        return d

    return update(default_config.copy(), user_config)


def validate_file(audio_file, allowed_extensions, max_audio_length):
    ext = splitext(audio_file.filename)[1]
    if ext not in allowed_extensions:
        return False, "File must be an MP3, WAV or M4A"

    audio = AudioSegment.from_file(io.BytesIO(audio_file.read()))
    audio_file.seek(0)  # Reset the pointer to allow re-reading

    if audio.duration_seconds > max_audio_length:
        return False, "File duration must be under 5 minutes"

    return True, audio_file