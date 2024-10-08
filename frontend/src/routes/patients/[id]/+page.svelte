<script lang="ts">
    import { page } from '$app/stores';
	import { calculateGAD7Score, formatTimeAgo } from '$lib/utils/helperFunctions';
    import Chart from 'chart.js/auto';
    import { afterUpdate } from 'svelte';
    export let data;
    import { initQuestionnaire } from '$lib/api';
    const { patients, questionnaires, templates } = data;
    import { formatDate } from '$lib/utils/helperFunctions'; // Assume this function exists
	import { theme } from '$lib/stores/theme.js';
	import { themeColors } from '$lib/styles/theme.js';



    $: patientId = $page.params.id;
    $: patient = patients.find(p => p.id === parseInt(patientId));
    $: selectedPatientId = parseInt(patientId);
    $: patient_questionnaires = questionnaires.filter(q => q.patient_id === patient?.id);
    $: completedQuestionnaires = patient_questionnaires
        .filter(q => q.current_status === 'Completed')
        .map(q => ({
            date: new Date(q.created_at),
            score: calculateGAD7Score(q.questions),
            comments: q.questions.comments ? q.questions.comments : []
        }))
        .sort((a, b) => a.date.getTime() - b.date.getTime())
        .map(q => ({
            ...q,
            date: formatDate(q.date)
        }));    
    let chartCanvas: HTMLCanvasElement;
    let chart: Chart | null = null;

    afterUpdate(() => {
    if (chartCanvas && completedQuestionnaires.length > 0) {
        if (chart) {
            chart.data.labels = completedQuestionnaires.map(q => q.date);
            chart.data.datasets[0].data = completedQuestionnaires.map(q => q.score);
            chart.update();
        } else {
            chart = new Chart(chartCanvas, {
                type: 'line',
                data: {
                    labels: completedQuestionnaires.map(q => q.date),
                    datasets: [{
                        label: 'GAD-7 Anxiety Score',
                        data: completedQuestionnaires.map(q => q.score),
                        borderColor: themeColors.light.violet,
                        backgroundColor: 'rgba(139, 92, 246, 0.1)',
                        tension: 0.4,
                        pointRadius: 6,
                        pointHoverRadius: 8,
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        x: {
                            grid: { display: false }
                        },
                        y: {
                            beginAtZero: true,
                            max: 21,
                            grid: { display: false }
                        }
                    },
                    plugins: {
                        legend: {
                            labels: {
                                usePointStyle: true,
                                pointStyle: 'circle'
                            }
                        },
                        tooltip: {
                            backgroundColor: 'white', // Customize this color as needed
                            titleColor: 'black',
                            bodyColor: 'black',
                            borderColor: 'black',
                            borderWidth: 1,
                            padding: 10,
                            bodyFont:{
                                size: 16,
                            },
                            usePointStyle: true,
                            callbacks: {
                                labelPointStyle: (context) => {
                                    return {
                                        pointStyle: false,
                                        rotation: 0,
                                    };
                                },
                                label: (context) => {
                                    const score = context.raw as number;
                                    return `Score: ${score}`;
                                },
                                afterLabel: (context) => {
                                    const dataIndex = context.dataIndex;
                                    const comments = completedQuestionnaires[dataIndex].comments;
                                    if (comments.length === 0) return [];

                                    const chunkComment = (comment: string, chunkSize: number = 5) => {
                                        const words = comment.split(' ');
                                        const chunks = [];
                                        for (let i = 0; i < words.length; i += chunkSize) {
                                            chunks.push(words.slice(i, i + chunkSize).join(' '));
                                        }
                                        return chunks;
                                    };

                                        const chunkedComments = comments.flatMap(comment => 
                                            chunkComment(`"${comment}"`).map(chunk => `  ${chunk}`)
                                        );

                                            return ['Comments:'].concat(chunkedComments);
                                    }
                                    },       
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
    <div class="w-1/4  h-screen p-4">
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
        <h2 class="text-xl mb-4">Anxiety Over Time</h2>
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
                                <span>{formatTimeAgo(questionnaire.created_at) || 'Untitled Questionnaire'}</span>
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