<script>
  import {
    mode,
    isRecording,
    hasStartedRecording,
    audioUrl,
    startRecording,
    stopRecording,
  } from "./stores/recordingStore";
  import { settings, updateSettings } from "./stores/settingsStore";
  import { languages, voices } from "./utils/config"; // Assuming config.js holds constant data
  import ModeSelector from "./components/ModeSelector.svelte";
  import SettingsPanel from "./components/SettingsPanel.svelte";
  import AudioPlayer from "./components/AudioPlayer.svelte";
  import Button from "./components/Button.svelte";

  let selectedModeSettings = {};

  // When the mode changes, update local settings to reflect the current mode's settings
  $: selectedModeSettings = $settings[$mode];

  // Function to handle mode change
  function switchMode(newMode) {
    mode.set(newMode);
  }
</script>

<div class="container">
  <h1>Audio Translation App</h1>

  <!-- Mode Selector -->
  <ModeSelector />

  <!-- Settings Panel -->
  <SettingsPanel person={$mode} />

  <!-- Recording and Submit Buttons -->
  <button
    on:click={isRecording ? stopRecording : startRecording}
    disabled={$hasStartedRecording}
    class:active={$isRecording}
    class:red={isRecording}
    class:record-button={true}
  >
    {$isRecording ? "Stop Recording" : "Start Recording"}
  </button>
  <button
    on:click={handleSubmit}
    disabled={!$audioUrl || $isRecording}
    class:loading={$isRecording || !$audioUrl}
  >
    Submit
  </button>

  <!-- Audio Player -->
  {#if $audioUrl}
    <div class="audio-player">
      <AudioPlayer />
    </div>
  {/if}
</div>

<style>
  :global(body) {
    font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
    background-color: #fbf6f6;
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
  .mode-selector button.active {
    background-color: #0056b3;
    color: white;
  }
  .settings select {
    width: 100%;
    padding: 8px;
    margin-top: 5px;
    border-radius: 4px;
    border: 1px solid #ccc;
  }
  .audio-player {
    margin-top: 20px;
  }

  h1 {
    color: #333;
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
</style>
