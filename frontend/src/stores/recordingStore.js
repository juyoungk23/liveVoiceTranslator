import { writable, get } from "svelte/store";
import { setupMediaRecorder } from "../utils/audioUtils";

export const mode = writable("person1");
export const isRecording = writable(false);
export const hasStartedRecording = writable(false);
export const audioUrl = writable("");
export const countdown = writable(30);

let mediaRecorder;
let countdownInterval;
let audioChunks = []; // This will store the chunks of audio data

export async function startRecording() {
  const onDataAvailable = (event) => {
    // Append received audio data to the audioChunks array
    audioChunks.push(event.data);
  };

  const onStop = () => {
    // Create a Blob from the recorded audio chunks
    const audioBlob = new Blob(audioChunks, { type: "audio/wav" });
    // Create a URL for the Blob for easy access and playback
    const audioUrlLocal = URL.createObjectURL(audioBlob);
    // Update the audioUrl store with the new URL to trigger UI updates
    audioUrl.set(audioUrlLocal);
    // Reset the audioChunks for the next recording session
    audioChunks = [];
    // Update recording states
    hasStartedRecording.set(false);
  };

  // Setup the MediaRecorder with the event handlers
  mediaRecorder = await setupMediaRecorder(onDataAvailable, onStop);
  if (mediaRecorder) {
    mediaRecorder.start(); // Start recording
    isRecording.set(true);
    hasStartedRecording.set(true);
    manageCountdown(); // Start the countdown
  }
}

function manageCountdown() {
  countdown.set(get(countdown)); // Initialize countdown with the set duration
  countdownInterval = setInterval(() => {
    countdown.update((n) => {
      if (n > 0) return n - 1;
      clearInterval(countdownInterval);
      stopRecording(); // Automatically stop recording when countdown ends
      return 0;
    });
  }, 1000);
}

export function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    mediaRecorder.stop(); // Stops the recording
    clearInterval(countdownInterval); // Clears the countdown interval
    isRecording.set(false);
    hasStartedRecording.set(false);
  }
}
