<script>
// @ts-nocheck

  import { writable } from 'svelte/store';
  
  let isSubmitting = false; 
  let audioFile;
  let inputLanguage = 'en-US';
  let outputLanguage = 'es';
  let voice = '';

  // Placeholder URL for the audio blob
  let audioUrl = writable(''); 
  let serverUrl = 'https://api.thevoicetranslator.com/process-audio';
  // let audioUrl = writable(''); // Store the URL for the audio blob

  let isRecording = false;
  let audioRecorder;
  let recordedAudio;
  let mode = 'record'; // Possible values: 'upload', 'record'


  const voices = [
    {label: 'Juyoung'},{label: 'Jessica'}, {label: 'Aditi'}, {label: 'Nimal'}, {label: "Jane"}
  ]

   const languages = [
    { label: 'Chinese', value: 'zh-CN' },
    { label: 'Korean', value: 'ko-KR' },
    { label: 'Dutch', value: 'nl-NL' },
    { label: 'Turkish', value: 'tr-TR' },
    { label: 'Swedish', value: 'sv-SE' },
    { label: 'Indonesian', value: 'id-ID' },
    { label: 'Filipino', value: 'fil-PH' },
    { label: 'Japanese', value: 'ja-JP' },
    { label: 'Ukrainian', value: 'uk-UA' },
    { label: 'Greek', value: 'el-GR' },
    { label: 'Czech', value: 'cs-CZ' },
    { label: 'Finnish', value: 'fi-FI' },
    { label: 'Romanian', value: 'ro-RO' },
    { label: 'Russian', value: 'ru-RU' },
    { label: 'Danish', value: 'da-DK' },
    { label: 'Bulgarian', value: 'bg-BG' },
    { label: 'Malay', value: 'ms-MY' },
    { label: 'Slovak', value: 'sk-SK' },
    { label: 'Croatian', value: 'hr-HR' },
    { label: 'Classic Arabic', value: 'ar-SA' },
    { label: 'Tamil', value: 'ta-IN' },
    { label: 'English', value: 'en-US' },
    { label: 'Polish', value: 'pl-PL' },
    { label: 'German', value: 'de-DE' },
    { label: 'Spanish', value: 'es-ES' },
    { label: 'French', value: 'fr-FR' },
    { label: 'Italian', value: 'it-IT' },
    { label: 'Hindi', value: 'hi-IN' },
    { label: 'Portuguese', value: 'pt-BR' }
 
  ];

  let recordingTimeout;

async function startRecording() {
  if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mediaRecorder = new MediaRecorder(stream);
    audioRecorder = mediaRecorder;
    mediaRecorder.start();

    const audioChunks = [];
    mediaRecorder.addEventListener("dataavailable", event => {
      audioChunks.push(event.data);
    });

    mediaRecorder.addEventListener("stop", () => {
      const audioBlob = new Blob(audioChunks.slice(0, 15)); // Trim to first 15 seconds
      const audioUrl = URL.createObjectURL(audioBlob);
      recordedAudio = new File([audioBlob], "recordedAudio.wav", { type: "audio/wav" });
      audioFile = recordedAudio; // Set the recorded audio as the file to be submitted
    });

    isRecording = true;

    // Automatically stop recording after 15 seconds
    recordingTimeout = setTimeout(stopRecording, 15000);
  } else {
    console.error("Recording not supported");
  }
}

function stopRecording() {
  if (audioRecorder) {
    audioRecorder.stop();
    clearTimeout(recordingTimeout);
    isRecording = false;
  }
}
  async function handleSubmit() {
    isSubmitting = true; // Disable the button and change text when submission starts
    console.log('Submitting form...');
    console.log(`Input Language: ${inputLanguage}, Output Language: ${outputLanguage}`);

    const formData = new FormData();
    formData.append('audio', audioFile);
    formData.append('input_lang', inputLanguage);
    formData.append('output_lang', outputLanguage.substring(0,2));
    formData.append('voice', voice);

    console.log('Sending request to server...');

    try {
      const response = await fetch(serverUrl, {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        console.log('Received response from server');
        const blob = await response.blob();
        console.log('Received blob:', blob);

        // Create a URL for the blob and update audioUrl
        audioUrl.set(URL.createObjectURL(blob));
      } else {
        console.error('Server error:', response);
      }
    } catch (error) {
      console.error('Error sending request to server:', error);
    }
    
    isSubmitting = false;
  }
</script>

<div class="container">
  <h1>Audio Translation App</h1>

  <!-- Tab-like buttons for mode selection -->
  <div class="mode-selector">
    <button class={mode === 'record' ? 'active' : ''} on:click={() => mode = 'record'}>Record Audio</button>
    <button class={mode === 'upload' ? 'active' : ''} on:click={() => mode = 'upload'}>Upload Audio</button>
  </div>

  <!-- Upload Audio -->
  {#if mode === 'upload'}
    <div>
      <label for="audioFile">Upload Audio:</label>
      <input type="file" accept="audio/*" on:change="{(e) => { audioFile = e.target.files[0]; console.log('Audio file selected:', audioFile.name); }}">
      <p>File length max 30 seconds...</p>
    </div>
  {/if}

<!-- Record Audio -->
{#if mode === 'record'}
  <div>
    <button on:click={() => (isRecording ? stopRecording() : startRecording())}>
      {isRecording ? 'Stop Recording' : 'Start Recording'}
    </button>
    <p>Can record up to 15 seconds...</p>
  </div>
{/if}

  <div>
    <label for="inputLanguage">Input Language:</label>
    <select bind:value={inputLanguage}>
      {#each languages as language}
        <option value={language.value}>{language.label}</option>
      {/each}
    </select>
  </div>

  <div>
    <label for="outputLanguage">Output Language:</label>
    <select bind:value={outputLanguage}>
      {#each languages as language}
        <option value={language.value}>{language.label}</option>
      {/each}
    </select>
  </div>

  <div>
    <label for="voice">Voice:</label>
    <select bind:value={voice}>
      {#each voices as voice}
        <option value={voice.label}>{voice.label}</option>
      {/each}
    </select>
  </div>


  <button on:click={handleSubmit} disabled={isSubmitting}>
    {isSubmitting ? 'Generating...' : 'Submit'}
  </button>

  <!-- Audio Player -->
  <div class="audio-player">
    {#if $audioUrl}
      <audio src="{$audioUrl}" controls></audio>
    {/if}
  </div>
</div>

<style>
  :global(body) {
    font-family: Arial, sans-serif;
    background-color: #f8f8f8;
    color: #333;
  }

  button:disabled {
  background-color: #cccccc; /* Gray background */
  color: #666666; /* Darker text to indicate it's disabled */
  cursor: not-allowed; /* Change cursor to indicate it's not clickable */
}


  h1 {
    color: #ff4500; /* International Orange */
  }
  select, input[type='file'], button {
    display: block;
    margin: 10px 0;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
    width: 100%;
    box-sizing: border-box;
  }
  button {
    background-color: #ff4500;
    color: white;
    cursor: pointer;
  }
  button:hover {
    background-color: #e03d00;
  }
  .container {
    max-width: 600px;
    margin: 0 auto;
    padding: 20px;
    text-align: center;
  }
  .audio-player {
    margin-top: 20px;
  }

  .mode-selector {
    display: flex;
    justify-content: center;
    margin-bottom: 20px;
  }

  .mode-selector button {
    background-color: #ddd;
    border: none;
    padding: 10px 20px;
    margin-right: 5px;
    cursor: pointer;
  }

  .mode-selector button.active {
    background-color: #ff4500;
    color: white;
  }

  .mode-selector button:last-child {
    margin-right: 0;
  }



</style>
