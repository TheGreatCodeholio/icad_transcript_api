import io
import json
import os
import time
import traceback

import pydub
from flask import Flask, request, render_template, jsonify
from faster_whisper import WhisperModel, download_model

from lib.address_handler import get_potential_addresses
from lib.config_handler import load_config_file, get_max_content_length, is_model_outdated
from lib.helpers import load_json, update_config, validate_audio_file, inject_alert_tone_segments
from lib.logging_handler import CustomLogger
from lib.replacement_handler import transcript_replacement
from lib.tone_removal_handler import cut_tones_from_audio, apply_agc_with_silence_detection
from lib.unit_handler import associate_segments_with_src

app_name = "icad_transcribe"
__version__ = "2.0"

root_path = os.getcwd()
config_file_name = "config.json"
hallucination_file_name = "hallucinations.json"

log_file_name = f"{app_name}.log"

log_path = os.path.join(root_path, 'log')
config_path = os.path.join(root_path, 'etc')

logging_instance = CustomLogger(1, f'{app_name}',
                                os.path.join(log_path, log_file_name))

last_transcript_data = {}

try:
    config_data = load_config_file(os.path.join(config_path, config_file_name))
    whisper_config_data = config_data.get("whisper", {})
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

model_cache_dir = os.path.join(os.getenv("TRANSFORMERS_CACHE", os.path.join(root_path, 'models')),
                               config_data.get("whisper", {}).get("model", "small"))

if is_model_outdated(model_cache_dir):
    logger.warning(
        f"Model is outdated or not found. Downloading model {config_data.get('whisper', {}).get('model', 'small')}...")
    model_dir = download_model(config_data.get("whisper", {}).get("model", "small"), output_dir=model_cache_dir)
else:
    logger.info(f"Using cached model. {config_data.get('whisper', {}).get('model', 'small')}")
    model_dir = model_cache_dir

try:
    if config_data.get("whisper", {}).get("device", None) in ["cpu", "cuda"]:
        model = WhisperModel(model_dir,
                             device=config_data.get("whisper", {}).get("device", "cpu"),
                             cpu_threads=config_data.get("whisper", {}).get("cpu_threads", 4),
                             compute_type=config_data.get("whisper", {}).get("compute_type", "float16"))
    else:
        logger.error(f'Whisper device needs to be either CPU or Cuda.')
        time.sleep(5)
        exit(1)

except Exception as e:
    logger.error(f'Exception Loading Whisper Model: {e}')
    time.sleep(5)
    exit(1)


@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({"success": False, "message": "Request body too large"}), 413


@app.route('/transcribe', methods=["POST"])
def transcribe():
    if request.method == "POST":
        start = time.time()
        audio_file = request.files.get('audioFile')
        json_file = request.files.get('jsonFile')
        user_whisper_config_data = request.form.get('whisper_config_data')
        detected_tones = {"two_tone": [], "long_tone": [], "hl_tone": []}

        if not audio_file:
            result = {"success": False, "message": "No audio file uploaded"}
            logger.error("No audio file uploaded")
            return jsonify(result), 400

        if json_file:
            # Load and validate JSON file data
            call_data, error = load_json(json_file)
            if error:
                logger.error(error)
                return jsonify({"success": False, "message": error}), 400
        else:
            call_data = {}

        # Update config data with user input
        if user_whisper_config_data:
            try:
                user_whisper_config_data = json.loads(user_whisper_config_data)
                user_whisper_config_data = update_config(whisper_config_data, user_whisper_config_data)
            except json.JSONDecodeError:
                logger.exception("Error parsing User Whisper Config Data")
                return jsonify({"success": False, "message": "Invalid Custom Whisper Config JSON data"}), 400
        else:
            user_whisper_config_data = whisper_config_data

        logger.debug(f"Using Whisper Configuration: {user_whisper_config_data}")

        transmission_sources = call_data.get('srcList', [{
            "pos": 0,
            "src": 0,
            "tag": "Speaker"
        }])

        short_name = call_data.get("short_name", "unknown")
        talkgroup_decimal = call_data.get("talkgroup_decimal", 0)

        # Validate audio file
        is_valid, validation_response = validate_audio_file(audio_file, config_data.get("audio_upload", {}).get(
            "allowed_extensions", ["audio/x-wav", "audio/x-m4a", "audio/mpeg"]),
                                                            config_data.get("audio_upload", {}).get("max_audio_length",
                                                                                                    300))
        if not is_valid:
            logger.error(validation_response)
            return jsonify({"success": False, "message": validation_response}), 400

        audio_file.seek(0)  # Rewind the buffer to the beginning

        audio_segment = pydub.AudioSegment.from_file(io.BytesIO(audio_file.read()))
        original_sample_rate = audio_segment.frame_rate

        if user_whisper_config_data.get("cut_tones", False):
            if call_data.get("tones", {}):
                detected_tones = call_data["tones"]
                logger.debug(f"Cutting Tones From Audio: {detected_tones}")
                audio_segment = cut_tones_from_audio(detected_tones, audio_segment,
                                                     pre_cut_length=user_whisper_config_data.get(
                                                         "cut_pre_tone", 0.5),
                                                     post_cut_length=user_whisper_config_data.get(
                                                         "cut_post_tone", 0.5))

        if user_whisper_config_data.get("amplify_audio", False):
            logger.debug(f"Amplifying Audio")
            audio_segment = apply_agc_with_silence_detection(audio_segment, target_peak=user_whisper_config_data.get(
                "amplify_target_peak", -25), silence_threshold=user_whisper_config_data.get("amplify_silence_threshold",
                                                                                            -48),
                                                             clipping_threshold=user_whisper_config_data.get(
                                                                 "amplify_clipping_threshold", -12))

        # Convert the PyDub AudioSegment to bytes
        audio_buffer = io.BytesIO()
        audio_segment.export(audio_buffer, format='wav', parameters=["-ar", str(original_sample_rate)])
        audio_buffer.seek(0)

        try:

            if user_whisper_config_data.get("use_last_as_initial_prompt", False) and call_data:
                initial_prompt = last_transcript_data.get(short_name, {}).get(str(talkgroup_decimal), {}).get(
                    "transcript", None)
            else:
                initial_prompt = user_whisper_config_data.get("initial_prompt", None)

            segments, info = model.transcribe(audio_buffer,
                                              beam_size=user_whisper_config_data.get("beam_size", 5),
                                              best_of=user_whisper_config_data.get("best_of", 5),
                                              language=user_whisper_config_data.get("language", "en"),
                                              initial_prompt=initial_prompt,
                                              word_timestamps=user_whisper_config_data.get("word_timestamps", False),
                                              vad_filter=user_whisper_config_data.get("vad_filter", False),
                                              vad_parameters=user_whisper_config_data.get("vad_parameters", {
                                                  "threshold": 0.5,
                                                  "min_speech_duration_ms": 250,
                                                  "max_speech_duration_s": 3600,
                                                  "min_silence_duration_ms": 2000,
                                                  "window_size_samples": 1024,
                                                  "speech_pad_ms": 400
                                              }))

            segment_texts = []
            segments_data = []
            segment_count = 0
            for segment in segments:
                segment_count += 1
                segment_texts.append(segment.text.strip())
                text = []
                word_id = 0
                if user_whisper_config_data.get("word_timestamps", False):
                    for word in segment.words:
                        word_id += 1
                        text.append({'word_id': word_id, 'word': word.word, 'start': word.start, 'end': word.end})
                else:
                    text = []

                segments_data.append(
                    {"segment_id": segment_count, "text": segment.text.strip(), "words": text, "unit_tag": "",
                     "start": segment.start,
                     "end": segment.end})

            if user_whisper_config_data.get("cut_tones", False) and user_whisper_config_data.get("show_tone_text", False):
                segments_data = inject_alert_tone_segments(segments_data, detected_tones)

            segments_data = associate_segments_with_src(segments_data, transmission_sources)

            transcribe_text = " ".join(segment['text'] for segment in segments_data)

        except Exception as e:
            traceback.print_exc()
            result = {"success": False, "message": f"Exception: {e}"}
            logger.error(result.get("message"))
            return jsonify(result), 400

        if not transcribe_text or len(transcribe_text.strip()) == 0:
            transcribe_text = []
            addresses = []
        else:
            addresses = get_potential_addresses(transcribe_text)

        if user_whisper_config_data.get("use_last_as_initial_prompt", False):
            last_transcript = {str(talkgroup_decimal): {"transcript": transcribe_text}}
            last_transcript_data[short_name] = last_transcript

        result = {"success": True, "message": "Transcribe Success!", "transcript": transcribe_text,
                  "addresses": addresses, "segments": segments_data,
                  "process_time_seconds": round((time.time() - start), 2)}

        if not user_whisper_config_data.get("word_timestamps", False):
            result = transcript_replacement(result, replacements_file_path=os.path.join(config_path, user_whisper_config_data.get("replacements_file", "transcribe_replacements.csv")))

        logger.info(result.get("message"))
        return jsonify(result), 200
    else:
        result = {"success": False, "message": "Method not allowed GET"}
        logger.error(result.get("message"))
        return jsonify(result), 405


@app.route('/')
def index():
    return render_template('index.html')

# if __name__ == '__main__':
#    app.run(host="0.0.0.0", port=3001, debug=False)
