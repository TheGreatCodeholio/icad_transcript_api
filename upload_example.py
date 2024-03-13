import requests
import os
import glob

# Define the URL
url = "http://localhost:9912/transcribe"

# Specify the directory containing the mp3 files
directory = '/home/ian/Documents/transcribe_test'

# # Get a list of all .mp3 files in the directory
# mp3_files = glob.glob(os.path.join(directory, '*.mp3'))
#
# # Loop through all .mp3 files
# for mp3_file in mp3_files:
#     # Open file in binary mode
#     with open(mp3_file, 'rb') as f:
#         # Use the 'files' parameter to attach the file
#         files = {'file': f}
#         response = requests.post(url, files=files)
#
#     # The response is in JSON format, so you can convert it to a Python object
#     response_data = response.json()
#
#     print(response_data)

with open('wyalusing_20240123_173313.mp3', 'rb') as f:
    files = {'file': f}
    response = requests.post(url, files=files)
    response_data = response.json()
    print(response_data)
