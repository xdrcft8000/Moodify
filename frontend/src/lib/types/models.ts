export interface Team {
    id: number;
    created_at: string;
    name: string;
    whatsapp_number: string;
    whatsapp_number_id: number;
    // users: User[];
    // templates: Template[];
  }
  
export interface User {
    id: number;
    created_at: string;
    first_name: string;
    last_name: string;
    title: string | null;
    email: string;
    team_id: number;
    // team: Team;
    // patients: Patient[];
    // templates: Template[];
    // questionnaires: Questionnaire[];
  }
  
export interface Patient {
    id: number;
    created_at: string;
    first_name: string;
    last_name: string;
    assigned_to: number | null;
    phone_number: string | null;
    email: string | null;
    // assigned_to_user: User;
    // questionnaires: Questionnaire[];
    // chat_logs: ChatLogMessage[];
    // conversations: Conversation[];
  }
  
export interface Template {
    id: number;
    created_at: string;
    owner: number;
    duration: string;
    questions: QuestionnaireResult; // JSONB type, could be more specific based on your needs
    title: string;
    team_id: number;
    // owner_user: User;
    // team: Team;
    // questionnaires: Questionnaire[];
  }
  
export interface Questionnaire {
    id: number;
    created_at: string;
    patient_id: number;
    template_id: number;
    user_id: number;
    questions: QuestionnaireResult;
    current_status: string;
    // patient: Patient;
    // template: Template;
    // user: User;
    // conversations: Conversation[];
  }
  
export interface ChatLogMessage {
    id: number;
    created_at: string;
    role: string;
    patient_id: number;
    message_text: string;
    conversation_id: number;
    // patient: Patient;
    // conversation: Conversation;
  }
  
export interface Conversation {
    id: number;
    created_at: string;
    ended_at: string | null;
    questionnaire_id: number;
    status: string;
    patient_id: number;
    // questionnaire: Questionnaire;
    // chat_logs: ChatLogMessage[];
    // patient: Patient;
  }



  export interface AnswerScheme {
    type: string;
    range: {
      start: number;
      end: number;
    };
    explanation: string;
    interpretations: {
      [key: string]: string;
    };
  }
  
  export interface Question {
    text: string;
    index: number;
    response_format: string;
    answer?: string;
  }
  
  export interface QuestionnaireResult {
    answer_schemes: {
      [key: string]: AnswerScheme;
    };
    questions_list: Question[];
    comments?: string[];
    status: string; // Added status field, marked as optional
  }