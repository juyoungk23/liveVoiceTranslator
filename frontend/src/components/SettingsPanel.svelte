<!-- SettingsPanel.svelte -->

<script>
  import { settings } from "../stores/settingsStore.js";
  import { languages, voices } from "../utils/config.js";

  export let person;
</script>

<div class="settings">
  <div class="column">
    <div>
      <label for={`${person}-inputLanguage`}>Input Language:</label>
      <select
        id={`${person}-inputLanguage`}
        bind:value={$settings[person].inputLanguage}
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
        bind:value={$settings[person].outputLanguage}
      >
        {#each languages as language}
          <option value={language.value}>{language.label}</option>
        {/each}
      </select>
    </div>
    <div>
      <label for={`${person}-voice`}>Voice:</label>
      <select id={`${person}-voice`} bind:value={$settings[person].voice}>
        {#each voices as voice}
          <option value={voice.value}>{voice.label}</option>
        {/each}
      </select>
    </div>
  </div>
</div>

<style>
  .settings {
    display: flex;
    justify-content: space-around;
    margin: 20px 0;
  }

  .column {
    flex-basis: 48%;
    display: block;
  }

  select {
    padding: 10px;
    width: 100%;
    margin-top: 5px;
    margin-bottom: 15px;
    box-sizing: border-box;
    border-radius: 5px;
    border: 1px solid #ccc;
  }

  label {
    margin-top: 10px;
    color: #333;
  }
</style>
