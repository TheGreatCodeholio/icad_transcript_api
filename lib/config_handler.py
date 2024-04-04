import json
import logging
import os
import time
from datetime import datetime, timedelta

module_logger = logging.getLogger('icad_transcribe.config')

default_config = {
    "log_level": 1,
    "audio_upload": {
        "allowed_extensions": ["audio/x-wav", "audio/x-m4a", "audio/mpeg"],
        "max_audio_length": 300,
        "max_file_size": 3,
        "cut_tones": 0,
        "cut_pre_tone": 0.5,
        "cut_post_tones": 0.5,
        "amplify_audio_for_vad": 0
    },
    "whisper": {
        "device": "cuda",
        "cpu_threads": 4,
        "compute_type": "float16",
        "model": "large-v3",
        "language": "en",
        "beam_size": 5,
        "best_of": 5,
        "vad_filter": True,
        "vad_parameters": {
            "threshold": 0.5,
            "min_speech_duration_ms": 250,
            "max_speech_duration_s": 3600,
            "min_silence_duration_ms": 2000,
            "window_size_samples": 1024,
            "speech_pad_ms": 400
        }
    }
}


def is_model_outdated(directory, days=7):
    """Check if the model files in the directory are older than 'days' days."""
    now = datetime.now()
    threshold = now - timedelta(days=days)

    if not os.path.exists(directory):
        # Directory does not exist, so model is considered outdated
        return True

    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        file_mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        if file_mod_time < threshold:
            # At least one file is older than the threshold, so model is outdated
            return True

    # All files are within the 'days' threshold
    return False


def get_max_content_length(config_data, default_size_mb=3):
    try:
        # Attempt to retrieve and convert the max file size to an integer
        max_file_size = int(config_data.get("audio_upload", {}).get("max_file_size", default_size_mb))
    except (ValueError, TypeError) as e:
        # Log the error and exit if the value is not an integer or not convertible to one
        module_logger.error(f'Max File Size Must be an Integer: {e}')
        time.sleep(5)
        exit(1)
    else:
        # Return the size in bytes
        return max_file_size * 1024 * 1024


def load_config_file(file_path):
    """
    Loads the configuration file and encryption key.
    """

    try:
        with open(file_path, 'r') as f:
            config_data = json.load(f)
    except FileNotFoundError:
        module_logger.warning(f'Configuration file {file_path} not found. Creating default.')
        save_config_file(file_path, default_config)  # Assuming this function is defined elsewhere
        return None
    except json.JSONDecodeError:
        module_logger.error(f'Configuration file {file_path} is not in valid JSON format.')
        return None
    except Exception as e:
        module_logger.error(f'Unexpected Exception Loading file {file_path} - {e}')
        return None

    return config_data


def save_config_file(file_path, default_data):
    """Creates a configuration file with default data if it doesn't exist."""
    try:
        with open(file_path, "w") as outfile:
            outfile.write(json.dumps(default_data, indent=4))
        return True
    except Exception as e:
        module_logger.error(f'Unexpected Exception Saving file {file_path} - {e}')
        return None
