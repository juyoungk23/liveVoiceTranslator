# audio_processing.py
import os
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError
from pydub.utils import mediainfo
import logging

def convert_audio_to_16_bit(input_file):
    """Converts an audio file to 16-bit WAV format."""
    output_file = os.path.splitext(input_file)[0] + '_16bit.wav'
    try:
        audio = AudioSegment.from_file(input_file)
        audio = audio.set_sample_width(2)  # 2 bytes (16 bits)
        audio.export(output_file, format='wav')
    except CouldntDecodeError as e:
        logging.error(f"Could not decode the input file: {e}")
        return None
    except Exception as e:
        logging.error(f"Error in converting audio file to 16-bit: {e}", exc_info=True)
        return None
    return output_file

def convert_audio_to_wav(input_file):
    """Converts an audio file to WAV format with 16-bit samples and trims it to 30 seconds."""
    output_file = os.path.splitext(input_file)[0] + '.wav'
    try:
        audio = AudioSegment.from_file(input_file)
        # Ensure the audio is 16-bit, mono, and at the desired frame rate
        audio = audio.set_sample_width(2)  # 2 bytes (16 bits)
        audio = audio.set_frame_rate(16000)  # 16 kHz
        audio = audio.set_channels(1)  # Mono
        audio.export(output_file, format='wav')
    except CouldntDecodeError as e:
        logging.error(f"Could not decode the input file: {e}")
        return None
    except Exception as e:
        logging.error(f"Error in converting audio file: {e}", exc_info=True)
        return None
    return output_file

def get_audio_info(speech_file):
    """Retrieves audio file information using mediainfo from pydub."""
    try:
        audio_info = mediainfo(speech_file)
        audio_format = audio_info.get('format_name', '').split(',')[0].lower()
        sample_rate = int(audio_info.get('sample_rate', '16000'))
        return audio_format, sample_rate
    except Exception as e:
        logging.error(f"Error in getting audio file info: {e}", exc_info=True)
        return None, None
