from json import JSONDecodeError

import requests

# Define the URL
url = "http://localhost:9912/transcribe"
audio_file = "test_audio/100-1711131089_155250000.0-call_20424.wav"
json_file = "test_audio/100-1711131089_155250000.0-call_20424.json"

with open(audio_file, 'rb') as af, open(json_file, 'rb') as jf:
    files = {'audioFile': af, 'jsonFile': jf}
    response = requests.post(url, files=files)
    try:
        response_data = response.json()
    except JSONDecodeError:
        response_data = response.text
    print(response_data)