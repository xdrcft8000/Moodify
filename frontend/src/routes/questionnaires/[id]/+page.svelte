<script lang="ts">
    import { page } from '$app/stores';
    import { appData } from '$lib/stores/appData';
    import { onMount } from 'svelte';

    $: templateId = $page.params.id;
    $: template = $appData.templates.find(t => t.id === parseInt(templateId));
</script>

<h1>{template!.title}</h1>

