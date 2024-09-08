<script lang="ts">
    import "../app.css";
    import { page } from '$app/stores';
    import { onMount } from 'svelte';
    import { theme } from '$lib/stores/theme';
    import { derived } from 'svelte/store';
    import { tweened } from 'svelte/motion';
    import { cubicOut } from 'svelte/easing';
    import { writable } from "svelte/store";
    export let data;
    import "$lib/fa";
    import { FontAwesomeIcon } from '@fortawesome/svelte-fontawesome';
    import { faUser } from '@fortawesome/free-solid-svg-icons';

    const { patients, questionnaires, templates } = data;
    function toggleTheme() {
        theme.update(currentTheme => currentTheme === 'dark' ? 'light' : 'dark');
    }

        // Update the HTML class when the theme changes
    $: {
        if (typeof document !== 'undefined') {
            document.documentElement.classList.toggle('dark', $theme === 'dark');
        }
    }


    let isDropdownOpen = false;
  
    function toggleDropdown() {
      isDropdownOpen = !isDropdownOpen;
    }


  
    // Close dropdown when clicking outside
    onMount(() => {
      const handleClickOutside = (event) => {
        if (isDropdownOpen && !event.target.closest('.profile-dropdown')) {
          isDropdownOpen = false;
        }
      };
      document.addEventListener('click', handleClickOutside);
      return () => {
        document.removeEventListener('click', handleClickOutside);
      };
    });



    const underlinePosition = tweened(0, {
        duration: 300,
        easing: cubicOut
    });

    const underlineWidth = tweened(0, {
        duration: 300,
        easing: cubicOut
    });

    $: {
        if ($page.url.pathname === '/patients') {
            underlinePosition.set(50);
            underlineWidth.set(90);
        } else if ($page.url.pathname === '/questionnaires') {
            underlinePosition.set(190);
            underlineWidth.set(155);
        }
    }

</script>

<style>
    :global(body) {
        display: flex;
        flex-direction: column;
        min-height: 100vh;
    }

    .nav-links {
        position: relative;
    }
    .nav-link span {
        position: relative;
        z-index: 1;
    }
    .underline {
        position: absolute;
        bottom: -2px;
        height: 2px;
        width: 50%;
        transition: transform 100ms cubic-bezier(0.25, 0.1, 0.25, 1);
    }
</style>


<nav class="flex justify-between items-center p-4 bg-primary dark:bg-primary-dark">
    <div class="flex items-center">
        <div class="text-5xl px-2 font-serif dark:text-secondary-dark">Moodulate.</div>
        <div class="space-x-6 pl-16 pt-2 nav-links">
            <a href="/patients" class="nav-link text-black text-2xl dark:text-white font-hangang">
                <span class="py-2 px-4 inline-block">Patients</span>
            </a>
            <a href="/questionnaires" class="nav-link text-black text-2xl dark:text-white font-hangang">
                <span class="py-2 px-4 inline-block">Questionnaires</span>
            </a>
            <div class="ml-16 underline bg-black dark:bg-white" style="width: {$underlineWidth}px; left: {$underlinePosition}px;"></div>
        </div>
    </div>
        <div class="relative flex items-center">
        <label class="inline-flex items-center cursor-pointer mr-4">
            <input type="checkbox" checked={$theme === 'dark'} on:change={toggleTheme} class="sr-only peer">
            <div class="relative w-11 h-6 bg-black dark:bg-white rounded-full peer 
            peer-checked:bg-violet-600 peer-focus:ring-4 peer-focus:ring-violet-300
            after:content-[''] after:absolute after:top-[2px] after:left-[2px] 
            after:bg-white dark:after:bg-black after:rounded-full after:h-5 after:w-5 
            after:transition-all peer-checked:after:translate-x-full
            dark:peer-checked:bg-violet-500 dark:peer-focus:ring-violet-800">
        </div>        </label>
        <button on:click={toggleDropdown} class="text-2xl bg-transparent border-none cursor-pointer profile-dropdown">
            <FontAwesomeIcon icon={faUser} />
        </button>
                {#if isDropdownOpen}
            <div class="profile-dropdown absolute right-0 top-full mt-2 w-48 bg-primary border border-secondary rounded-md shadow-lg z-10">
                <a href="/profile" class="block px-4 py-2 hover:bg-brown hover:text-white">Profile</a>
                <a href="/settings" class="block px-4 py-2 hover:bg-brown hover:text-white">Settings</a>
                <a href="/logout" class="block px-4 py-2 hover:bg-brown hover:text-white">Logout</a>
            </div>
        {/if}
    </div>
</nav>



<main class="bg-primary dark:bg-primary-dark flex-grow">
    <slot />
</main>
