from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import logging
import time
import sys
import tempfile
import os
import base64
from src import (transcribe_audio_google, transcribe_audio_whisper, transcribe_audio_deepgram_local, translate_text, generate_voice_file_eleven_labs, generate_voice_file_openai,
                 convert_audio_to_wav, get_last_three_conversations, add_conversation, delete_all_conversations, post_process_using_gpt)

app = Flask(__name__)
CORS(app) 

# Basic configuration for your application's logger
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')

# Setting third-party libraries' loggers to a higher log level
logging.getLogger('google.auth').setLevel(logging.WARNING)
logging.getLogger('google.auth.transport.requests').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Unhandled Exception: {e}", exc_info=True)
    return jsonify({"error": "An internal server error occurred"}), 500

@app.route('/start-new-conversation', methods=['GET'])
def start_new_conversation():
    delete_all_conversations()
    return jsonify({"message": "New conversation started. Previous conversations deleted"})

@app.route('/process-audio', methods=['POST'])
def process_audio():
    app.logger.info("#" * 100)

    overall_start_time = time.time()

    if 'audio' not in request.files:
        return jsonify({"error": "No audio file part"}), 400
    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    input_lang = request.form.get('input_lang', 'en-US')
    output_lang = request.form.get('output_lang', 'es')
    voice_name = request.form.get('voice', 'Jarvis')
    mode = request.form.get('mode', 'patient') # TODO: Change to 'patient' after testing


    app.logger.info(f"RECEIVED REQUEST: \nInput language: {input_lang}, \nOutput language: {output_lang}, \nVoice: {voice_name}, \nMode: {mode}")

    try:
        # Save to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            audio_file.save(temp_audio)
            temp_audio_path = temp_audio.name

        # Convert to the proper WAV format
        time_to_convert = time.time()
        # converted_audio_path = convert_audio_to_wav(temp_audio_path)
        converted_audio_path = temp_audio_path
        if not converted_audio_path:
            os.unlink(temp_audio_path)  # Clean up the original temporary file
            return jsonify({"error": "Failed to convert audio file"}), 500
        convert_time = time.time() - time_to_convert
        app.logger.info(f"Audio conversion took {convert_time:.2f} seconds")

        # Get previous messages
        previous_texts = get_last_three_conversations()
        
        # if input text is english use whisper, else use google
        # if input_lang == 'en-US':
        #     transcribed_text = transcribe_audio_whisper(converted_audio_path, previous_texts, mode)
        # else: 
        time_to_transcribe = time.time()
        transcribed_text = transcribe_audio_deepgram_local(converted_audio_path, input_lang)
        time_to_transcribe = time.time() - time_to_transcribe
        app.logger.info(f"Transcription took {time_to_transcribe:.2f} seconds")

        # remove unwanted text
        if "*doctor" in transcribed_text or "*patient" in transcribed_text or "TRANSCRIBE THE FOLLOWING TEXT =>" in transcribed_text:
            transcribed_text = transcribed_text.replace("*doctor", "").replace("*patient", "").replace("TRANSCRIBE THE FOLLOWING TEXT =>", "")

        # add_conversation(transcribed_text, person_type=mode)


        if not transcribed_text:
            os.unlink(converted_audio_path)  # Clean up the converted file
            return jsonify({"error": "Transcription failed"}), 500

        # # Translation
        translation_start_time = time.time()

        if transcribed_text == "No text was provided. Please try again.":
            translated_text = "No text was provided. Please try again."
        else:
            translated_text = post_process_using_gpt(transcribed_text, mode, input_lang, output_lang)


        if not translated_text:
            os.unlink(converted_audio_path)  # Clean up the converted file
            return jsonify({"error": "Translation failed"}), 500
        translate_time = time.time() - translation_start_time
        app.logger.info(f"Translation took {translate_time:.2f} seconds")

        # Voice generation
        voice_generation_start_time = time.time()

       
        # voice_file_path = generate_voice_file_openai(translated_text)
        voice_file_path = generate_voice_file_eleven_labs(translated_text, voice_name)
    
    
        if not voice_file_path:
            os.unlink(converted_audio_path)  # Clean up the converted file
            return jsonify({"error": "Voice generation failed"}), 500
        voice_time = time.time() - voice_generation_start_time
        app.logger.info(f"Voice generation took {voice_time:.2f} seconds")

        overall_time = time.time() - overall_start_time
        app.logger.info(f"OVERALL PROCESSING TIME: {overall_time:.2f} seconds")

        os.unlink(converted_audio_path)  # Clean up the converted file

        if not os.path.exists(voice_file_path):
            app.logger.error("Generated voice file not found.")
            return jsonify({"error": "Generated voice file not found"}), 500

        # Read and encode the audio file
        with open(voice_file_path, "rb") as audio_file:
            encoded_audio = base64.b64encode(audio_file.read()).decode('utf-8')

        os.unlink(voice_file_path)  # Clean up the generated audio file

        # return both the audio as attachment and transcribed text
        return jsonify({
            "transcribed_text": transcribed_text,
            "translated_text": translated_text,
            "mode": mode,
            "voice_file_base64": encoded_audio
        })

    except Exception as e:
        if 'temp_audio_path' in locals():
            os.unlink(temp_audio_path)  # Ensure cleanup in case of error
        app.logger.error(f"Unhandled exception: {e}")
        return jsonify({"error": "An error occurred"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
