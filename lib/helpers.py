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


def organize_detected_tones(detected_tone_data):
    final_detected_tones = []
    for key, tones in detected_tone_data.items():
        final_detected_tones.extend(tones)
    return final_detected_tones


def inject_alert_tone_segments(whisper_segments, detected_tones):
    whisper_segments = list(whisper_segments)
    final_segments = []
    index = 0  # Index to track the current segment position

    detected_tones_final = organize_detected_tones(detected_tones)

    # Iterate over each detected tone
    for tone in detected_tones_final:
        # Ensure we add all segments before the tone starts
        while index < len(whisper_segments) and whisper_segments[index]['end'] <= tone['start']:
            final_segments.append(whisper_segments[index])
            index += 1

        # Insert the alert tone segment
        final_segments.append({
            "text": "[Alert Tones]",
            "start": tone['start'],
            "end": tone['end'],
            "words": [{"start": tone['start'], "end": tone['end'], "word_id": 1, "word": "[Alert Tones]"}]
        })

        # Skip over any segments that overlap with the current tone
        while index < len(whisper_segments) and whisper_segments[index]['start'] < tone['end']:
            index += 1

    # After handling all tones, add the remaining segments that come after the last tone
    while index < len(whisper_segments):
        final_segments.append(whisper_segments[index])
        index += 1

    return final_segments
