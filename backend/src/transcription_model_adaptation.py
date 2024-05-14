
from google.cloud import speech_v1p1beta1 as speech


def transcribe_with_model_adaptation(
    project_id: str,
    location: str,
    storage_uri: str,
    custom_class_id: str,
    phrase_set_id: str,
) -> str:
    """Create`PhraseSet` and `CustomClasses` to create custom lists of similar
    items that are likely to occur in your input data.

    Args:
        project_id: The GCP project ID.
        location: The GCS location of the input audio.
        storage_uri: The Cloud Storage URI of the input audio.
        custom_class_id: The ID of the custom class to create

    Returns:
        The transcript of the input audio.
    """

    # Create the adaptation client
    adaptation_client = speech.AdaptationClient()

    # The parent resource where the custom class and phrase set will be created.
    parent = f"projects/{project_id}/locations/{location}"

    # Create the custom class resource
    adaptation_client.create_custom_class(
        {
            "parent": parent,
            "custom_class_id": custom_class_id,
            "custom_class": {
                "items": [
                    {"value": "sushido"},
                    {"value": "altura"},
                    {"value": "taneda"},
                ]
            },
        }
    )
    custom_class_name = (
        f"projects/{project_id}/locations/{location}/customClasses/{custom_class_id}"
    )
    # Create the phrase set resource
    phrase_set_response = adaptation_client.create_phrase_set(
        {
            "parent": parent,
            "phrase_set_id": phrase_set_id,
            "phrase_set": {
                "boost": 10,
                "phrases": [
                    {"value": f"Visit restaurants like ${{{custom_class_name}}}"}
                ],
            },
        }
    )
    phrase_set_name = phrase_set_response.name
    # The next section shows how to use the newly created custom
    # class and phrase set to send a transcription request with speech adaptation

    # Speech adaptation configuration
    speech_adaptation = speech.SpeechAdaptation(phrase_set_references=[phrase_set_name])

    # speech configuration object
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=24000,
        language_code="en-US",
        adaptation=speech_adaptation,
    )

    # The name of the audio file to transcribe
    # storage_uri URI for audio file in Cloud Storage, e.g. gs://[BUCKET]/[FILE]

    audio = speech.RecognitionAudio(uri=storage_uri)

    # Create the speech client
    speech_client = speech.SpeechClient()

    response = speech_client.recognize(config=config, audio=audio)

    for result in response.results:
        print(f"Transcript: {result.alternatives[0].transcript}")