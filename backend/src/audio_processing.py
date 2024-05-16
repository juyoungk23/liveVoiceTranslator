import subprocess
import os
import logging
import time

# Set up logging configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def convert_audio_to_wav(input_file):
    """Converts any audio file to WAV format with 16-bit samples, 16 kHz, mono, and trims silence using FFmpeg."""
    convert_audio_start_time = time.time()
    output_file = os.path.splitext(input_file)[0] + '.wav'

    # FFmpeg command to convert audio, ensuring it's mono, 16-bit, 16kHz, and trim silence
    command = [
        'ffmpeg',
        '-i', input_file,
        '-af', 'silenceremove=1:0:-50dB',  # Trimming silence: start_periods=1, start_duration=0, start_threshold=-50dB
        '-ar', '16000',  # Set sample rate to 16000 Hz
        '-ac', '1',      # Set audio to mono
        '-acodec', 'pcm_s16le',  # Set audio codec to PCM 16-bit little-endian
        '-y',            # Overwrite output file without asking
        output_file
    ]

    try:
        subprocess.run(command, check=True, stderr=subprocess.PIPE)
        logger.info(f"Audio converted and trimmed, saved to {output_file}")
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error: {e.stderr.decode()}")
        return None

    logger.info(f"Audio file converted in {time.time() - convert_audio_start_time:.2f} seconds.")
    return output_file

def get_audio_info(speech_file):
    """Uses FFmpeg to retrieve basic information about an audio file."""
    command = ['ffprobe', '-v', 'error', '-show_entries', 'format=format_name:stream=sample_rate', '-of', 'default=noprint_wrappers=1', speech_file]
    try:
        result = subprocess.run(command, text=True, capture_output=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"FFprobe error: {e.stderr}")
        return None
