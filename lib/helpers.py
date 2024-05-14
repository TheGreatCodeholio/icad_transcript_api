import io
import json
from os.path import splitext
import copy

import magic
from pydub import AudioSegment

hallucinations = [""]


def load_json(input_data):
    """
    Loads JSON data from a file-like object or a string.

    Parameters:
    -----------
    input_data : str or file-like object
        The input containing JSON data. If input_data has a `read` method, it will be treated
        as a file-like object, and the function will attempt to read from it. If input_data is
        a string, the function will attempt to decode it as JSON directly.

    Returns:
    --------
    tuple
        A tuple where the first element is the loaded JSON data or None if an error occurs,
        and the second element is an error message or None if no error occurs.
    """
    try:
        # Check if input_data is file-like; it must have a 'read' method
        if hasattr(input_data, 'read'):
            # Assuming input_data is a file-like object with 'read' method
            data = json.loads(input_data.read())
        else:
            # Assuming input_data is a string
            data = json.loads(input_data)
        return data, None
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON data: {e}"
    except Exception as e:
        # Catching unexpected errors
        return None, f"Error loading JSON data: {e}"


def update_config(default_config, user_config):
    def update(d, u):
        for k, v in u.items():
            if isinstance(v, dict):
                d[k] = update(d.get(k, {}), v)
            else:
                d[k] = v
        return d

    # Ensure we are working with a deep copy of the default_config to avoid modifying it directly
    default_copy = copy.deepcopy(default_config)
    return update(default_copy, user_config)


def validate_audio_file(audio_file, allowed_mimetypes, max_audio_length):
    mimetype = magic.from_buffer(audio_file.read(1024), mime=True)
    audio_file.seek(0)
    if mimetype not in allowed_mimetypes:
        return False, "Audio MIMETYPE must be in {}".format(allowed_mimetypes)

    audio = AudioSegment.from_file(io.BytesIO(audio_file.read()))

    if audio.duration_seconds > max_audio_length:
        return False, f"File duration must be under {max_audio_length * 60} minutes"

    return True, "Valid audio file"


def inject_alert_tone_segments(whisper_segments, detected_tones):
    whisper_segments = list(whisper_segments)
    alert_segments = []
    for tone_type in detected_tones:

        for tone in detected_tones.get(tone_type, []):
            alert_segments.append({
                "end": tone["end"],
                "segment_id": len(whisper_segments) + len(alert_segments) + 1,
                "start": tone["start"],
                "text": "[Alert Tones]",
                "unit_tag": 0,
                "words": []
            })

    # Merge the new segments with existing segments and sort by start time
    all_segments = whisper_segments + alert_segments
    all_segments.sort(key=lambda x: x["start"])

    # Update the segment IDs to maintain sequential order
    for i, segment in enumerate(all_segments):
        segment["segment_id"] = i + 1

    return all_segments
