import { writable } from 'svelte/store';
import type { Patient } from '../types/models';
import type { Questionnaire } from '../types/models';
import type { Template } from '../types/models';

export const appData = writable({
  patients: [] as Patient[],
  questionnaires: [] as Questionnaire[],
  templates: [] as Template[],
});