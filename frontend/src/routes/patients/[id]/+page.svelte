<script lang="ts">
    import { page } from '$app/stores';
	import { calculateGAD7Score } from '$lib/utils/helperFunctions';
    import Chart from 'chart.js/auto';
    import { afterUpdate } from 'svelte';
    export let data;
    import { initQuestionnaire } from '$lib/api';
    const { patients, questionnaires, templates } = data;


    $: patientId = $page.params.id;
    $: patient = patients.find(p => p.id === parseInt(patientId));
    $: selectedPatientId = parseInt(patientId);
    $: patient_questionnaires = questionnaires.filter(q => q.patient_id === patient?.id);
    console.log(patient_questionnaires);    
    $: completedQuestionnaires = patient_questionnaires.filter(q => q.current_status === 'Completed');
    $: gad7Scores = completedQuestionnaires.map(q => calculateGAD7Score(q.questions));
    $: dates = completedQuestionnaires.map(q => new Date(q.created_at).toLocaleDateString());
    let chartCanvas: HTMLCanvasElement;
    let chart: Chart | null = null;

    afterUpdate(() => {
        if (chartCanvas && gad7Scores.length > 0) {
            if (chart) {
                chart.data.labels = dates;
                chart.data.datasets[0].data = gad7Scores;
                chart.update();
            } else {
                chart = new Chart(chartCanvas, {
                    type: 'line',
                    data: {
                        labels: dates,
                        datasets: [{
                            label: 'GAD-7 Score',
                            data: gad7Scores,
                            borderColor: 'rgb(75, 192, 192)',
                            tension: 0.1
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                beginAtZero: true,
                                max: 21
                            }
                        }
                    }
                });
            }
        }
    });

    async function handleInitQuestionnaire() {
        try {
            const response = await initQuestionnaire({
                patient_id: patient!.id,
                template_id: 6,
                user_id: 3
            });
            console.log('Questionnaire initialized:', response);
            if (response.status === 'success') {
                alert('Questionnaire sent');
            } else {
                alert('Error sending questionnaire');
            }
        } catch (error) {
            console.error('Error initializing questionnaire:', error);
            alert('Error sending questionnaire');
        }
    }


</script>

<div class="flex items-center">
    <div class="flex-grow border-b-2 border-black"></div>
    <h1 class="text-3xl mx-8 font-hangang whitespace-nowrap">{patient?.first_name} {patient?.last_name}</h1>
    <div class="flex-grow border-b-2 border-black"></div>
</div>

<div class="flex">

    <!-- Left sidebar with patient list -->
    <div class="w-1/4 border-r border-gray-200 h-screen p-4">
        <a href="/patients" class="hover:underline mb-4 block">← {patients.length} Patients</a>
        <ul class="space-y-2 border-t py-4 border-black">
            {#each patients as listPatient (listPatient.id)}
                <li>
                    <a 
                        href="/patients/{listPatient.id}" 
                        class="block py-2 px-3 rounded {selectedPatientId === listPatient.id ? 'bg-gray-100' : 'hover:bg-gray-100'}"
                    >
                        {listPatient.first_name} {listPatient.last_name}
                    </a>
                </li>
            {/each}
        </ul>
    </div>

    <!-- Right side with patient details -->


    <div class="w-3/4 p-8">

            <div class="bg-white shadow-md rounded-lg p-6 mb-6">
        <h2 class="text-xl font-semibold mb-4">GAD-7 Scores Over Time</h2>
        {#if questionnaires.length > 0}
            <canvas bind:this={chartCanvas}></canvas>
        {:else}
            <p class="text-gray-600">No questionnaire data available to plot.</p>
        {/if}
    </div>

        {#if patient}
            
            <div class="bg-white shadow-md rounded-lg p-6 mb-6">
                <div class="flex justify-between items-center">
                    <h2 class="text-xl mb-4">Questionnaires</h2>
                    <button
                    class="bg-white hover:bg-violet hover:text-white text-black font-hangang py-2 px-4 rounded mb-4 border border-black"
                    on:click={handleInitQuestionnaire}
                >
                    Send new questionnaire
                </button>
                </div>
                {#if questionnaires.length > 0}
                    <ul class="space-y-2">
                        {#each patient_questionnaires as questionnaire (questionnaire.id)}
                            <li class="flex justify-between items-center py-2 px-3 hover:bg-gray-100 rounded">
                                <span>{questionnaire.created_at || 'Untitled Questionnaire'}</span>
                                <span class="text-sm text-gray-500">{questionnaire.current_status}</span>
                            </li>
                        {/each}
                    </ul>
                {:else}
                    <p class="text-gray-600">No questionnaires found for this patient.</p>
                {/if}
            </div>


            <div class="bg-white shadow-md rounded-lg p-6 mb-6">
                <h2 class="text-xl mb-4">Patient Details</h2>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <p class="text-gray-600">First Name</p>
                        <p class="font-medium">{patient.first_name}</p>
                    </div>
                    <div>
                        <p class="text-gray-600">Last Name</p>
                        <p class="font-medium">{patient.last_name}</p>
                    </div>
                    <!-- Add more patient details here -->
                </div>
            </div>

            <div class="bg-white shadow-md rounded-lg p-6">
                <h2 class="text-xl mb-4">Tracking</h2>
                <div class="space-y-2">
                    <div class="flex items-center justify-between">
                        <span>Sleep</span>
                        <input type="checkbox" class="form-checkbox h-5 w-5 text-blue-600">
                    </div>
                    <div class="flex items-center justify-between">
                        <span>Anxiety</span>
                        <input type="checkbox" class="form-checkbox h-5 w-5 text-blue-600" checked>
                    </div>
                    <!-- Add more tracking items here -->
                </div>
            </div>
        {:else}
            <p class="text-center text-gray-600 mt-8">Patient not found.</p>
        {/if}
    </div>
</div>