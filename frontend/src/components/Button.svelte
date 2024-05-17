<!-- Button.svelte -->
<script>
  export let text = "Button"; // Default button text
  export let onClick = () => {}; // Default click handler function
  export let disabled = false; // Boolean to disable the button
  export let loading = false; // Boolean to show loading state

  // This function handles the button click, respecting the disabled state
  function handleClick() {
    if (!disabled && !loading) {
      onClick();
    }
  }
</script>

<button on:click={handleClick} class:loading disabled={disabled || loading}>
  {loading ? "Loading..." : text}
</button>

<style>
  button {
    padding: 10px 20px;
    margin-top: 10px;
    width: 100%;
    box-sizing: border-box;
    border-radius: 5px;
    border: 1px solid #ccc;
    background-color: #ddd;
    cursor: pointer;
    font-size: 16px;
    transition: background-color 0.3s ease;
  }

  button:hover:not(:disabled) {
    background-color: #004085;
    color: white;
  }

  .loading {
    background-color: #ccc; /* Grey out the button when loading */
  }
</style>
