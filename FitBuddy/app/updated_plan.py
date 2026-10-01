from __future__ import annotations

from .config import settings
from .gemini_client import generate_structured
from .gemini_generator import generate_workout_gemini
from .schemas import UserInput, WorkoutPlan


def update_workout_plan(original_plan: str, user_feedback: str, user: UserInput) -> WorkoutPlan:
    if settings.mock_ai:
        base = generate_workout_gemini(user)
        base.overview += f" Feedback incorporated: {user_feedback}"
        return base

    prompt = f"""
You are FitBuddy's workout-plan revision assistant.

User profile:
- Name: {user.name}
- Age: {user.age}
- Weight: {user.weight} kg
- Goal: {user.goal}
- Intensity: {user.intensity}

Original 7-day plan:
{original_plan}

User feedback:
{user_feedback}

Revise the plan based on the feedback. Preserve useful parts of the original plan,
but make the requested changes clearly. Return exactly 7 days and keep the same
structured format: focus, warm-up, exercises with sets/reps/duration/rest,
cool-down, and recovery tip. Include sensible rest and avoid medical claims.
"""
    return generate_structured(
        model=settings.gemini_pro_model,
        prompt=prompt,
        response_schema=WorkoutPlan,
        temperature=0.65,
    )
