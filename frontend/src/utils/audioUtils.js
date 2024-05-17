// audioUtils.js
export async function setupMediaRecorder(onDataAvailable, onStop) {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    console.error("Recording not supported");
    return null;
  }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mediaRecorder = new MediaRecorder(stream);

    mediaRecorder.ondataavailable = onDataAvailable;
    mediaRecorder.onstop = onStop;

    return mediaRecorder;
  } catch (error) {
    console.error("Failed to setup media recorder:", error);
    return null;
  }
}
