import io
import os
import time
import traceback
from os.path import splitext

from flask import Flask, request, render_template, jsonify
from faster_whisper import WhisperModel
from pydub import AudioSegment

from lib.address_handler import get_potentional_addresses
from lib.config_handler import load_config_file, get_max_content_length
from lib.logging_handler import CustomLogger

app_name = "icad_transcribe"
__version__ = "2.0"

root_path = os.getcwd()
config_file_name = "config.json"
log_file_name = f"{app_name}.log"

log_path = os.path.join(root_path, 'log')
config_path = os.path.join(root_path, 'etc')

logging_instance = CustomLogger(1, f'{app_name}',
                                os.path.join(log_path, log_file_name))

try:
    config_data = load_config_file(os.path.join(config_path, config_file_name))
    logging_instance.set_log_level(config_data["log_level"])
    logger = logging_instance.logger
    logger.info("Loaded Config File")
except Exception as e:
    traceback.print_exc()
    print(f'Error while <<loading>> configuration : {e}')
    time.sleep(5)
    exit(1)

if not config_data:
    logger.error('Failed to load configuration.')
    time.sleep(5)
    exit(1)

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['MAX_CONTENT_LENGTH'] = get_max_content_length(config_data)

try:
    if config_data.get("whisper", {}).get("device", None) in ["cpu", "nvidia"]:
        model = WhisperModel(config_data.get("whisper", {}).get("model", "small"),
                             device=config_data.get("whisper", {}).get("device", "cpu"),
                             cpu_threads=config_data.get("whisper", {}).get("cpu_threads", 4),
                             compute_type=config_data.get("whisper", {}).get("compute_type", "float32"))
    else:
        logger.error(f'Whisper device needs to be either CPU or Nvidia.')
        time.sleep(5)
        exit(1)

except Exception as e:
    logger.error(f'Exception Loading Whisper Model: {e}')
    time.sleep(5)
    exit(1)


@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({"status": "error", "message": "Request body too large"}), 413


@app.route('/transcribe', methods=["POST"])
def transcribe():
    if request.method == "POST":
        start = time.time()
        file = request.files.get('file')
        if not file:
            result = {"status": "error", "message": "No file uploaded"}
            logger.error(result.get("message"))
            return jsonify(result), 400

        allowed_extensions = config_data.get("upload", {}).get("allowed_extensions", [])
        ext = splitext(file.filename)[1]
        if ext not in allowed_extensions:
            result = {"status": "error", "message": "File must be an MP3, WAV or M4A"}
            logger.error(result.get("message"))
            return jsonify(result), 400

        file_data = file.read()

        audio = AudioSegment.from_file(io.BytesIO(file_data))

        if audio.duration_seconds > 300:
            result = {"status": "error", "message": "File duration must be under 5 minutes"}
            logger.error(result.get("message"))
            return jsonify(result), 400
        try:
            segments, info = model.transcribe(io.BytesIO(file_data),
                                              beam_size=config_data.get("whisper", {}).get("beam_size", 5),
                                              best_of=config_data.get("whisper", {}).get("best_of", 5),
                                              language=config_data.get("whisper", {}).get("language", "en"),
                                              vad_filter=config_data.get("whisper", {}).get("vad_filter", False),
                                              vad_parameters=config_data.get("whisper", {}).get("vad_parameters", {
                                                  "threshold": 0.5,
                                                  "min_speech_duration_ms": 250,
                                                  "max_speech_duration_s": 3600,
                                                  "min_silence_duration_ms": 2000,
                                                  "window_size_samples": 1024,
                                                  "speech_pad_ms": 400
                                              }))
            transcribe_text = " ".join(segment.text for segment in segments)

        except Exception as e:
            result = {"status": "error", "message": f"Exception: {e}"}
            logger.error(result.get("message"))
            return jsonify(result), 400

        if not transcribe_text or len(transcribe_text.strip()) == 0:
            transcribe_text = []
            addresses = []
        else:
            addresses = get_potentional_addresses(transcribe_text)

        result = {"status": "ok", "message": "Transcribe Success!", "transcription": transcribe_text,
                  "addresses": addresses, "segments": segments, "process_time_seconds": round((time.time() - start), 2)}
        logger.info(result.get("message"))
        return jsonify(result), 200
    else:
        result = {"status": "error", "message": "Method not allowed GET"}
        logger.error(result.get("message"))
        return jsonify(result), 405


@app.route('/')
def index():
    return render_template('index.html')

# if __name__ == '__main__':
#    app.run(host="0.0.0.0", port=3001, debug=False)
