<script>
  import { writable } from "svelte/store";
  import { voices, languages } from "./config.js";
  let audioFile;
  let isSubmitting = false;
  let serverUrl = "https://api.thevoicetranslator.com/process-audio";
  let isRecording = false;
  let audioRecorder;
  let mode = writable("person1"); // Default to person1

  let audioUrl = writable("");

  let countdownDuration = 30;
  let countdown = writable(countdownDuration);
  let countdownInterval;

  // Person specific settings
  let settings = {
    person1: { inputLanguage: "en-US", outputLanguage: "es", voice: "" },
    person2: { inputLanguage: "en-US", outputLanguage: "es", voice: "" },
  };

  function resetAudio() {
    audioFile = undefined;
    audioUrl.set("");
    if (isRecording) {
      stopRecording();
    }
  }

  // Update the mode switch with a check to reset audio
  function switchMode(newMode) {
    if (!isRecording && $mode !== newMode) {
      resetAudio();
      $mode = newMode;
    }
  }

  async function startRecording() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      console.error("Recording not supported");
      return;
    }
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mediaRecorder = new MediaRecorder(stream);
    audioRecorder = mediaRecorder;
    mediaRecorder.start();

    let audioChunks = [];
    mediaRecorder.addEventListener("dataavailable", (event) => {
      audioChunks.push(event.data);
    });

    mediaRecorder.addEventListener("stop", () => {
      const audioBlob = new Blob(audioChunks);
      audioFile = new File([audioBlob], "recordedAudio.wav", {
        type: "audio/wav",
      });
      audioUrl.set(URL.createObjectURL(audioBlob));
    });

    isRecording = true;
    countdown.set(countdownDuration);
    countdownInterval = setInterval(() => {
      countdown.update((n) => (n > 0 ? n - 1 : 0));
    }, 1000);

    setTimeout(() => {
      if (isRecording) stopRecording();
    }, countdownDuration * 1000);
  }

  function stopRecording() {
    if (audioRecorder) {
      audioRecorder.stop();
      clearInterval(countdownInterval);
      isRecording = false;
      countdown.set(countdownDuration);
    }
  }

  async function handleSubmit() {
    isSubmitting = true;
    let currentSettings =
      $mode === "person1" ? settings.person1 : settings.person2;
    const formData = new FormData();
    formData.append("audio", audioFile);
    formData.append("input_lang", currentSettings.inputLanguage);
    formData.append(
      "output_lang",
      currentSettings.outputLanguage.substring(0, 2)
    );
    formData.append("voice", currentSettings.voice);

    // Debugging FormData contents
    for (let [key, value] of formData.entries()) {
      console.log(key, value);
    }

    try {
      const response = await fetch(serverUrl, {
        method: "POST",
        body: formData,
      });
      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        audioUrl.set(url);
      } else {
        console.error("Server error:", response);
      }
      isSubmitting = false;
    } catch (error) {
      console.error("Failed to submit audio:", error);
      isSubmitting = false;
    }
  }
</script>

<div class="container">
  <h1>Audio Translation App</h1>
  <div class="mode-selector">
    <button
      class:active={$mode === "person1"}
      on:click={() => switchMode("person1")}>Person 1</button
    >
    <button
      class:active={$mode === "person2"}
      on:click={() => switchMode("person2")}>Person 2</button
    >
  </div>

  <div class="settings">
    {#each Object.entries(settings) as [person, config]}
      <div class={`column ${$mode === person ? "active" : ""}`}>
        <h2>{person}</h2>
        <div>
          <label for={`${person}-inputLanguage`}>Input Language:</label>
          <select
            id={`${person}-inputLanguage`}
            bind:value={config.inputLanguage}
          >
            {#each languages as language}
              <option value={language.value}>{language.label}</option>
            {/each}
          </select>
        </div>
        <div>
          <label for={`${person}-outputLanguage`}>Output Language:</label>
          <select
            id={`${person}-outputLanguage`}
            bind:value={config.outputLanguage}
          >
            {#each languages as language}
              <option value={language.value}>{language.label}</option>
            {/each}
          </select>
        </div>
        <div>
          <label for={`${person}-voice`}>Voice:</label>
          <select id={`${person}-voice`} bind:value={config.voice}>
            {#each voices as voice}
              <option value={voice.label}>{voice.label}</option>
            {/each}
          </select>
        </div>
      </div>
    {/each}
  </div>
  <button
    on:click={isRecording ? stopRecording : startRecording}
    class:record-button={true}
    class:red={isRecording}
    disabled={isSubmitting}
  >
    {isRecording ? "Stop Recording" : "Start Recording"}
  </button>
  <p>Recording... <span>{$countdown}</span> seconds left</p>
  <button on:click={handleSubmit} disabled={isSubmitting || isRecording}>
    {isSubmitting ? "Submitting..." : "Submit"}
  </button>
  {#if $audioUrl}
    <div class="audio-player">
      <audio src={$audioUrl} controls></audio>
    </div>
  {/if}
</div>

<style>
  :global(body) {
    font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
    background-color: #f4f4f4;
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  .container {
    max-width: 800px;
    margin: 20px auto;
    padding: 20px;
    background-color: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 15px rgba(0, 0, 0, 0.1);
    text-align: center;
  }

  h1 {
    color: #333;
    margin-bottom: 20px;
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
    margin: 0 10px;
    font-size: 16px;
    cursor: pointer;
    border-radius: 20px;
    transition: background-color 0.3s;
  }

  .mode-selector button.active {
    background-color: #0056b3;
    color: white;
  }

  .settings {
    display: flex;
    justify-content: space-between;
    margin: 20px 0;
  }

  .column {
    display: none;
    flex-basis: 48%;
  }

  .column.active {
    display: block;
  }
  .record-button.red {
    background-color: red; /* Red color when recording */
  }

  .record-button {
    width: 100px;
    height: 100px;
    border-radius: 50%;
    background-color: green; /* Green color when ready to record */
    color: white;
    border: none;
    cursor: pointer;
    font-size: 16px;
    outline: none;
  }
  button,
  select {
    padding: 10px;
    margin-top: 10px;
    width: 100%;
    box-sizing: border-box;
    border-radius: 5px;
    border: 1px solid #ccc;
  }

  button:hover:not(:disabled) {
    background-color: #004085;
    color: white;
  }

  .audio-player {
    margin-top: 20px;
  }

  p {
    margin-top: 10px;
  }
</style>
