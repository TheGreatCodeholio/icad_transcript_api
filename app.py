import io
import time
from os.path import splitext

from flask import Flask, request, render_template, jsonify
from faster_whisper import WhisperModel
from pydub import AudioSegment

from lib.address_handler import get_potentional_addresses

model = WhisperModel("large-v3", device="cuda", compute_type="float32")

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 3 * 1024 * 1024


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
            print(result)
            return jsonify(result), 400

        allowed_extensions = ['.mp3', '.wav', '.m4a']
        ext = splitext(file.filename)[1]
        if ext not in allowed_extensions:
            result = {"status": "error", "message": "File must be an MP3, WAV or M4A"}
            print(result)
            return jsonify(result), 400

        file_data = file.read()

        audio = AudioSegment.from_file(io.BytesIO(file_data))

        if audio.duration_seconds > 300:
            result = {"status": "error", "message": "File duration must be under 5 minutes"}
            print(result)
            return jsonify(result), 400
        try:
            segments, info = model.transcribe(io.BytesIO(file_data), beam_size=20, best_of=15, language="en",
                                              vad_filter=True, vad_parameters={"min_silence_duration_ms": 500})
            transcribe_text = " ".join(segment.text for segment in segments)

        except Exception as e:
            result = {"status": "error", "message": f"Exception: {e}"}
            print(result)
            return jsonify(result), 400

        if not transcribe_text or len(transcribe_text.strip()) == 0:
            transcribe_text = []
            addresses = []
        else:
            addresses = get_potentional_addresses(transcribe_text)

        result = {"status": "ok", "message": "Success!", "transcription": transcribe_text,
                  "addresses": addresses, "process_time_seconds": round((time.time() - start), 2)}
        print(result)
        return jsonify(result), 200
    else:
        result = {"status": "error", "message": "Method not allowed GET"}
        print(result)
        return jsonify(result), 405


@app.route('/')
def index():
    return render_template('index.html')


# if __name__ == '__main__':
#    app.run(host="0.0.0.0", port=3001, debug=False)
