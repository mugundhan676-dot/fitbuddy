from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .config import settings
from .database import (
    get_all_users, get_db, get_original_plan, get_user,
    save_plan, save_user, update_plan
)
from .gemini_flash_generator import generate_nutrition_tip_with_flash
from .gemini_generator import generate_workout_gemini
from .schemas import FeedbackRequest, HealthResponse, UserInput
from .services import plan_to_text
from .updated_plan import update_workout_plan

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


def _admin_authorized(request: Request) -> bool:
    if not settings.admin_token:
        return True
    supplied = request.headers.get("X-Admin-Token") or request.query_params.get("token")
    return supplied == settings.admin_token


def _render_error(request: Request, message: str, code: int = 400):
    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context={"error": message, "status_code": code},
        status_code=code,
    )


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"title": settings.app_name},
    )


@router.post("/generate-workout", response_class=HTMLResponse)
def generate_workout_page(
    request: Request,
    name: Annotated[str, Form()],
    user_id: Annotated[str, Form()],
    age: Annotated[int, Form()],
    weight: Annotated[float, Form()],
    goal: Annotated[str, Form()],
    intensity: Annotated[str, Form()],
    db: Session = Depends(get_db),
):
    try:
        user = UserInput(
            name=name, user_id=user_id, age=age, weight=weight,
            goal=goal, intensity=intensity
        )
        plan = generate_workout_gemini(user)
        tip = generate_nutrition_tip_with_flash(user.goal)

        db_user = save_user(
            db, user_id=user.user_id, name=user.name, age=user.age,
            weight=user.weight, goal=user.goal, intensity=user.intensity
        )
        save_plan(db, db_user, plan_to_text(plan), tip.tip)

        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={
                "user": user,
                "workout_plan": plan,
                "nutrition_tip": tip.tip,
                "updated": False,
                "feedback": None,
            },
        )
    except Exception as exc:
        return _render_error(request, str(exc), 500)


@router.post("/submit-feedback", response_class=HTMLResponse)
def submit_feedback_page(
    request: Request,
    user_id: Annotated[str, Form()],
    feedback: Annotated[str, Form()],
    db: Session = Depends(get_db),
):
    try:
        request_data = FeedbackRequest(user_id=user_id, feedback=feedback)
        original = get_original_plan(db, request_data.user_id)
        db_user = get_user(db, request_data.user_id)

        if not original or not db_user:
            return _render_error(request, "No saved workout plan was found for that User ID.", 404)

        user = UserInput(
            name=db_user.name, user_id=db_user.user_id, age=db_user.age,
            weight=db_user.weight, goal=db_user.goal, intensity=db_user.intensity
        )
        updated = update_workout_plan(original, request_data.feedback, user)
        db_plan = update_plan(db, db_user, plan_to_text(updated), request_data.feedback)

        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={
                "user": user,
                "workout_plan": updated,
                "nutrition_tip": db_plan.nutrition_tip,
                "updated": True,
                "feedback": request_data.feedback,
            },
        )
    except Exception as exc:
        return _render_error(request, str(exc), 500)


@router.get("/view-all-users", response_class=HTMLResponse)
def view_all_users(request: Request, db: Session = Depends(get_db)):
    if not _admin_authorized(request):
        return _render_error(request, "Admin authorization required.", 401)

    users = []
    for user in get_all_users(db):
        plan = user.plans[0] if user.plans else None
        users.append({
            "user_id": user.user_id,
            "name": user.name,
            "age": user.age,
            "weight": user.weight,
            "goal": user.goal,
            "intensity": user.intensity,
            "original_plan": plan.original_plan if plan else None,
            "updated_plan": plan.updated_plan if plan else None,
            "feedback": plan.feedback if plan else None,
        })

    return templates.TemplateResponse(
        request=request,
        name="all_users.html",
        context={"users": users},
    )


@router.get("/api/health", response_model=HealthResponse)
def health():
    return {
        "status": "ok",
        "ai_enabled": bool(settings.gemini_api_key) and not settings.mock_ai
    }


@router.post("/api/generate-workout")
def api_generate_workout(payload: UserInput, db: Session = Depends(get_db)):
    try:
        plan = generate_workout_gemini(payload)
        tip = generate_nutrition_tip_with_flash(payload.goal)
        db_user = save_user(
            db, user_id=payload.user_id, name=payload.name, age=payload.age,
            weight=payload.weight, goal=payload.goal, intensity=payload.intensity
        )
        save_plan(db, db_user, plan_to_text(plan), tip.tip)
        return {
            "message": "Workout plan generated and saved successfully.",
            "user": payload.model_dump(),
            "workout_plan": plan.model_dump(),
            "nutrition_tip": tip.tip,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/api/nutrition-tip")
def api_nutrition_tip(goal: str):
    try:
        tip = generate_nutrition_tip_with_flash(goal)
        return {"goal": goal, "nutrition_tip": tip.tip}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/api/update-plan/{user_id}")
def api_update_plan(user_id: str, payload: FeedbackRequest, db: Session = Depends(get_db)):
    if payload.user_id != user_id:
        raise HTTPException(
            status_code=400,
            detail="Path user_id and payload user_id must match."
        )

    original = get_original_plan(db, user_id)
    db_user = get_user(db, user_id)
    if not original or not db_user:
        raise HTTPException(status_code=404, detail="Original workout plan not found.")

    try:
        user = UserInput(
            name=db_user.name, user_id=db_user.user_id, age=db_user.age,
            weight=db_user.weight, goal=db_user.goal, intensity=db_user.intensity
        )
        updated = update_workout_plan(original, payload.feedback, user)
        update_plan(db, db_user, plan_to_text(updated), payload.feedback)
        return {
            "message": "Workout plan updated successfully.",
            "user_id": user_id,
            "feedback": payload.feedback,
            "updated_plan": updated.model_dump(),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
