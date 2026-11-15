import json
import logging
import uuid
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Request, Response, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config import (
    APP_NAME,
    HOST,
    PORT,
    BASE_PATH,
    GEMINI_API_KEY,
    DEFAULT_GEMINI_MODEL,
    FAST_GEMINI_MODEL,
    PREVIEW_GEMINI_MODEL,
    STATIC_DIR,
)
from app.auth import (
    verify_password,
    create_access_token,
    verify_token,
    get_current_user,
    is_authenticated,
    COOKIE_NAME,
)
from app.skills import catalog
from app.resumes_data import (
    RESUME_TRACKS,
    CANDIDATE_PROFILE,
    build_resume_system_prompt,
)
from app.db import (
    init_db,
    create_session,
    get_session,
    list_sessions,
    update_session_phase,
    delete_session,
    add_message,
    get_messages,
    save_evaluation,
    get_evaluation,
)
from app.gemini import (
    SUPPORTED_MODELS,
    resolve_api_key,
    validate_gemini_key,
    stream_gemini_response,
    generate_gemini_response,
    generate_scorecard,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("interview_mentor")

# Initialize database
init_db()

app = FastAPI(
    title=APP_NAME,
    description="Interactive Technical Interview Preparation Platform powered by Google Gemini",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Models
class LoginRequest(BaseModel):
    password: str

class StartSessionRequest(BaseModel):
    skill_id: str
    model: Optional[str] = DEFAULT_GEMINI_MODEL
    custom_key: Optional[str] = None
    custom_instructions: Optional[str] = None

class StartResumeMockRequest(BaseModel):
    mode: Optional[str] = "full"  # 'full', 'grill', 'system_design', 'coding', 'behavioral'
    model: Optional[str] = DEFAULT_GEMINI_MODEL
    custom_key: Optional[str] = None
    custom_instructions: Optional[str] = None

class SendMessageRequest(BaseModel):
    content: str
    model: Optional[str] = None
    custom_key: Optional[str] = None
    action_type: Optional[str] = "chat"

class HintRequest(BaseModel):
    level: int = 1
    model: Optional[str] = None
    custom_key: Optional[str] = None

class AdvancePhaseRequest(BaseModel):
    phase: str
    model: Optional[str] = None
    custom_key: Optional[str] = None

class TestKeyRequest(BaseModel):
    api_key: str


# Helper for serving HTML files
def serve_html(filename: str):
    file_path = STATIC_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File {filename} not found")
    with open(file_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


# Helper to resolve skill or resume track context
def get_session_context(session: dict, custom_instructions: Optional[str] = None):
    skill_id = session.get("skill_id", "")
    if skill_id.startswith("resume_"):
        track_id = skill_id.replace("resume_", "")
        track = RESUME_TRACKS.get(track_id)
        if not track:
            return None, None
        skill = {
            "id": skill_id,
            "title": f"{track['title']} ({track['code']})",
            "role": track["target_roles"][0],
            "difficulty": "Senior / Staff Bar Raiser",
            "topic": track["subtitle"],
            "category": track["category"],
            "is_resume_track": True,
            "body_content": (
                f"Track: {track['title']}\n"
                f"Specialization: {track['subtitle']}\n\n"
                f"Work Experience Bullets:\n" + "\n".join(track["experience_bullets"]) + "\n\n"
                f"Key Metrics & Scale:\n" + "\n".join(track["key_metrics"]) + "\n\n"
                f"Core Tech Stack:\n" + ", ".join(track["core_stack"])
            )
        }
        mode = "full"
        title_lower = session.get("title", "").lower()
        if "grill" in title_lower:
            mode = "grill"
        elif "design" in title_lower:
            mode = "system_design"
        elif "coding" in title_lower or "algo" in title_lower:
            mode = "coding"
        elif "behavioral" in title_lower:
            mode = "behavioral"
        system_prompt = build_resume_system_prompt(track_id, mode=mode, custom_instructions=custom_instructions)
        return skill, system_prompt
    else:
        skill = catalog.get_skill(skill_id)
        if not skill:
            return None, None
        system_prompt = catalog.build_system_prompt(skill_id, custom_instructions=custom_instructions)
        return skill, system_prompt


# Setup API Router
from fastapi import APIRouter
router = APIRouter()

# --- Auth Endpoints ---

@router.post("/api/auth/login")
async def login(req: LoginRequest, response: Response):
    if not verify_password(req.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password. Access denied.",
        )
    token = create_access_token({"sub": "ashish", "role": "owner"})
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=30 * 24 * 3600,
        httponly=True,
        samesite="lax",
        path="/",
    )
    return {"success": True, "token": token, "message": "Authentication successful"}


@router.post("/api/auth/logout")
async def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")
    response.delete_cookie(COOKIE_NAME, path="/interview")
    return {"success": True, "message": "Logged out"}


@router.get("/api/auth/verify")
async def verify_auth(request: Request):
    auth = is_authenticated(request)
    return {"authenticated": auth}


# --- System & Model Endpoints ---

@router.get("/api/system/models")
async def get_models(user=Depends(get_current_user)):
    return {
        "models": [
            {"id": k, "name": v, "is_default": k == DEFAULT_GEMINI_MODEL}
            for k, v in SUPPORTED_MODELS.items()
        ],
        "default_model": DEFAULT_GEMINI_MODEL,
        "fast_model": FAST_GEMINI_MODEL,
        "preview_model": PREVIEW_GEMINI_MODEL,
    }


@router.get("/api/system/status")
async def get_system_status(user=Depends(get_current_user)):
    key_configured = bool(GEMINI_API_KEY and len(GEMINI_API_KEY) > 10)
    key_masked = f"{GEMINI_API_KEY[:6]}...{GEMINI_API_KEY[-4:]}" if key_configured else "Not Configured"
    return {
        "status": "online",
        "app_name": APP_NAME,
        "candidate": CANDIDATE_PROFILE["name"],
        "gemini_api_ready": key_configured,
        "default_key_masked": key_masked,
        "total_skills": len(catalog.skills),
        "total_categories": len(catalog.get_categories()),
        "total_resume_tracks": len(RESUME_TRACKS),
    }


@router.post("/api/system/test-key")
async def test_gemini_key(req: TestKeyRequest, user=Depends(get_current_user)):
    api_key_to_test = req.api_key.strip() if req.api_key else ""
    if not api_key_to_test or api_key_to_test == "server_default":
        api_key_to_test = GEMINI_API_KEY
    if not validate_gemini_key(api_key_to_test):
        return {"valid": False, "message": "Key does not match valid Google Gemini format."}
    try:
        test_res = await generate_gemini_response(
            messages=[{"role": "user", "content": "Ping"}],
            system_instruction="Reply with 'PONG'",
            model=FAST_GEMINI_MODEL,
            custom_key=api_key_to_test,
        )
        return {"valid": True, "message": "Gemini API key is active and responding!", "reply": test_res.strip()}
    except Exception as e:
        return {"valid": False, "message": f"Connection failed: {str(e)}"}


# --- Resume Tracks Endpoints (10 Tracks: 4 Java, 6 Python) ---

@router.get("/api/resumes")
async def get_resume_tracks(user=Depends(get_current_user)):
    java_tracks = [v for v in RESUME_TRACKS.values() if v["category"] == "java"]
    python_tracks = [v for v in RESUME_TRACKS.values() if v["category"] == "python"]
    return {
        "candidate": CANDIDATE_PROFILE,
        "summary": {
            "total_tracks": len(RESUME_TRACKS),
            "java_count": len(java_tracks),
            "python_count": len(python_tracks),
        },
        "java_tracks": java_tracks,
        "python_tracks": python_tracks,
        "all_tracks": list(RESUME_TRACKS.values()),
    }


@router.get("/api/resumes/{track_id}")
async def get_single_resume_track(track_id: str, user=Depends(get_current_user)):
    track = RESUME_TRACKS.get(track_id.upper())
    if not track:
        raise HTTPException(status_code=404, detail=f"Resume track '{track_id}' not found")
    return {
        "track": track,
        "candidate": CANDIDATE_PROFILE,
    }


@router.post("/api/resumes/{track_id}/mock")
async def start_resume_mock(
    track_id: str,
    req: StartResumeMockRequest,
    user=Depends(get_current_user),
):
    track = RESUME_TRACKS.get(track_id.upper())
    if not track:
        raise HTTPException(status_code=404, detail=f"Resume track '{track_id}' not found")

    session_id = str(uuid.uuid4())
    model = req.model if req.model in SUPPORTED_MODELS else DEFAULT_GEMINI_MODEL
    mode_titles = {
        "full": f"Full Mock: {track['title']} ({track['code']})",
        "grill": f"🔥 Grill My Resume: {track['title']} ({track['code']})",
        "system_design": f"System Design: {track['title']} ({track['code']})",
        "coding": f"Coding / Algo: {track['title']} ({track['code']})",
        "behavioral": f"Leadership / STAR: {track['title']} ({track['code']})",
    }
    session_title = mode_titles.get(req.mode, f"{track['title']} ({track['code']}) Mock")

    session = create_session(
        session_id=session_id,
        skill_id=f"resume_{track['id']}",
        skill_title=session_title,
        category=track["category"],
        title=session_title,
        model=model,
    )

    system_prompt = build_resume_system_prompt(track["id"], mode=req.mode or "full", custom_instructions=req.custom_instructions)

    opening_instructions = {
        "full": (
            "Start the interview in your persona. Greet Ashish warmly, establish yourself as the senior technical interviewer, "
            f"state that we are evaluating for {track['target_roles'][0]}, and ask him to kick things off with a crisp overview "
            "of his engineering journey and current responsibilities at Airtel International."
        ),
        "grill": (
            "You are a sharp, skeptical FAANG Bar Raiser. Open directly without pleasantries: "
            f"State that you've reviewed his resume for {track['title']}, pick his most prominent claim "
            f"({track['key_metrics'][0]}), and directly challenge him on how that architecture was designed, "
            "how the metrics were verified in production, and what failure modes he encountered."
        ),
        "system_design": (
            f"Start the System Design round for {track['title']}. Present a real-world, high-concurrency architecture problem "
            f"closely related to {track['subtitle']}. Ask him to start with requirements and scale estimates."
        ),
        "coding": (
            f"Start a live coding challenge calibrated to {track['title']}. Present a clear algorithmic or concurrency problem "
            "(LeetCode Medium to Hard level). Ask for time and space complexity before he begins writing code."
        ),
        "behavioral": (
            f"Start a Senior Engineer behavioral interview for {track['title']}. Ask a challenging question regarding "
            "an architectural disagreement, a high-severity production outage, or prioritizing technical debt over business timelines."
        )
    }

    opening_prompt = opening_instructions.get(req.mode or "full", opening_instructions["full"])

    try:
        opening_response = await generate_gemini_response(
            messages=[{"role": "user", "content": opening_prompt}],
            system_instruction=system_prompt,
            model=model,
            custom_key=req.custom_key,
            temperature=0.7,
        )
    except Exception as e:
        logger.error(f"Failed to generate resume mock opening: {e}")
        opening_response = (
            f"Hello Ashish. I'm your interviewer for the {track['title']} ({track['code']}) loop. "
            f"We'll be diving deep into your experience in {track['subtitle']}. "
            f"To get started, tell me about the architecture behind {track['key_metrics'][0]}."
        )

    initial_msg = add_message(session_id, role="model", content=opening_response, action_type="intro")

    return {
        "session": session,
        "track": track,
        "initial_message": initial_msg,
    }


# --- Domain Skill Catalog Endpoints (45 General Skills) ---

@router.get("/api/categories")
async def get_categories(user=Depends(get_current_user)):
    return catalog.get_categories()


@router.get("/api/skills")
async def list_skills(
    category: Optional[str] = None,
    search: Optional[str] = None,
    user=Depends(get_current_user),
):
    skills = catalog.list_skills(category=category, search=search)
    return skills


@router.get("/api/skills/{skill_id}")
async def get_skill_detail(skill_id: str, user=Depends(get_current_user)):
    skill = catalog.get_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


# --- Interview Session Endpoints ---

@router.get("/api/sessions")
async def get_sessions(user=Depends(get_current_user)):
    return list_sessions()


@router.post("/api/sessions")
async def start_session(req: StartSessionRequest, user=Depends(get_current_user)):
    skill = catalog.get_skill(req.skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{req.skill_id}' not found")

    session_id = str(uuid.uuid4())
    model = req.model if req.model in SUPPORTED_MODELS else DEFAULT_GEMINI_MODEL
    session_title = f"{skill['title']} Mock Interview"

    session = create_session(
        session_id=session_id,
        skill_id=skill["id"],
        skill_title=skill["title"],
        category=skill["category"],
        title=session_title,
        model=model,
    )

    system_prompt = catalog.build_system_prompt(req.skill_id, req.custom_instructions)
    opening_instruction = (
        "Candidate has just joined the room. As per your Activation rules, start the interview now with your "
        "persona greeting and the first question for Phase 1. Keep it clear, realistic, and direct."
    )

    try:
        opening_response = await generate_gemini_response(
            messages=[{"role": "user", "content": opening_instruction}],
            system_instruction=system_prompt,
            model=model,
            custom_key=req.custom_key,
            temperature=0.7,
        )
    except Exception as e:
        logger.error(f"Failed to generate opening question: {e}")
        opening_response = (
            f"Hello! I am your interviewer for today's {skill['title']} session. "
            f"We will focus on {skill['topic']} for the {skill['role']} role. "
            f"Let's dive into Phase 1: To kick things off, can you tell me how you approach this problem space?"
        )

    initial_msg = add_message(session_id, role="model", content=opening_response, action_type="intro")

    return {
        "session": session,
        "initial_message": initial_msg,
    }


@router.get("/api/sessions/{session_id}")
async def get_session_details(session_id: str, user=Depends(get_current_user)):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = get_messages(session_id)
    evaluation = get_evaluation(session_id)
    skill, _ = get_session_context(session)
    return {
        "session": session,
        "skill": skill,
        "messages": messages,
        "evaluation": evaluation,
    }


@router.delete("/api/sessions/{session_id}")
async def remove_session(session_id: str, user=Depends(get_current_user)):
    delete_session(session_id)
    return {"success": True, "message": "Session deleted"}


@router.post("/api/sessions/{session_id}/message")
async def send_message_endpoint(
    session_id: str,
    req: SendMessageRequest,
    user=Depends(get_current_user),
):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    skill, system_prompt = get_session_context(session)
    if not skill or not system_prompt:
        raise HTTPException(status_code=404, detail="Associated skill or track not found")

    # Record user message
    user_msg = add_message(session_id, role="user", content=req.content, action_type=req.action_type or "chat")

    # Get conversation history
    history = get_messages(session_id)
    formatted_history = [{"role": m["role"], "content": m["content"]} for m in history]

    model = req.model or session.get("model") or DEFAULT_GEMINI_MODEL

    async def event_generator():
        collected_text = []
        try:
            async for sse_chunk in stream_gemini_response(
                messages=formatted_history,
                system_instruction=system_prompt,
                model=model,
                custom_key=req.custom_key,
                temperature=0.7,
            ):
                if sse_chunk.startswith("data: "):
                    try:
                        data = json.loads(sse_chunk[6:])
                        if "text" in data:
                            collected_text.append(data["text"])
                    except Exception:
                        pass
                yield sse_chunk

            full_reply = "".join(collected_text).strip()
            if full_reply:
                add_message(session_id, role="model", content=full_reply, action_type="chat")
        except Exception as e:
            logger.exception("Error in streaming response")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/api/sessions/{session_id}/hint")
async def request_hint(
    session_id: str,
    req: HintRequest,
    user=Depends(get_current_user),
):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    skill, system_prompt = get_session_context(session)
    if not skill or not system_prompt:
        raise HTTPException(status_code=404, detail="Skill context not found")

    level_names = {
        1: "Level 1 (Nudge / High-level direction)",
        2: "Level 2 (Directional / Algorithmic pattern)",
        3: "Level 3 (Structural / Pseudocode / Key insight)",
        4: "Level 4 (Code Sketch / Solution blueprint)",
    }
    level_name = level_names.get(req.level, f"Level {req.level}")

    hint_prompt = (
        f"[CANDIDATE REQUESTED HINT: {level_name}]\n"
        f"Please provide ONLY a {level_name} hint according to progressive interview mentoring standards. "
        f"Do not give away the entire solution unless it is Level 4. Encourage the candidate to build upon it."
    )

    user_msg = add_message(session_id, role="user", content=f"💡 [Requested {level_name} Hint]", action_type="hint")

    history = get_messages(session_id)
    formatted_history = [{"role": m["role"], "content": m["content"]} for m in history[:-1]]
    formatted_history.append({"role": "user", "content": hint_prompt})

    model = req.model or session.get("model") or FAST_GEMINI_MODEL

    async def event_generator():
        collected_text = []
        try:
            async for sse_chunk in stream_gemini_response(
                messages=formatted_history,
                system_instruction=system_prompt,
                model=model,
                custom_key=req.custom_key,
                temperature=0.5,
            ):
                if sse_chunk.startswith("data: "):
                    try:
                        data = json.loads(sse_chunk[6:])
                        if "text" in data:
                            collected_text.append(data["text"])
                    except Exception:
                        pass
                yield sse_chunk

            full_reply = "".join(collected_text).strip()
            if full_reply:
                add_message(session_id, role="model", content=full_reply, action_type="hint")
        except Exception as e:
            logger.exception("Error in hint stream")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/api/sessions/{session_id}/diagram")
async def request_diagram(
    session_id: str,
    req: SendMessageRequest,
    user=Depends(get_current_user),
):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    skill, system_prompt = get_session_context(session)
    if not skill or not system_prompt:
        raise HTTPException(status_code=404, detail="Skill context not found")

    diagram_prompt = (
        "[CANDIDATE REQUESTED VISUAL / ASCII ARCHITECTURE DIAGRAM]\n"
        "Provide a clear, beautifully structured ASCII diagram or flowchart illustrating the component architecture, "
        "data flow, or algorithmic pointer layout discussed so far. Follow with a 2-3 sentence explanation."
    )

    add_message(session_id, role="user", content="📐 [Requested Architecture / ASCII Diagram]", action_type="diagram")

    history = get_messages(session_id)
    formatted_history = [{"role": m["role"], "content": m["content"]} for m in history[:-1]]
    formatted_history.append({"role": "user", "content": diagram_prompt})

    model = req.model or session.get("model") or DEFAULT_GEMINI_MODEL

    async def event_generator():
        collected_text = []
        try:
            async for sse_chunk in stream_gemini_response(
                messages=formatted_history,
                system_instruction=system_prompt,
                model=model,
                custom_key=req.custom_key,
                temperature=0.4,
            ):
                if sse_chunk.startswith("data: "):
                    try:
                        data = json.loads(sse_chunk[6:])
                        if "text" in data:
                            collected_text.append(data["text"])
                    except Exception:
                        pass
                yield sse_chunk

            full_reply = "".join(collected_text).strip()
            if full_reply:
                add_message(session_id, role="model", content=full_reply, action_type="diagram")
        except Exception as e:
            logger.exception("Error in diagram stream")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/api/sessions/{session_id}/advance")
async def advance_phase_endpoint(
    session_id: str,
    req: AdvancePhaseRequest,
    user=Depends(get_current_user),
):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    skill, system_prompt = get_session_context(session)
    if not skill or not system_prompt:
        raise HTTPException(status_code=404, detail="Skill context not found")

    update_session_phase(session_id, req.phase)

    advance_prompt = (
        f"[ADVANCING INTERVIEW TO: {req.phase}]\n"
        f"Acknowledge the transition into {req.phase}. Present the next core challenge, deep dive, or scenario "
        f"consistent with your interview structure. Stay in persona."
    )

    add_message(session_id, role="user", content=f"⏭️ [Advanced to {req.phase}]", action_type="advance")

    history = get_messages(session_id)
    formatted_history = [{"role": m["role"], "content": m["content"]} for m in history[:-1]]
    formatted_history.append({"role": "user", "content": advance_prompt})

    model = req.model or session.get("model") or DEFAULT_GEMINI_MODEL

    async def event_generator():
        collected_text = []
        try:
            async for sse_chunk in stream_gemini_response(
                messages=formatted_history,
                system_instruction=system_prompt,
                model=model,
                custom_key=req.custom_key,
                temperature=0.7,
            ):
                if sse_chunk.startswith("data: "):
                    try:
                        data = json.loads(sse_chunk[6:])
                        if "text" in data:
                            collected_text.append(data["text"])
                    except Exception:
                        pass
                yield sse_chunk

            full_reply = "".join(collected_text).strip()
            if full_reply:
                add_message(session_id, role="model", content=full_reply, action_type="advance")
        except Exception as e:
            logger.exception("Error in advance stream")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/api/sessions/{session_id}/evaluate")
async def evaluate_interview(
    session_id: str,
    req: SendMessageRequest,
    user=Depends(get_current_user),
):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    skill, _ = get_session_context(session)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill context not found")
    history = get_messages(session_id)

    if len(history) < 2:
        raise HTTPException(status_code=400, detail="Cannot evaluate an empty interview. Please have a conversation first.")

    try:
        eval_data = await generate_scorecard(skill, history, custom_key=req.custom_key)
        score = eval_data.get("score", 75)
        recommendation = eval_data.get("recommendation", "Hire")
        summary = eval_data.get("summary", "Evaluation complete.")

        save_evaluation(
            session_id=session_id,
            score=score,
            recommendation=recommendation,
            rubric_json=eval_data,
            feedback_markdown=summary,
        )

        scorecard_msg = (
            f"### 🏆 Final Interview Evaluation Scorecard\n\n"
            f"**Overall Score:** `{score}/100` | **Hiring Decision:** `{recommendation}`\n\n"
            f"{summary}\n\n"
            f"**Top Strengths:**\n" + "\n".join(f"- {s}" for s in eval_data.get("strengths", [])) + "\n\n"
            f"**Areas for Improvement:**\n" + "\n".join(f"- {a}" for a in eval_data.get("areas_for_growth", []))
        )
        add_message(session_id, role="model", content=scorecard_msg, action_type="evaluate")

        return {"success": True, "evaluation": eval_data}
    except Exception as e:
        logger.exception("Failed to generate scorecard")
        raise HTTPException(status_code=500, detail=f"Scorecard generation error: {str(e)}")


# --- UI Page Routes ---

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if is_authenticated(request):
        return RedirectResponse(url=f"{BASE_PATH}/", status_code=302)
    return serve_html("login.html")


@router.get("/", response_class=HTMLResponse)
async def index_page(request: Request):
    if not is_authenticated(request):
        return RedirectResponse(url=f"{BASE_PATH}/login", status_code=302)
    return serve_html("index.html")


# Mount router under /interview AND under root /
app.include_router(router, prefix=BASE_PATH)
app.include_router(router, prefix="")

# Mount static files
app.mount(f"{BASE_PATH}/static", StaticFiles(directory=str(STATIC_DIR)), name="static_prefixed")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static_root")
