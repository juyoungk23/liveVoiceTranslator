// settingsStore.js
import { writable } from "svelte/store";

export const settings = writable({
  person1: {
    inputLanguage: "en-US",
    outputLanguage: "es",
    voice: "",
  },
  person2: {
    inputLanguage: "en-US",
    outputLanguage: "es",
    voice: "",
  },
});

// Function to update settings for a specific mode
export function updateSettings(mode, newSettings) {
  settings.update((s) => {
    s[mode] = { ...s[mode], ...newSettings };
    return s;
  });
}
