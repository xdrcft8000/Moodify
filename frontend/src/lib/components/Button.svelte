<script lang="ts">
    export let variant: 'default' | 'primary' | 'secondary' = 'default';
    export let type: 'button' | 'submit' | 'reset' = 'button';
    export let disabled = false;
  
    const variantClasses = {
      default: 'bg-white text-gray-800 border border-gray-300 hover:bg-gray-100',
      primary: 'bg-indigo-600 text-white hover:bg-indigo-700',
      secondary: 'bg-gray-700 text-white hover:bg-gray-800'
    };
  </script>
  
  <button
    {type}
    {disabled}
    class="rounded px-4 py-2 transition-colors {variantClasses[variant]}"
    on:click
  >
    <slot />
  </button>