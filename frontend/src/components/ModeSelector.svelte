<!-- ModeSelector.svelte -->

<script>
  import { mode } from "../stores/recordingStore.js";

  function switchMode(newMode) {
    mode.set(newMode);
  }
</script>

<div class="mode-selector">
  <button
    class:active={$mode === "person1"}
    on:click={() => switchMode("person1")}
  >
    Doctor
  </button>
  <button
    class:active={$mode === "person2"}
    on:click={() => switchMode("person2")}
  >
    Patient
  </button>
</div>

<style>
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
</style>
