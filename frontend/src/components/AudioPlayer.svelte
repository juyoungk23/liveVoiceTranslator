<!-- AudioPlayer.svelte -->
<script>
  import { audioUrl } from "../stores/recordingStore.js";

  // Function to play audio when the metadata is loaded
  function playAudio(event) {
    if (event.target.getAttribute("data-playable") === "true") {
      event.target.play().catch((error) => {
        console.error("Error playing audio:", error.message);
      });
    }
  }
</script>

<!-- This conditionally renders the audio player if there is an audio URL -->
{#if $audioUrl}
  <div class="audio-player">
    <audio src={$audioUrl} controls on:loadedmetadata={playAudio}></audio>
  </div>
{/if}

<style>
  .audio-player {
    margin-top: 20px;
  }
</style>
