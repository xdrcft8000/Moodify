import type { QuestionnaireResult, Question } from "$lib/types/models";

function calculateGAD7Score(data: QuestionnaireResult): number {
    // Check if the status is completed (you may need to adjust this based on your actual data structure)
    const answers = data.questions_list.map((question: Question) => parseInt(question.answer!));
  
    // Ensure we have 7 answers
    if (answers.length !== 7) {
      throw new Error("GAD-7 requires 7 answers");
    }
  
    // Sum up the scores
    const totalScore = answers.reduce((sum: number, score: number) => sum + score, 0);
    // return totalScore;
    return totalScore;
  }
  
  // ... rest of the file remains unchanged ...

function interpretGAD7Score(score: number): string {
    if (score >= 0 && score <= 4) return "Minimal anxiety";
    if (score >= 5 && score <= 9) return "Mild anxiety";
    if (score >= 10 && score <= 14) return "Moderate anxiety";
    if (score >= 15 && score <= 21) return "Severe anxiety";
    return "Invalid score";
}


export function formatDate(date: string | Date): string {
    const dateObj = new Date(date);
    const day = dateObj.getDate().toString().padStart(2, '0');
    const month = (dateObj.getMonth() + 1).toString().padStart(2, '0');
    const year = dateObj.getFullYear();
    return `${day}/${month}/${year}`;
}

export function formatTimeAgo(date: string | Date): string {
    const now = new Date();
    const givenDate = new Date(date);
    const diffInSeconds = Math.floor((now.getTime() - givenDate.getTime()) / 1000);

    if (diffInSeconds < 60) {
        return `${diffInSeconds}s ago`;
    }

    const diffInMinutes = Math.floor(diffInSeconds / 60);
    if (diffInMinutes < 60) {
        return `${diffInMinutes}m ago`;
    }

    const diffInHours = Math.floor(diffInMinutes / 60);
    if (diffInHours < 24) {
        return `${diffInHours}h ago`;
    }

    const diffInDays = Math.floor(diffInHours / 24);
    if (diffInDays < 7) {
        return `${diffInDays}d ago`;
    }

    const diffInWeeks = Math.floor(diffInDays / 7);
    if (diffInWeeks < 4) {
        return `${diffInWeeks}w ago`;
    }

    const diffInMonths = Math.floor(diffInDays / 30);
    if (diffInMonths < 12) {
        return `${diffInMonths}mo ago`;
    }

    const diffInYears = Math.floor(diffInDays / 365);
    return `${diffInYears}y ago`;

}

export { calculateGAD7Score, interpretGAD7Score };
