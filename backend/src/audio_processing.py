import os
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
from pydub.exceptions import CouldntDecodeError
from pydub.utils import mediainfo
import logging
import time

# Ensure the logger uses the same configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Set the appropriate level if needed

def convert_audio_to_wav(input_file):
    """Converts an audio file to WAV format with 16-bit samples."""
    convert_audio_start_time = time.time()
    output_file = os.path.splitext(input_file)[0] + '.wav'
    try:
        audio = AudioSegment.from_file(input_file)
        # Ensure the audio is 16-bit, mono, and at the desired frame rate
        audio = audio.set_sample_width(2)  # 2 bytes (16 bits)
        audio = audio.set_frame_rate(16000)  # 16 kHz
        audio = audio.set_channels(1)  # Mono
        audio = trim_silence(audio)  # Trim silence from the audio
        audio.export(output_file, format='wav')
    except CouldntDecodeError as e:
        logger.error(f"Could not decode the input file: {e}")
        return None
    except Exception as e:
        logger.error(f"Error in converting audio file: {e}", exc_info=True)
        return None
    
    time_to_convert_audio = time.time() - convert_audio_start_time
    logger.info(f"Time to convert audio: {time_to_convert_audio:.2f} seconds")
    return output_file

def trim_silence(audio_segment, silence_threshold=-50.0, chunk_size=10):
    """
    Trims silence from an AudioSegment.

    :param audio_segment: AudioSegment object
    :param silence_threshold: The threshold in dBFS considered silence
    :param chunk_size: The size of chunks to use in milliseconds for silence detection
    :return: AudioSegment without silence
    """
    nonsilent_parts = detect_nonsilent(audio_segment, min_silence_len=chunk_size,
                                       silence_thresh=silence_threshold)
    trimmed_audio = audio_segment[:0]  # Create an empty audio segment
    for start_i, end_i in nonsilent_parts:
        trimmed_audio += audio_segment[start_i:end_i]  # Concatenate non-silent audio chunks
    return trimmed_audio

def get_audio_info(speech_file):
    """Retrieves audio file information using mediainfo from pydub."""
    try:
        audio_info = mediainfo(speech_file)
        audio_format = audio_info.get('format_name', '').split(',')[0].lower()
        sample_rate = int(audio_info.get('sample_rate', '16000'))
        return audio_format, sample_rate
    except Exception as e:
        logger.error(f"Error in getting audio file info: {e}", exc_info=True)
        return None, None
