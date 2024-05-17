// countdownUtils.js

// Start the countdown and provide an interval that can be stopped
export function startCountdown(setCountdown, duration) {
  let currentCount = duration;
  const interval = setInterval(() => {
    currentCount -= 1;
    setCountdown(currentCount);
    if (currentCount <= 0) {
      clearInterval(interval);
    }
  }, 1000);

  return interval;
}

// Stop the countdown interval
export function stopCountdown(interval) {
  clearInterval(interval);
  console.log("Countdown stopped");
}
