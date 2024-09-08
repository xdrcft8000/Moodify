<script lang="ts">
    export let data;
    const { templates } = data;
</script>

<h1>Questionnaires</h1>
{#if templates.length > 0}
    <ul>
        {#each templates as template (template.title)}
            <li>{template.title} {template.duration} <a href="/questionnaires/{template.id}">View</a> </li>
        {/each}
    </ul>
{/if}

