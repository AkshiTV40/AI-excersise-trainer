import logging
import os
import re
import numpy as np
from typing import Optional, Dict, Any, List

try:
    from ..config import config
    from ..models.exercise_analyzer import ExerciseType
except ImportError:
    from config import config
    from models.exercise_analyzer import ExerciseType

logger = logging.getLogger(__name__)


class GuidanceService:
    """Generate natural-language exercise coaching using Qwen2.5-Omni on Hugging Face."""

    DEFAULT_MODEL_NAME = "Qwen/Qwen2.5-Omni-7B"
    GENERATION_PARAMS = {
        "max_tokens": 500,
        "temperature": 0.4,
        "top_p": 0.9,
    }

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME):
        self.model_name = model_name
        self._client = None
        self._hf_token = None
        self._is_ready = False
        self._vision_ready = False

        self._hf_token = config.hf_token or os.getenv("HUGGINGFACE_API_TOKEN") or os.getenv("HF_TOKEN")
        # Check if token is a placeholder value
        placeholder_tokens = [
            "your_huggingface_token_here",
            "hf_token",
            "your_token_here",
            "insert_token_here",
            "",
            None
        ]
        if not self._hf_token or self._hf_token in placeholder_tokens:
            logger.warning("No valid HuggingFace token found. Set HF_TOKEN or HUGGINGFACE_API_TOKEN to enable Qwen guidance.")
            return

        try:
            from huggingface_hub import InferenceClient
            self._client = InferenceClient(token=self._hf_token)
            self._is_ready = True
            logger.info("GuidanceService initialized Qwen2.5-Omni through Hugging Face Inference API")
        except Exception as e:
            logger.warning(f"Qwen guidance initialization failed: {e}")

    @property
    def is_ready(self) -> bool:
        return self._is_ready

    @staticmethod
    def _has_cuda() -> bool:
        try:
            import torch
            return torch.cuda.is_available()
        except Exception:
            return False

    def generate_guidance(self, exercise_type: str, user_summary: Dict[str, Any], reference_summary: Optional[Dict[str, Any]] = None) -> str:
        """Generate a detailed coaching report for the exercise session."""
        if self._is_ready and self._client:
            try:
                prompt = self._build_prompt(exercise_type, user_summary, reference_summary)
                return self._generate_with_qwen(prompt)
            except Exception as e:
                logger.warning(f"Qwen guidance generation failed: {e}")

        return self._fallback_guidance(exercise_type, user_summary, reference_summary)

    def _generate_with_qwen(self, prompt: str) -> str:
        if not self._client:
            raise RuntimeError("Hugging Face client is not initialized")

        # Try chat_completion first
        try:
            response = self._client.chat_completion(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a practical strength and mobility coach. "
                            "Use only the provided biomechanics, rep count, joint angles, form score, and issues. "
                            "Be specific, encouraging, and actionable. Avoid generic fitness advice."
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                **self.GENERATION_PARAMS
            )

            try:
                if hasattr(response, 'choices') and len(response.choices) > 0:
                    message = response.choices[0].message
                    if hasattr(message, 'content'):
                        content = message.content.strip()
                        if content:  # Check if not empty
                            return content
                    elif isinstance(message, dict) and 'content' in message:
                        content = message['content'].strip()
                        if content:  # Check if not empty
                            return content
                
                # Fallback if response format is unexpected or empty
                logger.warning(f"Unexpected or empty response format from Qwen chat_completion: {type(response)}")
            except Exception as e:
                logger.warning(f"Error processing Qwen chat_completion response: {e}")
        except Exception as e:
            logger.warning(f"Qwen chat_completion failed: {e}")
            # Fall back to text_generation

        # Try text_generation as fallback
        try:
            response = self._client.text_generation(
                prompt=prompt,
                model=self.model_name,
                **self.GENERATION_PARAMS
            )
            
            if isinstance(response, str):
                content = response.strip()
                if content:  # Check if not empty
                    return content
            elif isinstance(response, dict) and 'generated_text' in response:
                content = response['generated_text'].strip()
                if content:  # Check if not empty
                    return content
            else:
                content = str(response).strip()
                if content:  # Check if not empty
                    return content
        except Exception as e:
            logger.warning(f"Qwen text_generation failed: {e}")
            
        # If both approaches fail or return empty content, raise exception to trigger fallback
        raise RuntimeError("All Qwen inference methods failed or returned empty response")

    def _build_prompt(self, exercise_type: str, user_summary: Dict[str, Any], reference_summary: Optional[Dict[str, Any]]) -> str:
        user_score = user_summary.get("overall_form_score", "unknown")
        user_raw = user_summary.get("summary", {})
        reference_score = None
        reference_raw = None

        if reference_summary:
            reference_score = reference_summary.get("overall_form_score", "unknown")
            reference_raw = reference_summary.get("summary", {})

        prompt = [
            "Analyze this exercise session and return a detailed coaching report.",
            f"Exercise: {exercise_type}",
            f"User form score: {user_score}",
            "User analysis:",
            self._format_summary(user_raw),
        ]

        if reference_score is not None:
            prompt.extend([
                f"Reference form score: {reference_score}",
                "Reference analysis:",
                self._format_summary(reference_raw),
                "Compare the user's form to the reference and explain the score gap."
            ])

        prompt.extend([
            "Return the report in this exact structure:",
            "1. Overall Summary",
            "2. What Went Well",
            "3. Form Issues Detected",
            "4. Top 4 Improvements",
            "5. Next Set Cues",
            "6. Safety Notes"
        ])

        return "\n".join(prompt)

    @staticmethod
    def _format_summary(summary: Any) -> str:
        if isinstance(summary, dict):
            return "\n".join(f"- {key}: {value}" for key, value in summary.items())
        return str(summary)

    def _fallback_guidance(self, exercise_type: str, user_summary: Dict[str, Any], reference_summary: Optional[Dict[str, Any]] = None) -> str:
        score = self._safe_float(user_summary.get("overall_form_score", 0), 0.0)
        summary = user_summary.get("summary", {}) if isinstance(user_summary.get("summary", {}), dict) else {}
        reference = reference_summary.get("summary", {}) if reference_summary and isinstance(reference_summary.get("summary", {}), dict) else {}

        status = summary.get("status", "UNKNOWN")
        frames = summary.get("frames_with_people", 0)
        total_frames = summary.get("total_frames", 0)
        critical = summary.get("critical_issues", 0)
        warnings = summary.get("warnings", 0)
        recommendations = summary.get("recommendations", [])
        issues = user_summary.get("form_issues", [])

        if score >= 85:
            verdict = "excellent"
        elif score >= 70:
            verdict = "good"
        elif score >= 50:
            verdict = "needs improvement"
        else:
            verdict = "needs major correction"

        comparison = ""
        if reference_summary:
            ref_score = self._safe_float(reference_summary.get("overall_form_score", 0), 0.0)
            gap = score - ref_score
            comparison = (
                f" Compared with the reference, you are {abs(gap):.1f} points "
                f"{'above' if gap >= 0 else 'below'} the reference score."
            )

        issue_lines = self._format_issues(issues)
        if not issue_lines:
            issue_lines = [
                "No severe issues were recorded, but consistency should be reviewed across the full set."
            ]

        improvement_plan = self._build_improvement_plan(exercise_type, issues, score)

        return (
            f"Overall Summary: Your {exercise_type} form was {verdict} with an average score of "
            f"{score:.1f}% across {frames}/{total_frames} analyzed frames. The system marked this as {status}."
            f"{comparison}\n\n"
            "What Went Well: You completed the movement with measurable rep tracking and joint-angle data. "
            "Keep the same camera angle and controlled tempo for the next set.\n\n"
            "Form Issues Detected:\n"
            f"{self._bullet_list(issue_lines)}\n\n"
            "Top Improvements:\n"
            f"{self._bullet_list(improvement_plan)}\n\n"
            "Next Set Cues: Reset your stance before each rep, move through a controlled range, pause briefly at the hardest position, "
            "and stop the set if the joint angles become inconsistent or pain appears.\n\n"
            "Safety Notes: If critical issues repeat, reduce range, reduce load, or review a reference tutorial before continuing."
        )

    @staticmethod
    def _fallback_guidance_from_prompt(prompt: str) -> str:
        """Generate a basic fallback guidance when Qwen fails to process properly."""
        # Extract exercise type from prompt if possible
        exercise_type = "exercise"
        if "Exercise:" in prompt:
            try:
                exercise_type = prompt.split("Exercise:")[1].split("\n")[0].strip()
            except:
                pass
        
        return (
            f"Overall Summary: Your {exercise_type} session has been recorded and analyzed.\n\n"
            "What Went Well: You completed the exercise session and provided valuable data for analysis.\n\n"
            "Form Issues Detected: Specific form analysis requires the Qwen guidance service which is currently unavailable.\n\n"
            "Top Improvements: Please ensure proper form and consider consulting with a fitness professional for personalized guidance.\n\n"
            "Next Set Cues: Focus on controlled movements, proper breathing, and maintaining good posture throughout each repetition.\n\n"
            "Safety Notes: If you experience pain or discomfort, stop the exercise and consult with a healthcare provider."
        )

    @staticmethod
    def _safe_float(value: Any, default: float) -> float:
        try:
            return float(value)
        except Exception:
            return default

    @staticmethod
    def _format_issues(issues: List[Dict[str, Any]]) -> List[str]:
        lines = []
        for issue in issues:
            severity = issue.get("severity", "info")
            message = issue.get("message", "Form issue detected")
            suggestion = issue.get("suggestion", "")
            line = f"{severity}: {message}"
            if suggestion:
                line += f" - {suggestion}"
            lines.append(line)
        return lines

    @staticmethod
    def _build_improvement_plan(exercise_type: str, issues: List[Dict[str, Any]], score: float) -> List[str]:
        exercise = exercise_type.lower()
        messages = [issue.get("message", "").lower() for issue in issues]
        suggestions = [issue.get("suggestion", "") for issue in issues]

        plan = []
        if exercise == "squat":
            plan.extend([
                "Keep your chest proud and brace your core before every rep.",
                "Track your knees in the same direction as your toes while you sit back and down.",
                "Use a depth you can control without the knees collapsing or the heels lifting.",
                "Pause for one second at the bottom, then drive through the whole foot."
            ])
        elif exercise == "pushup":
            plan.extend([
                "Keep your body in a straight line from head to heels.",
                "Lower until the elbows reach a controlled angle, then press evenly through both hands.",
                "Keep the neck neutral and avoid shrugging the shoulders.",
                "Move slower on the way down than on the way up."
            ])
        elif exercise == "lunge":
            plan.extend([
                "Step far enough that both knees can bend close to 90 degrees.",
                "Keep the front heel down and the torso tall.",
                "Push through the front foot to return to the start.",
                "Keep hips square and avoid twisting toward one side."
            ])
        elif exercise == "plank":
            plan.extend([
                "Keep shoulders stacked over elbows and hips level.",
                "Brace the abs as if preparing for a light tap to the stomach.",
                "Avoid sagging hips or lifting the hips too high.",
                "Use shorter, cleaner holds instead of long holds with poor alignment."
            ])
        elif exercise == "deadlift":
            plan.extend([
                "Start with the load close to your body.",
                "Hinge from the hips while keeping the spine neutral.",
                "Drive through the floor and stand tall without leaning back at the top.",
                "Use lighter weight until the hip hinge pattern is consistent."
            ])
        else:
            plan.extend([
                "Move through a controlled range of motion.",
                "Keep joints aligned and avoid sudden jerky movement.",
                "Reset your posture between reps.",
                "Stop if pain appears or form breaks down."
            ])

        if suggestions:
            plan.insert(0, suggestions[0])

        if score >= 85:
            plan.append("Maintain the current technique and focus on consistent tempo across every rep.")
        elif score < 50:
            plan.insert(0, "Reduce range or resistance first, then rebuild the movement pattern with clean reps.")

        return plan[:4]

    @staticmethod
    def _bullet_list(items: List[str]) -> str:
        return "\n".join(f"- {item}" for item in items)

    @staticmethod
    def get_token_guidance() -> Dict[str, str]:
        """Return expected token types for online Qwen/LLM access."""
        return {
            "huggingface": "Set HF_TOKEN or HUGGINGFACE_API_TOKEN to a Hugging Face read-access token.",
            "model": "Qwen/Qwen2.5-Omni-7B",
            "parameters": "max_tokens=500, temperature=0.4, top_p=0.9, chat_completion/text_generation."
        }

    def motion_to_words(self, keypoints: Dict[str, tuple], additional_context: Optional[str] = None) -> str:
        """Convert pose keypoints to a short movement description."""
        if not keypoints or len(keypoints) < 5:
            return "No valid pose detected to describe movement."

        specifics = []

        if "left_knee" in keypoints and "left_hip" in keypoints and "left_ankle" in keypoints:
            knee_y = keypoints["left_knee"][1]
            hip_y = keypoints["left_hip"][1]
            ankle_y = keypoints["left_ankle"][1]

            if knee_y < hip_y and hip_y < ankle_y:
                specifics.append("partial squat position")
            elif knee_y > hip_y and hip_y > ankle_y:
                specifics.append("standing upright")

        if "left_shoulder" in keypoints and "left_hip" in keypoints:
            shoulder_y = keypoints["left_shoulder"][1]
            hip_y = keypoints["left_hip"][1]
            if shoulder_y > hip_y + 0.08:
                specifics.append("upper-body lean forward")
            elif shoulder_y < hip_y - 0.08:
                specifics.append("upper-body lean backward")

        text = "The user appears to be " + ", ".join(specifics) if specifics else "The user appears to be in a neutral stance"

        if additional_context:
            text += f"; context: {additional_context}"

        return text

    def classify_exercise_from_description(self, motion_description: str) -> Optional[ExerciseType]:
        """Map motion text to a likely exercise type."""
        if not motion_description:
            return None

        motion_lower = motion_description.lower()

        mapping = {
            "squat": ["squat", "knee", "hip", "lowering"],
            "pushup": ["pushup", "push-up", "hands", "elbow", "floor"],
            "lunge": ["lunge", "forward leg", "back leg"],
            "plank": ["plank", "straight line", "core"],
            "deadlift": ["deadlift", "hinge", "hip hinge"],
            "jumping_jack": ["jumping jack", "jumping", "arms over head"]
        }

        for exercise_key, keywords in mapping.items():
            for keyword in keywords:
                if keyword in motion_lower:
                    try:
                        return ExerciseType(exercise_key)
                    except ValueError:
                        continue

        return None

    def analyze_movement_from_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        """Use Qwen2.5-Omni vision to analyze movement from a video frame."""
        result = {
            "movement_description": None,
            "matched_exercise": None,
            "analysis": None,
            "confidence": 0.0,
            "suggested_query": None
        }
 
        if not self._is_ready or not self._client:
            result["movement_description"] = "Vision model not initialized"
            return result
 
        try:
            import torch
            from PIL import Image
 
            pil_image = Image.fromarray(frame)
 
            prompt = """Analyze this image showing a person exercising. Describe:
1. What exercise they appear to be doing
2. Their body position and form
3. Key movement or motion pattern visible
 
Provide a clear 2-3 sentence description of the movement."""
 
            # Use the Inference API for vision tasks
            # For Qwen2.5-Omni, we can use image-to-text or visual question answering
            try:
                # Try using image_to_text first
                generated_text = self._client.image_to_text(pil_image, prompt=prompt)
                if isinstance(generated_text, str):
                    movement_desc = generated_text.strip()
                elif isinstance(generated_text, list) and len(generated_text) > 0:
                    movement_desc = generated_text[0].get('generated_text', str(generated_text[0])).strip()
                else:
                    movement_desc = str(generated_text).strip()
            except Exception as e1:
                logger.warning(f"image_to_text failed: {e1}")
                # Fallback to visual question answering
                try:
                    # Ask specific questions about the exercise
                    qa_result = self._client.visual_question_answering(
                        image=pil_image,
                        question="What exercise is the person doing and what is their form like?"
                    )
                    if isinstance(qa_result, dict) and 'answer' in qa_result:
                        movement_desc = qa_result['answer'].strip()
                    elif isinstance(qa_result, str):
                        movement_desc = qa_result.strip()
                    else:
                        movement_desc = str(qa_result).strip()
                except Exception as e2:
                    logger.warning(f"visual_question_answering failed: {e2}")
                    # Final fallback - describe what we can see without the model
                    movement_desc = "Person visible in frame, exercise analysis requires Qwen vision model"
 
            result["movement_description"] = movement_desc
            matched = self.classify_exercise_from_description(movement_desc)
            result["matched_exercise"] = matched.value if matched else "unknown"
            result["analysis"] = self._analyze_movement_quality(movement_desc)
            result["suggested_query"] = self.suggest_exercise_search_query(movement_desc)
            result["confidence"] = 0.85
 
        except Exception as e:
            logger.warning(f"Vision-based movement analysis failed: {e}")
            result["movement_description"] = f"Analysis failed: {str(e)}"
 
        return result

    def _analyze_movement_quality(self, movement_description: str) -> str:
        """Analyze movement quality based on description."""
        if self._is_ready and self._client:
            try:
                prompt = (
                    "Analyze this exercise movement and rate form quality. "
                    f"Movement: {movement_description}\n\n"
                    "Provide a one-sentence form quality assessment focusing on proper technique."
                )
                # Try chat_completion first
                try:
                    response = self._client.chat_completion(
                        model=self.model_name,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=80,
                        temperature=0.2,
                        top_p=0.9
                    )
                    
                    try:
                        if hasattr(response, 'choices') and len(response.choices) > 0:
                            message = response.choices[0].message
                            if hasattr(message, 'content'):
                                content = message.content.strip()
                                if content:  # Check if not empty
                                    return content
                            elif isinstance(message, dict) and 'content' in message:
                                content = message['content'].strip()
                                if content:  # Check if not empty
                                    return content
                    except Exception as e:
                        logger.warning(f"Error processing Qwen chat_completion response for quality analysis: {e}")
                except Exception as e:
                    logger.warning(f"Qwen chat_completion failed for quality analysis: {e}")
                    # Fall back to text_generation
                    try:
                        response = self._client.text_generation(
                            prompt=prompt,
                            model=self.model_name,
                            max_tokens=80,
                            temperature=0.2,
                            top_p=0.9
                        )
                        
                        if isinstance(response, str):
                            content = response.strip()
                            if content:  # Check if not empty
                                return content
                        elif isinstance(response, dict) and 'generated_text' in response:
                            content = response['generated_text'].strip()
                            if content:  # Check if not empty
                                return content
                        else:
                            content = str(response).strip()
                            if content:  # Check if not empty
                                return content
                    except Exception as e:
                        logger.warning(f"Qwen text_generation failed for quality analysis: {e}")
                        
            except Exception as e:
                logger.warning(f"Quality analysis failed: {e}")

        return self._fallback_quality_analysis(movement_description)

    def _fallback_quality_analysis(self, movement_description: str) -> str:
        """Fallback heuristic-based quality analysis."""
        movement_lower = movement_description.lower()

        if any(word in movement_lower for word in ["good", "proper", "correct", "great"]):
            return "Good form - maintain current technique"
        elif any(word in movement_lower for word in ["poor", "wrong", "incorrect", "knees", "back"]):
            return "Form issues detected - focus on controlled movement"
        else:
            return "Controlled tempo recommended throughout the movement"

    def suggest_exercise_search_query(self, motion_description: str) -> str:
        """Build a search query the model can use to look up similar exercises."""
        if not motion_description:
            return "exercise form guidance"

        text = re.sub(r"[^a-zA-Z0-9 ,]", "", motion_description)
        return f"find best exercise for movement: {text}"

    def remote_exercise_match(self, motion_description: str) -> Dict[str, Any]:
        """Use Qwen text generation to match the exercise and analyze movement."""
        exercise_result = {
            "motion_description": motion_description,
            "matched_exercise": None,
            "suggested_query": self.suggest_exercise_search_query(motion_description),
            "analysis": None,
            "note": "This method uses Qwen2.5-Omni through Hugging Face Inference API."
        }

        if self._is_ready and self._client:
            try:
                prompt = (
                    "Identify the most likely exercise and provide a one-sentence analysis for this motion. "
                    f"Movement description: {motion_description}\n"
                )
                # Try chat_completion first
                try:
                    response = self._client.chat_completion(
                        model=self.model_name,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=120,
                        temperature=0.2,
                        top_p=0.9
                    )
                    
                    try:
                        if hasattr(response, 'choices') and len(response.choices) > 0:
                            message = response.choices[0].message
                            if hasattr(message, 'content'):
                                out_text = message.content.strip()
                                if out_text:  # Check if not empty
                                    exercise_result["analysis"] = out_text
                            elif isinstance(message, dict) and 'content' in message:
                                out_text = message['content'].strip()
                                if out_text:  # Check if not empty
                                    exercise_result["analysis"] = out_text
                    except Exception as e:
                        logger.warning(f"Error processing Qwen chat_completion response for remote exercise match: {e}")
                except Exception as e:
                    logger.warning(f"Qwen chat_completion failed for remote exercise match: {e}")
                    # Fall back to text_generation
                    try:
                        response = self._client.text_generation(
                            prompt=prompt,
                            model=self.model_name,
                            max_tokens=120,
                            temperature=0.2,
                            top_p=0.9
                        )
                        
                        if isinstance(response, str):
                            out_text = response.strip()
                            if out_text:  # Check if not empty
                                exercise_result["analysis"] = out_text
                        elif isinstance(response, dict) and 'generated_text' in response:
                            out_text = response['generated_text'].strip()
                            if out_text:  # Check if not empty
                                exercise_result["analysis"] = out_text
                        else:
                            out_text = str(response).strip()
                            if out_text:  # Check if not empty
                                exercise_result["analysis"] = out_text
                    except Exception as e:
                        logger.warning(f"Qwen text_generation failed for remote exercise match: {e}")
                        
            except Exception as e:
                logger.warning(f"Qwen remote exercise matching failed: {e}")

        if not exercise_result["matched_exercise"]:
            inferred = self.classify_exercise_from_description(motion_description)
            exercise_result["matched_exercise"] = inferred.value if inferred else "unknown"

        return exercise_result
