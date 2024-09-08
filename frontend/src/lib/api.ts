// Import any necessary dependencies, e.g., fetch or axios

interface InitQuestionnaireParams {
    patient_id: number;
    template_id: number;
    user_id: number;
}

export async function initQuestionnaire(params: InitQuestionnaireParams) {
    const response = await fetch('/api/init_questionnaire', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(params),
    });

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
}

