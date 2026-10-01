# FitBuddy – AI Fitness Plan Generator

FitBuddy is a FastAPI + Jinja2 + SQLite application based on the supplied project documentation. It generates a personalized 7-day workout plan, provides a nutrition/recovery tip, and lets users revise their saved plan through feedback.

## Included

- FastAPI backend and automatic `/docs`
- Jinja2 HTML frontend
- SQLite + SQLAlchemy persistence
- Gemini integration using the current `google-genai` SDK
- Pydantic structured output validation
- 7-day workout generation
- Nutrition/recovery tip generation
- Feedback-based plan updates
- Admin/coach dashboard
- REST API
- `MOCK_AI=true` mode for testing without an API key
- Pytest tests

## Windows / VS Code

Open this folder in VS Code and run:

```powershell
python -m venv venv
.env\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env`:

```env
GEMINI_API_KEY=your_real_gemini_api_key
GEMINI_PRO_MODEL=gemini-2.5-pro
GEMINI_FLASH_MODEL=gemini-2.5-flash
MOCK_AI=false
```

For a first test without Gemini, use:

```env
MOCK_AI=true
```

Start the server:

```powershell
uvicorn app.main:app --reload
```

Open:

- http://127.0.0.1:8000
- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/view-all-users

Run tests:

```powershell
pytest -q
```

## Main workflow

1. Enter name, User ID, age, weight, goal and intensity.
2. Click Generate My Plan.
3. FitBuddy creates seven days of workouts plus a nutrition/recovery tip.
4. The data and original plan are stored in `fitbuddy.db`.
5. Submit feedback such as “Add more cardio” or “Include more rest days”.
6. Gemini revises the plan and the updated version is saved separately.
7. The admin/coach dashboard shows original and updated plans.

## API

### Generate
`POST /api/generate-workout`

```json
{
  "name": "Alex",
  "user_id": "alex001",
  "age": 25,
  "weight": 70,
  "goal": "muscle gain",
  "intensity": "medium"
}
```

### Nutrition
`POST /api/nutrition-tip?goal=muscle%20gain`

### Update
`POST /api/update-plan/alex001`

```json
{
  "user_id": "alex001",
  "feedback": "Add more cardio and include more rest."
}
```

### Health
`GET /api/health`

## Optional admin token

For local/demo use, `ADMIN_TOKEN=` leaves the dashboard open.

For basic token protection:

```env
ADMIN_TOKEN=my-secret-token
```

Then use:

`http://127.0.0.1:8000/view-all-users?token=my-secret-token`

For production, replace this with proper authentication/authorization.

## Implementation note

The supplied document describes Gemini 1.5 Pro and Gemini Flash. This implementation preserves that architecture and role separation, but uses the current Google GenAI SDK and configurable model IDs. The defaults are `gemini-2.5-pro` for structured workout generation/updates and `gemini-2.5-flash` for fast nutrition/recovery tips.

The document describes `<pre>` output; this version presents the same data as responsive workout-day cards for a more usable frontend.

FitBuddy is general fitness support, not medical diagnosis or treatment.
