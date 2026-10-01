from __future__ import annotations

from .config import settings
from .gemini_client import generate_structured
from .schemas import NutritionTip


def _mock_tip(goal: str) -> NutritionTip:
    goal_lower = goal.lower()
    if "muscle" in goal_lower:
        text = (
            "Include a protein-rich food in each main meal, stay hydrated, and pair "
            "training with adequate sleep and overall balanced meals."
        )
    elif "loss" in goal_lower or "fat" in goal_lower:
        text = (
            "Build meals around vegetables, a protein source, whole-food carbohydrates, "
            "and healthy fats. Choose portions that support your overall energy needs."
        )
    else:
        text = (
            "Keep meals balanced, drink water regularly, include protein and fiber, "
            "and prioritize consistent sleep and recovery."
        )
    return NutritionTip(tip=text)


def generate_nutrition_tip_with_flash(goal: str) -> NutritionTip:
    if settings.mock_ai:
        return _mock_tip(goal)

    prompt = f"""
You are FitBuddy's nutrition and recovery tip assistant.

The user's fitness goal is: {goal}

Give one concise, practical nutrition or recovery tip that complements a general
fitness plan. Keep it safe, non-diagnostic, and easy to understand. Do not provide
extreme dieting advice, unsafe calorie restriction, or medical treatment.
"""
    return generate_structured(
        model=settings.gemini_flash_model,
        prompt=prompt,
        response_schema=NutritionTip,
        temperature=0.4,
    )
