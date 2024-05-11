from flask import Flask, request, jsonify, send_file
import logging
import os
import time
import sys
from src import (transcribe_audio_google, transcribe_audio_whisper,
                 translate_text, generate_voice_file,
                 convert_audio_to_wav, get_secret)

app = Flask(__name__)

# Configure logging to write to stdout, suitable for Cloud Run
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Unhandled Exception: {e}", exc_info=True)
    return jsonify({"error": "An internal server error occurred"}), 500

@app.route('/process-audio', methods=['POST'])
def process_audio():
    overall_start_time = time.time()

    if 'audio' not in request.files:
        return jsonify({"error": "No audio file part"}), 400
    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    input_lang = request.form.get('input_lang', 'en-US')
    output_lang = request.form.get('output_lang', 'es')
    voice_id = request.form.get('voice', 'w0FTld3VgsXqUaNGNRnY')  # Ensure to manage default voice_id appropriately

    try:
        start_time = time.time()
        audio_file_path = os.path.join('uploads', audio_file.filename)
        audio_file.save(audio_file_path)
        save_time = time.time() - start_time
        app.logger.debug(f"Time taken to save audio file: {save_time} seconds")

        start_time = time.time()
        transcribed_text = transcribe_audio_google(audio_file_path, input_lang)
        if not transcribed_text:
            return jsonify({"error": "Transcription failed"}), 500
        transcribe_time = time.time() - start_time
        app.logger.debug(f"Time taken for transcription: {transcribe_time} seconds")

        start_time = time.time()
        translated_text = translate_text(transcribed_text, output_lang, input_lang)
        if not translated_text:
            return jsonify({"error": "Translation failed"}), 500
        translate_time = time.time() - start_time
        app.logger.debug(f"Time taken for translation: {translate_time} seconds")

        start_time = time.time()
        voice_file_path = generate_voice_file(translated_text, voice_id, get_secret('your_project_id', 'api_key_secret'))
        if not voice_file_path:
            return jsonify({"error": "Voice generation failed"}), 500
        generate_time = time.time() - start_time
        app.logger.debug(f"Time taken for generating voice file: {generate_time} seconds")

        total_processing_time = time.time() - overall_start_time
        app.logger.debug(f"Total processing time: {total_processing_time} seconds")
        return send_file(voice_file_path, as_attachment=True)
    except Exception as e:
        app.logger.error(f"Unhandled exception: {e}")
        return jsonify({"error": "An error occurred"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
