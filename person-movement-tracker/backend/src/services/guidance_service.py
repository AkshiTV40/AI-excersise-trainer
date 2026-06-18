import google.generativeai as genai
import os

class GuidanceService:
    def __init__(self):
        self.model_name = "gemini-2.0-flash"
        self.is_ready = False
        try:
            # Configure the API key from environment variable
            api_key = os.environ.get("GOOGLE_AI_API_KEY", "")
            if not api_key:
                print("Warning: GOOGLE_AI_API_KEY environment variable not set")
            else:
                genai.configure(api_key=api_key)
            self.client = genai.Client(api_key=api_key)
            self.is_ready = True
        except Exception as e:
            print(f"Failed to initialize GuidanceService: {e}")
            self.is_ready = False

    def generate_guidance(self, exercise_type: str, user_summary: dict, reference_summary: dict = None) -> str:
        if not self.is_ready:
            return "Guidance service is not available."

        # Construct the prompt
        prompt = f"""
        You are an expert fitness trainer providing feedback on exercise form.
        Exercise type: {exercise_type}
        
        User's performance:
        - Overall form score: {user_summary.get('overall_form_score', 'N/A')}%
        - Summary: {user_summary.get('summary', 'N/A')}
        - Form issues: {user_summary.get('form_issues', [])}
        """
        
        if reference_summary:
            prompt += f"""
            Reference performance:
            - Overall form score: {reference_summary.get('overall_form_score', 'N/A')}%
            - Summary: {reference_summary.get('summary', 'N/A')}
            """
        
        prompt += """
        Based on the above information, provide specific, actionable feedback to improve the user's form.
        Focus on the most critical issues first. Provide clear recommendations and encouragement.
        Keep your response concise and helpful.
        """
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text
        except Exception as e:
            print(f"Error generating guidance: {e}")
            return "Unable to generate guidance at this time."

    def motion_to_words(self, keypoints, additional_context=None):
        return "Motion description not implemented for Google AI model."

    def classify_exercise_from_description(self, motion_description):
        from ..models.exercise_analyzer import ExerciseType
        return ExerciseType.SQUAT

    def remote_exercise_match(self, motion_description):
        return {"suggested_query": "", "analysis": ""}

    def get_token_guidance(self):
        return "google_ai"