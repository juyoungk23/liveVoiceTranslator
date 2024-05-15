from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import logging
import time
import sys
import tempfile
import os
from src import (transcribe_audio_google, transcribe_audio_whisper, translate_text, generate_voice_file_eleven_labs, generate_voice_file_openai,
                 convert_audio_to_wav, get_last_three_conversations, add_conversation)

app = Flask(__name__)
CORS(app) 

# Basic configuration for your application's logger
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Setting third-party libraries' loggers to a higher log level
logging.getLogger('google.auth').setLevel(logging.WARNING)
logging.getLogger('google.auth.transport.requests').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Unhandled Exception: {e}", exc_info=True)
    return jsonify({"error": "An internal server error occurred"}), 500

@app.route('/start-new-conversation', methods=['POST'])
def start_new_conversation():
    return jsonify({"message": "New conversation started. PLACEHOLDER for future functionality."})

@app.route('/process-audio', methods=['POST'])
def process_audio():

    app.logger.info("#" * 50)

    overall_start_time = time.time()

    if 'audio' not in request.files:
        return jsonify({"error": "No audio file part"}), 400
    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    input_lang = request.form.get('input_lang', 'en-US')
    output_lang = request.form.get('output_lang', 'es')
    voice_name = request.form.get('voice', 'Jane')
    mode = request.form.get('mode', 'person2')

    if mode == 'person1': 
        mode = 'doctor' 
    else: mode = 'patient'

    app.logger.info(f"Processing audio file with \ninput language: {input_lang}, \noutput language: {output_lang}, \nvoice name: {voice_name}, \nmode: {mode}")

    try:
        # Save to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            audio_file.save(temp_audio)
            temp_audio_path = temp_audio.name

        # Convert to the proper WAV format
        converted_audio_path = convert_audio_to_wav(temp_audio_path)
        if not converted_audio_path:
            os.unlink(temp_audio_path)  # Clean up the original temporary file
            return jsonify({"error": "Failed to convert audio file"}), 500
    
        previousTexts = get_last_three_conversations()
        
        # Transcription
        transcription_start_time = time.time()

        transcribed_text = transcribe_audio_google(converted_audio_path, input_lang, previousTexts)
        # transcribed_text = transcribe_audio_whisper(converted_audio_path)

        add_conversation(transcribed_text, person_type=mode)

        if not transcribed_text:
            os.unlink(converted_audio_path)  # Clean up the converted file
            return jsonify({"error": "Transcription failed"}), 500
        transcribe_time = time.time() - transcription_start_time
        app.logger.info(f"Transcription took {transcribe_time:.2f} seconds")

        # Translation
        translation_start_time = time.time()
        translated_text = translate_text(transcribed_text, input_lang, output_lang)
        if not translated_text:
            os.unlink(converted_audio_path)  # Clean up the converted file
            return jsonify({"error": "Translation failed"}), 500
        translate_time = time.time() - translation_start_time
        app.logger.info(f"Translation took {translate_time:.2f} seconds")

        # Voice generation
        voice_generation_start_time = time.time()

        if mode == 'doctor':
            voice_file_path = generate_voice_file_eleven_labs(translated_text, voice_name)
        else:
            voice_file_path = generate_voice_file_openai(translated_text)

        if not voice_file_path:
            os.unlink(converted_audio_path)  # Clean up the converted file
            return jsonify({"error": "Voice generation failed"}), 500
        voice_time = time.time() - voice_generation_start_time
        app.logger.info(f"Voice generation took {voice_time:.2f} seconds")

        overall_time = time.time() - overall_start_time
        app.logger.info(f"Overall processing took {overall_time:.2f} seconds")

        os.unlink(converted_audio_path)  # Clean up the converted file

        if not os.path.exists(voice_file_path):
            app.logger.error("Generated voice file not found.")
            return jsonify({"error": "Generated voice file not found"}), 500

        app.logger.info("#" * 50)
        return send_file(voice_file_path, as_attachment=True, mimetype='audio/mpeg')



    except Exception as e:
        if 'temp_audio_path' in locals():
            os.unlink(temp_audio_path)  # Ensure cleanup in case of error
        app.logger.error(f"Unhandled exception: {e}")
        return jsonify({"error": "An error occurred"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
