from __future__ import annotations

from .config import settings
from .gemini_client import generate_structured
from .schemas import UserInput, WorkoutPlan


def _mock_plan(user: UserInput) -> WorkoutPlan:
    intensity_note = {
        "low": "Keep the effort comfortable and prioritize technique.",
        "medium": "Use a moderate effort and stop before technique breaks down.",
        "high": "Use a challenging but controlled effort; reduce load if form deteriorates.",
    }[user.intensity]

    focuses = [
        "Full Body Strength", "Cardio & Core", "Upper Body",
        "Active Recovery & Mobility", "Lower Body",
        "Full Body Conditioning", "Rest & Recovery",
    ]

    days = []
    for index, focus in enumerate(focuses, start=1):
        exercises = [
            {
                "name": "Bodyweight squat",
                "sets": "3",
                "reps_or_duration": "8–12 reps",
                "rest": "60–90 sec",
            },
            {
                "name": "Incline push-up",
                "sets": "3",
                "reps_or_duration": "8–12 reps",
                "rest": "60–90 sec",
            },
            {
                "name": "Glute bridge",
                "sets": "3",
                "reps_or_duration": "10–15 reps",
                "rest": "60 sec",
            },
        ]
        if index == 7:
            exercises = [
                {
                    "name": "Easy walk",
                    "sets": "1",
                    "reps_or_duration": "20–30 minutes",
                    "rest": "As needed",
                },
                {
                    "name": "Gentle mobility",
                    "sets": "1",
                    "reps_or_duration": "10 minutes",
                    "rest": "As needed",
                },
            ]

        days.append({
            "day": f"Day {index}",
            "focus": focus,
            "warm_up": "5–10 minutes of easy movement and dynamic mobility.",
            "exercises": exercises,
            "cool_down": "5–10 minutes of easy walking and gentle stretching.",
            "recovery_tip": intensity_note,
        })

    return WorkoutPlan(
        title=f"{user.name}'s 7-Day FitBuddy Plan",
        overview=(
            f"Goal: {user.goal}. Intensity: {user.intensity}. "
            "This starter plan emphasizes consistency, controlled technique, and recovery."
        ),
        days=days,
        important_notes=[
            "Start conservatively and adjust exercise difficulty to your current ability.",
            "Stop an exercise if you experience sharp pain, dizziness, or unusual symptoms.",
            "Hydrate throughout the day and prioritize sleep and recovery.",
        ],
    )


def generate_workout_gemini(user: UserInput) -> WorkoutPlan:
    if settings.mock_ai:
        return _mock_plan(user)

    prompt = f"""
You are FitBuddy, a careful fitness-planning assistant.

Create a personalized 7-day workout plan for:
- Name: {user.name}
- Age: {user.age}
- Weight: {user.weight} kg
- Fitness goal: {user.goal}
- Preferred intensity: {user.intensity}

Requirements:
1. Return exactly 7 days.
2. Each day must contain a clear focus, 5–10 minute warm-up, exercises with
   exercise name, sets, reps or duration, and rest interval, plus cooldown/recovery guidance.
3. Adapt exercise volume and difficulty to the selected intensity.
4. Include sensible rest/recovery rather than training hard every day.
5. Keep the plan practical for a general web application and avoid requiring specialized equipment.
6. Do not diagnose conditions or prescribe treatment.
7. The user did not provide an experience level, so use accessible exercise options and
   mention simple ways to scale difficulty.
8. The goal is general fitness support, not medical care.
"""
    return generate_structured(
        model=settings.gemini_pro_model,
        prompt=prompt,
        response_schema=WorkoutPlan,
        temperature=0.7,
    )
