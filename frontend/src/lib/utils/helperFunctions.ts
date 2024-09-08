import type { QuestionnaireResult, Question } from "$lib/types/models";

function calculateGAD7Score(data: QuestionnaireResult): number {
    // Check if the status is completed (you may need to adjust this based on your actual data structure)
    console.log("WE ARE HERE");
  
    // Extract answers from the questions_list
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

export { calculateGAD7Score, interpretGAD7Score };
