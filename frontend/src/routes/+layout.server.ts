import { error } from "@sveltejs/kit";
import type { LayoutServerLoad } from "./$types";
import type { Patient, Questionnaire, Template } from "$lib/types/models";
export const load: LayoutServerLoad = async ({ fetch }) => {
    try {
        const [patientsRes, questionnairesRes, templatesRes] = await Promise.all([
            fetch('/api/get_patients'),
            fetch('/api/get_questionnaires'),
            fetch('/api/get_templates')
        ]);

        if (!patientsRes.ok || !questionnairesRes.ok || !templatesRes.ok) {
            throw new Error(`${patientsRes.status} ${patientsRes.statusText} ${questionnairesRes.status} ${questionnairesRes.statusText} ${templatesRes.status} ${templatesRes.statusText} `);
        }

        const [patientsList, questionnairesList, templatesList] = await Promise.all([
            patientsRes.json(),
            questionnairesRes.json(),
            templatesRes.json()
        ]);
        
        const patients: Patient[] = patientsList;
        const questionnaires: Questionnaire[] = questionnairesList;
        const templates: Template[] = templatesList;
        return { patients, questionnaires, templates };
    } catch (err) {
        console.error('Error loading data:', err);
        throw error(500, 'Error loading data');
    }
};  
