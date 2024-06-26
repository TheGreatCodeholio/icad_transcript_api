import json

import requests
from json import JSONDecodeError

# Configuration variables for the user to set
AUDIO_FILE_PATH = 'test_audio/100-1711131089_155250000.0-call_20424.wav'
JSON_FILE_PATH = 'test_audio/100-1711131089_155250000.0-call_20424.json'
URL = "http://localhost:9912/transcribe"

WHISPER_CONFIG_DATA = {
    "language": "en",
    "beam_size": 5,
    "best_of": 5,
    "initial_prompt": None,
    "use_last_as_initial_prompt": False,
    "word_timestamps": False,
    "cut_tones": False,
    "show_tone_text": False,
    "cut_pre_tone": 0.5,
    "cut_post_tone": 0.5,
    "amplify_audio": False,
    "amplify_target_peak": -22,
    "amplify_silence_threshold": -40,
    "amplify_clipping_threshold": -11,
    "vad_filter": True,
    "vad_parameters": {
        "threshold": 0.3,
        "min_speech_duration_ms": 250,
        "max_speech_duration_s": 3600,
        "min_silence_duration_ms": 400,
        "window_size_samples": 1024,
        "speech_pad_ms": 400
    }
}


def post_audio_and_json(audio_file_path, json_file_path, url, config_data):
    """
    Posts an audio file and a JSON file to the specified URL along with configuration data and prints the response.

    Parameters:
    - audio_file_path (str): The file path to the audio file.
    - json_file_path (str): The file path to the JSON file.
    - url (str): The URL to which the files are posted.
    - config_data (dict): JSON configuration data for the request.
    """
    try:
        # Prepare the configuration data by converting it to a JSON string
        config_json_string = json.dumps(config_data)

        # Prepare the data payload with the JSON configuration as a string
        data = {'whisper_config_data': config_json_string}

        with open(audio_file_path, 'rb') as audio_file, open(json_file_path, 'rb') as json_file:
            files = {'audioFile': audio_file, 'jsonFile': json_file}
            response = requests.post(url, files=files, data=data)

            try:
                response_data = response.json()
            except JSONDecodeError:
                response_data = response.text

            print(response_data)

    except FileNotFoundError as e:
        print(f"Error: {e}. Please check the file paths.")
    except requests.RequestException as e:
        print(f"Error during the request: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


# Example usage of the function with configurable file paths and URL
post_audio_and_json(AUDIO_FILE_PATH, JSON_FILE_PATH, URL, WHISPER_CONFIG_DATA)