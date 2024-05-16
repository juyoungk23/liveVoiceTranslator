import subprocess
import os
import logging
import time

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def convert_audio_to_wav(input_file):
    """Converts any audio file to WAV format with 16-bit samples, 16 kHz, mono, and trims silence using FFmpeg."""
    output_file = os.path.splitext(input_file)[0] + '_converted.wav'
    if input_file == output_file:  # Prevent overwriting the input file
        output_file = os.path.splitext(input_file)[0] + '_new.wav'

    convert_audio_start_time = time.time()

    # Adjust silenceremove to allow some silence in the audio, preventing early termination during transcription
    silence_filter = (
        'silenceremove=start_periods=1:start_duration=0.5:start_threshold=-30dB:'
        'stop_periods=1:stop_duration=0.5:stop_threshold=-30dB'
    )

    command = [
        'ffmpeg',
        '-i', input_file,
        '-af', silence_filter,  # Updated silence removal filter with more tolerance
        '-ar', '16000',  # Set sample rate to 16000 Hz
        '-ac', '1',  # Set to mono channel
        '-acodec', 'pcm_s16le',  # Set codec to PCM 16-bit little-endian
        '-y',  # Overwrite output file without asking
        output_file
    ]

    try:
        subprocess.run(command, check=True, stderr=subprocess.PIPE)
        logger.info(f"Audio converted and trimmed, saved to {output_file}")
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error: {e.stderr.decode()}")
        return None

    conversion_time = time.time() - convert_audio_start_time
    logger.info(f"Audio file converted in {conversion_time:.2f} seconds.")
    return output_file

def get_audio_info(speech_file):
    """Retrieves basic information about an audio file using FFprobe."""
    command = ['ffprobe', '-v', 'error', '-show_entries', 'format=format_name:stream=sample_rate', '-of', 'default=noprint_wrappers=1', speech_file]
    try:
        result = subprocess.run(command, text=True, capture_output=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"FFprobe error: {e.stderr}")
        return None
