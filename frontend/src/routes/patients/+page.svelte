<script lang="ts">
    import { appData } from '$lib/stores/appData';
    export let data;
    const { patients, questionnaires, templates } = data;
</script>


<div class="flex items-center">
    <div class="flex-grow border-b-2 border-black"></div>
    <h1 class="text-3xl mx-8 font-hangang whitespace-nowrap">{patients.length} Patients</h1>
    <div class="flex-grow border-b-2 border-black"></div>
</div>
{#if patients.length > 0}
    <div class=" border-b border-black py-4 px-8">
        <ul class="space-y-1">
            {#each patients as patient (patient.id)}
            <li class="py-2 px-3 hover:bg-gray-100 cursor-pointer rounded">
                <a href="/patients/{patient.id}" class="block">
                    {patient.first_name} {patient.last_name}
                    </a>
                </li>
            {/each}
        </ul>
    </div>
{:else}
    <p class="text-gray-600">No patients found.</p>
{/if}